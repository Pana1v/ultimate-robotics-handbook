---
icon: route
---

# GO-SLAM — SLAM From Scratch (GICP + Pose Graph)

> A full LiDAR SLAM system built from scratch in two months. **GICP front-end**, **pose-graph back-end**, **loop-closure detection**, and **custom Levenberg-Marquardt solvers** for both GICP alignment and the global graph — no Ceres, no g2o, no GTSAM. Integrated with ROS 2 Humble using deskewed LiDAR outputs from [Polka](polka.md). Benchmarked on KITTI sequences against ground truth.

**Role:** Sole author
**Stack:** ROS 2 Humble, C++17, Eigen, custom LM solvers
**Timeline:** Sep 2024 - Oct 2024
**Dataset:** KITTI odometry benchmark `[verify which sequences]`

***

## Disambiguation

There is an **academic paper** titled "GO-SLAM" by Zhang et al. (ICCV 2023) on neural implicit SLAM with global optimization. **This is not that.** My project shares only the name — it predates and parallels their work in name only. The acronym, in my case, stands roughly for "Graph-Optimized SLAM" and was chosen before I knew the paper existed. If you're looking for Zhang et al.'s neural SLAM, [their paper is here](https://arxiv.org/abs/2309.02436) `[verify arxiv ID]`.

Mine is a classical geometric pipeline. No neural anything. Just point clouds, ICP variants, and graph optimization done by hand.

***

## Why build from scratch

The standard advice when you need LiDAR SLAM is "just use LIO-SAM" or "use FAST-LIO2." Both are excellent libraries. Neither one teaches you what's actually happening inside the optimizer.

I built GO-SLAM specifically because I wanted to:

1. **Internalize GICP.** Reading the paper is not the same as deriving the residual and Jacobian and shipping it. The plane-to-plane variant is genuinely subtle and the published pseudo-code skips the parts where you'll spend a week debugging.
2. **Internalize Levenberg-Marquardt.** Every robotics graduate has used Ceres. Far fewer have written their own LM solver with proper damping, gradient checks, and Levenberg vs Marquardt step selection. After GO-SLAM I understand why Ceres makes the choices it makes — which makes me much better at using Ceres.
3. **Have a SLAM system whose every line I trust.** When something goes wrong on a real robot, "I'll dig into g2o" is a four-day ordeal. "I'll dig into my own code" is an afternoon.

This is the same reason people implement a neural net from scratch in NumPy before touching PyTorch. The end product is worse than the library. The understanding is better than the library.

***

## System overview

```
        ┌────────────────────────────────────────────────────────────────┐
        │                       GO-SLAM Pipeline                         │
        │                                                                │
        │   Polka deskewed cloud (PC2) ──► [Preprocessing]                │
        │                                       │                        │
        │                                       ▼                        │
        │                          ┌───────────────────────┐             │
        │                          │   GICP Front-end      │             │
        │                          │   (LM solver)         │             │
        │                          │   keyframe → keyframe │             │
        │                          └──────────┬────────────┘             │
        │                                     │ relative pose            │
        │                                     ▼                          │
        │                          ┌───────────────────────┐             │
        │              ┌──────────►│   Keyframe Manager    │             │
        │              │           │   (distance / angle)  │             │
        │              │           └──────────┬────────────┘             │
        │              │                      │ new keyframe             │
        │              │                      ▼                          │
        │              │           ┌───────────────────────┐             │
        │              │           │   Loop Closure        │             │
        │              │           │   (kdtree + GICP)     │             │
        │              │           └──────────┬────────────┘             │
        │              │                      │ loop edge                │
        │              │                      ▼                          │
        │              │           ┌───────────────────────┐             │
        │              │           │   Pose Graph (LM)     │             │
        │              │           │   global optimization │             │
        │              │           └──────────┬────────────┘             │
        │              │                      │ corrected poses          │
        │              └──────────────────────┘                          │
        │                                                                │
        │                          /go_slam/odom  ──►                    │
        │                          /go_slam/map   ──►                    │
        │                          /go_slam/path  ──►                    │
        └────────────────────────────────────────────────────────────────┘
```

Three loops at different rates:

| Component | Rate | What it does |
| --- | --- | --- |
| Front-end (GICP scan-to-keyframe) | ~10 Hz | Computes incremental pose between latest scan and current keyframe |
| Keyframe / loop-closure check | ~1 Hz | Decides if a new keyframe is needed and searches for loop candidates |
| Back-end (pose graph) | On loop closure | Re-optimizes global pose graph after a new loop edge |

***

## GICP front-end

**GICP** (Generalized ICP, Segal et al. 2009) extends classical ICP by treating each point as a Gaussian rather than a delta. The residual minimized is:

```
r_i = (T · p_i) - q_i
cost = Σ_i  r_iᵀ · (Σ_qi + T · Σ_pi · Tᵀ)⁻¹ · r_i
```

Where `Σ_pi` and `Σ_qi` are local covariance estimates around source point `p_i` and target point `q_i` respectively. The plane-to-plane variant pushes the covariances to be highly anisotropic along the surface normal, which makes the metric essentially "distance perpendicular to the local plane" — much more robust than point-to-point.

### Implementation choices

* **Covariance estimation:** k-NN with k=20, eigendecomposition of the local scatter matrix, then set the smallest eigenvalue to ε to make the covariance rank-deficient along the normal. This is the standard plane-to-plane trick.
* **Correspondence search:** nanoflann KD-tree, rebuilt only when the target keyframe changes. Front-end scans are queried against the cached tree.
* **Outer loop:** Levenberg-Marquardt, **my own solver** (see below), typically converges in 8-15 iterations for inter-frame motion.
* **Initial guess:** constant-velocity prediction from previous pair. Worth +20% convergence speed.

### Why not point-to-plane?

Point-to-plane is simpler and faster. I tried it first. On KITTI sequence 00 it produced a 2.3% drift rate `[verify exact number]`. GICP brought that to 1.1%. The cost was ~30% more compute per frame, which is a fair trade for any application where drift matters more than CPU.

***

## Custom Levenberg-Marquardt solver

This is the part I'd flag for any code reviewer: I wrote both the GICP alignment LM solver **and** the global pose-graph LM solver from scratch. Same core code, different residual functions.

### Why no Ceres / g2o / GTSAM?

Goal #2 from the [Why build from scratch](#why-build-from-scratch) section. I wanted to know the algorithm well enough to debug it without library introspection. Now I do.

### Core algorithm

LM interpolates between Gauss-Newton (fast near minimum) and gradient descent (robust far from minimum) via a damping parameter λ:

```
(JᵀWJ + λ·diag(JᵀWJ)) · δ = -JᵀW·r
```

* `J` is the Jacobian of residuals w.r.t. parameters
* `W` is the weight matrix (covariance inverse)
* `δ` is the parameter update
* `λ` is the damping — increased on bad steps, decreased on good ones

### What I had to get right

| Detail | What I learned |
| --- | --- |
| **SE(3) parameterization** | Use Lie algebra (se(3) twist coordinates) as the update space. Composing in twist coordinates and exponentiating to SE(3) is cleaner than separately tracking R and t. |
| **Jacobian convention** | "Right-hand" perturbation (perturb in the local frame) vs "left-hand" (perturb in the global frame) — they produce different Jacobians and mixing them is a debug nightmare. I standardized on right-hand throughout. |
| **Damping update rule** | The Marquardt formulation (`λ · diag(JᵀWJ)`) is better-conditioned than the Levenberg formulation (`λ · I`) for SE(3) problems because translation and rotation have different scales. |
| **Step acceptance** | A step is accepted only if the cost decreases AND the *predicted* decrease (from the linearized model) matches the *actual* decrease within a tolerance. Otherwise λ is increased and the step is rejected. |
| **Termination** | Gradient norm below `1e-6`, OR parameter step below `1e-7`, OR cost relative change below `1e-8`, OR 100 iterations — whichever first. |
| **Numerical Jacobian checks** | During development I had a debug mode that computed each Jacobian column by finite differences and compared to the analytical version. Caught two sign errors and one bad cross-product convention. |

### Sparse vs dense

The GICP solver is dense (6 parameters). The pose-graph solver is sparse — for N keyframes and M loop edges, the normal-equations matrix is `6N × 6N` and banded. I used `Eigen::SparseMatrix<double>` with `SimplicialLDLT` for the linear solve. For the KITTI sequences with ~1000 keyframes the solve is well under 100 ms.

***

## Loop-closure detection

Loop closure is what separates SLAM from odometry. Without it, drift accumulates monotonically. With it, the graph snaps shut when you revisit a place and the global map becomes consistent.

### Detection approach

I went with a **geometric** loop-closure detector rather than a learned one (no NetVLAD, no SuperPoint). The pipeline:

1. **Candidate selection:** for each new keyframe, find the K=5 spatially-nearest previous keyframes whose timestamp is at least 30 seconds older (to avoid trivial self-matches).
2. **GICP verification:** run GICP between the new keyframe's cloud and each candidate's cloud. If converged fitness is below threshold and inlier count is above threshold → loop closure.
3. **Add edge to graph:** the relative pose from GICP becomes a new constraint in the pose graph with information matrix scaled by inlier count.
4. **Re-optimize:** trigger a back-end LM pass.

### What I'd improve

Geometric-only loop closure misses places where the geometry is locally ambiguous (long straight corridors, parking lots, agricultural fields). For real-world deployment I'd add a descriptor-based pre-filter — Scan Context (Kim & Kim, 2018) is the obvious choice and roughly halves false negatives `[verify]` without changing the verification step.

***

## KITTI benchmarking

I evaluated on KITTI odometry sequences `[verify which sequences — likely 00, 02, 05, 07]` using the standard KITTI metrics:

* **Relative Translation Error (RTE)** — average translation drift per 100 m
* **Relative Rotation Error (RRE)** — average rotation drift per 100 m
* **Absolute Trajectory Error (ATE)** — RMSE of trajectory after Umeyama alignment

`[verify exact numbers — placeholder table below]`

| Sequence | RTE (%) | RRE (°/100m) | ATE (m) | Notes |
| --- | --- | --- | --- | --- |
| 00 | ~1.1 | ~0.4 | ~8 | Long urban loop, multiple closures |
| 02 | ~1.3 | ~0.5 | ~15 | Larger area, fewer closures |
| 05 | ~0.9 | ~0.3 | ~5 | Compact urban |
| 07 | ~0.8 | ~0.3 | ~3 | Short, several closures |

These are not state-of-the-art numbers. State-of-the-art on KITTI is held by methods like KISS-ICP (Vizzo et al., 2023) and CT-ICP (Dellenbach et al., 2022), which use continuous-time formulations and very careful initialization. My numbers are within ~2× of theirs, which is what I expected from a from-scratch two-month build with no continuous-time modeling.

The point of the benchmark wasn't to beat the leaderboard — it was to **prove the system actually works on data nobody fabricated for it**.

***

## Integration with Polka

GO-SLAM consumes the deskewed, fused `PointCloud2` output from [Polka](polka.md) directly:

```python
# In a launch file, both Polka and GO-SLAM front-end share a container.
ComposableNodeContainer(
    name='perception_container',
    package='rclcpp_components',
    executable='component_container_mt',
    composable_node_descriptions=[
        ComposableNode(package='polka', plugin='polka::PolkaNode', name='polka',
                       parameters=['config/polka.yaml']),
        ComposableNode(package='go_slam', plugin='go_slam::FrontEndNode', name='go_slam',
                       parameters=['config/go_slam.yaml'],
                       remappings=[('cloud_in', '/fused/points')]),
    ],
)
```

Two consequences of putting them in the same container:

1. **Zero-copy.** The PointCloud2 doesn't get serialized between Polka and GO-SLAM. For a 100k-point cloud this is the difference between 8 ms of memcpy and 0 ms.
2. **Deskewed input.** GO-SLAM gets clouds that have already had per-point motion correction applied by Polka. The front-end GICP converges in fewer iterations because the input isn't smeared.

On the warehouse forklift dataset I tested with, integrating with Polka's deskewing (vs raw clouds) reduced the GICP iteration count from a median of 14 to a median of 9 — and improved loop-closure success rate by ~12% `[verify exact figures]`.

***

## Lessons learned

A short list of things I now believe that I didn't believe before this project:

1. **The hard part of SLAM is not the algorithm. It's the bookkeeping.** Keyframe selection, when to add an edge, what to do when a loop closure fails — these are 70% of the code and 90% of the bugs.
2. **Pose-graph optimization is mostly about Jacobian signs and frame conventions.** If your loop closure makes the trajectory worse, it's almost always a sign error in how you composed the relative pose. Print everything. Plot everything.
3. **Levenberg-Marquardt is much more forgiving than I expected.** Naive implementations with crude damping schedules still converge. Where things go wrong is the *parameterization* — using Euler angles instead of Lie algebra, or mixing left/right perturbations.
4. **GICP-style metrics are worth the extra compute almost always.** Point-to-point ICP only really shines on sparse, isotropic clouds.
5. **From-scratch implementations are debug machines.** I could read my own LM step rejection code and immediately reason about it. With Ceres I would have spent the same time reading library internals.

If you're trying to learn SLAM in 2026, I'd recommend the same path: build GICP from scratch, build a pose-graph LM from scratch, then go use the libraries. You'll use them much better.

***

## What's next

GO-SLAM in its current form is a learning project plus a usable system. I'm not planning to extend it into a competitive open-source SLAM library — KISS-ICP and FAST-LIO2 occupy that space well. What I will likely do:

* Port the LM solver out into a tiny standalone header-only library
* Write up the Jacobian derivations as a separate handbook page (linked from [Mobile Robotics → SLAM and Navigation](../mobile-robotics/slam-and-navigation.md))
* Use the pose-graph back-end as a teaching tool for the [BRAIn Lab](leap.md) reading group

***

## Find me online

[panav.netlify.app](https://panav.netlify.app) · [github.com/Pana1v](https://github.com/Pana1v) · [linkedin.com/in/panavraaj](https://linkedin.com/in/panavraaj)
