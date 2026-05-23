---
icon: hexagon-divide
---

# Linear Algebra for Robotics

### **Linear Algebra in Robotics and Computer Vision**

Linear algebra provides the mathematical language for describing and solving geometry, motion, perception, and control problems in robotics and computer vision. This overview covers key concepts and applications—from kinematic chains and dynamics to camera modeling, multi‐view geometry, state estimation, and feature extraction.

***

#### **Vector Spaces and Linear Mappings**

**Vectors and Norms**\
A vector v∈R encodes quantities like position or velocity. Its length is:

$$
n\mathbf{v} \in \mathbb{R}^nv∈Rn
$$



$$
∥v∥=v⊤v\| \mathbf{v} \| = \sqrt{\mathbf{v}^\top \mathbf{v}}∥v∥=v⊤v​
$$

Projections are given by:



$$
proju(v)=u⊤vu⊤uu\
$$



$$
\text{proj}_{\mathbf{u}}(\mathbf{v}) = \frac{\mathbf{u}^\top \mathbf{v}}{\mathbf{u}^\top \mathbf{u}} \mathbf{u}
$$

***

$$
proju​(v)=u⊤uu⊤v​u
$$

**Inner Products and Orthogonality**\
The dot product

$$
f(x) = x * e^{2 pi i \xi x}
$$



&#x20;measures similarity and defines angles via:

$$\cos \theta = \frac{\mathbf{u}^\top \mathbf{v}}{\|\mathbf{u}\| \, \|\mathbf{v}\|}$$

Orthonormal bases via Gram–Schmidt simplify coordinate transformations and least‐squares problems.

***

#### **Matrices, Determinants, and Invertibility**

**Linear Transformations**\
A matrix&#x20;

$$
A \in \mathbb{R}^{m \times n} \text{ maps } \mathbb{R}^n \rightarrow \mathbb{R}^m.
$$



&#x20;Composition is matrix multiplication:

$$
f(x) = x * e^{2 pi i \xi x}
$$

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

#### Rigid-Body Transforms & Denavit–Hartenberg (DH) Convention

**Rotation Matrices**

$$
R \in SO(3),\quad R^\top R = I,\quad \det(R) = 1
$$

Axis–angle and quaternion representations avoid gimbal lock.

**Homogeneous Transformations**

$$
T = \begin{bmatrix} R & \mathbf{t} \\ 0 & 1 \end{bmatrix},\quad \mathbf{p}_{\text{world}} = T \mathbf{p}_{\text{local}}
$$

**DH Parameters**

$$
(\theta, d, a, \alpha)
$$

Used for systematic forward and inverse kinematic derivation.

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

**Jacobian Matrix**\
Relates joint velocities q˙\dot{\mathbf{q\}}q˙​ to end-effector twist ξ\boldsymbol{\xi}ξ:

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

**Pinhole Camera Model**\
Maps 3D point X=\[X,Y,Z,1]

$$
⊤\mathbf{X} = [X, Y, Z, 1]^\topX=[X,Y,Z,1]⊤
$$

to image point

$$
x=[u,v,1]⊤\mathbf{x} = [u, v, 1]^\topx=[u,v,1]⊤
$$

:

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
