---
icon: route
---

# Learned SLAM - neural fields, Gaussian splatting

## What changed

Classical SLAM uses explicit representations: point clouds, occupancy grids, sparse landmark maps, voxel grids. The estimators (filters, factor graphs) live on top of these.

Around 2020 the community started asking: what if the map itself were a *neural network* - a function $$f_\theta(\mathbf{x})$$ that takes a 3D position and returns geometry (occupancy, signed distance) or appearance (color, density)? This is the **neural radiance field** lineage (NeRF, Mildenhall et al. 2020) ported into SLAM.

Then in 2023 came **3D Gaussian Splatting** (Kerbl, Kopanas, Leimkühler, Drettakis), which dropped the neural network in favor of millions of explicit 3D Gaussians and a differentiable splatting rasterizer. Faster training, real-time rendering. The SLAM community pivoted within a year. SplaTAM and Gaussian-Splatting SLAM appeared at the major venues in 2024.

This page covers the systems that defined the lineage.

***

## Disambiguation - two things called "GO-SLAM"

This is an unfortunate name collision. There are **two distinct projects** named GO-SLAM that you'll find on the internet:

1. **GO-SLAM (Zhang et al., ICCV 2023)** - an *academic neural / deep SLAM* paper from the Computer Vision Lab at ETH Zürich / KAIST and collaborators. Uses an implicit neural representation with online learning, global optimization, and loop closure. Visual SLAM. [arxiv.org/abs/2309.02436](https://arxiv.org/abs/2309.02436). This is what this page is about.

2. **[GO-SLAM (Pan's)](../authors-projects/go-slam.md)** - *my from-scratch classical LiDAR SLAM* with GICP front-end and a custom Levenberg-Marquardt pose-graph solver. Built in two months as a learning project. **No relation to the ETH/KAIST paper** - I just happened to pick the same acronym (Global Optimization SLAM) before realizing there was a published paper with that name. Mentioned in [lidar-slam.md](lidar-slam.md).

If a colleague says "go-slam" without context, ask which one. They are completely different systems.

***

## The neural field family

### NICE-SLAM (CVPR 2022)

Zhu, Peng, Larsson, Xu, Bao, Cui, Oswald, Pollefeys. ETH + Microsoft. [arxiv.org/abs/2112.12130](https://arxiv.org/abs/2112.12130). Code: [github.com/cvg/nice-slam](https://github.com/cvg/nice-slam).

The first widely-cited "neural implicit + multi-scale" RGB-D SLAM. Key ideas:

* **Multi-scale hierarchical grid of feature embeddings** instead of a single global MLP (which was iMAP's approach a year earlier and scaled badly to room-sized scenes).
* At each query point, trilinearly interpolate the grid features and pass them through small MLPs to predict occupancy and color.
* Joint optimization of camera poses and grid features via differentiable rendering.

NICE-SLAM works on Replica, ScanNet, TUM RGB-D scenes. It produces dense reconstructions in a way classical sparse SLAM cannot.

Trade-offs:
* GPU-bound. Real-time means "30 Hz on a desktop GPU," not "30 Hz on a Jetson."
* Loop closure is implicit through the joint optimization, but degrades on long sequences.
* Map representation is the grid + MLP weights - opaque, hard to edit, hard to use downstream for navigation.

### GO-SLAM (ICCV 2023) - the academic paper

Zhang, Sun, Tang, Lin, Wang, Theobalt, Pollefeys. [arxiv.org/abs/2309.02436](https://arxiv.org/abs/2309.02436). Code: [github.com/youmi-zym/GO-SLAM](https://github.com/youmi-zym/GO-SLAM).

Built on top of DROID-SLAM (Teed & Deng, NeurIPS 2021). Contributions:

* **Online loop closure detection** with dense bundle adjustment over the global trajectory - not just the local sliding window.
* **Online full bundle adjustment** updating the entire history when loops close.
* Implicit neural representation (similar lineage to NICE-SLAM) for the dense reconstruction.
* Works monocular, stereo, and RGB-D - flexibility classical neural-implicit systems didn't have.

This was the SOTA neural visual SLAM at ICCV 2023 (margin over NICE-SLAM, ESLAM, Co-SLAM on Replica / ScanNet trajectory accuracy). Not the SOTA anymore - Gaussian-splat SLAM took over within a year.

***

## Gaussian splatting takes over

### 3D Gaussian Splatting (SIGGRAPH 2023)

Kerbl, Kopanas, Leimkühler, Drettakis. [arxiv.org/abs/2308.04079](https://arxiv.org/abs/2308.04079). Code: [github.com/graphdeco-inria/gaussian-splatting](https://github.com/graphdeco-inria/gaussian-splatting).

Not a SLAM paper, but the foundation for everything that followed. The idea:

* Represent the scene as a (large) set of **3D Gaussians**, each with: position $$\mu \in \mathbb{R}^3$$, anisotropic covariance $$\Sigma$$, opacity $$\alpha$$, and view-dependent color (spherical harmonic coefficients).
* Render by **projecting each Gaussian to 2D** (a 2D Gaussian on the image plane), then alpha-blending front-to-back. This rasterization is differentiable.
* Optimize positions, shapes, colors, opacities by minimizing rendered-vs-ground-truth image loss. **Adaptive density control** clones / splits / prunes Gaussians as training proceeds.

Two things this gave you over NeRF:

1. **Faster training** - minutes instead of hours.
2. **Real-time rendering** - hundreds of FPS at 1080p on a single GPU.

And critically: the representation is *explicit*. You can move individual Gaussians. You can prune them. You can add new ones when you see new geometry. That made it tractable for online SLAM.

### SplaTAM (CVPR 2024)

Keetha, Karhade, Jatavallabhula, Yang, Scherer, Ramanan, Luiten. [arxiv.org/abs/2312.02126](https://arxiv.org/abs/2312.02126). Code: [github.com/spla-tam/SplaTAM](https://github.com/spla-tam/SplaTAM).

The first widely-adopted Gaussian-Splat SLAM. RGB-D.

* Map is a collection of 3D Gaussians.
* **Tracking** = optimize camera pose by minimizing rendering loss against the current RGB-D frame.
* **Mapping** = add new Gaussians where the silhouette mask says the current map is missing geometry; optimize all Gaussians in keyframes' frustums.
* Real-time on a single 4090-class GPU.

SplaTAM is closer to a "differentiable RGB-D fusion" than to a classical SLAM. There's no factor graph, no loop closure, no place recognition. Tracking is direct (in the photometric sense, like DSO) but expressed in the Gaussian-splat framework.

### Gaussian Splatting SLAM (CVPR 2024)

Matsuki, Murai, Kelly, Davison. Imperial College London. [arxiv.org/abs/2312.06741](https://arxiv.org/abs/2312.06741). Code: [github.com/muskie82/MonoGS](https://github.com/muskie82/MonoGS).

Andrew Davison's group (who did MonoSLAM in 2003 - the first real-time monocular visual SLAM) returned to the problem with Gaussians. Their contribution was **monocular** Gaussian-splat SLAM:

* No depth sensor required.
* Tracking via differentiable rendering against the current RGB frame, plus regularizers to keep the Gaussians from collapsing.
* Mapping via online Gaussian addition / refinement.
* They demonstrated stereo and RGB-D extensions as well.

The Davison-lab heritage shows: this is the cleanest framing of "SLAM as differentiable rendering" so far.

### GS-SLAM (CVPR 2024)

Yan, Qiu, Liu, Liu, Sun, Wang, Liu, Lin, Cui, Yang. [arxiv.org/abs/2311.11700](https://arxiv.org/abs/2311.11700). Code: [github.com/yanchi-3dv/GS-SLAM](https://github.com/yanchi-3dv/GS-SLAM) `[verify]`.

Another Gaussian-splat RGB-D SLAM, concurrent with SplaTAM. Adds an explicit coarse-to-fine selection strategy for which Gaussians to optimize per frame, and a render-then-refine loop. Comparable accuracy / speed to SplaTAM on standard benchmarks.

### Newer entrants (2024-2025)

The field is moving fast. Names to be aware of:

* **Gaussian-SLAM** (Yugay et al. 2024)
* **Photo-SLAM** (Huang et al. 2024)
* **GS-LiDAR** - combining LiDAR depth with Gaussian splatting.
* **MoNuSplat / MAGiC-SLAM** - 2024-2025 papers pushing toward monocular outdoor.

Expect the SOTA to shift twice a year in this corner of the field through 2026.

***

## Comparison

| System              | Sensor    | Map           | Real-time?  | Loop closure | GPU need              |
| ------------------- | --------- | ------------- | ----------- | ------------ | --------------------- |
| iMAP                | RGB-D     | Single MLP    | No (slow)   | No           | Desktop GPU           |
| NICE-SLAM           | RGB-D     | Hierarchical feature grid + MLPs | Yes (30 Hz)* | Implicit / weak | Desktop GPU |
| Co-SLAM             | RGB-D     | Hash grid + MLP | Yes        | Weak         | Desktop GPU           |
| GO-SLAM (ICCV 2023) | Mono / stereo / RGB-D | Implicit | ~10 Hz | Yes (online global BA) | Desktop GPU |
| SplaTAM             | RGB-D     | 3D Gaussians  | Yes         | No           | Desktop GPU (4090+)   |
| Gaussian Splatting SLAM | Mono / stereo / RGB-D | 3D Gaussians | Yes | No | Desktop GPU |
| GS-SLAM             | RGB-D     | 3D Gaussians  | Yes         | No           | Desktop GPU           |

\* "Real-time" in this field means "30 Hz on a desktop GPU." None of these run on a Jetson Orin or any robot you can fly. That's a real constraint.

***

## Where this is going - and where it isn't (yet)

### What learned SLAM is great at

* **Photoreal reconstruction.** Gaussian-splat maps are renderable from any viewpoint. NeRF/Gaussian-splat maps are what AR headsets and digital-twin pipelines want.
* **Dense geometry from sparse supervision.** A neural field interpolates plausible geometry between observations.
* **Joint optimization of pose + appearance + geometry** - the differentiable-rendering loss naturally couples all three.

### What learned SLAM is still bad at

* **Compute budget for real robots.** Drone CPU? Jetson Orin? Not yet. Until learned SLAM runs on edge compute, classical SLAM keeps its day job.
* **Long traverses, outdoor scenes.** Gaussian-splat papers are still mostly evaluated on Replica (small rooms), ScanNet (indoor scans), occasionally TUM-RGBD. Outdoor kilometer traverses are still classical LiDAR / VIO territory.
* **Loop closure at scale.** Most learned SLAMs in 2025 don't have classical loop closure. The trajectories they're benchmarked on are short enough that drift doesn't matter much.
* **Map editability and downstream consumption.** A pose-graph map is easy to convert to an occupancy grid for Nav2. A Gaussian-splat map is not. The downstream story is still being written.

### What's coming

* **Hybrid systems.** Classical front-end (LiDAR odometry, IMU preint, sparse features) + learned map / dense reconstruction back-end. GLIM is closer to this. So is anything labelled "neuralized" classical SLAM.
* **GPU SLAM stacks.** The same way classical SLAM moved from "research code on a laptop" to "production C++ on a robot," learned SLAM will move from "Python research code on a 4090" to "CUDA on Jetson." Several companies - including the one I work at in 2026 - are pushing here.
* **Foundation models for SLAM.** DUSt3R (Wang et al. 2024), MASt3R, and other models that produce pose + dense geometry from a pair of images are blurring the line between SfM and SLAM. The "pose from a transformer" approach is real.

***

## Should you use learned SLAM today?

In 2026, the honest answer for a robot that has to navigate:

* **Production deployment, ground robot, indoor / outdoor:** No. Use classical LiDAR or visual SLAM. The compute budget and loop closure story aren't there yet.
* **Production deployment, AR headset, dense reconstruction product:** Yes - SplaTAM / Gaussian-Splat SLAM if you have GPU, with classical visual-inertial tracking underneath.
* **Research baseline for a paper:** Yes. The field expects you to compare against at least one Gaussian-splat system.
* **Learning / exploration:** Absolutely. Build one. The differentiable-rendering formulation is the future of perception generally.

> **Field notes:** I work on GPU-accelerated SLAM in production because the ceiling is much higher than for CPU-bound classical SLAM. But every shipping product I've seen in 2026 still has a classical front-end somewhere. The Gaussian splat is the *map*. The tracker that produces the camera trajectory is usually classical-feeling underneath the differentiable rendering loss. Don't confuse "neural representation" with "neural tracker."

***

## Further reading

* Tewari et al. (2022 / 2023) "Advances in Neural Rendering" - state of the art at the moment NeRF/3DGS split.
* Original 3DGS paper: [arxiv.org/abs/2308.04079](https://arxiv.org/abs/2308.04079) - still the cleanest exposition of why splatting works.
* DROID-SLAM (Teed & Deng, NeurIPS 2021) - [arxiv.org/abs/2108.10869](https://arxiv.org/abs/2108.10869) - the foundation for the academic GO-SLAM and a great example of differentiable BA done well.
* DUSt3R (Wang et al. CVPR 2024) - [arxiv.org/abs/2312.14132](https://arxiv.org/abs/2312.14132) - pose + dense 3D from a transformer. Not yet SLAM but headed there.

### Cross-references in this handbook

* [GO-SLAM (Pan's)](../authors-projects/go-slam.md) - my classical from-scratch SLAM, **not** the ICCV 2023 paper covered above. See disambiguation at the top of this page.
* [Visual SLAM](visual-slam.md) - the classical visual SLAM systems neural SLAM is competing with.
* [LiDAR SLAM](lidar-slam.md) - the classical LiDAR SLAM systems and where GPU/learned LiDAR fits in (GLIM, etc.).
