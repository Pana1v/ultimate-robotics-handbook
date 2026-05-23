---
icon: location-arrow
---

# Trajectory Planning

### Trajectory Planning in Robotics <a href="#trajectory-planning-in-robotics" id="trajectory-planning-in-robotics"></a>

Trajectory planning is a critical component in robotics that determines _how_ a robot should move from a starting configuration to a goal configuration over a specific period. It goes beyond simply finding a geometric path; it involves generating a time-scheduled sequence of states (positions, velocities, and accelerations) that a robot's joints or end-effector must follow to execute a motion smoothly and efficiently, while respecting various constraints [1](https://www.slideshare.net/anandsreekantanthampy/trajectory-236467549)[5](https://blogs.mathworks.com/student-lounge/2019/11/06/robot-manipulator-trajectory/)[6](https://en.wikibooks.org/wiki/Robotics/Navigation/Trajectory_Planning).

Trajectory planning is a subset of the broader motion planning hierarchy, which typically looks like this [5](https://blogs.mathworks.com/student-lounge/2019/11/06/robot-manipulator-trajectory/):

1. **Task Planning:** Defining high-level goals (e.g., "pick up the object").
2. **Path Planning:** Generating a geometrically feasible sequence of configurations (waypoints) from a start to a goal, often focused on collision avoidance. A path does _not_ include timing information [1](https://www.slideshare.net/anandsreekantanthampy/trajectory-236467549)[5](https://blogs.mathworks.com/student-lounge/2019/11/06/robot-manipulator-trajectory/).
3. **Trajectory Planning:** Taking a path (or a set of desired waypoints) and generating a time history of control inputs (like positions, velocities, and accelerations) for the robot to follow that path [1](https://www.slideshare.net/anandsreekantanthampy/trajectory-236467549)[5](https://blogs.mathworks.com/student-lounge/2019/11/06/robot-manipulator-trajectory/).
4. **Trajectory Following/Control:** Executing the planned trajectory using the robot's controllers, ensuring the robot accurately tracks the desired motion.

The key distinction is that a **path** is a spatial description of movement, while a **trajectory** is a path parameterized by time, specifying _when_ the robot should be at each point along the path [1](https://www.slideshare.net/anandsreekantanthampy/trajectory-236467549)[5](https://blogs.mathworks.com/student-lounge/2019/11/06/robot-manipulator-trajectory/)[6](https://en.wikibooks.org/wiki/Robotics/Navigation/Trajectory_Planning).

***

### Core Concepts

* **Waypoints/Via Points:** These are specific configurations (positions and orientations) in the robot's workspace or joint space that the trajectory must pass through. Via points can be used to shape the trajectory or guide the robot around obstacles [1](https://www.slideshare.net/anandsreekantanthampy/trajectory-236467549).
* **Constraints:** Trajectory planning must consider various constraints:
  * **Kinematic Constraints:** Limits on joint positions, velocities, and accelerations.
  * **Dynamic Constraints:** Limits on joint torques/forces based on the robot's dynamics.
  * **Collision Avoidance:** Ensuring the trajectory is collision-free.
  * **Smoothness:** Minimizing jerk (rate of change of acceleration) for smoother motion and reduced wear.
* **Configuration Space (C-space):** The set of all possible configurations a robot can attain. Trajectories can be planned in joint space or task space [6](https://en.wikibooks.org/wiki/Robotics/Navigation/Trajectory_Planning).

***

### Approaches to Trajectory Planning

There are two primary spaces in which trajectories can be planned [1](https://www.slideshare.net/anandsreekantanthampy/trajectory-236467549):

1. **Joint Space Planning:**
   * **Description:** The trajectory is defined as a function of time for each of the robot's joints directly. The planner generates sequences of joint angles/positions.
   * **Pros:** Computationally simpler, easier to directly handle joint limits, and inherently avoids kinematic singularities if the path is defined in joint space.
   * **Cons:** The path of the end-effector in Cartesian space can be complex and less intuitive to predict or control.
2. **Cartesian Space (Task Space) Planning:**
   * **Description:** The trajectory of the robot's end-effector (or another point of interest) is planned in 3D Cartesian space.
   * **Pros:** Allows direct specification of the end-effector's path (e.g., moving in a straight line, drawing a circle), which is often more natural for task definition.
   * **Cons:** Requires an inverse kinematics solver to convert the Cartesian trajectory into joint space commands for the robot. This can be computationally intensive, may yield multiple solutions, or encounter singularities where a Cartesian motion is impossible.

***

### Common Trajectory Generation Methods

Several methods are used to generate the time-based functions for trajectories between waypoints:

* **Polynomial Trajectories** [**1**](https://www.slideshare.net/anandsreekantanthampy/trajectory-236467549)[**5**](https://blogs.mathworks.com/student-lounge/2019/11/06/robot-manipulator-trajectory/)**:**
  * Polynomial functions of time are used to interpolate between waypoints.
  * **Cubic Polynomials (3rd order):** Commonly used when positions and velocities at the start and end of a segment need to be specified. This provides 4 boundary conditions.
  * **Quintic Polynomials (5th order):** Used when positions, velocities, and accelerations at the start and end of a segment need to be specified. This provides 6 boundary conditions and results in smoother acceleration profiles.
  * Higher-order polynomials can ensure continuity of jerk or even higher derivatives.
  * **Pros:** Generate smooth trajectories with continuous derivatives.
  * **Cons:** Can lead to overshooting of velocity or acceleration limits between waypoints if boundary conditions are not carefully chosen.
* **Trapezoidal Velocity Profiles (LSPB - Linear Segment with Parabolic Blends)** [**5**](https://blogs.mathworks.com/student-lounge/2019/11/06/robot-manipulator-trajectory/)**:**
  * The trajectory segment is divided into three phases: constant acceleration, constant (maximum) velocity, and constant deceleration. This creates a trapezoidal shape for the velocity profile over time. The position profile is an s-curve (linear segments with parabolic blends).
  * **Pros:** Relatively easy to implement and tune. Maximum velocity and acceleration can be directly specified and adhered to.
  * **Cons:** Results in discontinuous jerk at the transitions between segments, which can cause vibrations. S-curve trajectory profiles (which are 7th order polynomials or based on sinusoidal jerk) can address this.
* **Splines (e.g., B-Splines)** [**5**](https://blogs.mathworks.com/student-lounge/2019/11/06/robot-manipulator-trajectory/)**:**
  * Splines are piecewise polynomial functions used to create smooth curves through a set of control points. For trajectory planning, these spatial splines are then parameterized by time, often by moving along the spline at a specified speed profile.
  * B-Splines are defined by intermediate control points. The spline does not necessarily pass through these control points but stays within their convex hull.
  * **Pros:** Offer flexibility in creating complex, smooth paths. Control points provide an intuitive way to shape the trajectory.
  * **Cons:** The time parameterization is an additional step.

***

### Trajectory Planning in ROS (Robot Operating System)

ROS provides a rich ecosystem of packages for motion planning, which inherently includes trajectory planning.

* **ROS Navigation Stack (`move_base`):** Primarily for 2D/3D mobile robot navigation.
  * It uses a global planner to find a path and a local planner to generate velocity commands to follow this path, effectively performing local trajectory planning.
  * **`base_local_planner`** [**2**](http://wiki.ros.org/base_local_planner)**:** A common local planner package that implements algorithms like the **Trajectory Rollout** and **Dynamic Window Approach (DWA)**. These methods simulate multiple possible short-term trajectories by sampling velocities, evaluate them against a cost function (considering proximity to the path, obstacles, goal, and robot kinematics), and select the best one to execute. It adheres to the `nav_core::BaseLocalPlanner` interface.
* **MoveIt!:** A comprehensive motion planning framework, primarily for robot manipulators.
  * It integrates various planning algorithms and tools for collision checking, kinematics, and trajectory execution.
  * **OMPL (Open Motion Planning Library)** [**3**](http://wiki.ros.org/motion_planners)**:** A core planning library within MoveIt!. It provides numerous sampling-based path planning algorithms (e.g., RRT, PRM). While OMPL primarily outputs geometric paths, MoveIt! includes utilities for **time parameterization** (e.g., Iterative Parabolic Time Parameterization, Time-Optimal Path Parameterization) to convert these paths into executable trajectories respecting velocity and acceleration limits.
  * **CHOMP (Covariant Hamiltonian Optimization for Motion Planning)** [**3**](http://wiki.ros.org/motion_planners)**:** An optimization-based planner available in MoveIt!. CHOMP directly optimizes an initial trajectory to make it smooth and collision-free.
  * **SBPL (Search-Based Planning Library)** [**3**](http://wiki.ros.org/motion_planners)**:** Another planner integrable with MoveIt!, employing graph search techniques.
  * **`trajopt`** [**4**](https://www.ros.org/news/2013/04/new-package-trajopt-trajectory-optimization-software-for-motion-planning.html)**:** A library for trajectory optimization specifically designed for generating collision-free paths for robot arms and mobile manipulators. It's built on OpenRAVE but can be integrated with ROS. It is known for its speed and ability to handle high-degree-of-freedom problems and various constraints (pose, velocity, collision).
* **Standard Trajectory Messages:**
  * ROS defines messages like `trajectory_msgs/JointTrajectory` and `trajectory_msgs/MultiDOFJointTrajectory`. These messages represent a sequence of points, where each point typically specifies positions, velocities, accelerations, and the `time_from_start` for each joint or for the multi-DOF end-effector. These messages are used by planners to send trajectories to robot controllers.

***

### Key Considerations

* **Collision Avoidance:** Trajectories must be checked to ensure they do not cause the robot to collide with itself or the environment.
* **Smoothness:** Smooth trajectories (continuous velocity, acceleration, and ideally jerk) are desirable to reduce mechanical stress, improve tracking accuracy, and enhance safety.
* **Computational Efficiency:** For dynamic environments or real-time applications, trajectory planning algorithms must be fast.
* **Optimality:** Depending on the application, trajectories might be optimized for time, energy, smoothness, or other criteria.

Trajectory planning is a fundamental bridge between high-level task goals and low-level robot control, enabling robots to move purposefully and effectively in their environments.
