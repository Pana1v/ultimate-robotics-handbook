---
icon: hexagon-divide
---

# Linear Algebra for Robotics

### **Linear Algebra in Robotics and Computer Vision**

Linear algebra provides the mathematical language for describing and solving geometry, motion, perception, and control problems in robotics and computer vision. This overview covers key concepts and applications—from kinematic chains and dynamics to camera modeling, multi‐view geometry, state estimation, and feature extraction.

***

#### **Vector Spaces and Linear Mappings**

**Vectors and Norms**

A vector $\mathbf{v} \in \mathbb{R}^n$ encodes quantities like position, velocity, or torque. Its length (the Euclidean norm) is:

$$
\|\mathbf{v}\| = \sqrt{\mathbf{v}^\top \mathbf{v}}
$$

The projection of $\mathbf{v}$ onto $\mathbf{u}$:

$$
\text{proj}_{\mathbf{u}}(\mathbf{v}) = \frac{\mathbf{u}^\top \mathbf{v}}{\mathbf{u}^\top \mathbf{u}} \mathbf{u}
$$

***

**Inner Products and Orthogonality**

The dot product $\mathbf{u}^\top \mathbf{v}$ measures similarity and defines the angle between vectors:

$$
\cos \theta = \frac{\mathbf{u}^\top \mathbf{v}}{\|\mathbf{u}\|\,\|\mathbf{v}\|}
$$

Orthonormal bases (built via Gram–Schmidt) simplify coordinate transforms and least-squares problems. In SLAM and bundle adjustment, this is the foundation of everything.

***

#### **Matrices, Determinants, and Invertibility**

**Linear Transformations**

A matrix $A \in \mathbb{R}^{m \times n}$ maps $\mathbb{R}^n \rightarrow \mathbb{R}^m$. Composition is matrix multiplication: $(AB)\mathbf{x} = A(B\mathbf{x})$. Order matters — rotation followed by translation is not the same as translation followed by rotation.

***

#### Determinant and Rank

A matrix is invertible if and only if its determinant is non-zero:

$$
\det(A) \neq 0 \Rightarrow A \text{ is invertible}
$$

Rank deficiency implies singularity — critical in kinematics when Jacobians lose rank.

***

#### Eigen Decomposition & Singular Value Decomposition

**Eigenvalues and Eigenvectors**\
To analyze modes and stability, solve:

$$
A \mathbf{x} = \lambda \mathbf{x}
$$

**Singular Value Decomposition (SVD)**

$$
A = U \Sigma V^\top
$$

**Pseudoinverse**

$$
A^+ = V \Sigma^+ U^\top
$$

Used to solve least-squares

$$
A \mathbf{x} = \mathbf{b}
$$

with minimum norm. In vision, used for decomposing the essential matrix.

***

#### Rigid-Body Transforms: SO(3), SE(3), and Friends

**Rotation Matrices — the group SO(3)**

A 3D rotation is a matrix $R \in SO(3)$ satisfying:

$$
R^\top R = I,\quad \det(R) = +1
$$

That's 9 entries with 6 constraints → 3 degrees of freedom (as expected for a 3D rotation). SO(3) is a *Lie group* — smooth, but not a vector space. Don't naively interpolate rotation matrices entry-wise.

**Three equivalent ways to represent a 3D rotation:**

| Representation | Parameters | Pros | Cons |
|---|---|---|---|
| Rotation matrix $R$ | 9 (with 6 constraints) | Compose by multiplication; geometric clarity | Redundant; orthogonality drifts under numerical updates |
| Euler angles $(\phi, \theta, \psi)$ | 3 | Intuitive | **Gimbal lock**; ambiguous (12+ conventions); never use these in production |
| Axis–angle / rotation vector $\boldsymbol{\omega} = \theta \hat{\mathbf{u}}$ | 3 | Minimal; matches Lie-algebra $\mathfrak{so}(3)$ | Singular at $\theta = 0$ unless using rotation-vector form |
| Quaternion $\mathbf{q} = [q_w, q_x, q_y, q_z]$ | 4 (with $\|\mathbf{q}\|=1$) | No gimbal lock; cheap composition; smooth interpolation (SLERP) | Sign ambiguity ($\mathbf{q}$ and $-\mathbf{q}$ are the same rotation) |

**Rule of thumb (Pan's field note):** internal storage and computation → quaternions. User input/display → Euler. Math derivations and dynamics → rotation matrices. Conversions are cheap; pick the right tool per layer.

**Homogeneous Transformations — the group SE(3)**

A rigid-body pose combines rotation and translation:

$$
T = \begin{bmatrix} R & \mathbf{t} \\ \mathbf{0}^\top & 1 \end{bmatrix} \in SE(3),\quad
\mathbf{p}_{\text{world}} = T\,\mathbf{p}_{\text{local}}
$$

Composition is matrix multiplication: $T_{ac} = T_{ab}\,T_{bc}$. Inversion is *not* matrix inverse:

$$
T^{-1} = \begin{bmatrix} R^\top & -R^\top \mathbf{t} \\ \mathbf{0}^\top & 1 \end{bmatrix}
$$

In ROS 2, `tf2` handles all this for you — but understanding the algebra is essential for SLAM, calibration, and IK.

**The Lie algebra side: $\mathfrak{so}(3)$ and $\mathfrak{se}(3)$**

Optimization on SO(3)/SE(3) (used in graph SLAM, bundle adjustment, MPC on manifolds) is done by *lifting* to the Lie algebra — a vector space — via the matrix logarithm, performing updates additively, and *retracting* back to the group via the exponential.

For SO(3): the algebra is the space of 3-vectors $\boldsymbol{\omega} \in \mathbb{R}^3$ (the *rotation vector*), mapped to a rotation by Rodrigues' formula:

$$
R = \exp([\boldsymbol{\omega}]_\times) = I + \frac{\sin\theta}{\theta}[\boldsymbol{\omega}]_\times + \frac{1-\cos\theta}{\theta^2}[\boldsymbol{\omega}]_\times^2
$$

where $\theta = \|\boldsymbol{\omega}\|$ and $[\cdot]_\times$ is the skew-symmetric cross-product matrix.

For SE(3): the algebra is 6-dimensional — a *twist* $\boldsymbol{\xi} = (\mathbf{v}, \boldsymbol{\omega}) \in \mathbb{R}^6$ combining linear and angular velocity.

You don't need to derive this from scratch — GTSAM, Sophus, manif, and `tf2` handle the algebra correctly. But you *do* need to know that "adding two rotations" is undefined; "composing on the manifold via the Lie group" is what you mean.

**DH Parameters**

$(\theta, d, a, \alpha)$ — the classical Denavit–Hartenberg convention encodes each joint of a kinematic chain in 4 numbers, allowing systematic forward and inverse kinematic derivation. Modified DH (Craig's convention) differs slightly in axis placement; pick one and document it.

In 2026, URDF/xacro + KDL or Pinocchio supersedes hand-derived DH for most production work — but DH still shows up in classical IK papers and in industry textbooks.

***

#### Forward & Inverse Kinematics

**Forward Kinematics**\
Compute end-effector pose as the product of transforms:

$$
T = T_1 T_2 \cdots T_n
$$

**Inverse Kinematics**\
Solve for joint variables:

$$
T(\mathbf{q}) = T_{\text{desired}}
$$

Closed-form or iterative solutions via Newton–Raphson:

$$
f(\mathbf{q}) = 0
$$

***

#### Differential Kinematics: The Jacobian

**Jacobian Matrix**

Relates joint velocities $\dot{\mathbf{q}}$ to end-effector twist $\boldsymbol{\xi}$:

$$
\boldsymbol{\xi} = \begin{bmatrix} \dot{\mathbf{p}} \\ \boldsymbol{\omega} \end{bmatrix}
$$

$$
\boldsymbol{\xi} = J(\mathbf{q}) \dot{\mathbf{q}}
$$

Singularities occur when:

$$
\det(J) = 0
$$

**Inverse Differential Kinematics**\
Use pseudoinverse:

$$
\dot{\mathbf{q}} = J^+ \boldsymbol{\xi}
$$

Or apply damped least squares near singularities.

***

#### Dynamics & Control

**Lagrange Formulation**

$$
M(\mathbf{q}) \ddot{\mathbf{q}} + C(\mathbf{q}, \dot{\mathbf{q}}) \dot{\mathbf{q}} + \mathbf{g}(\mathbf{q}) = \boldsymbol{\tau}
$$

Where:

* MMM: mass matrix
* CCC: Coriolis matrix
* g\mathbf{g}g: gravity vector

**State-Space & LQR**\
Solve Riccati equation for gain matrix:

$$
A^\top P + P A - P B R^{-1} B^\top P + Q = 0
$$

***

#### Camera Models & Projective Geometry

**Pinhole Camera Model**

Maps a 3D world point $\mathbf{X} = [X, Y, Z, 1]^\top$ to an image point $\mathbf{x} = [u, v, 1]^\top$ via:

$$
\mathbf{x} \sim K [R \mid \mathbf{t}] \mathbf{X}
$$

Where:

$$
K = \begin{bmatrix} f_x & s & c_x \\ 0 & f_y & c_y \\ 0 & 0 & 1 \end{bmatrix}
$$

**Homography**\
For planar scenes:

$$
\mathbf{x}' \sim H \mathbf{x},\quad H \in \mathbb{R}^{3 \times 3}
$$

***

#### Multi-View Geometry & Stereo Vision

**Epipolar Constraint**\
Essential matrix:

$$
E = [\mathbf{t}]_\times R
$$

Satisfies:

$$
\mathbf{x}'^\top E \mathbf{x} = 0
$$

Use 8-point algorithm plus SVD to estimate.

**Triangulation**\
Solve for 3D point via least squares:

$$
P_i \mathbf{X} = \mathbf{x}_i
$$

***

#### Feature Extraction & Dimensionality Reduction

**Convolution as Matrix Multiply**\
Image filtering = Toeplitz matrix multiplication. Accelerated via FFT with complexity:

$$
\mathcal{O}(n \log n)
$$

**PCA & Eigenfaces**\
Apply SVD to centered image matrix to extract eigenfaces for compression and recognition.

***

#### State Estimation: Kalman Filtering

**Linear Kalman Filter**

Prediction step:

$$
\hat{\mathbf{x}}_{k|k-1} = A \hat{\mathbf{x}}_{k-1|k-1} + B \mathbf{u}_{k-1}
$$

Update step:

$$
\hat{\mathbf{x}}_{k|k} = \hat{\mathbf{x}}_{k|k-1} + K_k \left( \mathbf{z}_k - H \hat{\mathbf{x}}_{k|k-1} \right)
$$

Where KkK\_kKk​ is the Kalman gain computed from Riccati recursion.

#### **Software Ecosystem**

* **MATLAB/Simulink**: Robotics Toolbox for kinematics, dynamics, vision.
* **Eigen (C++)**: Fast linear algebra.
* **NumPy/SciPy**: Python matrix ops.
* **OpenCV**: Camera models, calibration, stereo geometry.
* **ROS**: `tf`, `robot_state_publisher`, `filtering` for runtime transforms and estimation.
