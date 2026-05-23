---
icon: route
---

# Filter-based SLAM

## Why start with filters

Filters are the historically first answer to SLAM. They're also the cleanest way to internalize the Bayesian view of state estimation, which is the only mental model that survives once you move on to factor graphs.

In 2026 you will almost never deploy an EKF-SLAM system in production. But you will absolutely deploy:

* **AMCL** for localization on a known map (every ROS 2 nav stack uses it).
* **EKF / ESKF / IEKF** for tight IMU integration in modern VIO and LIO.
* **Particle filters** for global localization, kidnapped-robot recovery, and any state space that is multi-modal.

So filters are not dead — they just moved from being the whole pipeline to being one block inside a graph-based pipeline.

***

## The Bayes filter, properly

Every filter in this section is a special case of the recursive Bayes filter. Two steps, repeated forever:

**Prediction (motion update):**

$$
\overline{bel}(x_t) = \int p(x_t \mid u_t, x_{t-1})\, bel(x_{t-1})\, dx_{t-1}
$$

**Correction (measurement update):**

$$
bel(x_t) = \eta\, p(z_t \mid x_t)\, \overline{bel}(x_t)
$$

In English: propagate the belief forward through the motion model, then multiply by the measurement likelihood and normalize. That's it. EKF, UKF, particle filter, histogram filter — they're all approximations of this integral.

The trouble is the integral. In closed form it's tractable only for linear-Gaussian systems (the Kalman filter). For everything else you approximate:

* **EKF** — linearize the motion and measurement models around the current mean, then apply the Kalman update. Cheap, but assumes the posterior stays Gaussian.
* **UKF** — propagate a deterministic set of sigma points through the (nonlinear) models, refit a Gaussian. More accurate than EKF for moderate nonlinearity, more expensive.
* **Particle filter** — represent the belief as $N$ weighted samples. No linearization. Handles arbitrary distributions, including multi-modal.

If you remember one thing: **a filter assumes you can summarize your belief in a few numbers (a Gaussian, or $N$ particles). The moment that assumption breaks, the filter lies to you with a straight face.**

***

## EKF-SLAM

### What it is

State vector stacks the robot pose and every landmark:

$$
\mathbf{x} = \begin{bmatrix} \mathbf{x}_{robot} \\ \mathbf{m}_1 \\ \mathbf{m}_2 \\ \vdots \\ \mathbf{m}_N \end{bmatrix}, \quad \mathbf{P} \in \mathbb{R}^{(3+2N)\times(3+2N)}
$$

(for a 2D robot with 2D point landmarks). On each motion update you predict the new robot pose via the motion model $g(u_t, x_{t-1})$ and propagate the covariance:

$$
\mathbf{P}^- = \mathbf{G}_t \mathbf{P} \mathbf{G}_t^\top + \mathbf{R}_t
$$

where $\mathbf{G}_t = \partial g / \partial x$ is the Jacobian. On each landmark observation $z_t$ you apply the Kalman update with the measurement Jacobian $\mathbf{H}_t$:

$$
\mathbf{K}_t = \mathbf{P}^- \mathbf{H}_t^\top (\mathbf{H}_t \mathbf{P}^- \mathbf{H}_t^\top + \mathbf{Q}_t)^{-1}
$$

$$
\mathbf{x} = \mathbf{x}^- + \mathbf{K}_t (z_t - h(\mathbf{x}^-))
$$

$$
\mathbf{P} = (\mathbf{I} - \mathbf{K}_t \mathbf{H}_t) \mathbf{P}^-
$$

### Why it became unfashionable

Three reasons:

1. **$O(N^2)$ per update.** The covariance matrix is dense — every landmark correlates with every other. 1000 landmarks is already 1M entries you maintain forever. For modern SLAM with $10^4$ - $10^6$ map points, EKF-SLAM is dead on arrival.
2. **No revisiting.** Linearization is baked in at the moment of each update. When you close a loop, you can't go back and re-linearize old measurements with the corrected pose. The error you committed early in the trajectory is permanent.
3. **Inconsistency.** It's a well-known empirical result (Julier & Uhlmann; Bailey et al.) that EKF-SLAM's covariance shrinks faster than the true uncertainty — i.e., the filter becomes overconfident and diverges.

### When you'd still pick it

* Toy problems and teaching. It is the cleanest probabilistic SLAM derivation that fits on a chalkboard.
* Very small state spaces where the $O(N^2)$ cost is fine and the landmark set is fixed (e.g., a manipulator with a handful of fiducials).

### Canonical references

* Dissanayake, Newman, Clark, Durrant-Whyte, Csorba (2001) — "A solution to the simultaneous localization and map building (SLAM) problem." [IEEE T-RA](https://ieeexplore.ieee.org/document/938381) `[verify]`. The OG.
* Thrun et al., *Probabilistic Robotics*, chapter 10.

***

## Particle filters and FastSLAM

### The idea

Represent the posterior over robot pose by $N$ weighted samples (particles) instead of a Gaussian. Each particle is a hypothesis: "the robot is here." On each motion update you sample from the motion model. On each measurement update you reweight particles by the measurement likelihood and resample.

**The Rao-Blackwellization trick (FastSLAM, Montemerlo et al. 2002):** Conditional on a robot trajectory, the landmark positions are *independent*. So you don't need to put landmarks in the particles. Instead, each particle carries:

* a robot pose hypothesis
* a small EKF *per landmark*, conditional on that pose history

This collapses the joint distribution into something that scales as $O(N \log M)$ where $N$ is particles and $M$ is landmarks. The seminal paper:

* Montemerlo, Thrun, Koller, Wegbreit (2002) — [AAAI paper](https://www.aaai.org/Papers/AAAI/2002/AAAI02-089.pdf) `[verify]`. Reference impl: there are several open-source FastSLAM implementations, none truly canonical — the [openslam.org](https://openslam-org.github.io/) page lists them.

### gmapping — the ROS workhorse for a decade

`gmapping` (Grisetti, Stachniss, Burgard 2007) is a Rao-Blackwellized particle filter for grid-map SLAM. It was the default 2D LiDAR SLAM in ROS 1 forever. The key contribution beyond FastSLAM is an *improved proposal distribution* that uses the current scan to focus particles where they'll actually survive resampling — which dramatically cuts the number of particles needed.

* Grisetti, Stachniss, Burgard (2007) — "Improved techniques for grid mapping with Rao-Blackwellized particle filters." [IEEE T-RO](https://ieeexplore.ieee.org/document/4084563) `[verify]`. Repo: [github.com/OpenSLAM-org/openslam\_gmapping](https://github.com/OpenSLAM-org/openslam_gmapping) `[verify]`.

In ROS 2 it has largely been superseded by `slam_toolbox` (graph-based) and Cartographer. gmapping still ships but it's an old soldier.

### When particle filters win

* **Multi-modal posteriors.** Kidnapped-robot recovery, global localization in a known map (where the robot could be in several plausible places), tight indoor corridors where laser scans look identical for meters.
* **Highly nonlinear models.** Anything where linearization would be a lie — non-Gaussian noise, hard non-linear measurement functions.
* **Discrete map representations.** Occupancy grids don't have a useful "Jacobian." Particle filters don't care.

### When they collapse

Two failure modes you have to know:

**Particle deprivation.** After enough resampling, all your particles share a single ancestor. You've lost the entropy that lets you recover from being wrong. Diagnostics: track the effective sample size

$$
N_{eff} = \frac{1}{\sum_i (w^{(i)})^2}
$$

and only resample when $N_{eff} < N/2$. This is now standard but was a hard-won lesson.

**Sample impoverishment in high dimensions.** Particles scale exponentially with state dimension. 2D pose + 2D laser scan? Fine, 100-500 particles. 6-DoF camera pose + per-pixel depth? You need $10^6$ particles and you still won't cover the space. This is why particle filters basically don't appear in 6-DoF visual SLAM.

> **Field notes:** the first time I shipped a particle filter (AMCL on an indoor AMR) I forgot to gate resampling on $N_{eff}$. The robot would localize fine for 20 minutes then suddenly think it was in the next aisle over. The fix was three lines. It always is.

***

## AMCL — particle filter you actually use

AMCL = Adaptive Monte Carlo Localization. It's a particle filter for *localization on a known map* — not full SLAM. You give it an occupancy grid, scans, and odometry; it gives you the robot's pose distribution.

Key features:

* **KLD-sampling (Fox 2003):** dynamically resize the particle set based on KL-divergence between the sample distribution and the posterior. When the robot is well-localized, drop to 100 particles. When you "kidnap" it, expand to 5000.
* **Beam model / likelihood-field model** for the laser measurement likelihood. Likelihood-field is faster and the default.
* **Augmented MCL** with short-term and long-term average weights to detect divergence and inject random particles for recovery.

In ROS 2: [`nav2_amcl`](https://github.com/ros-navigation/navigation2/tree/main/nav2_amcl) `[verify]`. This is the localization layer for Nav2 unless you've replaced it (e.g., with `mcl_3dl` for 3D, or a custom EKF + map-matching).

> **Field notes:** AMCL is fine until your environment has long featureless corridors or repeating structure (warehouse aisles look identical for 30 m). Symptoms: pose suddenly jumps to a parallel aisle. Mitigations in order of effort: tune `recovery_alpha_*` parameters, add fiducials, switch to a graph-based SLAM with global descriptors, or fuse with WiFi/UWB. Don't expect AMCL to magically know which aisle it's in — give it more information.

### Canonical reference

* Fox, Burgard, Dellaert, Thrun (1999) — "Monte Carlo Localization: Efficient Position Estimation for Mobile Robots." [AAAI](https://www.aaai.org/Papers/AAAI/1999/AAAI99-049.pdf) `[verify]`.
* Fox (2003) — "Adaptive Real-Time Particle Filters for Robot Localization." (KLD-sampling.)

***

## Quick comparison

| Filter           | State            | Handles non-Gaussian? | Handles non-linear? | Cost per step | Where it lives in 2026                |
| ---------------- | ---------------- | --------------------- | ------------------- | ------------- | ------------------------------------- |
| Kalman           | Linear-Gaussian  | No                    | No                  | $O(d^3)$      | Linear systems only (rare in SLAM)    |
| EKF              | Gaussian         | No                    | Yes (linearized)    | $O(d^3)$      | IMU integration in VIO/LIO            |
| UKF              | Gaussian         | No                    | Yes (better than EKF) | $O(d^3)$    | Heavily nonlinear VIO, niche          |
| IEKF / ESKF      | Gaussian on manifold | No                | Yes (Lie group)     | $O(d^3)$      | Modern VIO/LIO (FAST-LIO2 uses IEKF)  |
| Particle filter  | Arbitrary        | Yes                   | Yes                 | $O(N \cdot d)$ for likelihood | AMCL, low-dim global localization |
| EKF-SLAM         | Gaussian joint over pose+map | No        | Yes (linearized)    | $O(N^2)$ in landmarks | Don't.                          |
| FastSLAM         | Particles + per-landmark EKFs | Partially | Yes                 | $O(N \log M)$ | Mostly historical                     |

***

## The pivot to graph SLAM

The single insight that killed EKF-SLAM as a serious pipeline:

> A Gaussian over the full joint of poses and landmarks has $O(N^2)$ dense entries. The same posterior, expressed as a *factor graph* over the same variables, has $O(N)$ sparse entries — because most pairs of variables are conditionally independent given a few others.

This is the Schur-complement story, the "the information matrix is sparse" story, and the entire reason graph SLAM exists. Continue to [graph-slam.md](graph-slam.md) for the next chapter.

***

## What to actually use today

| Task                                       | Use                                       |
| ------------------------------------------ | ----------------------------------------- |
| Localization on a known 2D map             | AMCL (`nav2_amcl`)                        |
| Localization on a known 3D map             | `mcl_3dl`, or NDT-based map matching      |
| Tight IMU integration inside a SLAM stack  | ESKF / IEKF (handled inside FAST-LIO2, OpenVINS, etc.) |
| Multi-hypothesis global localization       | Particle filter (KLD-sampled)             |
| Full SLAM                                  | Graph-based. Skip to [graph-slam.md](graph-slam.md). |
