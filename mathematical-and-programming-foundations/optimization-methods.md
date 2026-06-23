---
description: The optimization toolbox behind SLAM backends, MPC, and trajectory planning - what each method actually does and when to reach for it
icon: bullseye-arrow
---

# Optimization Methods

## Optimization is the hidden engine of modern robotics

Strip the branding off almost any serious robotics algorithm and you find a minimization problem underneath. Bundle adjustment is nonlinear least squares. The SLAM backend is nonlinear least squares on a sparse graph. MPC is a constrained QP or NLP solved 50 times a second. Inverse kinematics, calibration, contact-implicit locomotion, grasp synthesis - all of it is "write a cost, write constraints, hand it to a solver."

This matters practically: when your SLAM diverges or your MPC chatters, the bug is usually not in the solver. It's in your cost function, your initialization, or your Jacobians. You can't debug those without knowing what the solver is doing with them. This page is the working vocabulary - enough to read solver logs, pick the right method, and know when a problem is fundamentally hard versus just badly posed.

Prerequisite: comfort with gradients, Hessians, and linear systems. If $$\nabla f$$ and positive definiteness feel shaky, do [linear algebra](../foundations/linear-algebra-for-robotics.md) and [calculus](../foundations/calculus.md) first.

***

## The taxonomy: LP, QP, NLP, convex vs non-convex

The single most important question about any optimization problem: **is it convex?** Convex means every local minimum is global, solvers come with guarantees, and "did it converge?" has a clean answer. Non-convex means you get a local minimum that depends on your initial guess, and initialization becomes half the engineering.

The standard ladder, cheapest to hardest:

| Class | Cost | Constraints | Convex? | Robotics example |
| --- | --- | --- | --- | --- |
| **LP** | Linear | Linear | Yes | Grasp force feasibility, some footstep plans |
| **QP** | Quadratic (convex) | Linear | Yes | MPC tracking, whole-body control, inverse dynamics |
| **QCQP / SOCP** | Quadratic | Quadratic / cone | Yes (if cones) | Friction cone constraints, min-time with norm bounds |
| **NLP** | Anything smooth | Anything smooth | Usually not | Trajectory optimization, kinodynamic planning |
| **NLLS** | Sum of squared residuals | Usually none | No, but structured | SLAM, bundle adjustment, calibration |
| **MIP** | Linear/quadratic | Linear + integers | No (combinatorial) | Contact sequencing, task assignment |

Two practical rules I keep coming back to:

1. **If you can pose your problem as a QP, do it.** A well-conditioned QP solves in microseconds to low milliseconds, warm-starts beautifully, and never surprises you. This is why so much of whole-body control is "QP all the way down."
2. **Non-convexity is not a death sentence - bad initialization is.** SLAM and trajectory optimization are wildly non-convex, yet they work every day because the previous solution (or odometry, or a straight-line seed) is close enough to the right basin.

***

## Unconstrained methods: gradient descent to Levenberg-Marquardt

The core loop of all smooth optimization: pick a direction, pick a step length, repeat. The methods differ in how much curvature information they use.

**Gradient descent:** step along $$-\nabla f$$. Cheap per iteration, miserable convergence on ill-conditioned problems (long narrow valleys - which is what most robotics costs look like). In 2026 its home is deep learning (as SGD/Adam), not classical robotics solvers. If you're running vanilla gradient descent on a calibration problem, you're leaving a 100x speedup on the table.

**Newton's method:** solve $$\nabla^2 f \, \delta x = -\nabla f$$. Quadratic convergence near the minimum, but you need the Hessian, and far from the minimum the Hessian may not be positive definite, so the "downhill" direction can point uphill. Rarely used raw; used constantly in disguise.

**Gauss-Newton:** the disguise. For least-squares costs $$f(x) = \tfrac{1}{2}\sum_k \|r_k(x)\|^2$$, approximate the Hessian by $$J^\top J$$ (drop the second-order residual term) and solve

$$
J^\top J \, \delta x = -J^\top r
$$

You get near-Newton convergence using only first derivatives of the residuals. This approximation is good exactly when residuals are small at the solution - which is the regime SLAM and calibration live in.

**Levenberg-Marquardt:** Gauss-Newton with a trust region knob. Solve $$(J^\top J + \lambda I)\,\delta x = -J^\top r$$, increasing $$\lambda$$ when a step fails (behaves like small gradient descent steps) and decreasing it when steps succeed (behaves like Gauss-Newton). This is *the* default for nonlinear least squares, full stop.

**The SLAM backend story** ties this together. A factor graph backend is nothing but Gauss-Newton/LM on a huge sparse least-squares problem: linearize every factor, assemble the sparse normal equations, solve via sparse Cholesky (exploiting the graph structure - this is the Schur complement / variable elimination story), update poses on the $$SE(3)$$ manifold, repeat. That whole pipeline is laid out properly in [graph SLAM](../slam-and-state-estimation/graph-slam.md). When I wrote the LM solver for [GO-SLAM](../authors-projects/go-slam.md) by hand - no Ceres, no g2o - roughly 80% of the debugging time went into Jacobians and manifold updates, not the LM logic itself. The damping loop is 30 lines. The derivatives are where you bleed.

> One habit worth stealing: always check your analytic Jacobians against finite differences before trusting any solver output. Every "LM doesn't converge" bug I've personally hit was a sign error or a frame convention error in a Jacobian.

***

## Constrained optimization: Lagrangians, KKT, SQP, interior point

Real robots have joint limits, torque limits, obstacles, friction cones. Enter constraints:

$$
\min_x f(x) \quad \text{s.t.} \quad g(x) \le 0, \quad h(x) = 0
$$

The **Lagrangian** $$\mathcal{L}(x, \lambda, \mu) = f(x) + \lambda^\top g(x) + \mu^\top h(x)$$ turns constraints into prices. The **KKT conditions** are the first-order optimality test: stationarity of $$\mathcal{L}$$, primal feasibility, dual feasibility ($$\lambda \ge 0$$), and complementary slackness ($$\lambda_i g_i = 0$$ - a constraint either binds or its multiplier is zero). Every constrained solver is, one way or another, hunting for a KKT point. The multipliers are also genuinely useful outputs: in whole-body control, contact-force multipliers tell you how hard you're pushing on the world.

Two solver families dominate:

* **SQP (sequential quadratic programming):** repeatedly approximate the NLP by a QP (quadratic model of the Lagrangian, linearized constraints) and solve it. Warm-starts extremely well, which makes it the natural fit for receding-horizon problems where consecutive solves are nearly identical. ACADO/acados and most real-time MPC stacks are SQP-based, often deliberately truncated to one QP per control cycle ("real-time iteration").
* **Interior point:** follow a smooth central path by replacing inequalities with a log-barrier $$-\sigma \sum_i \log(-g_i(x))$$ and shrinking $$\sigma$$. Very robust on large sparse problems, mediocre at warm-starting. IPOPT is the canonical open-source implementation and my default for offline trajectory optimization.

Rule of thumb: **interior point offline, SQP online.** And for the QPs inside: OSQP (ADMM-based, embeddable) or qpOASES for small dense active-set problems.

***

## The robotics workhorses

Three problem shapes cover most of what you'll actually solve:

**Nonlinear least squares** - estimation. SLAM, bundle adjustment, camera/IMU/hand-eye calibration, ICP variants. Structure: many small residuals, sparse Jacobian, good initialization available. Method: LM or trust-region Gauss-Newton with robust losses (Huber, Cauchy) to survive outliers - in SLAM, one bad loop closure without a robust kernel can fold your entire map in half. Tooling: Ceres, GTSAM, g2o - compared honestly in [optimization libraries](../programming-for-robotics/optimization-libraries.md).

**MPC and MPPI** - control. MPC transcribes "track this reference over the next $$N$$ steps subject to dynamics and limits" into a QP (linear/linearized dynamics) or NLP (full nonlinear dynamics) and solves it every control tick, applying only the first action. The entire game is solve time: you have maybe 2-10 ms. Hence condensed QPs, warm starts, and real-time iteration SQP.

**MPPI** (model predictive path integral) is the derivative-free sibling: sample a few thousand control sequences, roll them through your dynamics model (on GPU, in parallel), weight by exponentiated cost, average. No gradients, no constraint linearization - costs can be discontinuous, dynamics can be a black box or a learned model. It handles the non-smooth, cluttered cost landscapes of aggressive navigation better than gradient-based MPC, which is why Nav2 shipped an MPPI controller and why it shows up in off-road racing stacks. The catch: it's sampling, so solution quality is noisy and you pay in compute. Tightly cluttered navigation of the [BARN Challenge](../authors-projects/barn-challenge.md) variety is exactly the regime where this tradeoff gets stress-tested.

**Trajectory optimization** - planning. Find a whole trajectory minimizing effort/time/jerk subject to dynamics, limits, and obstacles. Two transcription camps: **direct collocation / multiple shooting** (discretize states and controls into a large sparse NLP, feed to IPOPT or SNOPT) and **DDP/iLQR** (exploit the temporal structure with dynamic-programming sweeps - fast, feeds MPC, handles constraints less naturally). CHOMP and STOMP are the motion-planning-flavored variants (gradient-based and sampling-based respectively) you'll meet in manipulation stacks. Where this sits in the planning hierarchy is covered in [trajectory planning](../mobile-robotics/trajectory-planning.md).

***

## Sampling and stochastic methods

When gradients are unavailable, unreliable, or the landscape is full of cliffs and plateaus, stop differentiating and start sampling.

* **CEM (cross-entropy method):** keep a sampling distribution (usually a diagonal Gaussian over action sequences), draw $$N$$ samples, keep the top ~10% elites, refit the distribution to the elites, repeat. Embarrassingly simple, embarrassingly effective. CEM is the default planner inside model-based RL world models (PETS lineage) and a respectable MPC when your dynamics model is a neural network - see [modern RL](../robot-learning/reinforcement-learning-modern.md) for that thread. MPPI is essentially a smoothed, single-temperature cousin.
* **Evolutionary strategies (CMA-ES and friends):** CMA-ES adapts a full covariance, making it the strongest general-purpose black-box optimizer below ~100 dimensions. Good for: tuning controller gains, optimizing morphology or gait parameters, anything where one evaluation is a full simulation rollout. Bad for: anything high-dimensional or where you do have usable gradients.
* **Simulated annealing, random search:** mostly superseded, but plain random search remains an honest baseline that hyperparameter papers keep failing to beat decisively.

The honest framing: sampling methods trade sample efficiency for robustness to non-smoothness. With a GPU simulator giving you ~10k rollouts per second, that trade is often a bargain. With a real robot giving you one rollout per minute, it isn't.

***

## What to actually use

| Problem | Method | Library |
| --- | --- | --- |
| SLAM backend / pose graph | LM / iSAM2 on factor graph | GTSAM, g2o, Ceres |
| Bundle adjustment, calibration | LM with robust loss, Schur complement | Ceres |
| Whole-body control, tracking MPC | QP, warm-started | OSQP, qpOASES, ProxQP |
| Nonlinear MPC (legged, drones) | SQP / real-time iteration, iLQR | acados, OCS2, Crocoddyl |
| Sampling MPC in clutter | MPPI | Nav2 MPPI controller, custom GPU impl |
| Offline trajectory optimization | Direct collocation -> interior point | CasADi + IPOPT, Drake |
| Black-box gain / parameter tuning | CMA-ES, CEM | pycma, evosax |
| Modeling layer for any of the above | Symbolic + autodiff | CasADi, JAX, CVXPY (convex only) |

Full library-by-library detail, with code, lives in [optimization libraries](../programming-for-robotics/optimization-libraries.md). If forced to learn just two tools: **Ceres** for everything estimation-shaped, **CasADi + IPOPT** for everything control- and trajectory-shaped. That combination covers roughly 90% of the optimization problems a robotics engineer meets.

***

## Where to go next

* [Graph SLAM](../slam-and-state-estimation/graph-slam.md) - the Gauss-Newton/LM machinery of this page applied at scale, with sparsity and manifolds done properly.
* [Optimization libraries](../programming-for-robotics/optimization-libraries.md) - Ceres, GTSAM, g2o, CasADi, OSQP with working code and honest tradeoffs.
* [Trajectory planning](../mobile-robotics/trajectory-planning.md) - where trajectory optimization sits in the planning hierarchy and how paths become time-parameterized motions.
* [Modern RL](../robot-learning/reinforcement-learning-modern.md) - CEM-style planners inside world models, and what happens when the "solver" becomes a learned policy.
