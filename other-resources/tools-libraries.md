---
description: The libraries, simulators, and dev tools I actually reach for in 2026 - and how I would assemble a stack for a new robot
icon: toolbox
---

# Tools & Libraries

Every robotics project is mostly glue between a dozen mature libraries. The hard part is knowing which dozen. This page is my opinionated inventory - what I install on day one of a new project, what I avoid, and why. It is biased toward what has survived contact with real robots, not what has the prettiest landing page.

## The 2026 robotics stack at a glance

| Layer | Default choice | Serious alternative |
|---|---|---|
| Math | Eigen | NumPy (Python side) |
| Vision | OpenCV | - |
| Point clouds | PCL (legacy) / Open3D (new code) | small_gicp for registration |
| Optimization | Ceres or GTSAM | g2o (if inherited) |
| Middleware | ROS 2 (Jazzy/Kilted) | Zenoh-based custom stacks |
| Simulation | Gazebo or Isaac Sim/Lab | MuJoCo, Genesis, Webots |
| Learning | PyTorch + LeRobot | JAX (MJX/Brax workflows) |
| Visualization | Foxglove / Lichtblick + PlotJuggler | rviz2 |
| Recording | rosbag2 with MCAP | Raw MCAP writers |
| CAD | Onshape | Fusion 360, FreeCAD |
| EDA | KiCad | Altium (if someone else pays) |

If you adopt that table wholesale you will be fine. The rest of the page explains the judgment calls.

## Core C++ and Python libraries

**Eigen.** Header-only C++ linear algebra. It is in everything - ROS 2's tf2, PCL, Ceres, GTSAM all build on it. Learn the `Map` type (zero-copy views over raw buffers), learn the aliasing rules (`noalias()`), and learn that fixed-size types like `Matrix3d` get vectorized while dynamic ones may not. Most of the C++ performance pain I see in robot code is Eigen misuse, not Eigen.

**OpenCV.** Still the default for image I/O, calibration, ArUco/AprilTag-adjacent detection, and classical feature pipelines. The 4.x line has been stable for years. The deep-learning parts (`cv::dnn`) are fine for ONNX inference in a pinch, but for anything serious I run TensorRT or ONNX Runtime directly and keep OpenCV for pre/post-processing.

**PCL.** The grand old point cloud library. Enormous algorithm coverage (filters, registration, segmentation, surface reconstruction), template-heavy C++, and compile times that will radicalize you. I still use it because half the LiDAR ecosystem speaks `pcl::PointCloud`, but I do not start new algorithmic work in it.

**Open3D.** What I reach for in new code, especially anything Python-facing: clean API, good visualizer, tensor-based geometry that runs on GPU, solid ICP/registration and TSDF integration. The C++ API is usable too. For mesh and RGB-D work it has effectively replaced PCL for me; for raw LiDAR pipelines inside ROS 2, PCL's inertia still wins.

**GTSAM.** Factor graphs done right: iSAM2 incremental smoothing, native Lie group types, IMU preintegration that you should not reimplement yourself. If your problem is a SLAM back-end or any estimation problem with graph structure, start here. The conceptual background lives in [graph-slam.md](../slam-and-state-estimation/graph-slam.md).

**Ceres.** Google's nonlinear least squares solver. More general than GTSAM (any residual, autodiff out of the box), less SLAM-native (no built-in incremental mode). Calibration, bundle adjustment, curve fitting - Ceres. I keep a deeper comparison with worked examples in [optimization-libraries.md](../programming-for-robotics/optimization-libraries.md).

**g2o.** The pose-graph optimizer behind ORB-SLAM and a decade of visual SLAM. Lean and fast, but the API is rough and development is quiet. I only use it when I inherit a codebase that already does - for new work, GTSAM or Ceres.

| Problem | Use |
|---|---|
| Dense matrix math in C++ | Eigen |
| Camera calibration, classical CV | OpenCV |
| LiDAR pipeline inside ROS 2 | PCL (interop) + small_gicp for registration |
| RGB-D, meshes, Python prototyping | Open3D |
| SLAM back-end, incremental estimation | GTSAM |
| Calibration, bundle adjustment, generic NLS | Ceres |
| Maintaining ORB-SLAM-lineage code | g2o |

## Simulators

Full tour with videos on the [simulations page](../computer-aided-designs-and-simulations/simulations.md); here is the short version.

**Gazebo** (the post-Ignition lineage - Harmonic, Ionic). The ROS 2 default. Best sensor/plugin ecosystem for "simulate my actual robot with its actual URDF and actual nav stack." Physics fidelity is adequate, not exceptional. The [BARN Challenge](../authors-projects/barn-challenge.md) evaluates navigation stacks in Gazebo, which tells you something about where it sits in the community.

**Isaac Sim / Isaac Lab.** NVIDIA's Omniverse-based simulator plus its RL framework. The reason to accept the heavyweight install and GPU requirements: thousands of parallel environments on one GPU, photorealistic rendering for synthetic data, and the best sim-to-real story for learned locomotion and manipulation right now. If you are training policies at scale in 2026, you are probably here.

**MuJoCo.** Open source since 2021, maintained by DeepMind. The best contact dynamics per CPU cycle, and MJX gives you JAX-native GPU parallelism. The researcher's default for manipulation and locomotion benchmarks. Weak on sensors and "whole robot with LiDAR in a warehouse" scenarios - it is a physics engine first, robot simulator second.

**Genesis.** The 2024-2025 newcomer claiming enormous parallel-simulation speedups, with differentiable physics and generative scene tooling. Genuinely interesting, but as of mid-2026 I treat it as a research option, not a production default - the ecosystem and sensor support are still maturing. Watch it.

**Webots.** Underrated. Batteries-included, runs on a laptop, painless ROS 2 bridge, great for education and quick feasibility studies. Nobody brags about using Webots, plenty of people quietly ship prototypes with it.

Rule of thumb: ROS 2 system integration → Gazebo. Massively parallel RL or synthetic data → Isaac. Contact-rich research → MuJoCo. Teaching or a one-week prototype → Webots.

## The learning stack

PyTorch won. Unless your lab is JAX-native (usually because of MJX/Brax pipelines), every policy you train in 2026 is PyTorch, and fighting that costs more than any framework advantage returns.

On top of it, **LeRobot** (Hugging Face) has become the center of gravity for robot imitation learning: maintained implementations of ACT, Diffusion Policy, VQ-BeT and friends, a standard dataset format, teleop integrations for SO-10x/Koch-class arms, and the Hub for sharing datasets and checkpoints. The broader HF ecosystem matters too - `datasets` for streaming large episode collections, `transformers` for VLA backbones, the Hub as the de facto distribution channel for pretrained robot policies. The full treatment of when these methods work (and how much data they really need) is in [imitation-learning.md](../robot-learning/imitation-learning.md).

Deployment side: export to ONNX where you can, TensorRT on Jetson-class hardware, and keep the policy inference process separate from your ROS 2 control loop so a slow forward pass never blocks the safety-critical path.

## Daily-driver dev tools

These are the tools open on my machine on a normal day:

* **Docker** - every robot stack I work on builds and runs in containers, full stop. Reproducible onboarding, pinned ROS 2 distros, CI parity. The only debate left is bind-mount workflows vs. devcontainers.
* **Foxglove** - browser-based visualization, MCAP-native, excellent for remote robots and log review. Note the 2024 license change; evaluate the terms for commercial use.
* **Lichtblick** - the open-source Foxglove fork (BMW-initiated) that I have contributed to. Noticeably lighter on CPU and stays Apache-licensed. My default recommendation when the Foxglove licensing question comes up.
* **PlotJuggler** - time-series plotting that no ROS GUI comes close to. Drag a topic onto a plot, scrub a bag, find your timing bug. I contribute to it; I am biased, and also right.
* **colcon** - the ROS 2 build orchestrator. Learn `--symlink-install`, `--packages-up-to`, and `--event-handlers console_direct+` and your build-debug loop gets dramatically shorter.
* **rosbag2 + MCAP** - record everything during bring-up. MCAP has been the default storage format since Iron, and it is what Foxglove/Lichtblick read natively, so the record-then-replay-then-plot loop has zero conversion steps.

The deep dive on the visualization trio (rviz2 vs. Foxglove vs. Lichtblick vs. PlotJuggler) is on the [ROS 2 visualization page](../ros-2/visualization.md).

## CAD and EDA

**Onshape.** Cloud-native parametric CAD. Real version control on geometry (branching and merging, not "final_v3_FINAL.step"), runs in a browser, free tier for public documents. This is what I use for personal robot builds - the collaboration story alone justifies it.

**Fusion 360.** Stronger integrated CAM and simulation than Onshape, and a constrained free personal-use tier. The desktop install and Autodesk's habit of shuffling free-tier features are the tax. Common in startups that machine their own parts.

**KiCad.** Open-source EDA that crossed the "good enough for professional boards" line years ago - version 9-era releases have a solid router, decent library management, and a real Python scripting API. For robot electronics (motor driver carriers, sensor breakouts, power distribution) I see no reason to pay for Altium anymore. Board-level practice lives in [pcb-design.md](../computer-aided-designs-and-simulations/pcb-design.md).

FreeCAD deserves a mention: post-1.0 it is genuinely usable, and it is the only fully open option if cloud CAD bothers you.

## How I would pick a stack for a new robot in 2026

Assume a mobile manipulator or AMR-class robot, small team, real deadline. My defaults, in dependency order:

1. **ROS 2 Jazzy on Ubuntu 24.04, everything in Docker** from the first commit. Pin the distro; do not chase Rolling on a product.
2. **C++ for the control and perception hot path, Python for everything else.** Eigen + OpenCV + (PCL or Open3D depending on sensor mix) come along for free.
3. **Estimation:** `robot_localization` EKF for odometry fusion, GTSAM the moment a real SLAM back-end or calibration graph appears. Ceres for one-off calibration problems.
4. **Simulation:** Gazebo for system integration tests wired into CI. Add Isaac Lab only if there is a learned-policy workstream; do not pay its complexity cost for a nav-only robot.
5. **Learning:** PyTorch + LeRobot if manipulation skills are in scope. Start collecting teleop data weeks before you think you need it - data, not architecture, is the bottleneck.
6. **Observability:** rosbag2/MCAP recording from day one, Lichtblick layouts checked into the repo, PlotJuggler for control tuning. A robot you cannot replay is a robot you cannot debug.
7. **Hardware design:** Onshape for mechanics, KiCad for custom boards, and a strict rule that every fabricated part's source lives in version control next to the code.

This is roughly the shape of the stack behind my own projects - [Polka](../authors-projects/polka.md) on the robot side, [GO-SLAM](../authors-projects/go-slam.md) on the estimation/learning side. The point is not these exact tools; it is that every layer has one boring, well-supported default, and you should spend your novelty budget on the one layer where your robot actually differentiates.

## Where to go next

* [Important packages and libraries](../ros-2/important-packages-and-libraries.md) - the ROS 2-specific package catalog that complements this general-tools page.
* [Optimization libraries](../programming-for-robotics/optimization-libraries.md) - Ceres, GTSAM, and g2o with actual code and a deeper when-to-use-which discussion.
* [Simulations](../computer-aided-designs-and-simulations/simulations.md) - the full simulator tour, including the platforms this page skipped.
* [Imitation learning](../robot-learning/imitation-learning.md) - what the LeRobot/PyTorch stack is actually for, and how much data the methods really need.
