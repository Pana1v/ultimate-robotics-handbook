---
icon: gear
description: A composable multi-LiDAR fusion node for ROS 2 - what it actually merges, filters, deskews, and measures, checked against the shipped code.
---

# Polka - Multi-LiDAR Fusion for ROS 2

> A ROS 2 multi-LiDAR fusion node that merges heterogeneous `PointCloud2` and `LaserScan` streams into unified cloud and scan outputs through a **single composable pipeline**. Per-source and output-stage filtering, TF2-based fusion with last-known-good fallback, optional CUDA acceleration, and IMU-based deskewing with per-source IMU overrides for articulated platforms. Supports ROS 2 **Humble, Iron, Jazzy, Kilted, and Lyrical**.

**Role:** Creator
**Repo:** [github.com/Pana1v/polka](https://github.com/Pana1v/polka)
**Status:** Active (v0.5.0)

***

## Motivation

If you've worked on a real AMR with more than one LiDAR, you know the pain. The "standard" approach in ROS 2 looks something like this:

```
lidar_1 → relay_node → filter_node → tf_aligner → ┐
lidar_2 → relay_node → filter_node → tf_aligner → ├── merge_node → /points
lidar_3 → relay_node → filter_node → tf_aligner → ┘
```

Six to nine nodes per sensor stack. Each one is a process boundary. Each one is a serialization-deserialization round trip. Each one adds 1-5 ms of latency, and the launch file looks like a Jenga tower of `Node()` declarations with hand-aligned remappings.

> **Field note, not a repo benchmark:** on the warehouse AMR I worked on (Jetson Orin NX), this relay-filter-merge stack cost roughly **40 ms of end-to-end fusion latency**, most of it serialization between nodes rather than actual computation. This is my own recollection of that deployment - there is no artifact in the polka repo backing this number, unlike the measured figures later in this page.

Beyond the latency, that stack was responsible for:

* **Frequent topic-name remap typos** that silently produced empty merged clouds
* **No principled deskewing** - every motion blur in the cloud was either ignored or "fixed" by an ad-hoc downstream node
* **Configuration spread across 7 YAML files** because each filter/merger had its own params

I wrote Polka to collapse all of that into **one composable node** with **one YAML file** that describes every source, every filter, and every transform.

> **Note:** "Composable" here means the actual ROS 2 component sense - Polka registers as `polka::PolkaNode` via `rclcpp_components_register_nodes`, so it can be loaded into a component container and share an address space with whatever consumer you stack next to it, e.g. a costmap or a SLAM node, dropping the inter-process serialization hop. The shipped launch file doesn't use a container (more on that below), but the plugin is real and you can build your own container around it.

***

## Architecture

```
lidar_front (PC2)   ──┐
lidar_rear  (PC2)   ──┼──▶ per-source filter ──▶ TF lookup ──▶ Merge (CPU or CUDA) ──┬──▶ ~/merged_cloud   (PointCloud2)
lidar_2d    (Scan)  ──┘                                                            ▲ ├──▶ ~/merged_scan    (LaserScan)
                                                                                   │ └──▶ /diagnostics     (DiagnosticArray, absolute)
imu_main (sensor_msgs) ──▶ Deskew engine ◄── per-source IMU overrides              ┘
```

The whole thing is one process, one ROS 2 node, one config file - plus, since 0.5.0, a `polka_monitor` terminal dashboard the launch file starts alongside it by default (own section below).

On the CUDA path, the merge, output filters, voxel downsample, and scan flatten are fused into a single GPU pass rather than running as the separate downstream stages the diagram implies for CPU - that's covered in [CUDA path](#cuda-path).

***

## Per-source filtering

Each LiDAR has its own personality. The base-mounted 2D scanner sees a lot of forklift legs at 50 cm. The mast-mounted 3D LiDAR sees the ceiling lights as ghost returns. The rear LiDAR sees the robot's own bumper as a constant 12 cm obstacle.

In the relay-filter-merge soup, you fix this by spawning a separate `pointcloud_filter` node per source with a unique namespace. In Polka, you declare it inline, per source, as a keyed map of filter blocks rather than an ordered list:

```yaml
polka:
  ros__parameters:
    source_names: ["lidar_front", "lidar_rear"]

    sources:
      lidar_front:
        topic: "/lidar_front/points"
        type: "pointcloud2"
        qos_reliability: "best_effort"
        qos_history_depth: 1
        filters:
          range:
            enabled: true
            min: 0.15
            max: 30.0
          angular:
            enabled: true
            invert: false
            ranges: [270.0, 90.0]   # degrees, wraps through 0 -> keeps the front 180°
          box:
            enabled: false

      lidar_rear:
        topic: "/lidar_rear/points"
        type: "pointcloud2"
        qos_reliability: "best_effort"
        qos_history_depth: 1
        filters:
          range:
            enabled: true
            min: 0.20
            max: 25.0
          angular:
            enabled: false
          box:
            enabled: false
```

A `type: "laserscan"` source is converted to `PointCloud2` automatically - there's no separate upsampling flag to set.

Only three per-source filters exist: `range`, `angular`, and `box`. There's no per-source voxel grid or passthrough - decimation and field-based cropping only happen at the output stage (next section). The three run in a **fixed order** - range, then angular, then box, whichever are enabled - `build_filter_chain()` composes them that way in code; you toggle each stage on or off, you don't reorder them. That's still the cheap-first ordering you'd hand-tune with PCL, Polka just enforces it for you.

The `angular` filter works in **degrees**, not radians, as a list of `[start, end]` pairs that can wrap through 0° (`[270.0, 90.0]` keeps the front hemisphere, spanning through north). `invert: false` keeps the listed ranges; `invert: true` excludes them.

> **Self-filter, corrected:** the output-stage `self_filter` (see below) is **not** derived from URDF geometry or resolved through `robot_description` and TF2 - I want to be precise about this because I've seen it described that way elsewhere, including in an earlier draft of this page. It's exactly what it sounds like: a list of named, fixed, axis-aligned bounding boxes (`box_names`, each with its own `x_min`/`x_max`/`y_min`/`y_max`/`z_min`/`z_max`) that get rejected from the output cloud. No link geometry, no inflation parameter. It's a blunt tool and it's honest about being one. On the warehouse AMR this style of fixed box killed roughly **3% of points per frame** grazing the bumper sensors at oblique angles - that figure is my own field measurement from that deployment, not something the repo publishes.

***

## Output-stage filtering

Everything above runs per source, in that source's own frame, before the merge. The output stage runs once, on the merged cloud, in `output_frame_id`. It has more stages than the per-source filters do, and they also run in a fixed order: **range → angular → box → footprint (self-filter) → height cap → voxel**.

```yaml
polka:
  ros__parameters:
    outputs:
      cloud:
        enabled: true
        topic: "~/merged_cloud"
        filters:
          range:
            enabled: false
          angular:
            enabled: false
          box:
            enabled: false
        height_cap:
          enabled: true
          z_min: -1.0
          z_max: 3.0
        self_filter:
          enabled: true
          box_names: ["chassis"]
          chassis:
            x_min: -0.30
            x_max: 0.30
            y_min: -0.25
            y_max: 0.25
            z_min: -0.10
            z_max: 0.50
        voxel:
          enabled: true
          leaf_size: 0.05
```

> **A gotcha worth knowing:** any positive `voxel.leaf_size` turns voxel downsampling on internally, even if you left `voxel.enabled: false` sitting above it - the enabled flag and the leaf size aren't as independent as the schema suggests. Set `leaf_size` to `0.0` (or omit it) if you genuinely don't want voxelization. This is the kind of footgun that's easy to hit copying an example without reading it closely, which is exactly why I'm calling it out instead of writing around it.

`height_cap` clips to a z-range in the output frame - useful for stripping ground and overhead returns. `box` (output-level) keeps points inside an axis-aligned region, the mirror image of `self_filter`'s exclusion boxes. `voxel` takes either a uniform `leaf_size` or independent `leaf_x`/`leaf_y`/`leaf_z`.

***

## TF handling

Every source declares its own `frame_id` - taken from the incoming message header, not a config key. Polka resolves every source into `output_frame_id` (default `base_link`).

The lookup is `tf2_ros::Buffer::lookupTransform(output_frame_id, src.frame_id(), tf2::TimePointZero)`. `TimePointZero` means "give me the latest transform you have" - there's no timeout argument, and no age check against how stale that transform is. If the lookup throws (`TransformException`), Polka logs a throttled warning and **reuses the last-known-good transform for that source** rather than dropping the source's data. That's the opposite of what an earlier draft of this page claimed (a 100 ms staleness cutoff that dropped old transforms) - the real behavior degrades gracefully instead of failing closed.

If a source goes silent (cable yanked, driver crash) past `source_timeout` (0.5 s) but within `source_stale_reuse_window` (1.5 s) of its last message, Polka reuses that source's last-good cloud and last-good TF rather than dropping it outright - you'll see a log like `source 'lidar_rear' stale, reusing last-good cloud/TF`. Past the reuse window, the source drops and the merged output degrades to whichever sources are still alive, flagged on `/diagnostics`.

***

## CUDA path

For platforms with an NVIDIA GPU (Jetson, x86 dGPU), the merge engine can build as `polka_cuda`, enabled through the `WITH_CUDA` CMake option (**default ON**, not opt-in). At configure time, `check_language(CUDA)` probes for a CUDA compiler; if none is found, CMake prints `polka: CUDA not found, CPU-only build` and flips `WITH_CUDA` off automatically - the build never fails for lacking a GPU. At runtime, the `enable_gpu` parameter (default `true`, **read-only** - the merge engine and its device buffers are constructed once at startup) picks the engine; if the node was built without CUDA, it falls back to CPU and the startup banner prints `engine : CPU`. Two independent fallback layers, both automatic.

What actually runs on the GPU: a fused kernel path covering transform, the output filters (`pass_range`, `pass_angular`, `pass_box` device helpers), voxel insert/compact (`atomicAdd`-based stream compaction and slot allocation), and - easy to miss - 2D scan generation too (`flatten_kernel`, `scan_decode_kernel`), using pre-allocated `cudaMalloc` buffers and pinned host memory (`cudaMallocHost`). Because the whole output path is fused into that one pass, a CUDA run's `output_pipeline_ms` metric reads exactly `0.0` - it isn't that the stage is free, it's that it's folded into the merge kernel's own timing. The self-filter on GPU is plain AABB rejection, same as CPU - there's no host-side AABB tree or device point-in-polytope test.

Build with:

```bash
colcon build --packages-select polka --cmake-args -DWITH_CUDA=OFF   # force CPU-only
# omit the flag entirely to auto-detect (default ON)
```

**On the numbers:** I don't have a credible CPU-vs-CUDA millisecond comparison to give you, and I'd rather say that plainly than publish one. `doc/PERFORMANCE.md` puts it well: *"CUDA is a crossover, not a free win."* The GPU wins on heavy filter chains, where the fused pass hides per-point work the CPU would otherwise pay for serially. On a filterless merge, kernel dispatch and host-to-device transfer overhead dominate and the CPU stays competitive - there's nothing for the GPU to hide behind. Measure it on your own pipeline before assuming either side wins.

What the repo *does* stand behind, both CPU-path, both from the 0.5.0 CHANGELOG:

| Change | Before | After | Factor |
| --- | --- | --- | --- |
| Deskew stage latency (per source) | 9.8 ms | 1.6 ms | ~6.2x |
| CPU angular filter (per tick, 259k points) | 10.47 ms | 3.55 ms | ~3x |

The angular filter win came from replacing a per-point `atan2` with a precomputed cross-product half-plane test. The deskew win came from coarse-stride SE(3) rotation interpolation instead of recomputing a full pose per point (more on that below) - accuracy loss is negligible, on the order of 1.6e-7 cm max error. `doc/PERFORMANCE.md` is careful to flag that 6.2x as a **cost** claim, not a **quality** claim: it says the correction got cheaper to compute, it says nothing about how much distortion the correction removes.

Also worth citing with the same caveat the repo attaches to it: voxel downsampling took a demo clip from 69k to 5k points, about 14x - but that ratio is specific to the leaf size chosen for that clip, not a fixed or guaranteed speedup.

***

## IMU-based deskewing

This is the feature I'm proudest of, because it's the one that's almost never done correctly in production stacks.

### The problem

A spinning LiDAR doesn't capture a cloud instantaneously. A Velodyne VLP-16 at 10 Hz takes 100 ms to complete a full scan. During those 100 ms, the robot moves - and the points captured at t=0 ms and t=99 ms live in slightly different sensor frames.

If the robot is moving forward at 1 m/s, the cloud is **stretched by 10 cm** along the direction of motion. If the robot is turning at 1 rad/s, the cloud is **angularly skewed by ~57°/s × 100 ms ≈ 5.7°**.

Most stacks ignore this. The ones that don't usually deskew using **wheel odometry**, which fails on:

* Mecanum / omni platforms with wheel slip
* Articulated platforms where the LiDAR isn't on the base
* Any platform during sharp turns where wheel ticks lie

### The Polka approach

Deskewing corrects each point by an **SE(3) exponential map** motion model - constant angular velocity plus constant acceleration, integrated over the point's own relative timestamp within the scan window (`include/polka/util/se3_exp.hpp`). The motion model is inspired by [rko_lio](https://github.com/PRBonn/rko_lio) (PRBonn, Malladi et al., 2025, [arXiv:2509.06593](https://arxiv.org/pdf/2509.06593)) - credit where it's due, since deskewing is the thing I keep pointing people to this project for.

Since 0.5.0, the rotation isn't recomputed exactly at every point - it's computed exactly at a coarse stride and interpolated between strides, which is what took the per-source deskew stage from ~9.8 ms to ~1.6 ms (previous section).

Gravity handling is conditional, not unconditional subtraction:

1. If the IMU flags a valid orientation (`orientation_covariance[0] >= 0`) with a well-formed quaternion, gravity is subtracted using that orientation before double-integrating acceleration.
2. If the IMU flags no orientation at all (`orientation_covariance[0] < 0`), 0.5.0 estimates body-frame gravity via an EMA of the raw acceleration instead of giving up - logged once as `IMU has no orientation, estimating body-frame gravity via EMA` (contributed by an external PR, `kyrie2to11`, #28).
3. If the IMU flags a valid orientation but the quaternion itself is degenerate (garbage data), acceleration is zeroed and translation deskew is disabled for that sample - logged as `IMU has degenerate orientation quaternion, translation deskew disabled`.

Per-point timestamps are auto-detected by default (`deskew_timestamp_field: "auto"`, scanning for `time`, `t`, `timestamp`, and similar field names) - I've seen it log `detected per-point timestamp field 'timestamp' (offset=18, FLOAT64)` on a real driver's cloud. The IMU itself is buffered in a circular buffer of `sensor_msgs/Imu` (`imu_buffer_size: 200`, about 1 s at 200 Hz).

### Per-source IMU overrides

Here's where articulated platforms matter. If your robot has a mast that yaws independently of the base - say, a forklift with a sensor head on a turret - the **base IMU lies about the mast's motion**. The mast has its own angular velocity that the base IMU never sees.

There's no separate top-level `imus:` map to define - each source just points at a topic:

```yaml
polka:
  ros__parameters:
    motion_compensation:
      enabled: true
      imu_topic: "/imu/data"   # global / fallback IMU (chassis)
      max_imu_age: 0.2
      imu_buffer_size: 200
      per_point_deskew: true
      deskew_timestamp_field: "auto"

    source_names: ["turret_lidar", "chassis_lidar"]

    sources:
      turret_lidar:
        topic: "/turret/points"
        type: "pointcloud2"
        imu_topic: "/turret/imu/data"   # per-source override - its own IMU
        qos_reliability: "best_effort"
        qos_history_depth: 1

      chassis_lidar:
        topic: "/chassis/points"
        type: "pointcloud2"
        # no imu_topic override -> falls back to the global /imu/data
        qos_reliability: "best_effort"
        qos_history_depth: 1
```

What makes this actually work for a moving joint, and what the feature list has never given enough credit to: Polka looks up the **live TF** from each IMU's frame to its sensor's frame and rotates that IMU's angular velocity and linear acceleration into the sensor frame before deskewing, falling back to identity on TF failure. That transform can be dynamic - driven off `joint_states` for a turret encoder, for instance - so a rotating mast LiDAR deskews against the mast's own motion, not the chassis's, without you writing any of that logic yourself:

```
chassis IMU ──TF into sensor frame──▶ chassis LiDAR ──┐
                                                      ├──▶ polka ──▶ one merged, deskewed cloud
  turret IMU ──TF into sensor frame──▶ turret LiDAR ──┘
```

A full working example is `config/example_articulated_imu.yaml` in the repo.

> **Field note, not a repo benchmark:** on the warehouse forklift I ran this on, per-source IMU deskewing turned a roughly **8 cm cloud smear during sharp turns into about 0.8 cm**. That's my own before/after observation on that specific robot - there's no corresponding artifact in the repo, unlike the CHANGELOG-sourced deskew latency numbers above. Treat it as anecdote, not benchmark.

***

## Runtime tools: reconfiguration, diagnostics, and the monitor

A few things the feature list undersells because they were never mentioned on this page at all:

* **Full runtime reconfiguration.** Filters, outputs, deskewing parameters, and even the `source_names` list itself can be changed live via `ros2 param set`, validated in a two-phase apply so a bad value doesn't half-apply. The one exception is `enable_gpu`, which is read-only because the merge engine is constructed once. Covered by `test_runtime_reconfigure.cpp` in CI.
* **`/diagnostics`.** A `diagnostic_msgs/DiagnosticArray` published on the absolute topic `/diagnostics` (not namespaced under the node), with per-source rate, bandwidth, message age, stamp offset, and filter drop rate, plus node and output summaries. Consumable by `rqt_robot_monitor` or `diagnostic_aggregator` like any other ROS 2 diagnostics feed.
* **Drift detection.** `diagnostics.timing_drift` tracks an EWMA of each source's stamp offset from the median of its peers and flags after `min_ticks` consecutive bad ticks (default 5), clearing only once the offset drops back under 80% of the threshold - so one jittery tick doesn't flip the flag on and off. `diagnostics.rate_drift` does the equivalent for a source publishing slower than its `expected_rate` (or an auto-baselined rate if you don't set one).
* **`polka_monitor`.** A curses TUI dashboard, `ros2 run polka polka_monitor`, reading `/diagnostics` and rendering per-source status, output rates, and the active config in panels. The shipped launch file starts it by default alongside the node (re-attached to `/dev/tty` so curses gets a real terminal even under `ros2 launch`'s piped stdio); the node itself logs to file so the two don't fight over the same terminal.
* **`timestamp_strategy`.** Controls how the merged output's header stamp is chosen across sources: `earliest` (default), `latest`, `average`, or `local`.
* **Per-point timestamp passthrough.** `point_timestamps.enabled` / `.mode` (`offset` or `absolute`) adds a per-point `time` field to the merged cloud for downstream deskewing SLAM (GLIM-style), paired with `suppress_duplicate_timestamps` so a stalled merge doesn't republish the same stamp twice.
* **Per-output QoS**, independently on cloud and scan: reliability, durability, history depth, liveliness, deadline, and lifespan - plus `qos_reliability`/`qos_history_depth` per source.

***

## Five-distro support

Polka supports **Humble, Iron, Jazzy, Kilted, and Lyrical**, each on its own code-identical branch:

| Distro | Ubuntu | Branch |
| --- | --- | --- |
| Humble | 22.04 | `humble` |
| Iron | 22.04 | `iron` |
| Jazzy | 24.04 | `jazzy` |
| Kilted | 24.04 | `kilted` |
| Lyrical | 26.04 | `lyrical` |

The CI matrix (`.github/workflows/ci.yml`) builds and runs all five in `osrf/ros:<distro>-desktop` containers on every push and PR, `fail-fast: false`, backed by four gtest suites (`test_drift_tracker`, `test_stat_counters`, `test_config_preview`, `test_runtime_reconfigure`) plus `ament_lint_auto`.

The trick to keeping five branches identical is a single CMake capability check, not a version probe: `ament_target_dependencies()` was deprecated in Kilted and removed in Rolling/Lyrical, so the `CMakeLists.txt` branches on `if(COMMAND ament_target_dependencies)` and falls back to modern `target_link_libraries()` + `_TARGETS` variables when the macro doesn't exist. Development happens on `humble` as the source of truth; `scripts/sync-distros.sh` fans a merged change out to the other four branches, documented in `MAINTAINING.md`.

***

## How to use

### Install

```bash
git clone -b humble https://github.com/Pana1v/polka.git ~/ros2_ws/src/polka
# swap "humble" for iron / jazzy / kilted / lyrical to match your distro
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select polka
source install/setup.bash
```

### Launch

The shipped launch file is a plain node, not a component container - `ros2 launch polka polka.launch.py config_file:=<your_config.yaml>`. It also starts `polka_monitor` alongside it by default.

```bash
cp src/polka/config/example_params.yaml src/polka/config/my_robot.yaml   # edit topics + output_frame_id
ros2 launch polka polka.launch.py config_file:=src/polka/config/my_robot.yaml
```

Replaying a bag instead of live sensors? Pass `use_sim_time:=true` and play the bag with `--clock` - the default staleness check compares message stamps against wall time, so an unmodified bag replay looks like every source went silent and nothing gets published.

### Minimal config

This is close to the repo's own `config/example_params.yaml` - it will actually load:

```yaml
# config/my_robot.yaml
polka:
  ros__parameters:
    output_frame_id: "base_link"
    output_rate: 20.0
    enable_gpu: true                 # falls back to CPU automatically if unavailable

    outputs:
      cloud:
        enabled: true
        topic: "~/merged_cloud"
      scan:
        enabled: true
        topic: "~/merged_scan"
        z_min: -0.10
        z_max: 0.50

    source_names: ["front_3d", "rear_2d"]

    sources:
      front_3d:
        topic: "/front_lidar/points"
        type: "pointcloud2"
        qos_reliability: "best_effort"
        qos_history_depth: 1

      rear_2d:
        topic: "/rear_lidar/scan"
        type: "laserscan"
        qos_reliability: "best_effort"
        qos_history_depth: 1
```

```bash
ros2 topic hz /polka/merged_cloud
ros2 topic echo /diagnostics
```

(`~/merged_cloud` resolves to `/polka/merged_cloud` because the launch file names the node `polka`; both topic and QoS are configurable per output under `outputs.cloud` / `outputs.scan`.)

### Composing with a SLAM node

The shipped launch file won't do this for you, but the plugin registration is real - build your own `ComposableNodeContainer` and load `polka::PolkaNode` alongside a consumer, e.g. [GO-SLAM](go-slam.md), dropping the inter-process serialization hop:

```python
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode

container = ComposableNodeContainer(
    name='fusion_container',
    namespace='',
    package='rclcpp_components',
    executable='component_container_mt',
    composable_node_descriptions=[
        ComposableNode(
            package='polka',
            plugin='polka::PolkaNode',
            name='polka',
            parameters=['config/my_robot.yaml'],
        ),
        ComposableNode(
            package='go_slam',
            plugin='go_slam::FrontEndNode',
            name='go_slam',
            parameters=['config/go_slam.yaml'],
            remappings=[('cloud_in', '/polka/merged_cloud')],
        ),
    ],
    output='screen',
)
```

***

## Roadmap

* **Live re-config** - done. Two-phase runtime reconfigure shipped in 0.5.0; even the source list can change without a restart.
* **ROS 2 Iron support** - done, and Kilted and Lyrical shipped alongside it, beyond what was originally planned.
* **Recorded-bag mode** - partial. 0.5.0 added rosbag/clock misconfiguration detection and exposed `use_sim_time`, which gets you correct-timing bag replay. It's not yet the standalone offline-tuning replay mode (running bag data through Polka's filters without the live driver stack) that was originally the goal.
* **GPU TF cache** - still open. Keep transforms in device memory to avoid the host round-trip when the only consumer is also on GPU.
* **OpenCL fallback** - still open. For AMD-based industrial PCs without CUDA.

What people are actually asking for right now, from the open issues: better per-point timestamp field detection for Ouster drivers, deskew efficiency for LiDARs that scan vertically rather than horizontally, a clearer explanation of what the translation half of deskewing actually does, and switching output publishing to `point_cloud_transport`. If you want any of this to happen faster, [open an issue](https://github.com/Pana1v/polka/issues) or PR it.

***

## Find me online

[panav.netlify.app](https://panav.netlify.app) · [github.com/Pana1v](https://github.com/Pana1v) · [linkedin.com/in/panavraaj](https://linkedin.com/in/panavraaj)
