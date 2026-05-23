---
icon: code
---

# Author's Projects

## About this section

Most "robotics portfolios" you find online are toy demos: a TurtleBot following a line, a Gazebo world with three obstacles, a Jupyter notebook with a pretrained YOLO. This section is the opposite. Everything here is **real work from real production robotics** — code that ships on warehouse AMRs, SLAM stacks that get benchmarked against KITTI ground truth, optimization papers headed for peer review, and challenge submissions that move global leaderboards.

I'm Pan — a 2026 robotics engineer at [Eternal.ag](https://eternal.ag) (Bangalore), previously at 10xConstruction.ai and Addverb Technologies. I graduated IIT Patna with a BTech in Electrical & Electronics Engineering in 2025. The projects below are the ones I keep coming back to: each one taught me something about the gap between "this works on my laptop" and "this works on a robot at 3 AM in a customer's warehouse."

The pages here aren't a CV. They're engineering write-ups — motivation, design choices, what I'd do differently. If you find something useful, copy it. If you find something wrong, [tell me](https://panav.netlify.app).

***

## Projects

### [Polka](polka.md) — Multi-LiDAR Fusion for ROS 2

A single composable node that merges heterogeneous `PointCloud2` and `LaserScan` streams into unified outputs. Per-source filtering, TF2-aligned fusion, optional CUDA acceleration, and IMU-based deskewing with per-source overrides for articulated platforms. Supports both ROS 2 Humble and Jazzy. Built to replace the relay-filter-merge node soup that plagues most multi-LiDAR stacks.

> **Use case:** Production AMR platforms with 2+ LiDARs, mixed 2D/3D, mast-mounted + base-mounted on a yaw-articulated chassis.

***

### [GO-SLAM](go-slam.md) — SLAM From Scratch (GICP + Pose Graph)

A complete SLAM system I built from scratch in two months: GICP front-end, pose-graph back-end, loop closure, and **custom Levenberg-Marquardt solvers** for both alignment and global optimization — no Ceres, no g2o, no GTSAM. Integrated with ROS 2 Humble using deskewed LiDAR from Polka. Benchmarked on KITTI sequences against ground truth.

> **Not** the academic GO-SLAM paper by Zhang et al. (ICCV 2023). Same name, independent project.

***

### [LEAP](leap.md) — Learning-Augmented Exact Optimization for Pick-and-Place

Research at BRAIn Lab, IIT Patna. Pick-and-place sequencing is **not** symmetric TSP — the transition cost depends on which bin the previous item was placed in. LEAP formulates this as asymmetric TSP, replaces the standard Miller-Tucker-Zemlin subtour constraints with a CP-SAT Hamiltonian circuit formulation (5-7× speedup), then uses an imitation-learned heterogeneous GNN to prune the decision-variable space from O(N²) to O(Nk). 17.5× faster than baselines at N=200 with a worst-case optimality gap of 0.06%. Manuscript in preparation.

> **Advisor:** Dr. Atul Thakur, BRAIn Lab IIT Patna.

***

### [BARN Challenge 2026](barn-challenge.md) — Mapless Navigation, Solo Submission

IEEE ICRA BARN Challenge 2026 entry. Clearpath Jackal in Gazebo, 270° sensor coverage, dynamic obstacle fields. I built a **Breadcrumb Explorer** architecture instead of the standard SLAM-based baselines — no map, no laser odometry, just an odom-frame memory of "tasty" vs "stale" trajectories that improves over repeated trials. First submission scored **0.3682/0.5** — the highest score by an Indian team since the benchmark began in 2022. Physical finals in Vienna.

***

## Reading order

If you're here from my resume or LinkedIn and want the fastest path through this section:

1. Skim [Polka](polka.md) for the **engineering depth** signal (composable nodes, TF2, CUDA, IMU deskewing).
2. Read [GO-SLAM](go-slam.md) for the **fundamentals** signal (custom optimizers, no libraries).
3. Read [LEAP](leap.md) for the **research** signal (problem formulation, CP-SAT, GNN pruning).
4. Read [BARN](barn-challenge.md) for the **shipping under pressure** signal (solo, leaderboard, finals).

Each page is self-contained. Cross-references are linked where they're load-bearing — Polka feeds deskewed clouds into GO-SLAM, for example, and LEAP connects to the Robot Learning material elsewhere in this handbook.

***

## Find me online

[panav.netlify.app](https://panav.netlify.app) · [github.com/Pana1v](https://github.com/Pana1v) · [linkedin.com/in/panavraaj](https://linkedin.com/in/panavraaj)
