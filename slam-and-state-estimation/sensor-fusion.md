---
icon: route
---

# Sensor Fusion & State Estimation

## What this page is

SLAM is a special case of state estimation where one of the things you're estimating is the map. This page covers the more general problem: given a robot with $N$ sensors of different rates, accuracies, and biases, how do you produce one consistent estimate of where the robot is and how it's moving?

The math underneath is exactly the math from [filter-slam.md](filter-slam.md) and [graph-slam.md](graph-slam.md) — Bayesian filters and factor graphs. But the framing here is different: you usually have a known map (or no map at all), and the goal is *robust, high-rate state estimation* for control.

I'll cover three things:

1. **EKF / UKF for state estimation** — the workhorse for fusing IMU + wheel odometry + GPS + LiDAR + camera.
2. **ICP variants in depth** — the most common single fusion primitive in modern SLAM (matching new sensor data against a previous estimate).
3. **IMU preintegration** — what made tight visual-inertial and LiDAR-inertial fusion practical.

***

## The fusion question, properly framed

You have:
* A *prediction* of the state from one source (usually a high-rate IMU or motion model).
* A *correction* from another source (lower-rate but more accurate: GPS, LiDAR scan match, camera).

You want to combine them. The optimal Bayesian combiner is:

$$
p(x \mid z_1, z_2) \propto p(z_1 \mid x) p(z_2 \mid x) p(x)
$$

For Gaussians, this collapses to the Kalman update:

$$
x_{fused} = x_{pred} + K (z - H x_{pred})
$$

$$
K = P H^\top (H P H^\top + R)^{-1}
$$

where $K$ is the Kalman gain, $P$ is the prior covariance, and $R$ is the measurement covariance. This is the **only thing happening** in 95% of robot state estimators — even if it's wrapped in a fancy filter class with 20 parameters.

The art is:
* Picking the right *state representation* (Euclidean? on a Lie group? error-state?).
* Modeling the *noise covariances* correctly (this is where most filters fail in practice).
* Handling *outliers* (a single bad GPS jump can derail the filter).
* Handling *time synchronization* between sensors.

***

## EKF and UKF for state estimation

### EKF — the default

For a state $\mathbf{x} \in \mathbb{R}^n$ with nonlinear motion $f(x, u)$ and measurement $h(x)$ models, the EKF linearizes at the current mean and applies the Kalman update.

**Predict:**

$$
\hat{x}_{k|k-1} = f(\hat{x}_{k-1}, u_k)
$$

$$
P_{k|k-1} = F_k P_{k-1} F_k^\top + Q_k
$$

**Update:**

$$
y_k = z_k - h(\hat{x}_{k|k-1})
$$

$$
S_k = H_k P_{k|k-1} H_k^\top + R_k
$$

$$
K_k = P_{k|k-1} H_k^\top S_k^{-1}
$$

$$
\hat{x}_k = \hat{x}_{k|k-1} + K_k y_k
$$

$$
P_k = (I - K_k H_k) P_{k|k-1}
$$

with $F_k = \partial f / \partial x$ and $H_k = \partial h / \partial x$.

The EKF is fast, well-understood, and works when the nonlinearity isn't too bad relative to the noise. It fails when:
* The state lives on a manifold (rotations) and you treat it as Euclidean.
* The linearization point is far from the true state (initialization, large updates).
* Noise is heavy-tailed (outliers).

### UKF — the better-behaved cousin

The Unscented Kalman Filter (Julier & Uhlmann 1997) avoids linearization. Instead, it picks $2n+1$ **sigma points** that summarize the prior mean and covariance, propagates each through the *nonlinear* motion / measurement model, and refits a Gaussian to the propagated cloud.

* Captures the mean / covariance of a transformed Gaussian to second order (third for symmetric distributions), vs first for EKF.
* No Jacobian needed.
* About 2-3× more expensive than EKF per step.

In SLAM you'll see UKF mostly in VIO papers where IMU integration is highly nonlinear, but ESKF / IEKF have largely replaced it.

### Error-State Kalman Filter (ESKF)

The ESKF (Sola 2017) is the right way to do EKF when the state lives on a Lie group (rotations, SE(3) poses).

* Maintain a **nominal state** (the current best estimate) and an **error state** (a small perturbation in the tangent space).
* The error state lives in $\mathbb{R}^n$ — flat — so all the EKF math works.
* On update, the error correction is **injected** back into the nominal state via the manifold retraction (e.g., compose rotations).
* The error state is reset to zero after each update.

This is the canonical pattern for IMU integration in modern VIO and LIO. FAST-LIO2's filter is an *iterated* ESKF (re-linearize the measurement model inside the update loop) operating on $SE(3) \times \mathbb{R}^{velocity} \times \mathbb{R}^{biases}$.

Reading: **Joan Sola, "Quaternion kinematics for the error-state Kalman filter."** [arxiv.org/abs/1711.02508](https://arxiv.org/abs/1711.02508). The clearest derivation of ESKF for IMU integration.

### IEKF

The Invariant Extended Kalman Filter (Barrau & Bonnabel 2017). [arxiv.org/abs/1410.1465](https://arxiv.org/abs/1410.1465) `[verify]`. For state spaces with group structure (like $SE(3)$), the IEKF defines the error in a way that's invariant under group actions — leading to better consistency properties than the standard EKF on rotation states. Used in FAST-LIO2.

If you're writing a paper, use it and cite Barrau-Bonnabel. If you're shipping a product, ESKF is fine for the most part — the consistency gap matters mostly when biases are poorly observable.

***

## robot_localization — the ROS workhorse

In ROS 2, the de facto multi-sensor EKF is **`robot_localization`** (Tom Moore, formerly Locus Robotics; now widely maintained).

* Repo: [github.com/cra-ros-pkg/robot\_localization](https://github.com/cra-ros-pkg/robot_localization) `[verify]`
* Two nodes: `ekf_node` and `ukf_node`. EKF is the right default.

What it does:
* Fuses any number of `nav_msgs/Odometry`, `geometry_msgs/PoseWithCovarianceStamped`, `geometry_msgs/TwistWithCovarianceStamped`, and `sensor_msgs/Imu` streams.
* You declare which dimensions of each input to fuse (e.g., "use only x/y/yaw from this Odometry") and the EKF handles the rest.
* Publishes a single fused odometry estimate, typically in the `odom` frame.

The standard two-EKF pattern:

* **Local EKF** in `odom` frame: fuses IMU + wheel odom for high-rate, smooth, drifting estimate.
* **Global EKF** in `map` frame: fuses local odom + GPS (via `navsat_transform_node`) + AMCL / SLAM pose for global, jumpy-but-correct estimate.

This is the recommended ROS 2 setup for any outdoor wheeled robot.

> **Field notes:** the most common `robot_localization` failure I've seen is people fusing both wheel-odom *position* and IMU *yaw* into the same EKF without disabling wheel-odom yaw. The two yaw sources disagree and the filter jitters. Rule of thumb: each measurement dimension (x, y, z, roll, pitch, yaw, vx, vy, vz, etc.) should be fused from exactly one source. The other sources should have that dimension marked `false`.

***

## My Eternal.ag context

For background: at Eternal.ag in 2026 I work on a multimodal EKF state estimator that fuses 3D ICP scan matches with IMU and wheel encoders at high frequency. The pattern is roughly:

* **IMU pre-integration** drives the high-rate prediction (200 Hz).
* **3D ICP** between the latest scan and a local sliding-window map produces relative-pose measurements at ~10 Hz.
* **Wheel encoder velocity** acts as a slow constraint when the robot is stationary or moving slowly (anti-drift when ICP doesn't have enough geometric constraint).
* An **error-state EKF** on $SE(3) \times \mathbb{R}^{velocity} \times \mathbb{R}^{biases}$ fuses all three.

The reason for an EKF at this layer (rather than a graph) is *latency*. Control loops need pose at 200 Hz with sub-millisecond filter cost. A factor graph back-end runs alongside this at a lower rate to keep the map consistent over long traverses. This split — fast filter for state, slow graph for map — is the production pattern for most modern SLAM stacks.

***

## ICP variants in depth

Most fusion of point clouds against a map / previous frame is done with some ICP variant. I covered the high-level taxonomy in [lidar-slam.md](lidar-slam.md). Here's the math in more depth.

### Point-to-Point

For each source point $p_i$, find target nearest neighbor $q_i$. Minimize:

$$
E = \sum_i \| \mathbf{R} p_i + \mathbf{t} - q_i \|^2
$$

Closed-form solution per iteration via SVD:

1. Compute centroids $\bar{p}, \bar{q}$.
2. Build cross-covariance $H = \sum_i (p_i - \bar{p})(q_i - \bar{q})^\top$.
3. SVD: $H = U \Sigma V^\top$.
4. Rotation: $\mathbf{R} = V U^\top$ (with a sign correction if $\det(VU^\top) < 0$).
5. Translation: $\mathbf{t} = \bar{q} - \mathbf{R} \bar{p}$.

Apply, recompute correspondences, repeat. Converges in 10-50 iterations for good initializations.

### Point-to-Plane

Replace the cost with squared distance to the tangent plane at the target point:

$$
E = \sum_i \left( (\mathbf{R} p_i + \mathbf{t} - q_i) \cdot \mathbf{n}_i \right)^2
$$

No closed form for the SVD trick because the cost is no longer isotropic in residuals. Solve via Gauss-Newton: linearize the rotation as $\mathbf{R} \approx \mathbf{I} + [\boldsymbol{\omega}]_\times$ for small $\boldsymbol{\omega}$, solve a 6-DoF linear system per iteration.

The convergence is dramatically better for planar / urban scenes. Each iteration is more expensive, but you need fewer of them.

### GICP (Generalized ICP)

Segal, Hähnel, Thrun (2009). The probabilistic generalization. Each point has a local covariance $C_i$ (estimated from its neighbors — typically planar surfaces have a thin covariance along the surface normal). The cost:

$$
E = \sum_i d_i^\top (C^B_i + \mathbf{R} C^A_i \mathbf{R}^\top)^{-1} d_i
$$

where $d_i = q_i - (\mathbf{R} p_i + \mathbf{t})$. The weighting naturally interpolates between point-to-point (isotropic covariances) and point-to-plane (one tiny eigenvalue along the surface normal).

Solve via Gauss-Newton, just like point-to-plane. Reference implementation: PCL's `pcl::GeneralizedIterativeClosestPoint`. Used in [GO-SLAM](../authors-projects/go-slam.md) and many production LiDAR SLAM pipelines.

### Trimmed / Robust ICP

To handle outliers: at each iteration, sort the residuals and only keep the bottom 80% (or use a Huber kernel). Non-overlapping regions and dynamic objects no longer pull the alignment.

### Multi-resolution / Coarse-to-fine

Downsample both clouds to a coarse resolution, align, then refine at the next resolution down. Faster than running full-resolution ICP from a poor initial guess.

### Initialization matters more than the variant

ICP is a local optimizer. If you start it from a 30° off initial guess, every variant fails. Get the initial guess right (via IMU integration, constant-velocity prediction, or feature-based registration) and the variant choice matters far less than people think.

***

## IMU preintegration — the math

Cover this in [lidar-slam.md](lidar-slam.md) at the conceptual level. Here's the math more carefully.

### What an IMU measures

A 6-axis IMU at time $t$ gives you:

$$
\tilde{\boldsymbol{\omega}}_t = \boldsymbol{\omega}_t + b^g_t + n^g_t
$$

$$
\tilde{\mathbf{a}}_t = \mathbf{R}_t^\top (\mathbf{a}^W_t - \mathbf{g}^W) + b^a_t + n^a_t
$$

— angular velocity and specific force in the body frame, corrupted by gyro/accel biases and noise. ($\mathbf{g}^W$ is gravity in world frame, $\mathbf{a}^W$ is true acceleration.)

To get pose, you'd naively integrate:

$$
\mathbf{R}_{t+\Delta t} = \mathbf{R}_t \exp([\tilde{\boldsymbol{\omega}}_t - b^g_t]_\times \Delta t)
$$

$$
\mathbf{v}^W_{t+\Delta t} = \mathbf{v}^W_t + (\mathbf{R}_t (\tilde{\mathbf{a}}_t - b^a_t) - \mathbf{g}^W) \Delta t
$$

$$
\mathbf{p}^W_{t+\Delta t} = \mathbf{p}^W_t + \mathbf{v}^W_t \Delta t + \frac{1}{2}(\mathbf{R}_t (\tilde{\mathbf{a}}_t - b^a_t) - \mathbf{g}^W) \Delta t^2
$$

Problem: every step depends on $\mathbf{R}_t$ and $\mathbf{v}^W_t$, which depend on the starting state. If you're optimizing the starting state in a graph, you'd have to re-integrate every iteration.

### Forster et al.'s trick

Reformulate the integration so the precomputed quantities don't depend on the starting state — only on the **biases** (which change slowly).

Specifically, between keyframes $i$ and $j$, define:

$$
\Delta \mathbf{R}_{ij} = \mathbf{R}_i^\top \mathbf{R}_j
$$

$$
\Delta \mathbf{v}_{ij} = \mathbf{R}_i^\top (\mathbf{v}^W_j - \mathbf{v}^W_i - \mathbf{g}^W \Delta t_{ij})
$$

$$
\Delta \mathbf{p}_{ij} = \mathbf{R}_i^\top (\mathbf{p}^W_j - \mathbf{p}^W_i - \mathbf{v}^W_i \Delta t_{ij} - \frac{1}{2}\mathbf{g}^W \Delta t_{ij}^2)
$$

Now expand these as integrals of the *raw* IMU measurements. With careful algebra, $\Delta \mathbf{R}_{ij}, \Delta \mathbf{v}_{ij}, \Delta \mathbf{p}_{ij}$ can be computed by integrating the raw IMU between $t_i$ and $t_j$ — *without ever using $\mathbf{R}_i$ or $\mathbf{v}^W_i$*. Only the biases $b^g, b^a$ appear.

When biases change slightly (during optimization), apply first-order corrections via the precomputed bias Jacobians. No re-integration needed.

### What this gives you in the graph

A single **IMU factor** between keyframes $i$ and $j$:

* State at $i$: pose $\mathbf{T}_i$, velocity $\mathbf{v}^W_i$, biases $b^g_i, b^a_i$.
* State at $j$: pose $\mathbf{T}_j$, velocity $\mathbf{v}^W_j$, biases $b^g_j, b^a_j$.
* Constraint: the predicted $\Delta \mathbf{R}_{ij}, \Delta \mathbf{v}_{ij}, \Delta \mathbf{p}_{ij}$ from the IMU integration must match what you'd compute from $\mathbf{T}_i, \mathbf{T}_j, \mathbf{v}_i, \mathbf{v}_j$.
* Plus bias random walk constraints between consecutive keyframes.

GTSAM has all of this implemented in `PreintegratedImuMeasurements`. If you're rolling your own VIO/LIO, do not derive this from scratch — read Forster et al. 2017 and copy the formulas.

### Reading

* Forster, Carlone, Dellaert, Scaramuzza (2017) — "On-Manifold Preintegration for Real-Time Visual-Inertial Odometry." TRO. The canonical reference.
* Eckenhoff, Geneva, Huang (2019) — "Closed-form preintegration methods for graph-based visual-inertial navigation." More variants.
* Sola (2017) ESKF tutorial — for the simpler integration patterns.

***

## When to fuse what

Quick cheat sheet for picking your fusion architecture:

| Scenario                                          | Fusion architecture                              |
| ------------------------------------------------- | ------------------------------------------------ |
| Indoor wheeled robot, flat floor, no IMU          | Wheel odom only + SLAM pose, in robot\_localization local EKF |
| Indoor wheeled robot with IMU                     | Wheel odom + IMU in local EKF; SLAM pose in global EKF |
| Outdoor wheeled robot with GPS                    | Wheel + IMU in local EKF; +GPS in global EKF (with `navsat_transform_node`) |
| Drone                                             | Tightly-coupled VIO (VINS-Fusion) or VIO + GPS fallback |
| Heavy industrial robot with 3D LiDAR              | LIO-SAM or FAST-LIO2 as the SLAM-and-state pipeline; add wheel-encoder constraint for slow motions |
| Multi-LiDAR + IMU + wheel encoders (my setup)     | Deskew + fuse LiDAR via [Polka](../authors-projects/polka.md); ICP against local map; ESKF over $SE(3) \times$ velocity $\times$ biases |
| Aerial vehicle, high agility                      | OpenVINS or VINS-Fusion (tight visual-inertial); IMU at the top of the stack |

Two principles that save you headaches:

1. **High-rate prediction, low-rate correction.** Whatever updates fastest (usually IMU) drives prediction. Slower / less accurate sensors correct. Don't have your IMU correcting your LiDAR.
2. **Fuse in the right frame.** Wheel odom is in `base_link`. GPS is in `utm` or `enu`. LiDAR is in the LiDAR frame. Make sure each measurement is transformed correctly before it enters the filter, and that your filter is in a consistent frame.

***

## Common failure modes

A list of things I've personally debugged at 2 AM:

1. **Time sync is off.** A 30 ms timestamp offset between IMU and LiDAR will silently corrupt every IMU-deskewed point. Always validate timestamps before trusting fusion.
2. **Covariances are wrong.** People copy default covariances from tutorials. Your sensor's covariance is yours to measure. Run static calibration. Look at Allan variance for IMU noise (use [IMU TK](https://github.com/Kyle-ak/imu_tk) `[verify]` or [Kalibr](https://github.com/ethz-asl/kalibr) `[verify]`).
3. **Extrinsics are wrong.** A 3 cm offset between LiDAR and IMU frames creates a phantom angular component in IMU-deskewed scans. Calibrate, don't guess.
4. **One measurement source has unmodeled outliers.** GPS multipath, wheel slip, dynamic obstacles in LiDAR. Either gate the measurement (chi-square test) or use a robust kernel.
5. **The filter converged to a bad local minimum because initialization was bad.** Initialize aggressively (static IMU at startup to get gravity; static GPS to get initial position; etc.).

***

## Further reading

* Joan Sola — ESKF tutorial, [arxiv.org/abs/1711.02508](https://arxiv.org/abs/1711.02508). Read this.
* Tim Barfoot — *State Estimation for Robotics*, 2nd ed (2024). The textbook for Lie-group state estimation.
* Forster et al. 2017 — IMU preintegration TRO paper. Read it.
* Thrun, Burgard, Fox — *Probabilistic Robotics*. Chapters 3-4 for Kalman / EKF / UKF.

### Cross-references

* [Filter SLAM](filter-slam.md) — the EKF / particle-filter story when the map is also being estimated.
* [Graph SLAM](graph-slam.md) — the factor-graph formulation that subsumes filters for offline / smoothing problems.
* [LiDAR SLAM](lidar-slam.md) — ICP variants, deskewing, IMU preintegration in the LiDAR context.
* [Polka](../authors-projects/polka.md) — multi-LiDAR fusion + deskewing; the layer that feeds the EKF.
