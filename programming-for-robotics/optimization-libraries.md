---
icon: code
---

# Optimization Libraries

A surprising fraction of robotics reduces to "minimize this function." Bundle adjustment is least squares. SLAM is a factor graph. Trajectory optimization is constrained nonlinear. Task planning is sometimes integer programming. Knowing which library to reach for, and why, saves weeks.

This page covers the libraries I've actually used in shipped robot code. Each section: what it's for, what it's not for, a minimal example, and where to read more.

## Ceres Solver - nonlinear least squares

**Author:** Google. **License:** BSD-3-Clause. **Repo:** <https://github.com/ceres-solver/ceres-solver>

Ceres is the workhorse for bundle adjustment, SLAM back-ends, calibration, and any "I have a model with parameters and measurements with noise, find the parameters that best explain the data" problem. It's C++, with Python bindings via `pyceres` (community-maintained).

It solves problems of the form
$$\min_{x} \sum_i \rho_i\left(\|f_i(x_{i,1}, \dots, x_{i,k})\|^2\right)$$
where each `f_i` is a *cost function* (residual block) and `ρ` is an optional robust loss (Huber, Cauchy, etc., to downweight outliers).

```cpp
#include <ceres/ceres.h>

struct ReprojectionResidual {
    ReprojectionResidual(double u, double v) : u_(u), v_(v) {}

    template <typename T>
    bool operator()(const T* const camera,   // 6-DoF pose
                    const T* const point,    // 3D point
                    T* residuals) const {
        // project point with camera, residuals = projection - (u, v)
        // ...
        return true;
    }
    double u_, v_;
};

ceres::Problem problem;
for (const auto& obs : observations) {
    auto* cost = new ceres::AutoDiffCostFunction<ReprojectionResidual, 2, 6, 3>(
        new ReprojectionResidual(obs.u, obs.v));
    problem.AddResidualBlock(cost, new ceres::HuberLoss(1.0),
                             cameras[obs.cam_id], points[obs.point_id]);
}

ceres::Solver::Options options;
options.linear_solver_type = ceres::SPARSE_SCHUR;  // for BA structure
options.minimizer_progress_to_stdout = true;
ceres::Solver::Summary summary;
ceres::Solve(options, &problem, &summary);
```

**The killer feature:** automatic differentiation via templated cost functors. You write the residual once with `template <typename T>`, Ceres instantiates it with both `double` (for the residual) and a dual-number type (for the Jacobian). No hand-derived derivatives, no finite differences, no errors from sloppy chain rule.

**When to use:** camera calibration, hand-eye calibration, IMU-camera calibration (Kalibr uses Ceres), bundle adjustment, pose graph optimization, lidar-camera extrinsics. Anything that's least-squares-shaped.

**When not to use:** if you need a *factor graph* with structure-aware solvers (iSAM-style incremental updates), reach for GTSAM. If you need inequality constraints, Ceres has only bound constraints - use IPOPT or CasADi.

Docs: <http://ceres-solver.org/>

## g2o - general graph optimization

**Author:** Rainer Kümmerle et al. **License:** BSD-2-Clause. **Repo:** <https://github.com/RainerKuemmerle/g2o>

g2o is the historical SLAM back-end. ORB-SLAM2/3 uses it, many older pose-graph SLAM systems do too. It's a C++ framework for least-squares optimization on graphs where vertices are variables (poses, landmarks) and edges are measurements between them.

```cpp
#include <g2o/core/sparse_optimizer.h>
#include <g2o/types/slam3d/types_slam3d.h>

g2o::SparseOptimizer optimizer;
auto* solver = new g2o::OptimizationAlgorithmLevenberg(...);
optimizer.setAlgorithm(solver);

// Add pose vertices
for (int i = 0; i < n_poses; ++i) {
    auto* v = new g2o::VertexSE3();
    v->setId(i);
    v->setEstimate(initial_poses[i]);
    if (i == 0) v->setFixed(true);
    optimizer.addVertex(v);
}

// Add odometry edges
for (const auto& z : odom_measurements) {
    auto* e = new g2o::EdgeSE3();
    e->vertices()[0] = optimizer.vertex(z.from);
    e->vertices()[1] = optimizer.vertex(z.to);
    e->setMeasurement(z.relative_pose);
    e->setInformation(z.info_matrix);
    optimizer.addEdge(e);
}

optimizer.initializeOptimization();
optimizer.optimize(10);
```

**When to use:** maintaining or extending a pre-existing g2o-based system (ORB-SLAM, older RTAB-Map). Educational - the graph structure is very visible.

**When not to use:** for a new project in 2026, I'd reach for GTSAM or Ceres first. g2o development has slowed and the API feels dated next to GTSAM's. See `../slam-and-state-estimation/graph-slam.md` for a deeper comparison.

## GTSAM - factor graphs done right

**Author:** Frank Dellaert / Georgia Tech. **License:** BSD-3-Clause. **Repo:** <https://github.com/borglab/gtsam>

GTSAM models everything as a *factor graph*. Variables (poses, biases, landmarks) connect to factors (measurements, priors, constraints). The library knows how to do batch optimization (Levenberg-Marquardt), incremental optimization (iSAM2, the killer feature for online SLAM), and fixed-lag smoothing.

```cpp
#include <gtsam/nonlinear/NonlinearFactorGraph.h>
#include <gtsam/nonlinear/ISAM2.h>
#include <gtsam/slam/BetweenFactor.h>
#include <gtsam/geometry/Pose3.h>

using namespace gtsam;

ISAM2 isam(ISAM2Params{});
NonlinearFactorGraph graph;
Values initial;

// Prior on first pose
graph.emplace_shared<PriorFactor<Pose3>>(0, Pose3(), prior_noise);
initial.insert(0, Pose3());

// As measurements arrive online:
for (int i = 1; /* forever */; ++i) {
    Pose3 odom_delta = read_odometry();
    graph.emplace_shared<BetweenFactor<Pose3>>(i - 1, i, odom_delta, odom_noise);
    initial.insert(i, current_estimate * odom_delta);

    isam.update(graph, initial);
    Values result = isam.calculateEstimate();

    graph.resize(0);    // iSAM2 keeps internal state; clear local graph
    initial.clear();
}
```

**The killer feature:** iSAM2 incrementally updates the solution as new measurements arrive without re-solving from scratch. For online SLAM where you can't afford a full batch solve every iteration, this is the technique. <https://gtsam.org/>

GTSAM has Python bindings (`pip install gtsam`) that are first-class, not an afterthought. <https://gtsam.org/get_started/> [verify]

**When to use:** online SLAM, multi-sensor fusion via factor graphs, anything where the problem structure is naturally a graph of measurements. Modern alternatives like Kimera-VIO and LIO-SAM are built on GTSAM.

**When not to use:** simple least-squares with no graph structure - Ceres is lighter. Hard real-time inner loops - GTSAM is fast but not deterministic to the microsecond.

## CasADi - symbolic + autodiff + NLP

**License:** LGPL. **Repo:** <https://github.com/casadi/casadi>. **Web:** <https://web.casadi.org/>

CasADi is unusual: it's a symbolic math framework with built-in automatic differentiation, designed specifically for optimization and optimal control. You write your model in CasADi's symbolic language, it generates derivatives, and you pass the result to IPOPT, SQP, or its own QP solvers.

The dominant use case in robotics: **MPC**. You describe the system dynamics symbolically, define a cost and constraints, and CasADi gives you a callable function that solves the resulting NLP at each control step.

```python
import casadi as ca

# Decision variables: states x and controls u over horizon N
N = 20
x = ca.SX.sym('x', 3, N + 1)  # [px, py, theta]
u = ca.SX.sym('u', 2, N)      # [v, omega]
dt = 0.1

# Dynamics (unicycle)
def f(x, u):
    return ca.vertcat(u[0] * ca.cos(x[2]),
                      u[0] * ca.sin(x[2]),
                      u[1])

# Build cost and constraints
cost = 0
g = []  # equality constraints (dynamics)
for k in range(N):
    cost += ca.sumsqr(x[:, k] - x_ref[:, k]) + 0.01 * ca.sumsqr(u[:, k])
    g.append(x[:, k + 1] - (x[:, k] + dt * f(x[:, k], u[:, k])))

nlp = {'x': ca.vertcat(ca.reshape(x, -1, 1), ca.reshape(u, -1, 1)),
       'f': cost,
       'g': ca.vertcat(*g)}
solver = ca.nlpsol('solver', 'ipopt', nlp)

# At runtime, call solver with initial guess and bounds
sol = solver(x0=z_init, lbg=0, ubg=0, lbx=z_lb, ubx=z_ub)
```

**Killer features:** the symbolic-then-codegen workflow lets you generate optimized C code from your problem, which compiled-in is what makes embedded MPC possible.

**When to use:** MPC for mobile robots and drones, trajectory optimization, parameter estimation with nonlinear dynamics.

**When not to use:** convex problems where CVXPY is more ergonomic; embedded MPC where you really need the fastest possible runtime (acados is built on top of CasADi and is faster for that case).

## CVXPY - convex optimization

**License:** Apache-2.0. **Repo:** <https://github.com/cvxpy/cvxpy>. **Web:** <https://www.cvxpy.org/>

If your problem is convex (QP, SOCP, SDP, LP) - and a remarkable amount of control reduces to QP - CVXPY is the most ergonomic library. You write the problem in math-like notation, CVXPY transforms it to a standard form and dispatches to a backend solver (OSQP, ECOS, SCS, MOSEK).

```python
import cvxpy as cp
import numpy as np

# Simple QP-style controller: minimize ||u - u_des||^2 s.t. limits and CBFs
u = cp.Variable(2)
u_des = np.array([0.5, 0.0])

constraints = [
    cp.norm(u, 'inf') <= 1.0,           # input limits
    A @ u + b <= 0,                      # control barrier function (affine in u)
]
prob = cp.Problem(cp.Minimize(cp.sum_squares(u - u_des)), constraints)
prob.solve(solver=cp.OSQP)
u_safe = u.value
```

**When to use:** safe-control filters (CBF-QPs), low-level controllers expressible as QP, anything where you'd otherwise hand-write a QP setup. Prototyping is where it shines.

**When not to use:** hard real-time. CVXPY's per-solve overhead in pure Python is hundreds of microseconds even with cached compilation. For deployed real-time QPs, write directly against `osqp` (its Python and C interfaces) or use `cvxpygen` to generate C code from a CVXPY problem. <https://github.com/cvxgrp/cvxpygen> [verify]

## OR-Tools - combinatorial / integer

**Author:** Google. **License:** Apache-2.0. **Repo:** <https://github.com/google/or-tools>. **Web:** <https://developers.google.com/optimization>

When the variables are *discrete* - pick one of these N items, assign these jobs to these machines, visit these cities in some order - least squares doesn't help. You need constraint programming (CP-SAT), mixed integer programming (MIP), or specialized routing.

OR-Tools is Google's swiss army knife. The headline solver is **CP-SAT**, which is a SAT-based constraint programming solver that handles linear, boolean, and many global constraints with industrial-grade performance.

```python
from ortools.sat.python import cp_model

model = cp_model.CpModel()
n = len(items)

# x[i] = position of item i in the sequence (0..n-1)
x = [model.NewIntVar(0, n - 1, f'x_{i}') for i in range(n)]
model.AddAllDifferent(x)

# Add domain-specific constraints, e.g. order constraints from priorities
for a, b in must_be_before:
    model.Add(x[a] < x[b])

# Minimize total travel distance (a function of the order)
# ... build distance expression ...
model.Minimize(total_dist)

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 10.0
status = solver.Solve(model)
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    order = sorted(range(n), key=lambda i: solver.Value(x[i]))
```

**Pan used CP-SAT in LEAP** (his pick-and-place TSP project) for the task-sequencing layer - given a set of pick locations, place locations, and reachability constraints, find the order that minimizes manipulator travel time. CP-SAT was the right call because: small N (tens of items), hard ordering constraints, and the cost function wasn't quite a clean TSP. See [LEAP](../authors-projects/leap.md) for the project write-up.

**When to use:** task scheduling, pick orderings, multi-robot task allocation, anything with integer or boolean variables, vehicle routing (OR-Tools also has a dedicated VRP solver).

**When not to use:** anything continuous - wrong tool entirely.

## acados - embedded MPC

**License:** BSD-2-Clause. **Repo:** <https://github.com/acados/acados>. **Web:** <https://docs.acados.org/>

acados is for one thing: making MPC fast enough to run on real robots. It's a C library that, given a problem described in Python (using CasADi for the dynamics), generates highly optimized C code implementing SQP-RTI (real-time iteration) with HPIPM as the inner QP solver.

```python
from acados_template import AcadosOcp, AcadosOcpSolver
import casadi as ca

ocp = AcadosOcp()
# define model (x_dot = f(x, u)) using CasADi SX
# define cost (least-squares form is fastest)
# define constraints
ocp.solver_options.tf = 1.0
ocp.solver_options.N_horizon = 20
ocp.solver_options.nlp_solver_type = 'SQP_RTI'
ocp.solver_options.qp_solver = 'PARTIAL_CONDENSING_HPIPM'
ocp.solver_options.integrator_type = 'ERK'

solver = AcadosOcpSolver(ocp, json_file='ocp.json')
# Now `solver.solve()` is a generated C function - microseconds per iteration
```

**Killer feature:** real-time iteration MPC at sub-millisecond solve times on embedded hardware. This is what makes MPC viable for drone control, agile manipulation, etc.

**When to use:** any MPC you actually need to run on a robot at 50-1000 Hz. Quadrotors, autonomous racing, manipulation.

**When not to use:** prototyping (CasADi alone is friendlier). Non-MPC optimization problems.

## Drake - multi-purpose

**Author:** Toyota Research Institute / MIT (Russ Tedrake). **License:** BSD-3-Clause. **Repo:** <https://github.com/RobotLocomotion/drake>. **Web:** <https://drake.mit.edu/>

Drake is a kitchen-sink toolbox: dynamics simulation, motion planning, trajectory optimization, system identification, and a `MathematicalProgram` abstraction that uses Drake's own solvers (or wraps SNOPT, IPOPT, MOSEK, OSQP, Gurobi).

It's heavier than the other libraries on this page. The right answer is "use Drake when you're already in Drake's world" (Russ Tedrake's *Underactuated Robotics* and *Robotic Manipulation* courses are built on it, and that's how most people end up there).

```python
from pydrake.solvers import MathematicalProgram, Solve

prog = MathematicalProgram()
x = prog.NewContinuousVariables(2, 'x')
prog.AddCost(x[0]**2 + x[1]**2)
prog.AddConstraint(x[0] + x[1] == 1)
prog.AddBoundingBoxConstraint(0, 10, x)
result = Solve(prog)
print(result.GetSolution(x))
```

**When to use:** if you're already doing trajectory optimization for manipulation in Drake's `MultibodyPlant`, the integrated stack is hard to beat. Direct collocation, contact-implicit trajectory optimization, semi-definite programming for Lyapunov analysis - Drake has built-in support.

**When not to use:** standalone optimization problem with no need for Drake's simulation/dynamics. The dependency footprint is large.

## Decision table

| Problem shape | Reach for |
|---|---|
| Calibration, hand-eye, BA, pose graph (batch) | **Ceres** |
| Online/incremental SLAM, factor graphs | **GTSAM** (iSAM2) |
| Maintaining legacy SLAM pose graph | **g2o** |
| MPC prototyping | **CasADi** + IPOPT |
| MPC for deployment (real-time, embedded) | **acados** |
| Convex QP/SOCP control filter (CBFs, safety) | **CVXPY** → `osqp` for deployment |
| Discrete: scheduling, assignment, routing, TSP | **OR-Tools** (CP-SAT) |
| Trajectory optimization with multibody dynamics | **Drake** |
| Generic nonlinear with constraints | IPOPT directly, or CasADi as a friendly front-end |

## Honorable mentions

- **IPOPT** - the workhorse interior-point NLP solver under most of the above. <https://github.com/coin-or/Ipopt>
- **OSQP** - small, fast operator-splitting QP. Used by CVXPY by default. <https://osqp.org/>
- **HPIPM** - Hagen-Penzler interior-point QP, fast for MPC-shaped problems. Used inside acados. <https://github.com/giaf/hpipm> [verify]
- **NLOPT** - collection of nonlinear optimization algorithms, good for derivative-free. <https://nlopt.readthedocs.io/>
- **JAX + Optax** - for ML-flavored optimization, learned controllers. Different world but increasingly relevant.

## Related pages

- [LEAP - pick-and-place TSP with CP-SAT](../authors-projects/leap.md) - Pan's project applying OR-Tools CP-SAT to manipulator task sequencing.
- [Graph SLAM](../slam-and-state-estimation/graph-slam.md) - deeper dive into where Ceres/g2o/GTSAM fit in the SLAM back-end.

## Further reading

- *Convex Optimization* - Boyd & Vandenberghe. Free online. Foundational. <https://web.stanford.edu/~boyd/cvxbook/>
- *Numerical Optimization* - Nocedal & Wright. The reference for nonlinear methods.
- *Underactuated Robotics* - Russ Tedrake. Free online. The Drake-flavored tour of trajectory optimization. <https://underactuated.mit.edu/>
- *Factor Graphs for Robot Perception* - Dellaert & Kaess. The GTSAM-flavored tour. <https://www.cs.cmu.edu/~kaess/pub/Dellaert17fnt.pdf> [verify]

The skill that compounds: recognize the shape of a problem fast, and pick the library that's already designed for that shape. Don't bring CasADi to a least-squares fight; don't bring Ceres to an integer programming fight.
