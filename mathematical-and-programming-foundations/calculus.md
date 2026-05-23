---
icon: integral
---

# Calculus

### Differentiation in Kinematics <a href="#differentiation-in-kinematics" id="differentiation-in-kinematics"></a>

Robotic motion is often defined by a position function q(t)q(t) of joint angles or Cartesian coordinates over time. Differentiation yields:

* **Velocity**

$$
\dot{q}(t) = \frac{d}{dt}q(t)
$$

* **Acceleration**

$$$
$$
\ddot{q}(t) = \frac{d^2}{dt^2} q(t)
$$
$$$

Example: for a single-joint rotary robot moving from angle θ0θ0 to θfθf via a cubic trajectory, the velocity and acceleration profiles are polynomials in tt.

$$
theta(t) = a_0 + a_1 t + a_2 t^2 + a_3 t^3
$$

$$
theta(t) = a_1 + 2a_2\,t + 3a_3\,t^2
$$

$$
theta(t) = 2a_2 + 6a_3\,t
$$

### Integration in Motion and Sensing <a href="#integration-in-motion-and-sensing" id="integration-in-motion-and-sensing"></a>

Integration accumulates rates into displacements or sensor estimates:

* **Position from velocity**: q(t)=q(t0)+∫t0tq˙(τ) dτq(t)=q(t0)+∫t0tq˙(τ)dτ
* **State estimation (e.g., odometry)**: integrating wheel velocities to track robot pose.

Example: integrating a constant acceleration aa gives velocity and displacement:

$$
v(t) = v_0 + a\,t
$$

$$
s(t) = s_0 + v_0\,t + \tfrac12\,a\,t^2
$$

### Trajectory Planning <a href="#trajectory-planning" id="trajectory-planning"></a>

Selecting smooth paths between waypoints requires piecewise-polynomial fits that ensure continuous position, velocity, and sometimes acceleration. A common choice is the cubic segment between times titi and ti+1ti+1:

$$
q_i(\tau) = C_0 + C_1 \tau + C_2 \tau^2 + C_3 \tau^3,\quad \tau\in[0,\,T]
$$

With boundary conditions

$$
qi(0)=q(ti)
$$

$$
q˙i(0)=q˙(ti)
$$

$$
qi(T)=q(ti+1)
$$

$$
q˙i(T)=q˙(ti+1)
$$

$$
qi(0)=q(ti)
$$

$$
q˙i(0)=q˙(ti)
$$

$$
qi(T)=q(ti+1)
$$

$$
q˙i(T)=q˙(ti+1)
$$

### Dynamics via Lagrange’s Equations <a href="#dynamics-via-lagranges-equations" id="dynamics-via-lagranges-equations"></a>

Robot dynamics relate joint torques ττ, positions qq, and accelerations q¨q¨. The Euler–Lagrange formulation yields:

$$
M(q)\,\ddot q + C(q,\dot q)\,\dot q + g(q) = \tau
$$

where

* M(q)M(q) is the mass (inertia) matrix,
* C(q,q˙)C(q,q˙) contains Coriolis and centrifugal terms,
* g(q)g(q) is the gravity vector.

### Control System Design <a href="#control-system-design" id="control-system-design"></a>

Calculus underlies feedback controllers and optimizations:

* **PID control** uses proportional, integral, and derivative terms on tracking error e(t)e(t):

$$
u(t) = K_P e(t) + K_I \int_0^t e(\tau)\,d\tau + K_D \tfrac{d}{dt}e(t)
$$

* **Linear Quadratic Regulator (LQR)** solves continuous-time algebraic Riccati equations to minimize a quadratic cost.

### Perception and Computer Vision <a href="#perception-and-computer-vision" id="perception-and-computer-vision"></a>

In vision, image coordinates x(u,v)x(u,v) vary with time as cameras or objects move. Optical flow computes image velocity:

$$
\dot I + \nabla I \cdot \mathbf{v} = 0
$$

where I˙I˙ is the temporal image derivative, ∇I∇I its spatial gradient, and vv the pixel velocity.

Calculus thus weaves through every phase of robotics: from physical motion and sensor fusion to high-level planning and control, allowing robots to move smoothly, react reliably, and perceive accurately.
