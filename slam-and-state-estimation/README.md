---
icon: route
---

# SLAM & State Estimation

## What this section is

This is the authoritative SLAM reference in the handbook. The short page in `mobile-robotics/slam-and-navigation.md` is a primer — fine for a 10-minute overview. This section is what I wish I'd had when I started building SLAM systems: opinionated, math-grounded, and biased toward what actually works on real robots in 2026.

I built [GO-SLAM](../authors-projects/go-slam.md) from scratch in two months — GICP front-end, custom Levenberg-Marquardt solver, pose-graph back-end, loop closure — without leaning on Ceres, g2o, or GTSAM. I work on GPU-accelerated SLAM and multimodal EKF state estimation at [Eternal.ag](https://eternal.ag) (2026). Most of the opinions here come from things that broke at 3 AM in a warehouse.

If you only read one thing: **SLAM is a state estimation problem with a map as a side effect.** Everything else — features, ICP, factor graphs, neural fields — is implementation detail layered on top of probabilistic state estimation.

***

## SLAM taxonomy

SLAM literature is a swamp of acronyms. There are four orthogonal axes you can slice it on. Pick a point in this 4D space and you've picked an algorithm class.

### Axis 1: dimensionality — 2D vs 3D

| Dimension | Sensors                                  | Typical algorithms                | Use case                                |
| --------- | ---------------------------------------- | --------------------------------- | --------------------------------------- |
| 2D        | 2D LiDAR, wheel odometry                 | gmapping, Cartographer (2D mode), slam\_toolbox | Indoor AMRs on flat floors              |
| 3D        | 3D LiDAR, stereo/RGB-D camera, IMU       | LIO-SAM, FAST-LIO2, ORB-SLAM3     | Drones, outdoor robots, multi-floor     |

**Field notes:** 2D SLAM is *not* obsolete. If your robot lives on a flat warehouse floor, a Hokuyo URG-04LX and slam\_toolbox will outperform a 64-beam Ouster running FAST-LIO2 every time on compute-per-dollar. Reach for 3D only when 2D fails you.

### Axis 2: estimator — filter vs graph

| Type         | What it is                                                                 | Strength                                  | Weakness                                 |
| ------------ | -------------------------------------------------------------------------- | ----------------------------------------- | ---------------------------------------- |
| **Filter**   | Recursive Bayes filter (EKF, UKF, particle filter). Online, marginalizes past poses. | Constant per-step cost, online            | No revisiting; linearization errors compound |
| **Graph**    | Build a factor graph of poses + landmarks, batch-optimize when needed.    | Loop closure trivially fixes drift        | Need to re-solve when graph changes      |

Modern SLAM is mostly graph-based. Filters survive in two niches: AMCL for pure localization on a known map, and tight IMU integration where the IMU is the highest-frequency signal (you'll see "IEKF" or "ESKF" in VIO papers).

Details: [filter-slam.md](filter-slam.md), [graph-slam.md](graph-slam.md).

### Axis 3: representation — dense vs sparse

| Type       | Map representation                                | Algorithms                                | Trade-off                                  |
| ---------- | ------------------------------------------------- | ----------------------------------------- | ------------------------------------------ |
| **Sparse** | Keyframes + 3D point landmarks                    | ORB-SLAM3, VINS-Fusion, FAST-LIO2 (point map) | Fast, scales well, no surface           |
| **Semi-dense** | Pixels with strong gradient + depth           | LSD-SLAM, DSO                             | Middle ground                              |
| **Dense**  | Every pixel / every voxel has geometry            | KinectFusion, NICE-SLAM, Gaussian-Splat SLAM | Beautiful maps, GPU-bound               |

Sparse wins for navigation. Dense wins for AR, mapping-as-product, or anything that needs photoreal reconstruction.

### Axis 4: cadence — online vs batch

* **Online:** every-frame estimation with bounded latency. The only mode that matters for a robot deciding where to go right now.
* **Batch:** post-process the whole log. Useful for ground-truth-grade maps, calibration, dataset construction. SfM (Structure from Motion) is batch SLAM.

***

## Which SLAM do I use? — decision tree

```
Is your robot indoors on a flat floor?
├── Yes → 2D LiDAR + slam_toolbox. Stop reading.
└── No  → Continue.

Do you have GPS that works (outdoor, sky-visible)?
├── Yes → GPS + IMU + wheel odom in an EKF (robot_localization). You don't need SLAM, you need state estimation.
└── No  → Continue.

What's your dominant sensor?
├── 3D LiDAR + IMU
│   └── Real-time, CPU-bound? → FAST-LIO2 (ikd-tree, IEKF, no loop closure)
│       Robust loop closure mandatory? → LIO-SAM (factor-graph back-end)
│       Simple, no IMU? → KISS-ICP
├── Camera only (monocular/stereo/RGB-D)
│   └── Need scale (mono)? → Add IMU → VINS-Mono / VINS-Fusion
│       Have stereo or RGB-D? → ORB-SLAM3
│       Indoor reconstruction priority? → SplaTAM / Gaussian-Splat SLAM
└── Camera + IMU + LiDAR (multi-modal)
    └── LIO-SAM + visual loop closure, or roll your own graph (this is where research lives).
```

I don't include "EKF-SLAM" in the tree because in 2026 you should not use EKF-SLAM for a new system. It's a teaching tool. See [filter-slam.md](filter-slam.md) for why.

***

## The subpages

| File                                       | What's in it                                                                                                            |
| ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| [filter-slam.md](filter-slam.md)           | EKF-SLAM, particle filter / FastSLAM, AMCL. Bayes filter intuition, when particles collapse.                            |
| [graph-slam.md](graph-slam.md)             | Pose graph optimization, factor graphs, g2o, GTSAM, Ceres. Information matrix, Schur complement, marginalization.       |
| [visual-slam.md](visual-slam.md)           | ORB-SLAM3, VINS-Mono/Fusion, DSO/LDSO. Monocular vs stereo vs RGB-D. Feature-based vs direct.                           |
| [lidar-slam.md](lidar-slam.md)             | LOAM → LIO-SAM → FAST-LIO2 → KISS-ICP. Deskewing, ICP variants, IMU preintegration.                                     |
| [learned-slam.md](learned-slam.md)         | NICE-SLAM, the ICCV 2023 GO-SLAM, GS-SLAM, SplaTAM, Gaussian-Splat SLAM. (Not Pan's GO-SLAM — see disambig note inside.) |
| [sensor-fusion.md](sensor-fusion.md)       | EKF/UKF, ICP variants, IMU preintegration, robot\_localization. When to fuse what.                                      |
| [slam-evaluation.md](slam-evaluation.md)   | KITTI, TUM RGB-D, EuRoC, Newer College, Hilti. ATE / RPE / evo. Benchmarking pitfalls.                                  |

***

## What the textbooks don't tell you

A few opinions I've earned the hard way:

1. **The hardest part of SLAM is not SLAM.** It's TF trees, clock synchronization, sensor calibration, deskewing, and outlier handling. Get those right and a mediocre back-end will look great. Get them wrong and the best back-end will diverge.

2. **Loop closure is mostly about descriptors, not optimization.** g2o vs GTSAM vs Ceres for the back-end barely matters — they all converge to the same minimum if your data association is correct. Place recognition (BoW, NetVLAD, Scan Context) is where most loop closure failures live.

3. **IMU preintegration (Forster et al. 2015/2017) changed everything.** Before it, tight visual-inertial coupling was a research curiosity. After it, every modern VIO and LIO system uses it. If you don't know what it is, read [sensor-fusion.md](sensor-fusion.md) before anything else.

4. **GPU SLAM is the present, not the future.** Gaussian splatting, neural fields, GPU ikd-trees — by 2026 the question is no longer "should I use GPU?" but "which parts run where?" My current work at Eternal.ag is exactly this.

5. **Benchmark on your own data.** KITTI is solved. EuRoC is solved. Your warehouse with reflective floors, dynamic forklifts, and a tilted dock leveler is not. See [slam-evaluation.md](slam-evaluation.md).

***

## Canonical references

These are the books and surveys I keep open:

* **Probabilistic Robotics** — Thrun, Burgard, Fox (2005). Still the foundation. Chapters 9-15 cover EKF, particle filter, and GraphSLAM.
* **Factor Graphs for Robot Perception** — Dellaert & Kaess (2017). [Free PDF from author](https://www.cc.gatech.edu/~dellaert/FrankDellaert/Frank_Dellaert/Frank_Dellaert.html) `[verify]`. The mental model for modern SLAM back-ends.
* **State Estimation for Robotics** — Tim Barfoot (2nd ed, 2024). Lie groups, on-manifold optimization, the math under GTSAM.
* **Past, Present, and Future of SIM — Cadena et al. (2016)** — [arxiv.org/abs/1606.05830](https://arxiv.org/abs/1606.05830). The "where is SLAM going" survey everyone cites.
* **Visual SLAM survey** — Macario Barros et al. (2022). [arxiv.org/abs/2209.02786](https://arxiv.org/abs/2209.02786) `[verify]`.

***

## Cross-references in this handbook

* [Polka](../authors-projects/polka.md) — my multi-LiDAR fusion + deskewing node. Deskewing is covered in depth in [lidar-slam.md](lidar-slam.md).
* [GO-SLAM (Pan's)](../authors-projects/go-slam.md) — my from-scratch GICP + pose-graph SLAM. Linked from [lidar-slam.md](lidar-slam.md) and called out in [learned-slam.md](learned-slam.md) to disambiguate from the ICCV 2023 paper of the same name.
* [Cameras, Depth Sensors and LiDAR](../ml-and-perception/cameras-depth-sensors-and-lidar.md) — sensor-level details that SLAM builds on.
* [Linear Algebra for Robotics](../mathematical-and-programming-foundations/linear-algebra-for-robotics.md) — SE(3), rotations, the linear algebra under every estimator on this page.
