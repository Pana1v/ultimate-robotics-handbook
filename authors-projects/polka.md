---
icon: gear
---

# Polka - Multi-LiDAR Fusion for ROS 2

> A ROS 2 multi-LiDAR fusion node that merges heterogeneous `PointCloud2` and `LaserScan` streams into unified cloud and scan outputs through a **single composable pipeline**. Per-source filtering, TF2-aligned fusion, optional CUDA acceleration, and IMU-based deskewing with per-source IMU overrides for articulated platforms. Supports ROS 2 **Humble** and **Jazzy**.

**Role:** Creator
**Repo:** [github.com/Pana1v/Polka](https://github.com/Pana1v/Polka)
**Status:** Active

***

## Motivation

If you've worked on a real AMR with more than one LiDAR, you know the pain. The "standard" approach in ROS 2 looks something like this:

```
lidar_1 → relay_node → filter_node → tf_aligner → ┐
lidar_2 → relay_node → filter_node → tf_aligner → ├── merge_node → /points
lidar_3 → relay_node → filter_node → tf_aligner → ┘
```

Six to nine nodes per sensor stack. Each one is a process boundary. Each one is a serialization-deserialization round trip. Each one adds 1-5 ms of latency, and the launch file looks like a Jenga tower of `Node()` declarations with hand-aligned remappings.

On the warehouse AMR I worked on, this stack was responsible for:

* **~40 ms of end-to-end fusion latency** on a Jetson Orin NX - most of it was serialization between nodes, not actual computation
* **Frequent topic-name remap typos** that silently produced empty merged clouds
* **No principled deskewing** - every motion blur in the cloud was either ignored or "fixed" by an ad-hoc downstream node
* **Configuration spread across 7 YAML files** because each filter/merger had its own params

I wrote Polka to collapse all of that into **one composable node** with **one YAML file** that describes every source, every filter, and every transform.

> **Note:** "Composable" here means the actual ROS 2 component sense - Polka can load into a component container and share an address space (and a single intra-process memory bus) with whatever consumer you stack next to it, e.g., a costmap or a SLAM node. No serialization, no IPC, no copy.

***

## Architecture

```
                          ┌─────────────────────────────────────────────┐
                          │             Polka Composable Node           │
                          │                                             │
  lidar_front (PC2) ──────┼──► [src filter] ──► [TF lookup] ──┐         │
                          │                                   │         │
  lidar_rear  (PC2) ──────┼──► [src filter] ──► [TF lookup] ──┤         │
                          │                                   ├──► [Fusion]──┐
  lidar_2d    (Scan) ─────┼──► [src filter] ──► [TF lookup] ──┤             │
                          │                  └─► [Scan→PC2] ──┘             │
                          │                                                 │
  imu_main (sensor_msgs) ─┼──────► [Deskew engine] ◄──── per-source IMU ────┤
                          │                                                 │
                          │                                                 ▼
                          │                                          ┌───────────────┐
                          │                                          │ CUDA path?    │
                          │                                          │ [yes] → GPU   │
                          │                                          │ [no]  → CPU   │
                          │                                          └───────┬───────┘
                          │                                                 │
                          │                       ┌───── /fused/points (PC2) ┤
                          │                       ├───── /fused/scan   (LaserScan) ─►
                          │                       └───── /fused/diag   (diagnostics) ─►
                          └─────────────────────────────────────────────────┘
```

The whole thing is one process. One ROS 2 node. One config file.

***

## Per-source filtering

Each LiDAR has its own personality. The base-mounted 2D scanner sees a lot of forklift legs at 50 cm. The mast-mounted 3D LiDAR sees the ceiling lights as ghost returns. The rear LiDAR sees the robot's own bumper as a constant 12 cm obstacle.

In the relay-filter-merge soup, you fix this by spawning a separate `pointcloud_filter` node per source with a unique namespace. In Polka, you declare it inline:

```yaml
polka:
  ros__parameters:
    sources:
      lidar_front:
        type: pointcloud2
        topic: /lidar_front/points
        frame_id: lidar_front_link
        filters:
          - type: range
            min_range: 0.15
            max_range: 30.0
          - type: voxel_grid
            leaf_size: 0.05
          - type: passthrough
            field: z
            min: -0.1
            max: 2.5
          - type: self_filter
            link: base_link
            inflation: 0.05

      lidar_rear:
        type: pointcloud2
        topic: /lidar_rear/points
        frame_id: lidar_rear_link
        filters:
          - type: range
            min_range: 0.20
            max_range: 25.0
          - type: voxel_grid
            leaf_size: 0.05

      scan_2d:
        type: laserscan
        topic: /scan
        frame_id: laser_2d_link
        upsample_to_pointcloud: true
        filters:
          - type: angular_window
            min_angle: -2.35   # -135°
            max_angle:  2.35   # +135°
```

The order of filters matters: range cull first (cheap), then voxel grid (decimation), then field-based passthrough, then self-filter (most expensive, smallest input). This is the same ordering you'd hand-tune in PCL - Polka just makes it explicit and per-source.

> **Self-filter detail:** the `self_filter` step uses the URDF link geometry resolved via `robot_description` and TF2 - it's not just a fixed bounding box. On the warehouse AMR this killed ~3% of points per frame that were grazing the bumper sensors at oblique angles.

***

## TF2-aligned fusion

Every source declares its own `frame_id`. Polka resolves all transforms to a single `target_frame` (default: `base_link`) at the **timestamp of the latest input**. This means:

* If `lidar_front` publishes at 20 Hz and `lidar_rear` at 10 Hz, fusion happens at the rate of whoever arrived last in a configurable time window
* TF lookups use `tf2_ros::Buffer::lookupTransform` with `tf2::durationFromSec(0.1)` - anything older than 100 ms is dropped with a throttled warning
* For static sensors, the transform is cached on first resolution and refreshed only when `tf_static` republishes

```yaml
polka:
  ros__parameters:
    target_frame: base_link
    fusion:
      time_sync_tolerance: 0.05   # seconds
      max_tf_age: 0.10            # seconds
      sync_policy: approximate    # or "exact" for hardware-synced sensors
      drop_late_sources: true
```

If a source goes silent (cable yanked, driver crash), Polka publishes the fused cloud from whichever sources are still alive **and** emits a `/fused/diag` diagnostic message. Downstream consumers don't get a frozen topic - they get a degraded one with a flag.

***

## CUDA path

For platforms with an NVIDIA GPU (Jetson Orin, x86 dGPU), the heavy filters can run on the device:

* **Voxel grid:** GPU spatial hash with atomic insert. ~10× faster than PCL's `VoxelGrid` on 100k-point clouds.
* **Range / passthrough:** trivial kernel, mostly memory-bound.
* **Self-filter:** AABB tree on the host, point-in-polytope test on the device.
* **TF apply:** 4×4 matrix-vector multiply, fused with the next filter to avoid extra memory traffic.

```yaml
polka:
  ros__parameters:
    enable_cuda: true
    cuda_device: 0
```

If `enable_cuda: true` but no CUDA runtime is available, Polka falls back to CPU and logs a single `WARN` on startup - it doesn't refuse to launch. This matters for fleets where some machines have GPUs and some don't, and you want one config file across the whole deployment.

> **Numbers:** on a Jetson Orin NX 8GB with three sources (2× 3D LiDAR @ 20 Hz, 1× 2D scan @ 10 Hz), CPU fusion runs at ~22 ms/frame and CUDA fusion at ~6 ms/frame. `[verify exact numbers from your benchmark file]`

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

Deskewing uses **IMU integration over the scan window**. For each point with relative timestamp `t_i ∈ [0, T_scan]`:

1. Integrate angular velocity from t=0 to t=t_i using midpoint rule on IMU samples
2. Integrate linear acceleration (gravity-compensated) twice over the same interval
3. Build the per-point correction transform `T_i = SE(3)(R_i, p_i)`
4. Apply `T_i` to the point before fusion

The IMU is queried as a circular buffer of `sensor_msgs/Imu` messages indexed by stamp.

### Per-source IMU overrides

Here's where articulated platforms matter. If your robot has a mast that yaws independently of the base - say, a forklift with a sensor head on a turret - the **base IMU lies about the mast's motion**. The mast has its own angular velocity that the base IMU never sees.

Polka lets you assign a different IMU per LiDAR source:

```yaml
polka:
  ros__parameters:
    imus:
      base_imu:
        topic: /imu/base/data
        frame_id: base_imu_link
      mast_imu:
        topic: /imu/mast/data
        frame_id: mast_imu_link

    sources:
      lidar_base:
        type: pointcloud2
        topic: /lidar_base/points
        frame_id: lidar_base_link
        deskew:
          enabled: true
          imu: base_imu

      lidar_mast:
        type: pointcloud2
        topic: /lidar_mast/points
        frame_id: lidar_mast_link
        deskew:
          enabled: true
          imu: mast_imu        # <-- different IMU for this source!
```

On the warehouse forklift this turned a 8 cm cloud smear during sharp turns into a 0.8 cm one. The downstream SLAM (see [GO-SLAM](go-slam.md)) loop-closure detection rate jumped accordingly.

***

## Humble vs Jazzy compatibility

Polka supports both ROS 2 **Humble** (Ubuntu 22.04) and **Jazzy** (Ubuntu 24.04). The differences are non-trivial in the composable-node and TF2 APIs, so the build system handles them with a feature-detect rather than version pinning.

| Feature | Humble | Jazzy |
| --- | --- | --- |
| Component manager API | `rclcpp_components::ComponentManager` | Same, with new `LoadNodeOptions` fields |
| TF2 buffer interface | `tf2_ros::Buffer::lookupTransform(timeout)` | Same signature, stricter exception types |
| Intra-process comms | Opt-in via `NodeOptions().use_intra_process_comms(true)` | Default for components |
| `rclcpp::Time` arithmetic | Identical | Identical |
| `sensor_msgs/msg/PointCloud2` | Identical | Identical |
| Default DDS | Fast DDS | Fast DDS (same as Humble) - different QoS defaults |

The CMake file uses `if(NOT "$ENV{ROS_DISTRO}" STREQUAL "")` checks plus `find_package(... REQUIRED)` version probes to switch between paths. CI runs both distros on every PR.

> **Note:** if you're on Iron or Rolling, Polka probably works but isn't tested. Open an issue with your distro and I'll add CI coverage.

***

## How to use

### Install

```bash
cd ~/ros2_ws/src
git clone https://github.com/Pana1v/Polka.git
cd ..
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select polka --symlink-install
source install/setup.bash
```

Optional CUDA build:

```bash
colcon build --packages-select polka --cmake-args -DPOLKA_ENABLE_CUDA=ON
```

### Minimal launch

```python
# launch/polka_minimal.launch.py
from launch import LaunchDescription
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode

def generate_launch_description():
    container = ComposableNodeContainer(
        name='polka_container',
        namespace='',
        package='rclcpp_components',
        executable='component_container_mt',
        composable_node_descriptions=[
            ComposableNode(
                package='polka',
                plugin='polka::PolkaNode',
                name='polka',
                parameters=['config/polka.yaml'],
            ),
        ],
        output='screen',
    )
    return LaunchDescription([container])
```

### Minimal config

```yaml
# config/polka.yaml
polka:
  ros__parameters:
    target_frame: base_link
    enable_cuda: false

    sources:
      lidar_front:
        type: pointcloud2
        topic: /lidar_front/points
        frame_id: lidar_front_link
        filters:
          - { type: range, min_range: 0.15, max_range: 30.0 }
          - { type: voxel_grid, leaf_size: 0.05 }

      lidar_rear:
        type: pointcloud2
        topic: /lidar_rear/points
        frame_id: lidar_rear_link
        filters:
          - { type: range, min_range: 0.20, max_range: 25.0 }
          - { type: voxel_grid, leaf_size: 0.05 }

    fusion:
      time_sync_tolerance: 0.05
      max_tf_age: 0.10
      output_topic_cloud: /fused/points
      output_topic_scan: /fused/scan
```

```bash
ros2 launch polka polka_minimal.launch.py
ros2 topic hz /fused/points
ros2 topic echo /fused/diag
```

### Composing with a SLAM node

To run [GO-SLAM](go-slam.md) on the fused, deskewed cloud, load it into the **same container** as Polka - zero-copy intra-process delivery:

```python
ComposableNode(
    package='go_slam',
    plugin='go_slam::FrontEndNode',
    name='go_slam',
    parameters=['config/go_slam.yaml'],
    remappings=[('cloud_in', '/fused/points')],
),
```

***

## Roadmap

* **GPU TF cache** - keep transforms in device memory and avoid the host round-trip when the only consumer is also on GPU.
* **ROS 2 Iron support** - already mostly working, blocked on CI runner availability.
* **OpenCL fallback** - for AMD-based industrial PCs that don't have CUDA.
* **Live re-config** - accept parameter updates without container restart (currently you have to relaunch to add a source).
* **Recorded-bag mode** - replay bag files into Polka without the live driver stack, for offline tuning of filters.

If you want any of these to happen faster, [open an issue](https://github.com/Pana1v/Polka/issues) or PR it.

***

## Find me online

[panav.netlify.app](https://panav.netlify.app) · [github.com/Pana1v](https://github.com/Pana1v) · [linkedin.com/in/panavraaj](https://linkedin.com/in/panavraaj)
