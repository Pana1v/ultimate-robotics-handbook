---
icon: gear
---

# MoveIt 2

MoveIt is what Nav2 is for arms: the de facto manipulation framework on ROS 2. It owns motion planning, kinematics, collision checking, trajectory execution, and a planning-scene representation of the world. If you are building a robot with a 6+ DOF arm in 2026, you almost certainly start here.

The upstream repo is [github.com/moveit/moveit2](https://github.com/moveit/moveit2) \[verify]. The docs at [moveit.picknik.ai](https://moveit.picknik.ai) \[verify] are maintained by PickNik Robotics, who also operate the commercial **MoveIt Pro** product.

My ROS 2 production experience is heavier on mobile than manipulation, but MoveIt 2 is the standard answer when a question involves an arm, so this page covers what you need to know to make sensible architecture choices.

## Architecture overview

MoveIt is not one node - it's a swarm. The pieces that matter:

```
                    ┌───────────────────────────────────┐
                    │       move_group node             │  Central planning service
                    │  ┌─────────────────────────────┐  │
                    │  │  Planning Pipeline (OMPL)   │  │
                    │  │  Planning Scene             │  │
                    │  │  Constraint Manager         │  │
                    │  │  Trajectory Execution Mgr   │  │
                    │  └─────────────────────────────┘  │
                    └────────────┬──────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
┌────────────────┐       ┌────────────────┐       ┌────────────────┐
│  RViz Motion   │       │ MoveIt Python  │       │  Custom client │
│  Planning UI   │       │   bindings     │       │  via C++/Python│
└────────────────┘       └────────────────┘       └────────────────┘

                    ┌───────────────────────────────────┐
                    │  ros2_control + controllers       │  Actually moves the arm
                    └───────────────────────────────────┘
```

### `move_group`

The hub. It exposes action servers (`MoveGroup`, `ExecuteTrajectory`, `Pickup`, `Place`) and services for IK, FK, and scene management. Most of your code talks to `move_group` through the `MoveGroupInterface` (C++) or `moveit_py` (Python).

### Planning Scene

A 3D representation of the world that MoveIt uses for collision checking. It contains:

* The robot itself (URDF + SRDF).
* Attached objects (things rigidly held by the gripper).
* Collision objects (boxes, meshes, point clouds added by your perception code).
* The Octomap layer (optional) for incorporating raw depth data.

Keeping this representation in sync with reality is the single biggest source of "MoveIt isn't working" tickets. If your perception node isn't adding the right collision objects, the planner will happily route through obstacles.

### OMPL - the default planner

OMPL (Open Motion Planning Library, [ompl.kavrakilab.org](https://ompl.kavrakilab.org) \[verify]) is the sampling-based planning library MoveIt uses by default. It's not a single algorithm - it's a library of planners.

Planners you'll see in the `ompl_planning.yaml`:

| Planner    | Algorithm              | Notes                                              |
| ---------- | ---------------------- | -------------------------------------------------- |
| RRTConnect | Bi-directional RRT     | Fast, the default. Good for most cases.            |
| RRTstar    | Asymptotically optimal RRT | Returns better paths the longer you give it.   |
| PRMstar    | Probabilistic Roadmap  | Builds reusable roadmaps. Good for repeated queries. |
| KPIECE     | Kinodynamic            | When dynamics matter.                              |
| ESTkConfigDefault | Expansive Space Trees | Sometimes works when RRT struggles.        |

99% of the time `RRTConnectkConfigDefault` is fine. If you need shorter paths, switch to `RRTstarkConfigDefault` and increase planning time.

OMPL planners are *sampling-based* - they don't guarantee a path exists, and the path they find depends on the seed. For deterministic motion (industrial use cases) you want Pilz, below.

### CHOMP and STOMP

Optimization-based planners shipped alongside OMPL. They start from a seed trajectory and locally optimize it against cost functions (smoothness, obstacle clearance). Slower than RRTConnect, but produce smoother trajectories. Use when you've already got a rough path and want to polish it.

## ros2\_control integration

MoveIt plans trajectories. To actually move the arm, those trajectories need to reach motor controllers - that's ros2\_control's job.

`ros2_control` ([control.ros.org](https://control.ros.org) \[verify]) is a hardware abstraction framework. You write:

* A **hardware interface** that reads sensor state and writes commands to your specific motor controllers (EtherCAT, CAN, serial, vendor SDK).
* A **controller** (usually `joint_trajectory_controller`) that follows the trajectory MoveIt sends.

The MoveIt side is configured in `moveit_controllers.yaml`:

```yaml
controller_names:
  - arm_controller

arm_controller:
  type: FollowJointTrajectory
  action_ns: follow_joint_trajectory
  default: true
  joints:
    - shoulder_pan_joint
    - shoulder_lift_joint
    - elbow_joint
    - wrist_1_joint
    - wrist_2_joint
    - wrist_3_joint
```

The pair you need active at runtime:

* `controller_manager` (ros2\_control side) - owns the hardware interface, runs control loops.
* `move_group` (MoveIt side) - sends trajectories to the `joint_trajectory_controller`.

This separation is good - MoveIt does not know what motors you have, and the hardware interface does not know about motion planning.

### Common ros2\_control gotchas

* **Hardware interface published joint state with the wrong frame** - `move_group` reads `/joint_states` to know where the robot is. If the URDF joints don't match the names in `joint_states`, you get cryptic IK failures.
* **Two controllers claiming the same joint** - you can't have `joint_trajectory_controller` and `velocity_controller` both active on the same joint. Deactivate one explicitly.
* **`forward_command_controller` instead of `joint_trajectory_controller`** - MoveIt only knows how to talk to action-server-based controllers. Bare command controllers won't work.

## Pilz industrial motion planner

The sampling-based OMPL planners are great for "get from A to B around obstacles." They are bad for "draw a straight line in Cartesian space" - sampling-based planners produce non-deterministic, non-straight paths.

Pilz (originally from Pilz GmbH, now part of MoveIt) fills that gap with three deterministic planners:

| Planner | Motion           | Use case                                   |
| ------- | ---------------- | ------------------------------------------ |
| PTP     | Point-to-point (joint space) | Fast moves where the Cartesian path doesn't matter. |
| LIN     | Linear (Cartesian) | Straight-line moves between poses.       |
| CIRC    | Circular         | Arc moves through a known waypoint.       |

You select Pilz by setting the planning pipeline:

```cpp
move_group.setPlanningPipelineId("pilz_industrial_motion_planner");
move_group.setPlannerId("LIN");
```

Pilz is the right choice for industrial pick-and-place where determinism and repeatability matter. Use OMPL for cluttered environments where you have to plan around obstacles.

## MoveIt Pro

PickNik Robotics maintains a commercial product called [MoveIt Pro](https://picknik.ai/moveit-pro) \[verify] that bundles MoveIt with a behavior-tree based skill framework, a web UI, and commercial support. If you are building a manipulation product and don't want to roll your own task planner, it's worth looking at.

The open source MoveIt is everything you actually need; MoveIt Pro is the productized layer on top.

## When MoveIt fits - and when it doesn't

MoveIt is the right tool when:

* You have a kinematic chain (arm, mobile manipulator).
* You need collision checking against a representation of the world.
* You want a mature, well-tested planner.
* You're targeting industrial use cases where the framework's ecosystem (TRAC-IK, Pilz, planning scene tooling) pays off.

MoveIt is the wrong tool when:

* You're doing reactive, sub-100ms control with no obstacle constraints - a custom IK + Cartesian impedance controller will be cleaner.
* You're doing learning-based manipulation where the policy outputs joint targets directly - MoveIt's planning loop is dead weight.
* You only need IK and FK once - call `kdl_kinematics_plugin` or [Pinocchio](https://github.com/stack-of-tasks/pinocchio) \[verify] directly.
* The arm is single-purpose and the path is hardcoded - a trajectory msg published directly to `joint_trajectory_controller` is enough.

For trajectory planning on a mobile base, you do not want MoveIt - that's Nav2's job. See [Nav2 Deep Dive](nav2-deep-dive.md).

## Python interface

`moveit_py` is the modern Python binding (replaces the older `moveit_commander`). It's a `pybind11` wrapper over the C++ API.

```python
from moveit.planning import MoveItPy
from geometry_msgs.msg import PoseStamped

moveit = MoveItPy(node_name="moveit_py_example")
arm = moveit.get_planning_component("arm")

target = PoseStamped()
target.header.frame_id = "base_link"
target.pose.position.x = 0.4
target.pose.position.y = 0.0
target.pose.position.z = 0.5
target.pose.orientation.w = 1.0

arm.set_start_state_to_current_state()
arm.set_goal_state(pose_stamped_msg=target, pose_link="tool0")

plan = arm.plan()
if plan:
    moveit.execute(plan.trajectory, controllers=[])
```

This is much cleaner than the old `moveit_commander` API. Use it for scripting and integration tests.

## C++ interface

`MoveGroupInterface` is the C++ entry point:

```cpp
#include <moveit/move_group_interface/move_group_interface.h>
#include <rclcpp/rclcpp.hpp>

int main(int argc, char** argv) {
    rclcpp::init(argc, argv);
    auto node = std::make_shared<rclcpp::Node>(
        "moveit_example",
        rclcpp::NodeOptions().automatically_declare_parameters_from_overrides(true));

    moveit::planning_interface::MoveGroupInterface move_group(node, "arm");
    move_group.setPlanningTime(5.0);
    move_group.setMaxVelocityScalingFactor(0.5);

    geometry_msgs::msg::Pose target;
    target.position.x = 0.4;
    target.position.y = 0.0;
    target.position.z = 0.5;
    target.orientation.w = 1.0;
    move_group.setPoseTarget(target);

    moveit::planning_interface::MoveGroupInterface::Plan plan;
    if (move_group.plan(plan) == moveit::core::MoveItErrorCode::SUCCESS) {
        move_group.execute(plan);
    }

    rclcpp::shutdown();
    return 0;
}
```

## SRDF - the file you'll forget about

The URDF describes the robot's geometry. The SRDF (Semantic Robot Description Format) adds the semantic information MoveIt needs:

* **Planning groups** - "arm" is joints A, B, C, D, E, F; "gripper" is joints G, H.
* **End effectors** - which link is the tool.
* **Disabled collision pairs** - links that are adjacent and shouldn't trigger self-collision checks.
* **Named poses** - "home", "park", "ready".

You generate the SRDF via the MoveIt Setup Assistant (`ros2 launch moveit_setup_assistant setup_assistant.launch.py` \[verify]). Run this once per robot. The Setup Assistant produces a full MoveIt config package you then customize.

### Disabled collision pairs

The Setup Assistant tries every pair of links in the robot and disables collision checks between pairs that are always touching or never possibly colliding. This list can have hundreds of entries on a complex robot. **Don't edit by hand; re-run the assistant when geometry changes.**

If you miss a pair, you'll get spurious self-collision errors that make IK fail.

## Common pitfalls

* **TF tree incomplete at planning time** - `move_group` queries TF for the current state. If `base_link → tool0` isn't available when you call `plan()`, you'll get an empty trajectory and an unhelpful error. Wait for the chain to be valid before planning.

* **SRDF planning group includes the wrong joints** - easy to miss when you have multiple kinematic chains. Symptom: IK returns success but the arm ends up in the wrong configuration. Re-check the planning group definition.

* **Wrong planning frame** - `setPoseTarget` defaults to the planning frame defined in the SRDF, not your end-effector frame. If you pass a pose in the camera frame and forget to transform it, the arm goes somewhere weird. Always use `PoseStamped` with an explicit `frame_id`.

* **Octomap stale or wrong** - if you feed `move_group` a point cloud topic, the resulting Octomap reflects whatever the sensor saw, including ghosts from old static obstacles. Clear it before each plan if your scene changes.

* **Pilz LIN through a workspace singularity** - Pilz can refuse to plan a linear move that crosses a singularity. Add waypoints, or use OMPL.

* **Two controllers fighting** - `joint_trajectory_controller` active for "arm", `velocity_controller` also active for the same joints. The arm shakes. Deactivate one in your controller spawner launch.

* **Hardware interface returns stale joint states** - MoveIt thinks the arm is somewhere it isn't, plans through obstacles. Verify `/joint_states` updates at ≥50 Hz before debugging anything else.

* **`use_sim_time` mismatch with controllers** - in simulation, `move_group`, `controller_manager`, and the joint state publisher all need the same `use_sim_time` value. Mismatched clocks cause trajectories to execute "too fast" or stall.

## Where to go next

* [docs.moveit.picknik.ai](https://docs.moveit.picknik.ai) \[verify] - the canonical MoveIt 2 docs, well maintained.
* [control.ros.org](https://control.ros.org) \[verify] - ros2\_control reference.
* [Nav2 Deep Dive](nav2-deep-dive.md) - the mobile counterpart.
* [Lifecycle and Composition](lifecycle-and-composition.md) - `move_group` itself is composable; useful when you embed it into a larger application.
* [Optimization libraries](../mathematical-and-programming-foundations/optimization-libraries.md) - what's underneath CHOMP, STOMP, and modern trajectory optimization.
