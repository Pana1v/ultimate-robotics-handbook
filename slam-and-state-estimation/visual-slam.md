---
icon: route
---

# Visual SLAM

## Why cameras

A monocular camera is the cheapest, lightest, lowest-power sensor that can give you a full 6-DoF pose and a 3D map. Two reasons it matters:

1. **Information density.** A 1080p image at 30 Hz is ~60M pixels/sec. No LiDAR comes close in raw scene information.
2. **Cost.** A $20 camera vs $5000+ for a 64-beam LiDAR. For drones, AR, and consumer robots, vision is the only option.

The catch: cameras give you *bearing* measurements, not range. Monocular SLAM is scale-ambiguous (you don't know if you moved 1 m or 1 km). You break that ambiguity with stereo, depth sensor, or IMU.

This page covers the three dominant paradigms - feature-based, direct, and visual-inertial - and the canonical systems that defined each.

***

## Feature-based vs direct - the philosophical split

| Aspect              | Feature-based                              | Direct                                       |
| ------------------- | ------------------------------------------ | -------------------------------------------- |
| What it tracks      | Detected keypoints (ORB, SIFT, FAST+BRIEF) | Pixel intensities, usually high-gradient pixels |
| Cost function       | Reprojection error of matched features     | Photometric error (intensity difference)     |
| Robustness to blur  | Bad - keypoints fail under motion blur     | Better - gradient survives modest blur       |
| Robustness to lighting | Better - descriptors are invariant      | Bad - photometric error breaks under lighting changes (needs photometric calibration) |
| Map representation  | Sparse 3D points                           | Sparse / semi-dense pixels with depth        |
| Loop closure        | Easy - bag of visual words over descriptors | Hard - no descriptors to match              |
| Canonical systems   | ORB-SLAM family, VINS-Mono/Fusion          | LSD-SLAM, DSO, LDSO                          |

There's also a **hybrid** middle ground: SVO (Forster, Pizzoli, Scaramuzza 2014) uses direct alignment for tracking and features for mapping. Modern systems increasingly blur the line.

***

## ORB-SLAM3 - the feature-based reference

If you implement one visual SLAM system, this is it. ORB-SLAM3 (Campos, Elvira, Gómez Rodríguez, Montiel, Tardós 2021) is the third generation of a line of work that started with ORB-SLAM (2015) and added stereo / RGB-D (ORB-SLAM2, 2017). The 3 brings two huge additions: **tightly-coupled visual-inertial SLAM** and **multi-map (Atlas) operation**.

* Paper: [arxiv.org/abs/2007.11898](https://arxiv.org/abs/2007.11898)
* Code: [github.com/UZ-SLAMLab/ORB\_SLAM3](https://github.com/UZ-SLAMLab/ORB_SLAM3)

### Architecture

Three parallel threads - the same template you'll see in almost every modern visual SLAM:

1. **Tracking** - every frame: extract ORB features, match to local map, estimate camera pose by motion-only BA.
2. **Local Mapping** - for new keyframes: triangulate new map points, run local BA over the last $N$ keyframes.
3. **Loop and Map Merging** - detect loops via DBoW2, run a pose graph optimization, then full BA to clean up.

The Atlas system maintains multiple disconnected sub-maps. When tracking is lost, ORB-SLAM3 doesn't crash - it starts a new map. If place recognition later finds a connection back to an old map, the two are merged into one.

### Sensor configurations

ORB-SLAM3 handles, with the same code base:

* Monocular, monocular + IMU
* Stereo, stereo + IMU
* RGB-D, RGB-D + IMU
* Fisheye cameras (Kannala-Brandt model)

The visual-inertial mode does *tightly-coupled* fusion with IMU preintegration (see [sensor-fusion.md](sensor-fusion.md)) inside the local-BA window. Initialization is done via the IMU initialization procedure from Mur-Artal & Tardós (2017), which estimates gravity, IMU biases, and scale before VIO takes over.

### When it wins

* You have stereo or RGB-D and want a turnkey, well-tested system.
* Your environment has texture (corners, edges) - ORB needs features.
* You want loop closure and global consistency built in.

### When it loses

* Low-texture environments (white corridors, plain walls). No features, no SLAM.
* High motion blur. ORB extraction breaks under blur.
* Repetitive structure. DBoW2 will false-match identical scenes - though geometric verification catches most of these.
* High-DoF aggressive drone motion. The tracking thread runs at camera rate (~30 Hz); aggressive drones need 200+ Hz state from the IMU. Use VINS-Fusion or OKVIS instead.

> **Field notes:** ORB-SLAM3 is rightly the default. But it is C++17 with non-trivial dependency on OpenCV 3 / 4 and a Pangolin viewer. Building it on aarch64 Ubuntu 22.04 in 2024 took me an afternoon of CMake gymnastics. Once it builds, it just works.

***

## VINS-Mono and VINS-Fusion

VINS = Visual-INertial System. From the HKUST Aerial Robotics group (Qin, Li, Shen et al.). The killer system for drone VIO.

* **VINS-Mono** (Qin, Li, Shen 2018) - monocular + IMU. [arxiv.org/abs/1708.03852](https://arxiv.org/abs/1708.03852). Code: [github.com/HKUST-Aerial-Robotics/VINS-Mono](https://github.com/HKUST-Aerial-Robotics/VINS-Mono).
* **VINS-Fusion** (Qin et al. 2019) - extension to stereo, stereo+IMU, GPS fusion. Code: [github.com/HKUST-Aerial-Robotics/VINS-Fusion](https://github.com/HKUST-Aerial-Robotics/VINS-Fusion).

### Why it matters

VINS-Mono made *robust* monocular VIO real. Before it, monocular VIO existed (MSCKF, OKVIS) but initialization was fragile and most papers required hand-tuned trajectories. VINS-Mono introduced:

* **Robust automatic initialization** - visual-only SfM bootstrap, then IMU alignment for scale, gravity, biases.
* **Sliding-window optimization** with marginalization (see [graph-slam.md](graph-slam.md)).
* **Loop closure** with DBoW2 + 4-DoF pose graph (loop closure can't constrain absolute roll/pitch when IMU is observable).
* **Online extrinsic + temporal calibration** between camera and IMU.

The result was a system you could mount on a drone, fly aggressively, and trust.

### Architecture (sliding window)

Maintain a window of the last $N$ frames (typically 10-20). State per frame: pose, velocity, IMU biases. Variables: also extrinsic camera-IMU transform, time offset, and feature inverse-depths.

Cost = visual reprojection + IMU preintegration + marginalization prior. Ceres solves it every frame.

When the window fills, **marginalize** out the oldest frame's state (Schur complement) and absorb its information into the marginalization prior. This bounds memory while keeping information.

### When to pick VINS over ORB-SLAM3

* Aggressive 6-DoF motion (drones).
* You need temporal calibration with the IMU and the camera-IMU extrinsic isn't perfectly known.
* You want a smaller, more readable codebase to fork.
* You want GPS fusion (VINS-Fusion).

***

## DSO and LDSO - the direct school

Direct Sparse Odometry (Engel, Koltun, Cremers 2017) is the canonical direct visual odometry. No features. Instead: pick ~2000 high-gradient pixels per keyframe and minimize photometric error across keyframes.

* DSO paper: [arxiv.org/abs/1607.02565](https://arxiv.org/abs/1607.02565)
* Code: [github.com/JakobEngel/dso](https://github.com/JakobEngel/dso)
* LDSO (DSO + loop closure, Gao, Wang, Cremers 2018): [github.com/tum-vision/LDSO](https://github.com/tum-vision/LDSO)

### Why direct methods exist

A feature-based system throws away 99% of the pixel information by reducing each frame to ~2000 keypoints. Direct methods say: just optimize the image likelihood directly. The cost:

$$
E_{photo} = \sum_{p} \sum_{q \in \mathcal{N}(p)} \| I_j(\pi(\mathbf{T}_{ji} \pi^{-1}(q, d_q))) - I_i(q) \|
$$

In English: project pixel $q$ from frame $i$ into frame $j$ using the depth and relative pose, then compare intensities. Minimize over poses and depths.

### The catch - photometric calibration

DSO requires careful photometric calibration of your camera: exposure time, vignette, response curve. Without it, the photometric error is meaningless (a change in exposure looks like a change in geometry).

This made DSO popular as a research benchmark but limited its production deployment. ORB-SLAM3 just works with whatever camera you have. DSO needs a tuned camera.

### Where direct wins

* Low-texture environments where features fail but gradients still exist (e.g., gradients on a slightly textured wall).
* Highly accurate trajectory estimation in well-calibrated setups (DSO's accuracy on TUM monoVO is excellent).
* AR / dense mapping research where you want pixel-level geometry.

### LDSO and the loop closure problem

Pure DSO has no loop closure - direct methods don't naturally have descriptors. LDSO adds:

* ORB features extracted on top of DSO's high-gradient pixels (so loop closure piggybacks).
* DBoW2 for place recognition.
* Pose graph optimization in Sim(3) to handle scale drift.

It's a clever hack and it works. It also gives away the philosophical purity of "no features," which is fine - engineering beats philosophy.

***

## Monocular vs stereo vs RGB-D

| Sensor    | Pros                                                                 | Cons                                                                |
| --------- | -------------------------------------------------------------------- | ------------------------------------------------------------------- |
| Monocular | Cheapest, smallest, lightest. Long range.                            | No absolute scale (needs IMU, known landmark, or motion). Pure rotation is degenerate (no parallax). |
| Stereo    | Absolute scale from baseline. Robust to pure rotation.               | Range limited by baseline (typical 20-50 cm baselines work to 10-20 m). Needs careful stereo calibration. |
| RGB-D     | Direct depth measurement. Excellent for indoor mapping.              | Indoor only (active sensors fail in sunlight). Range limited (4-6 m for Realsense, Kinect). |

### Choosing

* Drone with VIO → monocular + IMU (weight). VINS-Mono or ORB-SLAM3.
* Indoor mobile robot → RGB-D. RTAB-Map or ORB-SLAM3 RGB-D mode.
* Outdoor robot / AR headset → stereo (or stereo + IMU). ORB-SLAM3 stereo-inertial.
* Self-driving car → stereo with wide baseline, or stereo + LiDAR. Visual SLAM alone won't cut it.

### The mono initialization problem

Monocular SLAM has to bootstrap from nothing. The classic chicken-and-egg: you need a map to estimate pose, you need pose to triangulate a map. The standard trick:

1. Detect features in two frames a few cm apart (typical: wait for sufficient parallax).
2. Compute either the **essential matrix** (calibrated case) or **homography** (planar scene case) between them.
3. Pick whichever has the better geometric fit (essential for general scene, homography for planar). Triangulate the initial map.
4. Set scale arbitrarily (e.g., median scene depth = 1). All future motion is up to this unknown scale factor - unless an IMU resolves it.

This is fragile. Many monocular SLAM failures are at initialization, not steady-state. IMU initialization (Mur-Artal & Tardós 2017) made this much more robust by aligning gravity and using IMU-predicted motion to bootstrap the visual SfM.

***

## A note on RGB-D SLAM specifically

RTAB-Map (Labbé & Michaud 2019) is the production RGB-D SLAM. Not as accurate as ORB-SLAM3 in head-to-head benchmarks but it ships an entire system: drivers, loop closure, occupancy grid output, multi-session SLAM, ROS integration.

* Paper: [introlab.github.io/rtabmap](https://introlab.github.io/rtabmap/)
* Code: [github.com/introlab/rtabmap](https://github.com/introlab/rtabmap)

Pick RTAB-Map when you want SLAM-as-product (your project is "build a 3D map of a building") and don't have time to integrate ORB-SLAM3 into ROS yourself.

***

## Comparison - pick one

| System         | Sensor configs                          | Loop closure | Tightly-coupled IMU | Repo                                  |
| -------------- | --------------------------------------- | ------------ | ------------------- | ------------------------------------- |
| ORB-SLAM3      | mono / stereo / RGB-D, ± IMU, fisheye   | Yes (DBoW2)  | Yes                 | UZ-SLAMLab/ORB\_SLAM3                 |
| VINS-Mono      | mono + IMU                              | Yes (DBoW2)  | Yes                 | HKUST-Aerial-Robotics/VINS-Mono       |
| VINS-Fusion    | mono / stereo, ± IMU, ± GPS             | Yes          | Yes                 | HKUST-Aerial-Robotics/VINS-Fusion     |
| OpenVINS       | mono / stereo + IMU                     | No (pure VIO) | Yes (MSCKF style)  | rpng/open\_vins                       |
| DSO            | mono                                    | No           | No                  | JakobEngel/dso                        |
| LDSO           | mono                                    | Yes          | No                  | tum-vision/LDSO                       |
| RTAB-Map       | RGB-D, stereo                           | Yes          | Loose IMU fusion    | introlab/rtabmap                      |
| SVO            | mono / stereo                           | No (pure VO) | Optional            | uzh-rpg/rpg\_svo\_pro\_open            |

***

## What I'd actually do in 2026

* **Building a drone:** VINS-Fusion (mono+IMU or stereo+IMU). Battle-tested for aggressive motion.
* **Indoor mobile robot:** RTAB-Map RGB-D mode - fastest path to a working system. ORB-SLAM3 if you need higher accuracy.
* **AR / dense mapping:** SplaTAM or NICE-SLAM - see [learned-slam.md](learned-slam.md). The classic visual SLAM stack is being eaten alive here.
* **Self-driving / outdoor robot:** visual SLAM as a *complement* to LiDAR SLAM, not a replacement. See [lidar-slam.md](lidar-slam.md).
* **Research baseline:** ORB-SLAM3. It is what reviewers expect you to compare against.

***

## Further reading

* Cadena et al. (2016) survey, "Past, Present, and Future of SLAM" - [arxiv.org/abs/1606.05830](https://arxiv.org/abs/1606.05830). The visual SLAM landscape circa 2016, still mostly relevant.
* Macario Barros et al. (2022) "A Comprehensive Survey of Visual SLAM Algorithms." [mdpi.com/2218-6581/11/1/24](https://www.mdpi.com/2218-6581/11/1/24).
* Scaramuzza & Fraundorfer two-part tutorial on Visual Odometry (IEEE RAM 2011 / 2012) - still the cleanest intro to VO fundamentals.

Continue to [lidar-slam.md](lidar-slam.md) for the LiDAR side of the story.
