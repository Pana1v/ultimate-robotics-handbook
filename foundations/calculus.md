---
icon: integral
---

# Calculus

Calculus is the mathematical language of *change* — and robotics is the engineering of motion, sensing, and control. Every velocity comes from a derivative, every odometry estimate from an integral, every controller from minimizing a cost. This page covers the calculus concepts you actually use on a robot.

### Differentiation in Kinematics

Robotic motion is defined by a position function $q(t)$ of joint angles or Cartesian coordinates over time. Differentiation yields:

* **Velocity**

$$
\dot{q}(t) = \frac{d}{dt}q(t)
$$

* **Acceleration**

$$
\ddot{q}(t) = \frac{d^2}{dt^2} q(t)
$$

**Example — cubic joint trajectory.** For a single-joint rotary robot moving smoothly from $\theta_0$ to $\theta_f$ via a cubic in $t$:

$$
\theta(t) = a_0 + a_1 t + a_2 t^2 + a_3 t^3
$$

$$
\dot{\theta}(t) = a_1 + 2 a_2 t + 3 a_3 t^2
$$

$$
\ddot{\theta}(t) = 2 a_2 + 6 a_3 t
$$

Cubics give continuous velocity but discontinuous jerk — fine for low-speed manipulators, painful for high-acceleration arms or AMRs. For those, use quintic polynomials or s-curves.

### Integration in Motion and Sensing

Integration accumulates rates into displacements or sensor estimates:

* **Position from velocity:** $q(t) = q(t_0) + \int_{t_0}^{t} \dot{q}(\tau)\, d\tau$
* **Odometry:** integrating wheel velocities to track robot pose (and accumulating drift in the process — this is why you fuse with IMU/LiDAR).

**Example — constant acceleration:**

$$
v(t) = v_0 + a\,t
$$

$$
s(t) = s_0 + v_0\,t + \tfrac{1}{2}\,a\,t^2
$$

### Trajectory Planning

Smooth paths between waypoints require piecewise-polynomial fits with continuous position, velocity, and (often) acceleration. A common segment between times $t_i$ and $t_{i+1}$ is the cubic:

$$
q_i(\tau) = C_0 + C_1 \tau + C_2 \tau^2 + C_3 \tau^3,\quad \tau \in [0,\,T]
$$

With boundary conditions tying segments together:

$$
q_i(0) = q(t_i),\quad \dot{q}_i(0) = \dot{q}(t_i)
$$

$$
q_i(T) = q(t_{i+1}),\quad \dot{q}_i(T) = \dot{q}(t_{i+1})
$$

This gives four equations for the four unknowns $C_0, C_1, C_2, C_3$. Higher-order splines (quintic, septic) add acceleration/jerk continuity at extra computational cost.

### Dynamics via Lagrange's Equations

Robot dynamics relate joint torques $\boldsymbol{\tau}$, positions $\mathbf{q}$, velocities $\dot{\mathbf{q}}$, and accelerations $\ddot{\mathbf{q}}$. The Euler–Lagrange formulation yields the canonical manipulator equation:

$$
M(\mathbf{q})\,\ddot{\mathbf{q}} + C(\mathbf{q},\dot{\mathbf{q}})\,\dot{\mathbf{q}} + \mathbf{g}(\mathbf{q}) = \boldsymbol{\tau}
$$

Where:

* $M(\mathbf{q})$ is the mass (inertia) matrix
* $C(\mathbf{q},\dot{\mathbf{q}})$ contains Coriolis and centrifugal terms
* $\mathbf{g}(\mathbf{q})$ is the gravity vector

Inverse dynamics (compute $\boldsymbol{\tau}$ from $\ddot{\mathbf{q}}$) is the basis for computed-torque control. Forward dynamics (compute $\ddot{\mathbf{q}}$ from $\boldsymbol{\tau}$) drives simulation.

### Control System Design

Calculus underlies feedback controllers and optimal control:

**PID control** combines proportional, integral, and derivative terms on tracking error $e(t)$:

$$
u(t) = K_P\,e(t) + K_I \int_0^{t} e(\tau)\,d\tau + K_D\,\frac{d}{dt}\,e(t)
$$

The integral term eliminates steady-state error; the derivative term provides damping. Tuning is mostly empirical — start with P, add D for damping, add I last and sparingly (it causes wind-up).

**Linear Quadratic Regulator (LQR)** solves the continuous-time algebraic Riccati equation to minimize a quadratic cost $J = \int (\mathbf{x}^\top Q \mathbf{x} + \mathbf{u}^\top R \mathbf{u})\,dt$. The result is a state-feedback gain $\mathbf{u} = -K\mathbf{x}$ that's optimal for the linearized system.

**Model Predictive Control (MPC)** rolls the optimization forward in time over a finite horizon, re-solving every timestep. Heavier compute, but handles constraints (joint limits, obstacle avoidance) natively. See `../programming-for-robotics/optimization-libraries.md`.

### Perception and Computer Vision

In vision, image intensity $I(u, v, t)$ varies with camera/object motion. The **optical flow constraint equation** assumes brightness constancy:

$$
\frac{\partial I}{\partial t} + \nabla I \cdot \mathbf{v} = 0
$$

Where $\partial I / \partial t$ is the temporal derivative, $\nabla I = (I_u, I_v)$ is the spatial gradient, and $\mathbf{v}$ is the pixel velocity field. This single equation per pixel is under-constrained (two unknowns, one equation — the aperture problem), so methods like Lucas-Kanade add a smoothness assumption over a local window.

### Probability and Sensor Fusion (a teaser)

For state estimation (Kalman filters, particle filters), calculus shows up as:

* **Gaussian densities** — multiplying, marginalizing, conditioning all involve integrals.
* **Linearization** — the EKF approximates a nonlinear function $f(\mathbf{x})$ via its first-order Taylor expansion $f(\mathbf{x}) \approx f(\mathbf{x}_0) + J_f(\mathbf{x}_0)(\mathbf{x} - \mathbf{x}_0)$. The Jacobian $J_f$ is pure calculus.
* **Optimization** — graph SLAM (g2o, GTSAM, Ceres) minimizes nonlinear least squares via Gauss-Newton or Levenberg-Marquardt, both gradient-based.

See `../slam-and-state-estimation/sensor-fusion.md` and `../programming-for-robotics/optimization-libraries.md` for how these become real code.

---

Calculus weaves through every layer of robotics — from physical motion and sensor fusion to high-level planning and optimal control. Master it once, and the same intuition transfers from PID tuning to bundle adjustment to training neural policies.
