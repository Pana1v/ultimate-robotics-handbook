---
icon: gear
---

# DDS and QoS

This is the page I send junior engineers to when they ask "why aren't my messages arriving?" Nine times out of ten the answer is a QoS mismatch they cannot see in `ros2 topic list`. The tenth time it's discovery on a flaky wireless network. Both root-cause in the same place: the DDS layer underneath ROS 2.

## Why DDS

ROS 1 had a single `roscore` running the central name service. Every node connected to the master to discover everyone else, and every topic was effectively TCP-with-headers. It worked, but it had three problems that killed it for production:

1. **Single point of failure** — `roscore` dies, your robot dies.
2. **No quality of service** — every subscriber got every message, in order, with TCP reliability you could not turn off. Great for a desk demo, useless for a 100 Hz LiDAR over Wi-Fi.
3. **Custom transport** — TCPROS / UDPROS were homegrown protocols that no one outside the ROS ecosystem implemented.

DDS solves all three. It is an OMG standard (Data Distribution Service) that has been used in avionics, defense, and industrial automation for two decades. The properties that matter for robots:

* **Decentralized discovery** — every participant broadcasts its endpoints over multicast; there is no master. A node can join and leave the network without restarting the world.
* **Per-endpoint QoS** — reliability, durability, deadlines, lifespan, history depth, liveliness. The publisher and subscriber negotiate compatibility at discovery time.
* **Multiple vendor implementations** — DDS is a spec, not an implementation. You can swap the underlying library without changing your application code.

The trade-off is complexity. In ROS 1 every topic Just Worked because there were no knobs. In ROS 2 there are about a dozen knobs and the defaults are sometimes wrong for your use case. The rest of this page is a guide to which knob does what.

## RMW implementations

ROS 2 talks to DDS through a thin layer called **RMW** (ROS middleware). The same `rclcpp` or `rclpy` code runs unchanged on any RMW. You pick which one with the `RMW_IMPLEMENTATION` environment variable:

```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ros2 run my_pkg my_node
```

The implementations you will actually see in 2026:

| RMW                     | Vendor          | Status in 2026                                      |
| ----------------------- | --------------- | --------------------------------------------------- |
| `rmw_cyclonedds_cpp`    | Eclipse Cyclone | **Default on Humble and Jazzy.** Solid, fast discovery. |
| `rmw_fastrtps_cpp`      | eProsima Fast DDS | Was the default on Foxy/Galactic. Heavier, more configurable. Still well supported. |
| `rmw_zenoh_cpp`         | Eclipse Zenoh   | Newer, designed for lossy/wireless networks and routing across NAT. Gaining adoption \[verify]. |
| `rmw_connextdds`        | RTI Connext     | Commercial, used in regulated industries (automotive, defense).  |

Pick one and pin it across your whole network. They interoperate via the DDS-RTPS spec, but discovery quirks differ — discovery storms across mixed RMWs are a known headache. The official RMW comparison: [docs.ros.org/en/jazzy/Concepts/Intermediate/About-Different-Middleware-Vendors.html](https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Different-Middleware-Vendors.html) \[verify].

For most projects: **stick with Cyclone DDS.** It is the lightest, has the fastest discovery, and is what the Jazzy installers ship. Only reach for Fast DDS if you need its specific tuning knobs (XML profile files, large discovery, etc.) or for Zenoh if you have a hostile network.

### Switching RMW per-launch

`RMW_IMPLEMENTATION` is read once at process startup. To pin it for a launched group:

```python
# my_launch.py
import os
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='my_pkg',
            executable='my_node',
            additional_env={'RMW_IMPLEMENTATION': 'rmw_cyclonedds_cpp'},
        ),
    ])
```

## QoS profile components

A QoS profile is a bundle of settings that the publisher and subscriber each declare. At discovery time, DDS checks that they are *compatible* (not necessarily identical). If they are not, you get no error — you just silently never receive the messages. This is the #1 cause of "my topic shows up in `ros2 topic list` but I never get callbacks."

The components you actually configure:

### Reliability

| Value          | Behavior                                                                  |
| -------------- | ------------------------------------------------------------------------- |
| `RELIABLE`     | DDS retransmits lost messages. Like TCP. Subscriber gets every message or backpressure occurs. |
| `BEST_EFFORT`  | DDS sends once and forgets. Like UDP. Subscriber drops missed messages.   |

Use `BEST_EFFORT` for sensor data (LiDAR, cameras, IMU) where the next sample arrives in a few ms anyway. Use `RELIABLE` for commands and config that must arrive.

**Compatibility rule**: A `BEST_EFFORT` subscriber will not receive from a `RELIABLE` publisher (it can, by spec — but the practical default is no). A `RELIABLE` subscriber will not receive from a `BEST_EFFORT` publisher. **They must match.**

### Durability

| Value              | Behavior                                                                  |
| ------------------ | ------------------------------------------------------------------------- |
| `VOLATILE`         | New subscriber only gets messages published *after* it connected.         |
| `TRANSIENT_LOCAL`  | Publisher remembers the last N messages (where N = history depth) and delivers them to late-joining subscribers. |

`TRANSIENT_LOCAL` is what gives you "latched topics" — useful for `/map`, `/robot_description`, anything published once at startup that late-joiners need to see.

**Compatibility rule**: a `VOLATILE` subscriber cannot receive from a `TRANSIENT_LOCAL` publisher? Actually, yes it can — the subscriber just won't get the historical replay. The breaking case is a `TRANSIENT_LOCAL` subscriber against a `VOLATILE` publisher: incompatible, no messages received.

### History and Depth

| Value         | Behavior                                                       |
| ------------- | -------------------------------------------------------------- |
| `KEEP_LAST`   | Buffer the last `depth` messages.                              |
| `KEEP_ALL`    | Buffer everything. Bounded by RMW resource limits.             |

`Depth` is the buffer size for `KEEP_LAST`. For sensors, `5` is plenty. For commands, `10` is standard. `KEEP_ALL` is almost never what you want — it leaks memory if the subscriber is slow.

### Deadline

The maximum expected interval between published messages. If the publisher misses the deadline, both sides get a callback (`offered_deadline_missed`, `requested_deadline_missed`). Useful for safety-critical systems where a missing heartbeat means "the other node is broken."

In production I set deadlines on critical command topics like `/cmd_vel` and `/emergency_stop`. The handler logs the miss and triggers a safety controller fallback.

### Lifespan

How long a message stays valid after publishing. After lifespan expires, DDS drops the message from the buffer. Use this for stale-data prevention — a target pose that arrived 5 seconds ago should not silently re-trigger when a subscriber late-joins.

### Liveliness

How DDS decides whether the publisher is still alive. `AUTOMATIC` is fine for almost everything. `MANUAL_BY_TOPIC` is for when you want the application to explicitly assert liveliness — rare.

### Lease duration

For liveliness — how often the publisher must signal it's alive. Default is effectively infinite. Combined with `Deadline`, this gives you a heartbeat mechanism without rolling your own.

## Standard profiles

`rclcpp` and `rclpy` ship a small set of pre-baked profiles that cover most needs. Use these by name unless you have a real reason to roll your own.

### C++

```cpp
#include <rclcpp/qos.hpp>

// Best-effort, depth 5 — for high-frequency sensors
auto qos_sensor = rclcpp::SensorDataQoS();

// Reliable, transient_local, depth 1 — for /map, /robot_description
auto qos_latched = rclcpp::QoS(1).reliable().transient_local();

// Reliable, depth 10 — for commands like /cmd_vel
auto qos_control = rclcpp::QoS(10).reliable();

// Service QoS — reliable, volatile, depth 10
auto qos_service = rclcpp::ServicesQoS();

// Parameter QoS — reliable, depth 1000 (parameter events fan out wide)
auto qos_params = rclcpp::ParametersQoS();

auto pub = node->create_publisher<sensor_msgs::msg::LaserScan>("scan", qos_sensor);
```

### Python

```python
from rclpy.qos import (
    QoSProfile,
    QoSReliabilityPolicy,
    QoSDurabilityPolicy,
    QoSHistoryPolicy,
    qos_profile_sensor_data,
    qos_profile_services_default,
    qos_profile_parameters,
)

# Use the preset for sensor data
scan_pub = node.create_publisher(LaserScan, 'scan', qos_profile_sensor_data)

# Latched profile for /map
map_qos = QoSProfile(
    reliability=QoSReliabilityPolicy.RELIABLE,
    durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=1,
)
map_pub = node.create_publisher(OccupancyGrid, 'map', map_qos)
```

## QoS compatibility table

This is the cheat sheet. When publisher and subscriber settings disagree, the more strict subscriber loses — i.e., the subscriber asking for more reliability than the publisher offers gets nothing.

| Publisher          | Subscriber         | Compatible? |
| ------------------ | ------------------ | ----------- |
| RELIABLE           | RELIABLE           | yes         |
| RELIABLE           | BEST\_EFFORT       | yes (subscriber relaxed) |
| BEST\_EFFORT       | RELIABLE           | **no**      |
| BEST\_EFFORT       | BEST\_EFFORT       | yes         |
| TRANSIENT\_LOCAL   | TRANSIENT\_LOCAL   | yes         |
| TRANSIENT\_LOCAL   | VOLATILE           | yes (subscriber gets no history) |
| VOLATILE           | TRANSIENT\_LOCAL   | **no**      |
| VOLATILE           | VOLATILE           | yes         |

You can inspect compatibility live with:

```bash
ros2 topic info /my_topic --verbose
```

It prints the QoS of every endpoint. The first time a topic looks "dead," run this and compare.

## What profile for what data

The cheat sheet I keep in my head:

| Data type                | Reliability   | Durability        | Depth | Example                                |
| ------------------------ | ------------- | ----------------- | ----- | -------------------------------------- |
| High-rate sensor         | BEST\_EFFORT  | VOLATILE          | 1–5   | `/scan`, `/camera/image_raw`, `/imu/data` |
| Velocity command         | RELIABLE      | VOLATILE          | 10    | `/cmd_vel`                             |
| Joint state              | BEST\_EFFORT  | VOLATILE          | 5     | `/joint_states` (if at high rate)      |
| Latched config           | RELIABLE      | TRANSIENT\_LOCAL  | 1     | `/map`, `/robot_description`           |
| Diagnostics              | RELIABLE      | VOLATILE          | 10    | `/diagnostics`                         |
| TF                       | RELIABLE      | VOLATILE          | 100   | `/tf`                                  |
| Static TF                | RELIABLE      | TRANSIENT\_LOCAL  | 100   | `/tf_static`                           |
| Action goals/results     | RELIABLE      | VOLATILE          | 1     | (handled by action infrastructure)     |
| Service request/response | RELIABLE      | VOLATILE          | 10    | (handled by service infrastructure)    |

Nav2 and MoveIt set these correctly for you. Where you have to think is in your own message bus — anything you create with `create_publisher` directly.

## Inspecting QoS at runtime

The CLI tools have gotten much better since Humble:

```bash
# List every endpoint on a topic, with its QoS
ros2 topic info /scan --verbose

# Show compatibility warnings between publishers and subscribers
ros2 topic info /scan --verbose | grep -i "incompatible\|deadline\|liveliness"

# Echo a topic, overriding QoS (useful for debugging BEST_EFFORT topics)
ros2 topic echo /scan --qos-reliability best_effort
```

If `ros2 topic echo` works only with `--qos-reliability best_effort` while your subscriber is reliable, you found the bug.

## DDS tuning for high-throughput data

The defaults are tuned for "a few hundred kilobytes per second across half a dozen topics." Real robots running cameras and LiDARs blow past that easily. The tuning levers, ordered by impact:

### 1. Increase the UDP buffer sizes

By default the Linux kernel allows tiny UDP buffers (~200 KB). When a 5 MP camera dumps a 5 MB frame onto the socket, the kernel drops the tail. Bump them:

```bash
sudo sysctl -w net.core.rmem_max=2147483647
sudo sysctl -w net.core.rmem_default=8388608
sudo sysctl -w net.core.wmem_max=2147483647
sudo sysctl -w net.core.wmem_default=8388608
```

Persist in `/etc/sysctl.d/60-dds.conf`. Cyclone DDS will log a warning at startup if your buffers are smaller than its expected receive size.

### 2. Use shared memory transport for same-machine traffic

Cyclone DDS supports the `iceoryx` shared-memory plugin; Fast DDS has its own SHM transport. Both let two processes on the same host bypass the UDP loopback entirely — useful when you're piping a 4K camera into a perception node on the same machine.

For Cyclone DDS, edit a `cyclonedds.xml` config file and point `CYCLONEDDS_URI` at it:

```xml
<CycloneDDS>
    <Domain Id="any">
        <SharedMemory>
            <Enable>true</Enable>
        </SharedMemory>
    </Domain>
</CycloneDDS>
```

```bash
export CYCLONEDDS_URI=file:///etc/cyclonedds.xml
```

Verify the spec at [github.com/eclipse-cyclonedds/cyclonedds](https://github.com/eclipse-cyclonedds/cyclonedds) \[verify].

### 3. Composable nodes (intra-process zero-copy)

If two nodes can share a process, they can communicate via intra-process zero-copy — no DDS, no serialization. This is the single biggest perf win in ROS 2 and is covered in [lifecycle-and-composition.md](lifecycle-and-composition.md).

### 4. Disable multicast on Wi-Fi

Multicast discovery is fine on wired networks, terrible on wireless. Most consumer access points throttle multicast aggressively. Symptom: discovery takes 30+ seconds, topics drop in and out.

For Cyclone DDS, force unicast discovery:

```xml
<CycloneDDS>
    <Domain Id="any">
        <General>
            <AllowMulticast>false</AllowMulticast>
        </General>
        <Discovery>
            <ParticipantIndex>auto</ParticipantIndex>
            <Peers>
                <Peer Address="192.168.1.10"/>
                <Peer Address="192.168.1.11"/>
            </Peers>
        </Discovery>
    </Domain>
</CycloneDDS>
```

This is also the right configuration for cloud / multi-site deployments where multicast isn't routed.

### 5. Discovery server (Fast DDS)

Fast DDS supports a centralized discovery server that participants connect to instead of broadcasting. Adds a single point of coordination back (irony noted), but solves the discovery storm problem on large fleets. Docs: [fast-dds.docs.eprosima.com](https://fast-dds.docs.eprosima.com) \[verify].

### 6. Pin endpoint count

Every publisher and subscriber consumes RMW resources. A node with 50 topics × 5 sensor instances pre-allocated will hit Cyclone DDS' default participant limits. Set them explicitly in the XML config, or refactor toward fewer, larger topics.

## Debugging a QoS mismatch — the workflow

When a topic looks dead:

1. `ros2 topic list` — is it even there?
2. `ros2 topic info /topic --verbose` — pub and sub both present?
3. Check the QoS of every endpoint. Look for reliability or durability mismatches.
4. `ros2 topic hz /topic` — publisher actually publishing?
5. `ros2 topic echo /topic --qos-reliability best_effort` — bypass any reliability mismatch to confirm the data exists.
6. If 5 works but the original subscriber doesn't, you've confirmed a QoS mismatch. Fix the subscriber to match.

For network-level issues: `tcpdump -i any 'udp port 7400 or udp port 7401'` shows DDS discovery and user traffic. Cyclone uses 7400 (discovery) and 7401+ (data). If you see no packets, multicast is being blocked.

## Where to go next

* [Lifecycle and Composition](lifecycle-and-composition.md) — composable nodes are the biggest perf lever once QoS is right.
* [Visualization](visualization.md) — rviz2 and Foxglove have their own QoS subtleties when you subscribe to a robot's topics.
* The deeper DDS spec lives at [omg.org/spec/DDS](https://www.omg.org/spec/DDS/) \[verify] — useful if you ever have to debug something exotic like partition keys or content-filtered topics.
