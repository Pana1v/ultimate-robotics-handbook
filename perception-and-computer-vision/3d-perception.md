---
icon: eye
---

# 3D Scene Understanding

Most robots have to reason about 3D space, not just pixels. The space of "how to represent the world in 3D" has changed dramatically - five years ago it was meshes, voxels, and point clouds. Today NeRFs and 3D Gaussian Splats are real engineering options, and monocular depth from foundation models is shockingly usable. But classical 3D (point clouds, TSDFs, occupancy grids) still owns production robotics.

This page is about how to choose between them and what each one actually does well.

### 1. The landscape

There are five practical 3D representations for robotics:

| Representation               | What it stores                                  | Typical sensor      | Good for                                 |
| ---------------------------- | ----------------------------------------------- | ------------------- | ---------------------------------------- |
| Point cloud                  | Unordered (x, y, z) + optional intensity/color  | LiDAR, depth camera | Geometry, obstacle detection, ICP        |
| Voxel grid / occupancy grid  | 3D grid of occupied/free/unknown cells          | Any depth source    | Planning, mapping                        |
| TSDF (truncated signed distance field) | Volumetric implicit surface              | Depth camera        | Dense reconstruction, mesh extraction    |
| NeRF (neural radiance field) | MLP that maps (x, y, z, view dir) → (color, density) | Posed images    | Novel view synthesis, photorealism       |
| 3D Gaussian Splatting        | Set of 3D Gaussians (mean, cov, color, opacity) | Posed images        | Fast novel view, real-time rendering     |

Classical robotics owns the top three. The bottom two are eating into reconstruction and SLAM. Each is good at different things; the right answer is almost always "use both, for different parts of the pipeline."

### 2. Point clouds and PCL/Open3D

A point cloud is just (x, y, z) points - sometimes with color or intensity. It's the universal language of 3D sensors: LiDARs, depth cameras, stereo rigs all output point clouds.

#### 2.1 Point Cloud Library (PCL)

[PCL](https://pointclouds.org/) is the C++ workhorse of point cloud processing. Filters, segmentation, registration (ICP), feature extraction (FPFH, SHOT), surface reconstruction. Old, big, and somewhat clunky to build - but it's what's already in ROS, what `pcl_ros` wraps, and what most production robotics code uses.

* Repo: [github.com/PointCloudLibrary/pcl](https://github.com/PointCloudLibrary/pcl)
* Tutorials: [pcl.readthedocs.io](https://pcl.readthedocs.io/) `[verify]`

Common operations every robotics engineer will write at some point:

* **Voxel grid downsampling** - `pcl::VoxelGrid` to reduce point density before any expensive op.
* **Statistical / radius outlier removal** - clean LiDAR noise before SLAM or registration.
* **RANSAC plane / cylinder fitting** - extract the floor, walls, pipes.
* **Euclidean clustering** - split a point cloud into object-like blobs.
* **ICP / GICP / NDT** - register two clouds (frame-to-frame or frame-to-map).
* **Normal estimation + FPFH** - features for global registration.

A general performance note: PCL is templated heavily on point type. Pick `pcl::PointXYZ` or `pcl::PointXYZI` and stick with it; `PointXYZRGB` doubles your memory footprint for no reason if you're not using color.

#### 2.2 Open3D

[Open3D](https://www.open3d.org/) is the modern, Python-first alternative. Better visualization, cleaner API, GPU-accelerated tensor operations, and a much more pleasant development loop than PCL.

* Repo: [github.com/isl-org/Open3D](https://github.com/isl-org/Open3D)

I default to Open3D for prototyping and PCL for production C++ ROS 2 nodes. Open3D's tensor backend (`open3d.t.geometry.PointCloud`) gets close to PCL performance for many operations and lets you keep data on GPU.

| When to use         | PCL                              | Open3D                                  |
| ------------------- | -------------------------------- | --------------------------------------- |
| ROS 2 C++ node      | Yes - `pcl_ros` integration      | Possible but painful                    |
| Python research     | Awkward bindings                 | Yes - first-class Python                |
| GPU acceleration    | Limited                          | Tensor API + CUDA                       |
| Production deploy   | Battle-tested                    | Improving but younger                   |
| Visualization       | Crusty (PCLVisualizer)           | Modern (Open3D viewer)                  |

### 3. Monocular depth - MiDaS and Depth Anything

Sometimes you don't have a depth sensor. Sometimes your depth sensor doesn't work outdoors, or in glare, or on transparent objects. Monocular depth from a foundation model is now good enough to be useful as a primary or backup signal.

* **MiDaS** (Intel ISL) - the classic. Relative depth, multiple model sizes. [github.com/isl-org/MiDaS](https://github.com/isl-org/MiDaS)
* **Depth Anything v2** (HKU + TikTok, 2024) - current state of the art for monocular relative depth. [github.com/DepthAnything/Depth-Anything-V2](https://github.com/DepthAnything/Depth-Anything-V2)
* **UniDepth** - metric monocular depth without test-time scaling. [arxiv.org/abs/2403.18913](https://arxiv.org/abs/2403.18913) `[verify]`
* **Marigold** - diffusion-based, beautiful but slow. [arxiv.org/abs/2312.02145](https://arxiv.org/abs/2312.02145)

Full discussion of these models, latency, and integration is in [foundation-vision-models.md](foundation-vision-models.md). For 3D perception purposes the question is **how to use monocular depth**:

* **Relative depth → don't trust the scale.** Without metric calibration, your "depth" is up to an unknown affine. Don't compute distances from it.
* **Fuse with sparse metric signal.** A few LiDAR points or an IMU-gravity scale solver can anchor monocular depth to metric. This is the practical pattern.
* **Use it for completeness, not accuracy.** Depth Anything fills in transparent/reflective surfaces where stereo/LiDAR fail. Use it as a complement to a sensor, not a replacement.

### 4. NeRF (Neural Radiance Fields)

**NeRF** (Mildenhall et al., ECCV 2020) trains an MLP to map a 3D point and viewing direction to a color and density. Render by ray-marching through the MLP. The result is photorealistic novel-view synthesis from a set of posed images.

* Paper: [arxiv.org/abs/2003.08934](https://arxiv.org/abs/2003.08934)
* Original code: [github.com/bmild/nerf](https://github.com/bmild/nerf)

**What changed:** vanilla NeRF takes hours to train and seconds to render a frame - useless for robotics. Then **Instant-NGP** happened.

#### 4.1 Instant-NGP

**Instant-NGP** (NVIDIA, SIGGRAPH 2022) replaces the giant MLP with a multi-resolution hash grid + tiny MLP. Trains in seconds to minutes, renders in real time.

* Paper: [arxiv.org/abs/2201.05989](https://arxiv.org/abs/2201.05989)
* Code: [github.com/NVlabs/instant-ngp](https://github.com/NVlabs/instant-ngp)

This is what made NeRF a real engineering option. The hash grid trick (multi-resolution feature grids indexed by spatial hashing) is one of those ideas that's both elegant and obviously practical.

#### 4.2 nerfstudio

For robotics, the practical toolkit is **nerfstudio** - a modular framework supporting many NeRF variants, exporters to point clouds/meshes, and an actually-usable viewer.

* Site: [nerf.studio](https://nerf.studio)
* Repo: [github.com/nerfstudio-project/nerfstudio](https://github.com/nerfstudio-project/nerfstudio)

Useful variants in nerfstudio: **Nerfacto** (their default, balanced), **Splatfacto** (Gaussian Splatting in the same framework), **Instant-NGP** integration.

#### 4.3 NeRF in robotics

Where NeRF (and especially its Gaussian-Splat cousin below) has made it into real robotics:

* **High-fidelity environment scanning** for simulation / digital twins.
* **Asset capture** for pick-and-place training (capture once, render thousands of training views).
* **Localization** - render a candidate view from the NeRF and match to a real image to refine pose.
* **Sim-to-real** - render photorealistic synthetic data for policy training.

Where it has *not* made it: live SLAM on a moving robot, on-board obstacle avoidance, anything requiring sub-second updates from raw sensor data. The cost-to-quality ratio just isn't there yet for fast-moving robotics. NeRF is mostly an offline / staged tool.

### 5. 3D Gaussian Splatting

**3D Gaussian Splatting** (Kerbl et al., SIGGRAPH 2023) replaces the implicit MLP of NeRF with an explicit set of anisotropic 3D Gaussians. Each Gaussian has a mean (position), covariance (shape/size/orientation), color (spherical harmonics), and opacity. Rendering is a differentiable rasterization of these splats into the camera's image plane.

* Paper: [arxiv.org/abs/2308.04079](https://arxiv.org/abs/2308.04079)
* Code: [github.com/graphdeco-inria/gaussian-splatting](https://github.com/graphdeco-inria/gaussian-splatting)

**Why it's eating NeRF's lunch:**

1. **Real-time rendering** at 100+ FPS on a desktop GPU.
2. **Faster training** than vanilla NeRF, comparable to Instant-NGP.
3. **Explicit representation** - you can edit, prune, transform, merge scenes.
4. **Differentiable through the whole pipeline** - gradients flow into the splat parameters cleanly.

The trade-off: it can produce floaters and surface-quality issues that NeRF handles better, and storage size scales with the number of Gaussians (often 100k-10M of them).

#### 5.1 SplaTAM and Gaussian Splatting SLAM

The interesting robotics application: SLAM that builds a 3D Gaussian Splat map online.

* **SplaTAM** (CMU, CVPR 2024) - Gaussian Splatting for RGB-D SLAM. Builds a map of 3D Gaussians, tracks camera against it. [arxiv.org/abs/2312.02126](https://arxiv.org/abs/2312.02126), code: [github.com/spla-tam/SplaTAM](https://github.com/spla-tam/SplaTAM)
* **Gaussian Splatting SLAM (MonoGS)** (Imperial College, CVPR 2024) - does it from monocular RGB. [arxiv.org/abs/2312.06741](https://arxiv.org/abs/2312.06741), code: [github.com/muskie82/MonoGS](https://github.com/muskie82/MonoGS)
* **GS-ICP SLAM** - combines Gaussian splats with ICP-based tracking. `[verify]`
* **Photo-SLAM** - photorealistic SLAM using Gaussian splatting. [arxiv.org/abs/2311.16728](https://arxiv.org/abs/2311.16728) `[verify]`

These systems run at single-digit-to-low-tens of FPS on a desktop GPU. On a Jetson Orin they're not real-time yet, but they're the direction the field is moving. If you're starting a new dense reconstruction project in 2026, you should at least evaluate splat-based SLAM.

#### 5.2 Gaussian Splatting variants worth knowing

* **2D Gaussian Splatting** - surface-aligned 2D Gaussians for better mesh extraction. [arxiv.org/abs/2403.17888](https://arxiv.org/abs/2403.17888)
* **SuGaR** - surface-aligned regularization on top of 3DGS, much cleaner meshes. [arxiv.org/abs/2311.12775](https://arxiv.org/abs/2311.12775)
* **Mip-Splatting** - fixes aliasing at varying scales. [arxiv.org/abs/2311.16493](https://arxiv.org/abs/2311.16493) `[verify]`
* **4D Gaussian Splatting** - adds time, for dynamic scenes. `[verify]`
* **Scaffold-GS** - structured Gaussians around an anchor grid, more compact. [arxiv.org/abs/2312.00109](https://arxiv.org/abs/2312.00109) `[verify]`

### 6. NeRF vs Gaussian Splatting vs traditional 3D reconstruction

The actual decision table for picking a 3D representation:

| Use case                                  | Best fit                                     | Why                                          |
| ----------------------------------------- | -------------------------------------------- | -------------------------------------------- |
| Live obstacle avoidance                   | Point cloud + voxel/occupancy grid           | Sub-ms queries, deterministic                |
| Path planning                             | Voxel grid / OctoMap                         | Fast collision checks                        |
| Dense indoor reconstruction (offline)     | TSDF (e.g., KinectFusion, Open3D)            | Clean meshes, well-understood                |
| Photorealistic scene capture for sim      | 3D Gaussian Splatting (or NeRF)              | Photorealism, novel views                    |
| High-quality novel view synthesis         | NeRF or 3DGS                                 | NeRF slightly cleaner, 3DGS faster           |
| Online dense SLAM                         | TSDF or Gaussian Splatting SLAM              | TSDF mature, GS-SLAM emerging                |
| Object pose estimation (known objects)    | Mesh + ICP / FoundationPose                  | Strong priors win                            |
| Localization in a pre-built map           | Point cloud (LiDAR) or learned features      | Robust, well-tooled                          |
| Open-set semantic 3D understanding        | Point cloud + CLIP-distilled features        | E.g., OpenScene, LERF                        |

A few opinionated takes:

* **Don't put a NeRF on a moving robot for SLAM in 2026.** The latency-quality trade isn't there yet. Use Gaussian Splatting if you must, or stick with classical RGB-D SLAM.
* **Splat-based SLAM is the medium-term winner** for dense mapping. The trajectory of speed improvements over 2023-2025 has been steep.
* **Point clouds aren't going anywhere.** They're the lingua franca of LiDAR robotics and will be for at least another decade. Get fluent in PCL and Open3D.
* **TSDFs are still the right answer** for many bounded indoor reconstruction problems. Boring, but mature.

### 7. Inference cost on Jetson Orin / desktop GPU

| Operation                               | RTX 4090       | Jetson Orin NX | Notes                                        |
| --------------------------------------- | -------------- | -------------- | -------------------------------------------- |
| Open3D voxel downsample 100k pts        | ~1-3 ms        | ~10-30 ms      | CPU-bound `[verify]`                         |
| PCL GICP (10k → 10k)                    | ~50-200 ms     | ~200-800 ms    | CPU `[verify]`                               |
| Depth Anything v2 Small @ 518²          | ~12 ms         | ~70 ms         | FP16 TensorRT `[verify]`                     |
| Instant-NGP training (typical scene)    | 1-5 min        | impractical    | Use desktop offline `[verify]`               |
| Instant-NGP rendering @ 1080p           | 30-60 FPS      | 1-3 FPS        | `[verify]`                                   |
| Gaussian Splatting training (1M splats) | 10-30 min      | impractical    | `[verify]`                                   |
| Gaussian Splatting rendering @ 1080p    | 100-300 FPS    | 5-15 FPS       | `[verify]`                                   |
| SplaTAM tracking                        | ~3-8 FPS       | sub-1 FPS      | RGB-D, depends on map size `[verify]`        |
| MonoGS tracking                         | ~3-10 FPS      | sub-1 FPS      | Monocular `[verify]`                         |

**Reality check**: most NeRF/3DGS work today still happens on desktop or workstation GPUs. The "deploy on Jetson" story for splat-based methods is improving but not mature. If your robot has a thin GPU (Orin Nano), you're going to want a classical 3D stack and treat NeRF/3DGS as offline / ground-station tools.

### 8. Pipeline patterns that actually ship

#### 8.1 Classical RGB-D perception pipeline

```
RGB-D camera → cv_bridge → point cloud (organized) → voxel grid downsample
   → statistical outlier removal → RANSAC ground plane segmentation
   → Euclidean clustering → per-cluster bounding box + centroid
```

This is what 90% of mobile manipulators are running for object detection in 2026. Boring, fast, reliable.

#### 8.2 Foundation-model augmented pipeline

```
RGB → Grounding DINO (offline) → labels per frame
RGB → Depth Anything v2 → relative depth (live, low rate)
RGB-D (depth from camera) → metric depth (live, high rate)
   → fuse relative depth + sparse metric depth for completion
   → point cloud → classical processing as above
```

Use the foundation model where the sensor is weak (transparent surfaces, dark areas) and trust the sensor where it's strong.

#### 8.3 Scene capture for sim training

```
Camera trajectory around scene → COLMAP for poses
   → nerfstudio (Splatfacto) → trained 3DGS
   → render N novel views at various poses → training data for policy
```

Used heavily in 2024-2025 work on sim-to-real for manipulation.

### 9. Coordinate frames and a recurring footgun

Everything in 3D perception has a coordinate frame. Mix them up and your robot drives into walls. The two patterns to be religious about:

* **Always publish your point clouds in a known TF frame.** `sensor_msgs/PointCloud2.header.frame_id` matters. If a downstream node has to guess, it'll be wrong.
* **OpenCV / image conventions vs ROS / right-hand world conventions are different.** OpenCV: x right, y down, z forward. ROS REP-103: x forward, y left, z up. NeRF/3DGS code is typically OpenCV-style. Convert at the boundary.
* **NeRF training expects camera-to-world poses**, but COLMAP exports world-to-camera. Read the conversion code carefully.

### 10. Further reading and references

* PCL tutorials: [pcl.readthedocs.io](https://pcl.readthedocs.io/) `[verify]`
* Open3D docs: [www.open3d.org/docs](https://www.open3d.org/docs/)
* nerfstudio docs: [docs.nerf.studio](https://docs.nerf.studio/) `[verify]`
* 3DGS awesome list: [github.com/MrNeRF/awesome-3D-gaussian-splatting](https://github.com/MrNeRF/awesome-3D-gaussian-splatting)
* NeRF awesome list: [github.com/awesome-NeRF/awesome-NeRF](https://github.com/awesome-NeRF/awesome-NeRF)
* For monocular depth and other foundation models, see [foundation-vision-models.md](foundation-vision-models.md).
* For depth sensors and LiDAR hardware, see [cameras-depth-sensors-and-lidar.md](cameras-depth-sensors-and-lidar.md).
