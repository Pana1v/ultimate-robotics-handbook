---
icon: route
---

# LiDAR SLAM

## Why LiDAR

A LiDAR gives you precise 3D range measurements directly, with none of the texture / lighting / scale ambiguity that haunts visual SLAM. The trade-off is cost (a Velodyne or Ouster used to be $5-30k; cheap solid-state units have brought that down), weight, and power.

But for ground robots in industrial settings, autonomous vehicles, and outdoor robots in 2026, LiDAR + IMU + (optional camera) is the de-facto stack. This page walks the lineage that got us here:

```
LOAM (2014) → LeGO-LOAM (2018) → LIO-SAM (2020) → FAST-LIO / FAST-LIO2 (2021/2022)
                                              ↘
                                                KISS-ICP (2023) — the minimalist counter-revolution
```

Each step solved a specific weakness of the previous one. Knowing why each happened tells you where SLAM is going.

***

## The problem nobody warned you about: deskewing

Before any LiDAR SLAM math, the most common cause of bad results: **motion-distorted point clouds.**

A spinning LiDAR doesn't capture a frame instantaneously. A 10 Hz Velodyne or Ouster sweeps 360° in 100 ms. If the robot moves during that 100 ms (and it does — that's the whole point), then points captured at the start of the sweep and at the end are in different reference frames *within the same scan*.

If you treat the scan as if it were captured at a single timestamp, you get a smeared point cloud. Walls bow. Corners ghost. ICP fails because it's trying to match a deformed source to a clean target.

**Deskewing** is the operation of un-warping a scan back to a single reference time, typically using IMU integration to know how the LiDAR moved during the sweep.

The basic recipe:

1. Each point $p_i$ has a timestamp $t_i$ (most modern drivers expose this; if yours doesn't, your driver is broken — fix it).
2. Integrate IMU between scan-start time $t_0$ and $t_i$ to get the relative transform $\mathbf{T}(t_0, t_i)$.
3. Transform the point back: $p_i' = \mathbf{T}(t_0, t_i) \cdot p_i$.

The result: every point in the scan is expressed in the body frame at $t_0$. Now you can run ICP, NDT, or feed it to a SLAM stack.

> **Field notes:** I wrote [Polka](../authors-projects/polka.md) specifically because every multi-LiDAR ROS 2 stack I encountered re-implemented deskewing badly. Polka does deskewing + per-source overrides + TF2-aligned fusion in a single composable node — the deskewing layer is the foundation everything else stands on. If your downstream SLAM is misbehaving on a moving platform, deskew first, debug second.

### Other first-class preprocessing concerns

* **Intensity / reflectivity normalization** — useful if your front-end uses intensity (LeGO-LOAM does for ground segmentation).
* **Distance filtering** — drop points beyond $d_{max}$ (too noisy) and below $d_{min}$ (often the robot's own chassis).
* **Ring isolation** — many algorithms exploit the ring (laser-channel) structure of a mechanical LiDAR. If you have a solid-state LiDAR with no ring structure, some of these front-ends won't work as-is.
* **Static-frame transformation** — make sure all your LiDARs publish in a consistent base frame. Pose-graph SLAM does not handle silently mis-extrinsicked sensors.

***

## ICP and friends — the kinematic primitive

Every LiDAR SLAM has, at its core, **point cloud registration**: given two clouds, find the transform that aligns them. The family:

### Point-to-Point ICP

The original Besl & McKay (1992) algorithm:

1. For each point in the source cloud, find the nearest point in the target.
2. Compute the rigid transform minimizing the sum of squared point-to-point distances.
3. Apply, repeat to convergence.

Cost function:

$$
E_{PP}(\mathbf{R}, \mathbf{t}) = \sum_i \| \mathbf{R} p_i + \mathbf{t} - q_i \|^2
$$

where $q_i$ is the nearest neighbor of $p_i$ in the target. Closed-form SVD solution per iteration. Simple. **Slow to converge near planar surfaces** because the cost has zero gradient along the planar tangent direction.

### Point-to-Plane ICP

Chen & Medioni (1992). Replace the cost with the squared distance from the source point to the *tangent plane* at the target point:

$$
E_{Pl}(\mathbf{R}, \mathbf{t}) = \sum_i \left( (\mathbf{R} p_i + \mathbf{t} - q_i) \cdot \mathbf{n}_i \right)^2
$$

where $\mathbf{n}_i$ is the surface normal at $q_i$. Massively better convergence on structured indoor/urban scenes. The standard for most LiDAR SLAM front-ends in 2010-2020.

### Generalized ICP (GICP)

Segal, Hähnel, Thrun (2009). Probabilistic generalization: each point has a covariance describing its local surface uncertainty. The cost weights residuals by the combined source + target covariances:

$$
E_{GICP}(\mathbf{T}) = \sum_i d_i^\top (C^B_i + \mathbf{R} C^A_i \mathbf{R}^\top)^{-1} d_i
$$

where $d_i = q_i - (\mathbf{R} p_i + \mathbf{t})$ and $C^A_i$, $C^B_i$ are the local covariances of source and target points.

GICP smoothly interpolates between point-to-point and point-to-plane based on local geometry. Plane-like local structure → behaves like point-to-plane. Isotropic noise → behaves like point-to-point.

> [GO-SLAM](../authors-projects/go-slam.md) uses GICP as its front-end. I picked GICP specifically because it gracefully handles the mix of planar (warehouse walls/floors) and rough (cluttered shelves) geometry that real environments throw at you.

### NDT — the alternative

Normal Distributions Transform (Biber & Strasser 2003). Discretize the target cloud into a 3D grid; in each cell, fit a Gaussian. The cost is now the negative log-likelihood of source points under the target's Gaussian mixture model:

$$
E_{NDT}(\mathbf{T}) = -\sum_i \exp\left(-\frac{1}{2} (\mathbf{T} p_i - \mu_i)^\top \Sigma_i^{-1} (\mathbf{T} p_i - \mu_i)\right)
$$

NDT is differentiable (no nearest-neighbor search inside the inner loop after the grid is built), often faster than ICP for global registration, and handles partial overlap well. Autoware uses NDT for map matching. It's a perfectly fine alternative to ICP — you'll mostly see it in automotive contexts.

### KISS-ICP — what minimalism looks like

Vizzo, Guadagnino, Mersch, Wiesmann, Behley, Stachniss (2023). [arxiv.org/abs/2209.15397](https://arxiv.org/abs/2209.15397). Code: [github.com/PRBonn/kiss-icp](https://github.com/PRBonn/kiss-icp) `[verify]`.

The thesis: most modern LiDAR odometry papers introduce a forest of features, preprocessing tricks, and tuning knobs. KISS-ICP shows you can match (and often beat) them with:

* Point-to-point ICP (not even point-to-plane).
* A *single* adaptive parameter — the maximum correspondence distance, set by the current motion estimate.
* Constant-velocity motion model for prediction.
* No IMU. No features. No machine learning.

The Bonn group (Cyrill Stachniss et al.) showed this beats LIO-SAM and FAST-LIO2 on KITTI in many configurations. The point isn't "KISS-ICP is always best" — it's "your fancy pipeline might not be earning its complexity."

Use KISS-ICP when:
* You want a strong baseline before adding complexity.
* You don't have a good IMU (it'll work without one).
* You want pose estimates from any LiDAR (3D or 2D) with minimal tuning.

***

## IMU preintegration — the LIO unlock

Christian Forster, Luca Carlone, Frank Dellaert, Davide Scaramuzza (2015 / TRO 2017). The paper that made tight IMU-LiDAR (and IMU-visual) fusion practical.

* Paper: [arxiv.org/abs/1512.02363](https://arxiv.org/abs/1512.02363)
* IEEE TRO version: ["On-Manifold Preintegration for Real-Time Visual-Inertial Odometry"](https://ieeexplore.ieee.org/document/7557075) `[verify]`

### The problem

An IMU at 200 Hz gives you a measurement every 5 ms. A LiDAR or camera keyframe is every 100 ms. In between, you have 20 IMU measurements you'd like to fuse.

Naively, you could put each IMU measurement as its own factor in the graph. That's 20× more factors per keyframe — too expensive. But if you marginalize them naively, you'd have to re-integrate the IMU every time the start pose changed, because IMU integration depends on the world-frame attitude (gravity in body frame is "rotated" by the start pose's rotation).

### The insight

Express the IMU "delta" between two keyframes in a way that **does not depend on the starting pose, only on starting biases.** Then:

* When the start pose changes, you don't re-integrate — you just transform the precomputed delta.
* When biases change (during optimization), you apply a *first-order correction* using the precomputed bias Jacobians.

The preintegrated quantities are:

$$
\Delta \mathbf{R}_{ij}, \quad \Delta \mathbf{v}_{ij}, \quad \Delta \mathbf{p}_{ij}
$$

— relative rotation, velocity, and position change between keyframes $i$ and $j$, expressed in the body frame at $i$. Plus the bias Jacobians:

$$
\frac{\partial \Delta \mathbf{R}}{\partial b_g}, \quad \frac{\partial \Delta \mathbf{v}}{\partial b_a}, \quad \ldots
$$

In the graph, you add a single **IMU factor** between consecutive keyframes that constrains the relative motion and the biases. GTSAM has this built in (`PreintegratedImuMeasurements`), which is why LIO-SAM and many other VIO/LIO systems were built on top of GTSAM.

If you don't internalize anything else about modern SLAM, internalize preintegration. Every tightly-coupled VIO and LIO since 2017 uses it.

***

## LOAM and its descendants

### LOAM (2014)

Zhang & Singh. [Paper (RSS 2014)](http://www.roboticsproceedings.org/rss10/p07.pdf) `[verify]`. The first LiDAR odometry to crack KITTI's top of the leaderboard.

Key ideas:

* Extract two feature types per scan ring: **edge points** (high curvature) and **planar points** (low curvature).
* Two-stage processing:
  * High-frequency *odometry* thread: scan-to-scan registration at scan rate (10 Hz).
  * Low-frequency *mapping* thread: scan-to-map registration against an accumulated voxel map, slower but more accurate.
* The odometry de-skews points using its own velocity estimate. (Bootstrap-y, but works.)

No IMU. No loop closure. Pure LiDAR odometry. The blueprint everyone copied.

* Open-source re-implementation: [A-LOAM](https://github.com/HKUST-Aerial-Robotics/A-LOAM) `[verify]` — easier to read than the original CMU code.

### LeGO-LOAM (2018)

Shan & Englot. [IROS 2018](https://ieeexplore.ieee.org/document/8594299) `[verify]`. Code: [github.com/RobustFieldAutonomyLab/LeGO-LOAM](https://github.com/RobustFieldAutonomyLab/LeGO-LOAM) `[verify]`.

LOAM was designed for cars on roads. LeGO-LOAM ("Lightweight and Ground-Optimized LOAM") added:

* **Ground segmentation** as a first-class step. Ground points constrain roll/pitch/Z; non-ground points constrain yaw/X/Y. Two separate two-step optimizations.
* **Loop closure** with ICP-based scan matching against past keyframes.
* Lower compute — suitable for ground UGVs, not just KITTI cars.

LeGO-LOAM is what most people meant when they said "LOAM" for a few years.

### LIO-SAM (2020)

Shan, Englot, Meyers, Wang, Ratti, Rus. [IROS 2020](https://arxiv.org/abs/2007.00258). Code: [github.com/TixiaoShan/LIO-SAM](https://github.com/TixiaoShan/LIO-SAM) `[verify]`.

The next leap: tightly-coupled LiDAR-IMU-GPS via factor graphs.

* Pre-integrates IMU between LiDAR keyframes (Forster et al. preintegration).
* Uses GTSAM's iSAM2 as the back-end — incremental smoothing over the pose graph.
* Four factor types: IMU preintegration, LiDAR odometry, GPS (optional), and loop closure.
* Loop closure via Euclidean-distance + ICP verification. Scan-Context can be slotted in for stronger place recognition.

The architecture is everything you want in a production LiDAR SLAM: tight IMU integration for high-rate state, optional GPS fusion for global anchoring, factor graph for loop closure, sensible scan-matching front-end.

> **Field notes:** LIO-SAM on a rough outdoor traverse is hard to beat in 2026 if you have a good IMU and don't mind the compute. On rough terrain with frequent revisits, its loop closure pulled my trajectory back into alignment in scenarios where pure odometry (FAST-LIO2) drifted away.

### FAST-LIO / FAST-LIO2 (2021 / 2022)

Xu, Cai, He, Lin, Zhang. From the MARS Lab at HKU.

* FAST-LIO paper (2021): [arxiv.org/abs/2010.08196](https://arxiv.org/abs/2010.08196)
* FAST-LIO2 paper (2022): [arxiv.org/abs/2107.06829](https://arxiv.org/abs/2107.06829)
* Code: [github.com/hku-mars/FAST\_LIO](https://github.com/hku-mars/FAST_LIO) `[verify]`

The thesis: do tight LiDAR-IMU fusion *without* a factor graph back-end. Just an **Iterated Extended Kalman Filter** that lives entirely on-manifold ($SO(3) \times \mathbb{R}^n$).

Key contributions:
* **Direct raw-point registration**, no feature extraction. Every LiDAR point becomes a measurement in the EKF update.
* **ikd-Tree** (incremental k-d tree, Cai, Xu, Zhang 2021) for the local map. Insert / delete / nearest-neighbor in one structure with bounded memory. This was the engineering unlock.
* Iterated update — re-linearize the measurement model around the latest estimate inside the update step.
* No loop closure (in the base version).

FAST-LIO2 beats LIO-SAM on accuracy and *massively* on CPU. It runs comfortably on a single core. The lack of loop closure is a feature in some settings (no warping artifacts) and a bug in others (drift on long traverses).

> **Field notes:** I've run FAST-LIO2 and LIO-SAM head to head on the same rough-terrain dataset. FAST-LIO2 won on CPU usage (~1 core vs ~3) and short-traverse accuracy. LIO-SAM won on long traverses with loop closures because it could close them. Pick based on whether you can afford the ikd-tree memory (FAST-LIO2 trims it aggressively but it's still RAM) and whether your traverses will revisit (LIO-SAM closes loops, FAST-LIO2 doesn't).

### Beyond — the 2023-2025 landscape

* **Point-LIO** (Xu et al. 2023) — per-point continuous-time IMU fusion, better at very high motions.
* **DLO / DLIO** (Chen et al. 2022, 2023) — Direct LiDAR (Inertial) Odometry. Lightweight, popular for drones.
* **GLIM** (Koide 2024) — GPU-accelerated graph-based LiDAR-IMU mapping. [arxiv.org/abs/2407.10344](https://arxiv.org/abs/2407.10344) `[verify]`.
* **MULLS** (Pan, Zhang, Wang 2021) — multi-metric linear least-squares LiDAR odometry.

And the GO-SLAM-style learned approaches — see [learned-slam.md](learned-slam.md).

***

## Comparison

| System         | IMU coupling | Back-end       | Loop closure        | CPU cost   | Best for                                 |
| -------------- | ------------ | -------------- | ------------------- | ---------- | ---------------------------------------- |
| LOAM / A-LOAM  | None         | Frame-by-frame | No                  | Moderate   | Reading the original ideas                |
| LeGO-LOAM      | Loose        | Pose graph (g2o-style) | ICP-based   | Low        | Ground UGVs, baseline                     |
| LIO-SAM        | Tight (preint.) | GTSAM iSAM2 | Yes                 | High       | Production outdoor robots with revisits   |
| FAST-LIO2      | Tight (IEKF) | None (filter)  | No                  | **Very low** | Drones, CPU-constrained, no revisits   |
| Point-LIO      | Tight        | IEKF           | No                  | Moderate   | Aggressive motion                         |
| KISS-ICP       | None         | None           | No                  | Low        | Strong minimal baseline                   |
| GLIM           | Tight        | Graph, GPU     | Yes                 | GPU       | Heavy mapping workloads                   |

### Cross-references in this handbook

* [Polka](../authors-projects/polka.md) — multi-LiDAR fusion + IMU-deskew + per-source overrides. The preprocessing layer that feeds any of the systems above.
* [GO-SLAM (Pan's)](../authors-projects/go-slam.md) — my from-scratch SLAM with GICP front-end + custom LM pose-graph solver. (Not to be confused with the ICCV 2023 academic paper of the same name — see [learned-slam.md](learned-slam.md).)
* [Sensor fusion](sensor-fusion.md) — EKF/UKF basics, ICP variants in depth, IMU preintegration the math.

***

## What I'd build with today

* **3D LiDAR ground robot, indoor + outdoor mix, modest CPU:** FAST-LIO2 + Scan-Context loop closure layer + offline pose-graph refinement when needed. This is roughly what FR-LIO and similar derivatives do.
* **Outdoor robot with rough terrain and frequent revisits:** LIO-SAM. The loop closure is non-optional.
* **Aerial robot:** FAST-LIO2 or DLIO. CPU matters more than loop closure.
* **Autonomous vehicle scale (kilometers of trajectory):** GLIM if you have GPU; LIO-SAM + GPS otherwise.
* **Custom SLAM as a learning project:** roll your own. GICP front-end, custom LM solver, pose-graph back-end, Scan-Context for loop closure. That's roughly what I did with GO-SLAM. The implementation pain teaches you more than any paper.

Continue to [learned-slam.md](learned-slam.md) for the neural / Gaussian-splat side of LiDAR/RGB SLAM, or [sensor-fusion.md](sensor-fusion.md) for the math under all of the above.
