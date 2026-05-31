---
icon: route
---

# Graph-based SLAM

## The insight that changed SLAM

Filter SLAM marginalizes out past poses on every step. Once a pose is collapsed into the covariance, you can't go back and revise it. That's why loop closure is so painful in EKF-SLAM - the error you made on pose 100 is permanently baked into your belief about pose 5000.

Graph SLAM does the opposite. **Keep every variable explicit; encode every measurement as a constraint between variables; solve the whole thing as a nonlinear least squares.**

When you close a loop, you just add one more edge. The optimizer re-distributes error across the graph. Magic.

This is the model behind every serious SLAM back-end since about 2010: g2o, GTSAM, Ceres, iSAM2, SE-Sync. Same math, different software.

***

## Factor graphs - the mental model

A factor graph (Kschischang, Frey, Loeliger 2001; popularized in robotics by Frank Dellaert and Michael Kaess) is a bipartite graph with two node types:

* **Variable nodes** - the things you want to estimate. Poses $$\mathbf{x}_i$$, landmarks $$\mathbf{l}_j$$, IMU biases, calibration parameters.
* **Factor nodes** - the constraints / measurements. Each factor is a function of a small subset of variables and contributes a term to the global cost.

The joint posterior factorizes as:

$$
p(\mathbf{X} \mid \mathbf{Z}) \propto \prod_k \phi_k(\mathbf{X}_k)
$$

where each $$\phi_k$$ is one factor (e.g., a relative pose measurement, a landmark observation, an IMU preintegration factor).

In log space and assuming Gaussian factors, this becomes the familiar nonlinear least-squares cost:

$$
\mathbf{X}^* = \arg\min_{\mathbf{X}} \sum_k \| r_k(\mathbf{X}_k) \|^2_{\Sigma_k}
$$

where $$r_k$$ is the residual of factor $$k$$ (measured minus predicted) and $$\| \cdot \|_{\Sigma}^2 = (\cdot)^\top \Sigma^{-1} (\cdot)$$ is the Mahalanobis distance.

If you can write your measurement as "predicted minus observed, weighted by uncertainty," it's a factor.

> Read: Dellaert & Kaess (2017), *Factor Graphs for Robot Perception*. This is the book. [Now-Publishers PDF](https://www.cs.cmu.edu/~kaess/pub/Dellaert17fnt.pdf).

***

## Pose graph optimization - the simplest case

Strip out landmarks entirely. Keep only poses connected by relative-pose measurements (odometry edges, loop-closure edges). That's pose graph optimization (PGO):

$$
\{\mathbf{x}_i\}^* = \arg\min_{\{\mathbf{x}_i\}} \sum_{(i,j) \in \mathcal{E}} \| \log\left( \tilde{\mathbf{T}}_{ij}^{-1} \mathbf{T}_i^{-1} \mathbf{T}_j \right)^\vee \|_{\Sigma_{ij}}^2
$$

where $$\mathbf{T}_i \in SE(3)$$ is the $$i$$-th pose, $$\tilde{\mathbf{T}}_{ij}$$ is the measured relative transform, and $$\log(\cdot)^\vee$$ extracts the Lie-algebra vector from the residual transform.

This is what every LiDAR SLAM back-end is doing once you strip the front-end away - taking scan-to-scan + loop-closure transforms and optimizing the trajectory. It's also what I built in [GO-SLAM](../authors-projects/go-slam.md): a custom LM solver over $$SE(3)$$ pose nodes with GICP edges from the front-end.

***

## Solving the nonlinear least squares

Standard Gauss-Newton / Levenberg-Marquardt loop. Linearize at the current estimate, solve the linear system, update on the manifold, repeat.

### Linearization

For a small perturbation $$\delta \mathbf{x}$$, each residual is approximated as:

$$
r_k(\mathbf{x} \boxplus \delta \mathbf{x}) \approx r_k(\mathbf{x}) + \mathbf{J}_k \delta \mathbf{x}
$$

where $$\mathbf{J}_k$$ is the Jacobian of $$r_k$$ with respect to $$\delta \mathbf{x}$$ on the manifold (using the $$\boxplus$$ retraction). The total cost becomes quadratic:

$$
F(\delta \mathbf{x}) = \sum_k \| r_k + \mathbf{J}_k \delta \mathbf{x} \|_{\Sigma_k}^2
$$

### The normal equations

Setting $$\partial F / \partial \delta \mathbf{x} = 0$$ gives:

$$
\mathbf{H} \delta \mathbf{x} = -\mathbf{b}
$$

where

$$
\mathbf{H} = \sum_k \mathbf{J}_k^\top \Sigma_k^{-1} \mathbf{J}_k, \quad \mathbf{b} = \sum_k \mathbf{J}_k^\top \Sigma_k^{-1} r_k
$$

$$\mathbf{H}$$ is the **information matrix** (Gauss-Newton approximation of the Hessian). Levenberg-Marquardt adds a damping term $$\lambda \mathbf{I}$$ (or $$\lambda \text{diag}(\mathbf{H})$$):

$$
(\mathbf{H} + \lambda \mathbf{I}) \delta \mathbf{x} = -\mathbf{b}
$$

When $$\lambda$$ is large, you take a small gradient-descent step. When $$\lambda$$ is small, you take a Gauss-Newton step. The whole game is adjusting $$\lambda$$ each iteration based on whether the step reduced the cost. LM is robust where Gauss-Newton diverges.

### Why this is fast - sparsity

Each factor touches only a few variables (a pose edge touches 2 poses; a landmark observation touches 1 pose + 1 landmark). So $$\mathbf{J}_k$$ is mostly zero, and $$\mathbf{H}$$ - the sum of $$\mathbf{J}_k^\top \mathbf{J}_k$$ - has a **sparse block structure** mirroring the graph topology.

> This is the punchline of graph SLAM: a Gaussian over the full posterior has a dense covariance matrix, but its inverse - the information matrix - is sparse. EKF-SLAM operates on the dense covariance ($$O(N^2)$$ entries). Graph SLAM operates on the sparse information matrix ($$O(N)$$ non-zeros). That's how you scale to $$10^5$$ poses.

A sparse Cholesky decomposition of $$\mathbf{H}$$ (CHOLMOD, SuiteSparse) solves the linear system in roughly $$O(N^{1.5})$$ for 2D problems, scaling worse but still tractable for 3D.

***

## The Schur complement and marginalization

Many SLAM problems have a special structure: lots of landmarks, fewer poses. If you split the variables into poses $$\mathbf{x}_p$$ and landmarks $$\mathbf{x}_l$$:

$$
\begin{bmatrix} \mathbf{H}_{pp} & \mathbf{H}_{pl} \\ \mathbf{H}_{pl}^\top & \mathbf{H}_{ll} \end{bmatrix} \begin{bmatrix} \delta \mathbf{x}_p \\ \delta \mathbf{x}_l \end{bmatrix} = -\begin{bmatrix} \mathbf{b}_p \\ \mathbf{b}_l \end{bmatrix}
$$

The landmark block $$\mathbf{H}_{ll}$$ is **block-diagonal** (each landmark is observed by some poses, but landmarks don't directly constrain each other). You can invert it cheaply - just invert each $$3\times 3$$ block. Substituting back yields the Schur-complement system for the poses alone:

$$
(\mathbf{H}_{pp} - \mathbf{H}_{pl} \mathbf{H}_{ll}^{-1} \mathbf{H}_{pl}^\top) \delta \mathbf{x}_p = -(\mathbf{b}_p - \mathbf{H}_{pl} \mathbf{H}_{ll}^{-1} \mathbf{b}_l)
$$

Now you only solve over the (much smaller) pose space. Once you have $$\delta \mathbf{x}_p$$, back-substitute to get $$\delta \mathbf{x}_l$$.

This is exactly what bundle adjustment does (Triggs et al. 2000) and what ORB-SLAM, COLMAP, and Ceres all use under the hood.

**Marginalization** is the same operation viewed differently. To remove a variable from a graph while preserving the information it contributed, you compute the Schur complement against that variable. The result is a new, denser factor over the remaining variables (the "marginal prior"). This is how sliding-window VIO systems like OKVIS and VINS-Mono keep memory bounded - they marginalize old states out of the window and absorb their information into a prior.

> **Field notes:** marginalization sounds clean. In practice, the *fill-in* it creates is a real cost - the marginal prior is a dense factor over everything connected to the marginalized variable. If you marginalize a pose that was observed from 10 keyframes, you now have a 10-way prior connecting all of them. That's why FEJ (First-Estimates Jacobian) tricks and careful keyframe selection matter so much in VIO.

***

## The big four: g2o, GTSAM, Ceres, iSAM2

| Library    | Author / origin                | Sweet spot                                       | Math idiom                       |
| ---------- | ------------------------------ | ------------------------------------------------ | -------------------------------- |
| **g2o**    | Kümmerle et al. (2011), Freiburg | Pose graphs, BA, classic SLAM back-ends         | Hyper-graph; explicit vertex/edge types |
| **GTSAM**  | Dellaert, Georgia Tech         | Factor graphs, VIO, smoothing-and-mapping (iSAM/iSAM2) | Factor graph; symbolic; Lie groups |
| **Ceres**  | Agarwal & Mierle, Google       | General nonlinear LSQ; bundle adjustment at scale | Cost functions + parameter blocks |
| **iSAM2**  | Kaess et al. (2012); ships in GTSAM | Incremental smoothing - update solution as new factors arrive without re-solving everything | Bayes tree |

### g2o

**General Graph Optimization.** Kümmerle, Grisetti, Strasdat, Konolige, Burgard (2011). [Paper](http://www2.informatik.uni-freiburg.de/~kuemmerl/pdf/kuemmerle11icra.pdf) `[verify]`. Repo: [github.com/RainerKuemmerle/g2o](https://github.com/RainerKuemmerle/g2o).

* Born as the back-end for many 2D / 3D SLAM systems (ORB-SLAM, ORB-SLAM2 used g2o; ORB-SLAM3 moved to a custom solver).
* Plug-in linear solvers (CSparse, CHOLMOD, PCG, dense, Eigen).
* You write vertex types (e.g., `VertexSE3`) and edge types (e.g., `EdgeSE3`) and the framework does the rest.
* Lightweight. Good for pose graphs and BA. Less convenient if you want non-standard factor types.

### GTSAM

Georgia Tech Smoothing and Mapping. Dellaert et al. Repo: [github.com/borglab/gtsam](https://github.com/borglab/gtsam). Project page: [gtsam.org](https://gtsam.org).

* Factor graph as first-class API. Adding a factor is `graph.add(BetweenFactor<Pose3>(key1, key2, measured, noise))`.
* Excellent Lie group support - poses live on $$SE(3)$$, rotations on $$SO(3)$$, etc., with proper retractions and Jacobians built in.
* Includes **iSAM2** for incremental updates - when a new factor arrives, only the affected portion of the Bayes tree is re-solved. This is what makes GTSAM ideal for online SLAM.
* IMU preintegration factor is built in. This is the reason LIO-SAM picked GTSAM.
* Python bindings actually work (`pip install gtsam`).

### Ceres

Google's general-purpose nonlinear LSQ library. Repo: [github.com/ceres-solver/ceres-solver](https://github.com/ceres-solver/ceres-solver). Docs: [ceres-solver.org](http://ceres-solver.org).

* Not SLAM-specific. Designed for bundle adjustment at Google scale (Street View, photo tours).
* You write **cost functors** with automatic differentiation (`AutoDiffCostFunction`) - no hand-derived Jacobians. This is enormous for prototyping.
* Excellent at large-scale BA, structure-from-motion, calibration problems. VINS-Mono and VINS-Fusion both use Ceres.
* No native Lie-group manifold types - you write a `LocalParameterization` (now `Manifold` in newer versions) for $$SO(3)$$ / $$SE(3)$$. Slightly annoying but well-documented.

### When each wins

| Scenario                                            | Reach for          |
| --------------------------------------------------- | ------------------ |
| Pose graph optimization, ORB-SLAM-style back-end    | g2o or GTSAM       |
| Tightly-coupled VIO with IMU preintegration         | GTSAM (cleanest API) or Ceres (if you want autodiff) |
| Bundle adjustment, SfM, calibration                 | Ceres              |
| Incremental online SLAM (smoothing as you go)       | GTSAM iSAM2        |
| You need to ship custom factor types fast           | Ceres (autodiff saves days) |
| You want to read existing reference code            | Depends - pick the library your reference uses |

> **Field notes:** I deliberately did *not* use any of these for [GO-SLAM](../authors-projects/go-slam.md). I rolled custom LM solvers for both the GICP alignment and the global pose-graph optimization. Why? Because the two-month deadline made debugging someone else's framework slower than writing the math myself, and because I wanted to understand the optimization end-to-end. In a production system I would use GTSAM. For learning, write your own LM solver once - you'll never look at these libraries the same way again.

***

## Loop closure - the part nobody emphasizes enough

The pose-graph optimizer is the easy part. The hard part is:

1. **Detecting** that you've returned to a previously-visited place (place recognition).
2. **Verifying** the candidate match (geometric verification - RANSAC over feature matches, or scan-to-scan ICP with a tight inlier threshold).
3. **Adding** the loop-closure factor with a sensible covariance.
4. **Surviving** the moment when the optimizer pulls the entire trajectory through the new constraint.

Approaches you'll see:

| Approach                                | Used in                                |
| --------------------------------------- | -------------------------------------- |
| Bag-of-Words (DBoW2, DBoW3)             | ORB-SLAM family                        |
| NetVLAD / SuperGlue / LightGlue         | Modern learned visual descriptors      |
| Scan Context (Kim & Kim 2018)           | LIO-SAM, many LiDAR systems            |
| Scan Context++ (Kim & Kim 2021)         | LIO-SAM derivatives                    |
| BoW3D                                   | LiDAR loop closure with 3D ORB         |

> **Field notes:** a wrong loop closure is worse than no loop closure. A false positive will warp your map permanently. Always pair the descriptor match with geometric verification, and put a robust kernel (Huber, Cauchy, DCS) on the loop-closure factor in the optimizer so a bad match has limited damage.

### Robust kernels

The naive least-squares cost $$\|r\|^2$$ is quadratic - an outlier with residual 100 contributes 10,000 to the cost and dominates everything. Robust kernels replace $$\|r\|^2$$ with $$\rho(\|r\|)$$ where $$\rho$$ grows sub-quadratically. Common choices:

* **Huber:** quadratic inside threshold, linear outside. The safe default.
* **Cauchy:** $$\rho(r) = c^2 \log(1 + (r/c)^2)$$. More aggressive.
* **DCS (Agarwal et al. 2013):** Dynamic Covariance Scaling. Scales the residual covariance based on the residual magnitude - effectively rejects outliers without hard thresholding.
* **Switchable Constraints (Sünderhauf 2012):** add a switch variable per loop-closure edge; the optimizer can turn the edge off if it's inconsistent with the rest. Powerful but expensive.

Ceres and g2o both have built-in robust kernels. GTSAM has them via `noiseModel::Robust`.

***

## SE-Sync, certifiable optimization, and other advanced topics

Briefly, since this section is already long:

* **SE-Sync (Rosen, Carlone, Bandeira, Leonard 2019)** - global, certifiably optimal pose graph optimization via semidefinite relaxation. When it converges, it returns a certificate that the solution is the global optimum. Used as a research benchmark for "did the optimizer find the right answer." [arxiv.org/abs/1611.00128](https://arxiv.org/abs/1611.00128).
* **Square-root SAM (Dellaert & Kaess 2006)** - solve via QR factorization of the Jacobian instead of Cholesky of the information matrix. More numerically stable.
* **Maximum-Mixture / GMM factors (Olson & Agarwal 2013)** - model multi-modal uncertainty in single factors. Useful when data association is ambiguous.

Read these once you're comfortable with the basics. None of them changes the day-to-day workflow.

***

## What to actually use today

| Task                                                  | Use                                       |
| ----------------------------------------------------- | ----------------------------------------- |
| Pose graph back-end for a LiDAR SLAM you're building  | GTSAM if you want IMU preintegration; g2o for pure PGO |
| Online incremental SLAM                               | GTSAM with iSAM2                          |
| Bundle adjustment / SfM / calibration                 | Ceres                                     |
| Visual SLAM you're consuming (not writing)            | Whatever ORB-SLAM3 / VINS / OKVIS uses - read their code first |
| Learning the math                                     | Build your own LM solver over $$SE(3)$$. Once.     |

Continue to [visual-slam.md](visual-slam.md) and [lidar-slam.md](lidar-slam.md) to see how these back-ends get wired to actual sensor front-ends.
