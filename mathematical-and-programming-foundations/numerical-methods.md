---
description: Floating point, linear solvers, integration, and the numerical bugs that actually bite on robots
icon: calculator
---

# Numerical Methods

Every robotics estimator, controller, and simulator is a numerical algorithm running on finite-precision hardware. Most of the "mystery bugs" I've debugged in state estimation were not modeling errors - they were numerics: a covariance that quietly lost positive-definiteness, a float32 timestamp that ran out of resolution, an integrator that pumped energy into a simulated joint. This page is the working engineer's version of a numerical methods course: the failure modes you'll actually hit and the standard fixes.

## Floating point will betray you

A `float` gives you ~7 significant decimal digits, a `double` ~15-16. That sounds like plenty until you realize how robotics code consumes precision.

**Float vs double on embedded.** Cortex-M4F and M7 parts have a single-precision FPU only; `double` arithmetic falls back to software emulation and is roughly an order of magnitude slower. So on MCUs you write `1.0f`, you call `sinf()` not `sin()`, and you accept float32. The catch is what float32 can't represent:

- **Timestamps.** Seconds-since-boot stored in a `float` loses millisecond resolution after roughly 4-5 hours of uptime, because the spacing between adjacent floats grows with magnitude. Symptom: the robot runs fine in every test, then control timing degrades on the overnight soak test. Store time as integer microseconds/nanoseconds, always.
- **Accumulated integrals.** Summing tiny `dt`-scaled increments into a large accumulator silently drops the increments once the accumulator is big. Kahan summation fixes this in two extra lines if you can't switch to double.

**Catastrophic cancellation** is the other classic: subtracting two nearly equal numbers annihilates your significant digits. Places it shows up on real robots:

- Variance via $$E[x^2] - E[x]^2$$ - use Welford's online algorithm instead.
- Angle between two unit vectors via `acos(dot(a, b))` - near 0 or $$\pi$$ the dot product saturates at $$\pm 1$$ and the result is garbage. Use `atan2(norm(cross(a, b)), dot(a, b))`.
- The quadratic formula when $$b^2 \gg 4ac$$ - compute the stable root first, derive the other from the product of roots.
- Finite-difference Jacobians with too small a step. The sweet spot is around $$\sqrt{\epsilon_{machine}}$$ times the variable scale (~1e-8 for double, ~3e-4 for float). Smaller steps make the derivative *worse*.

Rule of thumb: float32 is fine for individual sensor values and per-step math; anything that accumulates over time or subtracts near-equal quantities wants double or a reformulation.

## Solving linear systems: LU, QR, Cholesky, and why sparsity is everything in SLAM

First commandment: **never compute an explicit matrix inverse to solve a system**. `x = A.inverse() * b` is slower and less accurate than a factorization-based solve, and in 15 years of robotics code I've needed an actual inverse maybe twice (covariance reporting, basically).

| Factorization | Requirements | Relative cost | When to use |
| --- | --- | --- | --- |
| LU (partial pivoting) | Square, invertible | 1x | General square systems |
| Cholesky (LLT) | Symmetric positive definite | ~0.5x | Covariances, information matrices, normal equations |
| LDLT | Symmetric, possibly semi-definite | ~0.5x | SPD-ish matrices that might be borderline |
| QR (column pivoting) | Any shape | ~2x | Least squares, rank questions |
| SVD | Any shape | ~10x+ | Rank-deficient, ill-conditioned, "I need the truth" |

Two things worth internalizing:

1. **Cholesky doubles as a PD test.** It fails cleanly (Eigen reports it via `.info()`) the moment the matrix isn't positive definite. Cheaper and more decisive than checking eigenvalues.
2. **Normal equations square the condition number.** Solving least squares via $$A^\top A x = A^\top b$$ gives $$\kappa(A^\top A) = \kappa(A)^2$$. For well-conditioned problems nobody cares; for calibration and bundle adjustment it's the difference between converging and not. QR solves the same problem on $$A$$ directly.

**Sparsity is the entire reason modern SLAM works.** The Hessian / information matrix of a factor graph is sparse - each factor touches a handful of variables. Sparse Cholesky with a fill-reducing ordering (AMD/COLAMD) plus the Schur complement trick on landmarks turns a problem that would be $$O(n^3)$$ dense into something that solves $$10^5$$ variables in tens of milliseconds. That observation, not better filters, is what killed EKF-SLAM - the full story is in [graph-slam.md](../slam-and-state-estimation/graph-slam.md). GTSAM, g2o, and Ceres are at heart sparse linear algebra engines with a Lie-group veneer.

## Why your covariance went non-positive-definite

This is the most common numerical failure in Kalman filtering, and the [filter SLAM page](../slam-and-state-estimation/filter-slam.md) gives you the equations that cause it. The textbook covariance update

$$
\mathbf{P} = (\mathbf{I} - \mathbf{K}\mathbf{H})\mathbf{P}^-
$$

is a subtraction of nearly equal matrices when measurements are informative. Roundoff makes $$\mathbf{P}$$ slightly asymmetric, then slightly indefinite, then your Mahalanobis gating produces NaNs and the filter diverges - typically hours into a run, never on your desk.

Fixes, in the order I'd apply them:

1. **Symmetrize after every update**: `P = 0.5 * (P + P.transpose())`. One line, removes the asymmetry drift. Should be in every hand-rolled EKF.
2. **Use the Joseph form**:

$$
\mathbf{P} = (\mathbf{I} - \mathbf{K}\mathbf{H})\mathbf{P}^-(\mathbf{I} - \mathbf{K}\mathbf{H})^\top + \mathbf{K}\mathbf{R}\mathbf{K}^\top
$$

It's a sum of PSD terms, so it stays PSD for *any* gain $$\mathbf{K}$$, including a suboptimal one. Costs maybe 2-3x the flops of the short form - on any state under a few hundred dimensions you will not notice, and it removes a whole class of field failures.

3. **Square-root filtering.** Propagate a Cholesky factor of $$\mathbf{P}$$ instead of $$\mathbf{P}$$ itself. Effectively halves the condition number exponent, and PD is guaranteed by construction. This was mandatory in the float32 avionics era; today it matters mostly on MCUs and for badly scaled states.
4. **Mind your units.** A state mixing millimeters, radians, and gyro bias in rad/s can hit condition numbers of 1e12 before any algorithm misbehaves. Scale states to be O(1) and half your conditioning problems disappear.
5. **Eigenvalue clamping / adding $$\epsilon \mathbf{I}$$** - the duct tape. It works, but it's hiding a bug in steps 1-4. Treat it as a tripwire that logs loudly, not a silent fix.

> **Field notes:** the symptom of a near-indefinite covariance is rarely a crash. It's a filter that becomes weirdly overconfident in one state direction, rejects valid measurements via gating, and then drifts. If your innovation gating starts rejecting good measurements after long runtimes, check `P`'s symmetry and minimum eigenvalue before touching the noise parameters.

## Numerical integration: Euler to RK4, and what physics engines actually do

You integrate ODEs constantly: simulating dynamics, propagating IMU state, rolling out motion models.

- **Explicit Euler**: $$x_{k+1} = x_k + h f(x_k)$$. First-order error, and for oscillatory systems it *adds energy* every step - a simulated pendulum swings higher and higher until it explodes. Acceptable only for short rollouts with small $$h$$.
- **Semi-implicit (symplectic) Euler**: update velocity first, then position using the *new* velocity. Same cost as explicit Euler, but it doesn't pump energy. This is what most game and robotics physics engines actually run as their default - MuJoCo and Bullet included (MuJoCo also offers an RK4 mode).
- **RK4**: fourth-order, four function evaluations per step. The default answer for smooth dynamics - IMU propagation, vehicle models, anything where you control $$f$$ and it's not stiff.
- **Implicit methods**: stable at large steps for stiff systems, at the price of solving a (non)linear system per step. Drake leans on these for stiff contact-rich simulation.

The word that matters is **stiff**. Contact, high-gain joint controllers, and stiff spring-dampers put fast eigenvalues into your dynamics; explicit integrators then need step sizes inversely proportional to the fastest mode or they blow up. Physics engines mostly sidestep this by *not* integrating contact as stiff springs - they formulate contact as constraints solved each step (LCP / projected Gauss-Seidel style solvers, or MuJoCo's smooth convex relaxation). So "what integrator does the engine use" is half the story; the constraint solver settings (iterations, solver tolerance) usually affect sim fidelity more than the integrator choice. More on the engines themselves in [simulations.md](../computer-aided-designs-and-simulations/simulations.md).

Practical defaults: RK4 for your own smooth models, the engine's semi-implicit default for physics sims, and if your simulation jitters at contacts, increase solver iterations before shrinking the timestep.

## Root finding and nonlinear solvers

Root finding is "solve $$f(x) = 0$$." In 1D, bisection is slow but cannot fail on a bracketed root; Newton's method converges quadratically but can diverge from a bad start. Brent's method (what `scipy.optimize.brentq` implements) combines both and is the right 1D default.

The robotics version is multidimensional: **inverse kinematics is root finding**. You want joint angles $$q$$ such that

$$
f(q) = \mathrm{FK}(q) - x_{target} = 0
$$

Newton's step is $$\Delta q = -J^{-1} f(q)$$ with $$J$$ the manipulator Jacobian. Everything that makes numerical IK annoying is a root-finding pathology wearing a robotics costume:

- **Singularities** = rank-deficient Jacobian. The fix is damped least squares: $$\Delta q = -J^\top (J J^\top + \lambda^2 \mathbf{I})^{-1} f(q)$$, which is exactly a Levenberg-Marquardt step. The damping $$\lambda$$ trades convergence speed near the solution against not exploding near singularities.
- **Multiple solutions** = multiple roots; Newton finds whichever basin you start in. Seed from the current configuration for tracking, from multiple restarts for redundancy resolution.
- **Joint limits** turn it into constrained root finding - this is why plain Newton-Raphson IK (KDL's classic solver) fails near limits and why TRAC-IK-style solvers add an SQP formulation.

For least-squares problems (calibration, SLAM back-ends, bundle adjustment), the same Newton family appears as **Gauss-Newton** (drop the second-order residual terms) and **Levenberg-Marquardt** (Gauss-Newton plus adaptive damping). LM is the sane default: it degrades gracefully to gradient descent when the linearization is bad and accelerates to Gauss-Newton when it's good. Writing one from scratch is a genuinely useful exercise - I did exactly that for the pose-graph back-end in [GO-SLAM](../authors-projects/go-slam.md), and nothing teaches you damping schedules and convergence criteria faster than watching your own solver oscillate. For production, use [an existing library](../programming-for-robotics/optimization-libraries.md) - Ceres, GTSAM, g2o.

## Interpolation and splines for trajectories

Connecting waypoints sounds trivial and isn't, because robots care about derivatives.

- **Linear interpolation** gives discontinuous velocity at every waypoint - fine for lookup tables, unacceptable for joint commands (you're asking for infinite acceleration).
- **Cubic splines** give continuous position, velocity, and acceleration ($$C^2$$). The standard choice for smooth joint-space trajectories through waypoints.
- **Quintic polynomials** let you specify position, velocity, *and* acceleration at both endpoints - the default for point-to-point segments where you want to start and stop at rest, and what most industrial trajectory generators hand you.
- **B-splines** trade exact interpolation for local control and the convex hull property: the curve stays inside the hull of its control points, which makes corridor and collision constraints easy to enforce. That's why uniform B-splines dominate quadrotor trajectory optimization and show up in continuous-time SLAM.
- **High-degree polynomial interpolation through many points** - don't. Runge's phenomenon makes the curve oscillate wildly between samples. Use piecewise low-degree splines instead.

For rotations: never lerp quaternion components and hope. **SLERP** between two orientations; for smooth trajectories through many orientations, use squad or B-splines formulated on the manifold. And remember $$q$$ and $$-q$$ are the same rotation - check the dot product sign before interpolating or you'll get the long way around.

How these primitives slot into the planning stack - time parameterization, velocity limits, jerk constraints - is covered in [trajectory-planning.md](../mobile-robotics/trajectory-planning.md).

## Practical advice

Eigen idioms that matter (more C++ context in [cpp-for-robotics.md](../programming-for-robotics/cpp-for-robotics.md)):

- `A.ldlt().solve(b)` for SPD systems, `A.partialPivLu().solve(b)` for general square, `A.colPivHouseholderQr().solve(b)` for least squares. Pick the decomposition deliberately; don't reach for `.inverse()`.
- **Never use `auto` with Eigen expressions.** `auto x = A * b;` captures an expression template referencing temporaries that may be dead by the time you read `x`. This is the single most common Eigen footgun. Write the concrete type.
- `.noalias()` on products you know don't alias (`C.noalias() = A * B;`) skips a temporary.
- Fixed-size types (`Matrix3d`, `Vector6d`) get fully unrolled and vectorized - use them for anything pose-sized. Heap-allocated dynamic matrices inside a 1 kHz control loop are a self-inflicted wound.
- For sparse systems use `SimplicialLLT` / `SimplicialLDLT` and **check `.info() == Eigen::Success`** after factorization. A failed sparse factorization returns garbage, not an exception.

When to trust `solve()`: when the residual says so. A cheap post-check - `(A*x - b).norm() / b.norm()` - catches most disasters. If you suspect conditioning, the ratio of largest to smallest singular value is the diagnosis tool; as a rough guide you lose $$\log_{10}\kappa$$ digits of accuracy, so $$\kappa \approx 10^{12}$$ in double precision leaves you ~3-4 trustworthy digits. Robotics problems usually get ill-conditioned through unit mismatches and degenerate geometry (coplanar calibration targets, unobservable states), and the fix is reformulation, not a fancier solver.

Last one: write a regression test that runs your filter or solver for *simulated hours*, not seconds. Every numerical failure mode in this page - timestamp resolution, covariance asymmetry, energy drift - is invisible in a 10-second unit test and obvious in a 10-hour one.

## Where to go next

- [Linear Algebra for Robotics](../foundations/linear-algebra-for-robotics.md) - the decompositions and geometry this page assumes you've met once.
- [Graph-based SLAM](../slam-and-state-estimation/graph-slam.md) - sparse nonlinear least squares as a complete, deployed system.
- [Optimization Libraries](../programming-for-robotics/optimization-libraries.md) - Ceres, GTSAM, OSQP and friends, so you don't hand-roll the solvers from this page.
- [Trajectory Planning](../mobile-robotics/trajectory-planning.md) - where the splines and integrators get used in anger.
