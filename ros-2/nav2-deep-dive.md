---
icon: gear
---

# Nav2 Deep Dive

Nav2 is the ROS 2 reincarnation of the ROS 1 Navigation Stack — except that "reincarnation" sells it short. The team rebuilt it from scratch around behavior trees, lifecycle nodes, and composable plugins. It is the de facto standard for mobile robot navigation in 2026, and most of what I do at work is one or another layer of it.

This page is a guided tour of the stack, focused on the parts where you actually have decisions to make. I draw on production experience from [10xConstruction.ai](https://10xconstruction.ai) \[verify], where I worked on the Swerve Drive MPPI motion model, custom BT nodes, and improvements to the Collision Monitor.

The upstream repo is [github.com/ros-navigation/navigation2](https://github.com/ros-navigation/navigation2) \[verify]. The docs at [docs.nav2.org](https://docs.nav2.org) \[verify] are excellent and worth reading end-to-end at least once.

## Architecture

Nav2 is a fleet of lifecycle nodes wired together by a behavior tree. The major components:

```
                       ┌──────────────────────┐
                       │   bt_navigator       │  Executes the behavior tree
                       └──┬───────────────────┘
                          │ (BT nodes call action servers)
       ┌──────────────────┼──────────────────┬────────────────┐
       ▼                  ▼                  ▼                ▼
┌────────────────┐ ┌─────────────────┐ ┌──────────────┐ ┌────────────────┐
│ planner_server │ │controller_server│ │behavior_server│ │ smoother_server│
│  Global plans  │ │ Local control   │ │ Spins, backups│ │ Path smoothing │
└──────┬─────────┘ └────────┬────────┘ └──────────────┘ └────────────────┘
       │                    │
       ▼                    ▼
┌──────────────────┐  ┌──────────────────┐
│ global_costmap   │  │ local_costmap    │
│  (large, static) │  │ (small, rolling) │
└──────────────────┘  └──────────────────┘

         ┌──────────────────────────┐
         │  lifecycle_manager       │  Drives configure → activate
         └──────────────────────────┘

         ┌──────────────────────────┐
         │  collision_monitor       │  Independent safety layer
         └──────────────────────────┘
```

Every one of these is a `LifecycleNode` and can be loaded as a composable component into a single container — see [Lifecycle and Composition](lifecycle-and-composition.md). For production you absolutely want the composed launch.

### What each server does

| Server               | Job                                                                |
| -------------------- | ------------------------------------------------------------------ |
| `bt_navigator`       | Runs the navigation behavior tree. Owns the "navigate" action server. |
| `planner_server`     | Global pathfinding (A*, Hybrid A*, lattice). One-shot, runs on demand. |
| `controller_server`  | Local control loop. Outputs `/cmd_vel`. Runs at the controller frequency (typically 20 Hz). |
| `behavior_server`    | Discrete recovery / utility behaviors (spin, back up, wait).       |
| `smoother_server`    | Optional path post-processing. Reduces jagged plans.               |
| `waypoint_follower`  | Sequences multiple goals. Optional.                                |
| `lifecycle_manager`  | Sequences the configure/activate transitions on all of the above.  |
| `collision_monitor`  | Independent safety. Subscribes to sensors, vetoes `/cmd_vel`.      |

## The behavior tree (BT.CPP)

The BT is what makes Nav2 reconfigurable without recompiling. Instead of hardcoded recovery logic in C++, you write an XML tree that calls action servers in order. Default tree lives in `nav2_bt_navigator/behavior_trees/navigate_to_pose_w_replanning_and_recovery.xml` \[verify].

A simplified version:

```xml
<root main_tree_to_execute="MainTree">
  <BehaviorTree ID="MainTree">
    <RecoveryNode number_of_retries="6" name="NavigateRecovery">
      <PipelineSequence name="NavigateWithReplanning">
        <RateController hz="1.0">
          <ComputePathToPose goal="{goal}" path="{path}" planner_id="GridBased"/>
        </RateController>
        <FollowPath path="{path}" controller_id="FollowPath"/>
      </PipelineSequence>
      <ReactiveFallback name="RecoveryFallback">
        <GoalUpdated/>
        <RoundRobin name="RecoveryActions">
          <Sequence name="ClearingActions">
            <ClearEntireCostmap service_name="local_costmap/clear_entirely_local_costmap"/>
            <ClearEntireCostmap service_name="global_costmap/clear_entirely_global_costmap"/>
          </Sequence>
          <Spin spin_dist="1.57"/>
          <Wait wait_duration="5"/>
          <BackUp backup_dist="0.30" backup_speed="0.05"/>
        </RoundRobin>
      </ReactiveFallback>
    </RecoveryNode>
  </BehaviorTree>
</root>
```

Reading the tree: every second, replan globally; meanwhile follow the path locally; on failure, try clearing costmaps, spinning, waiting, backing up. Six retries total.

### Custom BT nodes

When the built-in nodes can't express your behavior, you write your own. At 10x I wrote custom condition and action nodes to handle:

* Gating navigation on a domain-specific safety state (machine in a known location, perception confidence threshold).
* Triggering pre-planned escape maneuvers when the collision monitor detected an imminent stop.
* Driving an external manipulator coordination loop.

A condition node skeleton (C++):

```cpp
#include <behaviortree_cpp_v3/condition_node.h>
#include <nav2_behavior_tree/bt_conversions.hpp>

class IsBatteryOk : public BT::ConditionNode {
public:
    IsBatteryOk(const std::string& name, const BT::NodeConfiguration& config)
        : BT::ConditionNode(name, config),
          min_pct_(0.0f)
    {
        getInput("min_pct", min_pct_);
    }

    static BT::PortsList providedPorts() {
        return {BT::InputPort<float>("min_pct", "Minimum battery percentage")};
    }

    BT::NodeStatus tick() override {
        // ... read /battery_state from the blackboard or a subscriber ...
        return current_pct_ > min_pct_ ? BT::NodeStatus::SUCCESS : BT::NodeStatus::FAILURE;
    }

private:
    float min_pct_;
    float current_pct_{1.0f};
};

#include <behaviortree_cpp_v3/bt_factory.h>
BT_REGISTER_NODES(factory) {
    factory.registerNodeType<IsBatteryOk>("IsBatteryOk");
}
```

Then point the BT plugin search path at your shared library in `nav2_params.yaml`:

```yaml
bt_navigator:
  ros__parameters:
    plugin_lib_names:
      - nav2_compute_path_to_pose_action_bt_node
      - nav2_follow_path_action_bt_node
      - my_pkg_bt_nodes      # ← your library
```

Plugin development docs: [docs.nav2.org/plugins](https://docs.nav2.org/plugins) \[verify].

## Controllers

The controller is what closes the loop on the local plan and produces `/cmd_vel`. Nav2 ships several; you pick by setting the `FollowPath` plugin name.

| Controller       | Algorithm                              | Good for                                      |
| ---------------- | -------------------------------------- | --------------------------------------------- |
| DWB              | Dynamic Window Approach (trajectory rollout) | Differential drive, conservative environments. Inherits from ROS 1's DWA. |
| **MPPI**         | Model Predictive Path Integral (sampling-based MPC) | Holonomic, swerve, omni — anything where DWB's circular-arc assumption is too restrictive. |
| RPP              | Regulated Pure Pursuit                 | Cheap, smooth following on differential drive when DWB is overkill. |
| Graceful Controller | Curvature-continuous pursuit          | When you need smooth approach to goal pose with orientation. |

### MPPI in production

MPPI is the one I have hands-on production experience with. At 10x I worked on a **Swerve Drive MPPI motion model** — the stock MPPI in Nav2 ships motion models for differential, omni, and Ackermann; swerve needed a custom model that handled the per-wheel steer / drive coupling correctly.

The structure of the upstream `nav2_mppi_controller` plugin:

* `MotionModel` interface — predicts next-state given current state + control sample.
* `Critic` interface — scores a trajectory rollout against goals, obstacles, path adherence, etc.
* `Optimizer` — samples controls, weights, computes the next command.

Adding a motion model is a `~200`-line C++ file (the math is most of it). The MPPI design doc is at [docs.nav2.org/configuration/packages/configuring-mppic.html](https://docs.nav2.org/configuration/packages/configuring-mppic.html) \[verify].

Tuning MPPI is mostly about the critics' weights. A starter `nav2_params.yaml`:

```yaml
controller_server:
  ros__parameters:
    controller_frequency: 20.0
    FollowPath:
      plugin: "nav2_mppi_controller::MPPIController"
      time_steps: 56
      model_dt: 0.05
      batch_size: 2000
      vx_std: 0.2
      vy_std: 0.2
      wz_std: 0.4
      vx_max: 0.5
      vx_min: -0.35
      vy_max: 0.5
      wz_max: 1.9
      motion_model: "Omni"  # or "DiffDrive", "Ackermann", "Swerve" (custom)
      critics:
        ["ConstraintCritic", "ObstaclesCritic", "GoalCritic",
         "GoalAngleCritic", "PathAlignCritic", "PathFollowCritic",
         "PathAngleCritic", "PreferForwardCritic"]
      ObstaclesCritic:
        cost_weight: 4.0
      GoalCritic:
        cost_weight: 5.0
      PathAlignCritic:
        cost_weight: 14.0
```

The trade-off vs DWB: MPPI handles non-trivial dynamics far better, but the sampling cost is higher (the `batch_size: 2000` above is 2000 trajectory rollouts every 50 ms). On a Jetson Orin we ran 56 steps × 2000 samples at 20 Hz comfortably; on a Pi 4 you'd be hurting.

### RPP and the "simple" path

For a basic differential-drive AMR on smooth floors, Regulated Pure Pursuit is dramatically simpler and just works. Three real knobs (lookahead distance, max linear velocity, max angular velocity) and it does the right thing 95% of the time. Skip DWB entirely unless you have a reason.

## Planners

The planner produces the global path that the controller follows. Nav2 supports several plugins; you pick by setting the `GridBased` plugin name in the `planner_server`.

| Planner        | Algorithm                          | Good for                                         |
| -------------- | ---------------------------------- | ------------------------------------------------ |
| NavFn          | Dijkstra / A* on the 2D costmap    | Default, classic. Fast on small maps.           |
| Smac 2D        | A* on 2D, with Reed-Shepp / Dubins | Like NavFn but properly tuned, supports approximation tolerances. |
| Smac Hybrid-A* | Hybrid A* (state lattice)          | Ackermann / car-like robots that need feasibility (no in-place rotation). |
| Smac Lattice   | State lattice                      | Holonomic robots that need motion-primitive-respecting paths. |
| Theta\*        | Any-angle path                     | When you want straighter paths over open space. |

The Smac family ([github.com/ros-navigation/navigation2/tree/main/nav2\_smac\_planner](https://github.com/ros-navigation/navigation2/tree/main/nav2_smac_planner) \[verify]) is what most modern projects use. NavFn is still there for compatibility but Smac 2D is a strict upgrade.

```yaml
planner_server:
  ros__parameters:
    planner_plugins: ["GridBased"]
    GridBased:
      plugin: "nav2_smac_planner/SmacPlanner2D"
      tolerance: 0.25
      downsample_costmap: false
      downsampling_factor: 1
      allow_unknown: true
      max_iterations: 1000000
      max_planning_time: 2.0
      cost_travel_multiplier: 2.0
      use_final_approach_orientation: false
```

## Costmap layers

A costmap is a 2D grid of cost values (`0`–`254`, plus `255` for unknown). Each cell's cost is computed by stacking *layers* — independent plugins that each contribute. The order matters: layers execute in sequence, each reading the prior and writing on top.

| Layer        | What it does                                                          |
| ------------ | --------------------------------------------------------------------- |
| Static       | Reads `/map` (typically from SLAM or a pre-built map). Marks known obstacles. |
| Obstacle     | Subscribes to `LaserScan` / `PointCloud2`. Marks cells with sensor returns. |
| Voxel        | 3D version of obstacle layer. More expensive, handles overhangs.      |
| Inflation    | Expands all lethal cells outward by the robot's inflation radius, with a decay. |
| Range Sensor | Sonar / time-of-flight integration.                                   |
| Keepout      | Reads a "no-go zone" map. For loading docks, charger areas, etc.      |
| Speed Limit  | Marks cells where max velocity is reduced. For around-people / around-machines zones. |

Stack them like this:

```yaml
local_costmap:
  local_costmap:
    ros__parameters:
      update_frequency: 5.0
      publish_frequency: 2.0
      global_frame: odom
      robot_base_frame: base_link
      rolling_window: true
      width: 5
      height: 5
      resolution: 0.05
      robot_radius: 0.30
      plugins: ["voxel_layer", "inflation_layer"]
      voxel_layer:
        plugin: "nav2_costmap_2d::VoxelLayer"
        enabled: true
        publish_voxel_map: true
        origin_z: 0.0
        z_resolution: 0.05
        z_voxels: 16
        observation_sources: scan
        scan:
          topic: /scan
          max_obstacle_height: 2.0
          clearing: true
          marking: true
          data_type: "LaserScan"
      inflation_layer:
        plugin: "nav2_costmap_2d::InflationLayer"
        cost_scaling_factor: 3.0
        inflation_radius: 0.55
```

### Inflation radius — the most important number

`inflation_radius` is how far the inflation layer pushes out around lethal cells, with cost decaying via `cost_scaling_factor`. Get this wrong and your robot will either bump into things (too small) or refuse to enter doorways (too large).

Rule of thumb: `inflation_radius = robot_radius + safety_margin`. A 30 cm radius robot in an open warehouse: `inflation_radius: 0.55`. The same robot in a tight aisle: drop to `0.40`. There is no universal value.

## Collision Monitor

The Collision Monitor (`nav2_collision_monitor`, [source](https://github.com/ros-navigation/navigation2/tree/main/nav2_collision_monitor) \[verify]) is an independent safety layer that subscribes to raw sensor data and can override `/cmd_vel` in real time. It does not depend on the costmaps or planner — even if Nav2 itself is unhealthy, the collision monitor still vetoes commands that would lead to a crash.

It works on the notion of **polygons**: you define one or more polygons around the robot, classify them as `stop`, `slowdown`, or `approach`, and a triggering action when any polygon contains sensor points.

```yaml
collision_monitor:
  ros__parameters:
    base_frame_id: "base_link"
    odom_frame_id: "odom"
    cmd_vel_in_topic: "cmd_vel_smoothed"
    cmd_vel_out_topic: "cmd_vel"
    polygons: ["PolygonStop"]
    PolygonStop:
      type: "polygon"
      points: [0.4, 0.3, 0.4, -0.3, 0.0, -0.3, 0.0, 0.3]
      action_type: "stop"
      min_points: 4
      visualize: true
      polygon_pub_topic: "polygon_stop"
    observation_sources: ["scan"]
    scan:
      type: "scan"
      topic: "/scan"
```

### Pan's work on the Collision Monitor

At 10x I contributed improvements to the Collision Monitor focused on configurability and reaction-time. Specific areas:

* **Reaction polygon hysteresis** — preventing chatter when an obstacle hovers near a polygon boundary.
* **Tighter integration with the BT** — exposing collision state as a blackboard variable so recovery behaviors can branch on it.
* **Better observability** — publishing the per-polygon active state for logging.

The general lesson from production: **the collision monitor must be its own process**, not composed into the Nav2 container. If the perception or planner code crashes, you still need an active safety layer. We ran the monitor in its own systemd unit with a heartbeat to the watchdog.

## Recovery behaviors

The `behavior_server` exposes discrete recoveries as action servers:

* `Spin` — rotate in place by an angle.
* `BackUp` — drive backward a fixed distance at a fixed slow speed.
* `Wait` — block for a duration.
* `DriveOnHeading` — go straight a fixed distance.
* `AssistedTeleop` — hand control to a remote operator.

Wire them into the BT's `RecoveryFallback` subtree. The order matters: prefer cheap recoveries first (clear costmap), expensive ones last (assisted teleop).

## Lifecycle Manager

`nav2_lifecycle_manager` configures and activates all the Nav2 nodes in order:

```yaml
lifecycle_manager:
  ros__parameters:
    autostart: true
    node_names: ["controller_server", "smoother_server", "planner_server",
                 "behavior_server", "bt_navigator", "waypoint_follower",
                 "velocity_smoother", "collision_monitor"]
    bond_timeout: 4.0
    attempt_respawn_reconnection: true
```

`bond_timeout` is the heartbeat — if a node stops responding, the manager declares it dead. Combined with `attempt_respawn_reconnection`, a single node crash is recoverable.

## Tuning tips

The settings that actually matter, in rough order of impact:

| Setting                                    | Default      | What it controls                                          |
| ------------------------------------------ | ------------ | --------------------------------------------------------- |
| `controller_frequency`                     | 20.0 Hz      | How often the controller runs. Lower if CPU-bound; never go below 5 Hz. |
| `inflation_radius`                         | 0.55 m       | Doorway clearance vs collision. Tune per environment.     |
| `robot_radius` or `footprint`              | varies       | The robot's collision shape. Use `footprint` for non-circular robots. |
| `global_costmap.resolution`                | 0.05 m       | Smaller = more accurate, more memory. 0.05 is the sweet spot. |
| `local_costmap.width/height`               | 5x5 m        | Larger = better avoidance of distant obstacles, slower update. |
| `xy_goal_tolerance` / `yaw_goal_tolerance` | 0.25 m / 0.25 rad | How close the robot must get to the goal before BT says "done". |
| `cost_scaling_factor`                      | 3.0          | How fast inflation cost decays. Higher = sharper.        |
| `controller_frequency` × `model_dt` (MPPI) | depends      | Sets the prediction horizon. Tune together.              |

### Footprint vs robot\_radius

If your robot isn't circular — and most aren't — use `footprint` instead of `robot_radius`:

```yaml
footprint: "[[0.3, 0.2], [0.3, -0.2], [-0.3, -0.2], [-0.3, 0.2]]"
```

This costs a bit more (per-cell polygon checks vs radius checks) but lets the robot navigate aisles correctly. With `robot_radius`, a rectangular robot wastes 30%+ of usable space.

### Sim time gotcha

When testing in Gazebo or Isaac Sim, every Nav2 node needs `use_sim_time: True`. Set it once in the YAML for the whole stack:

```yaml
/**:
  ros__parameters:
    use_sim_time: True
```

The `/**:` is a wildcard that applies to all nodes.

## Common pitfalls

* **`/map` not latched** — late-joining nodes never get the map. Use `qos_durability: transient_local` on the publisher (SLAM stack does this by default; check your map server).
* **TF tree incomplete** — Nav2 fails silently waiting for `map → odom → base_link → laser`. Run `ros2 run tf2_tools view_frames` and stare at the output.
* **Controller frequency too high for the CPU** — the controller misses deadlines and the robot stutters. Drop to 10 Hz before chasing more exotic causes.
* **Default BT for differential-drive robot using MPPI** — MPPI tuned for omni doesn't work well on differential drive. Use the right `motion_model` or switch to DWB / RPP.
* **Collision monitor disabled "for testing"** — and then someone deploys to the field with it still off. Make the lifecycle manager fail-start if the monitor isn't `Active`.
* **Costmap layers in the wrong order** — inflation before obstacle marking means obstacles aren't inflated. Order is `static → obstacle → inflation`.

## Where to go next

* [Lifecycle and Composition](lifecycle-and-composition.md) — the runtime substrate Nav2 sits on.
* [DDS and QoS](dds-qos.md) — for `/map`, `/scan`, `/cmd_vel` tuning.
* [LiDAR SLAM](../slam-and-state-estimation/lidar-slam.md) — the perception layer that produces the `/map` and `odom` Nav2 needs.
* [MoveIt 2](moveit2.md) — the manipulation counterpart for arms.
* [Polka](../authors-projects/polka.md) — my own platform running this stack.
* [Optimization libraries](../mathematical-and-programming-foundations/optimization-libraries.md) — the math underneath MPPI and the Smac planners.
