---
description: ROS 2 — middleware for robotics from setup to Nav2, MoveIt 2, microROS, and production deployment on Humble and Jazzy.
icon: gear
---

# ROS 2

ROS 1 reached end-of-life with Noetic in **May 2025**. If you are starting a robotics project in 2026, you start it on ROS 2 - full stop. This section is the modern, ROS 2 first counterpart to the legacy `ros-advanced/ros-1/` material, which we keep around purely so older codebases and tutorials still make sense to readers.

I have been writing ROS 2 code daily since Foxy, shipped a Humble + Jazzy mobile platform ([Polka](../authors-projects/polka.md)), and contributed upstream to Nav2 and PlotJuggler. The pages in this section reflect what I actually do at work, not just what the docs say.

### In this section

<table data-view="cards"><thead><tr><th></th><th data-type="content-ref"></th><th data-hidden data-card-cover data-type="files"></th></tr></thead><tbody><tr><td>Setup</td><td><a href="setup.md">setup.md</a></td><td></td></tr><tr><td>DDS and QoS</td><td><a href="dds-qos.md">dds-qos.md</a></td><td><a href="../.gitbook/assets/dds.gif">dds.gif</a></td></tr><tr><td>Lifecycle and Composition</td><td><a href="lifecycle-and-composition.md">lifecycle-and-composition.md</a></td><td><a href="../.gitbook/assets/lifecycle.jpeg">lifecycle.jpeg</a></td></tr><tr><td>Nav2 Deep Dive</td><td><a href="nav2-deep-dive.md">nav2-deep-dive.md</a></td><td><a href="../.gitbook/assets/nav2-pure-pursuit.gif">nav2-pure-pursuit.gif</a></td></tr><tr><td>MoveIt 2</td><td><a href="moveit2.md">moveit2.md</a></td><td><a href="../.gitbook/assets/ik1.gif">ik1.gif</a></td></tr><tr><td>micro-ROS</td><td><a href="micro-ros.md">micro-ros.md</a></td><td><a href="../.gitbook/assets/ESP32-blink-gif.gif">ESP32-blink-gif.gif</a></td></tr><tr><td>Visualization (rviz2, Foxglove, Lichtblick, PlotJuggler)</td><td><a href="visualization.md">visualization.md</a></td><td><a href="../.gitbook/assets/ros2-visualization.gif">ros2-visualization.gif</a></td></tr><tr><td>Important Packages and Libraries</td><td><a href="important-packages-and-libraries.md">important-packages-and-libraries.md</a></td><td></td></tr></tbody></table>

### Why ROS 2 (and not ROS 1)

ROS 1 was a brilliant research framework that grew organically from 2007. It had a single ROS Master, no real QoS, no security story, no real-time guarantees, and a transport built on custom TCPROS/UDPROS. It was great for prototyping, painful in production.

ROS 2 was a rewrite, not a port. The headline changes:

| Concern              | ROS 1                          | ROS 2                                                 |
| -------------------- | ------------------------------ | ----------------------------------------------------- |
| Discovery            | Centralized `roscore` (master) | Fully distributed via DDS                             |
| Transport            | Custom TCPROS / UDPROS         | DDS-RTPS (CycloneDDS, Fast DDS, Zenoh RMW)            |
| QoS                  | Effectively none               | Reliability, Durability, History, Deadline, Liveliness |
| Multi-machine        | Awkward, single master         | Native - `ROS_DOMAIN_ID` partitions networks          |
| Threading            | Mostly single-threaded         | Executors, callback groups, true multi-threading     |
| Real-time            | Not realistic                  | Designed for real-time-capable runtimes              |
| Security             | None                           | SROS2 (DDS-Security)                                  |
| Lifecycle            | Hand-rolled                    | First-class managed nodes                             |
| Composition          | One node per process           | Composable nodes, intra-process zero-copy            |
| Microcontrollers     | rosserial (limited, ROS 1 only)| micro-ROS (proper DDS-XRCE)                          |
| Language support     | C++, Python (rospy)            | C++ (rclcpp), Python (rclpy), Rust, others           |
| Build system         | catkin                         | colcon + ament                                       |
| Launch               | XML                            | Python (and XML/YAML if you must)                    |

The trade-off is real complexity in places ROS 1 hid from you - QoS mismatches between publishers and subscribers will silently drop your data the first time you forget about them. That is the price for actually working over wireless and across machines.

### Distros in 2026

ROS 2 ships on a roughly biannual cadence, alternating LTS and non-LTS releases. As of 2026 the two distros that matter for production are:

| Distro                | Released       | EOL              | Ubuntu       | Notes                                                  |
| --------------------- | -------------- | ---------------- | ------------ | ------------------------------------------------------ |
| **Humble Hawksbill**  | May 2022 (LTS) | May 2027 | 22.04 Jammy  | The conservative choice - most third-party packages still target it |
| **Jazzy Jalisco**     | May 2024 (LTS) | May 2029 | 24.04 Noble  | The current default for new work                       |
| **Kilted Kaiju**      | May 2025       | Dec 2026 | 24.04 Noble  | Non-LTS, mostly used by Nav2/MoveIt developers chasing new features |
| **Rolling Ridley**    | Continuous     | n/a              | tracks latest| The development branch - never deploy this to a robot |

When I start a new project today I default to **Jazzy on Ubuntu 24.04**. I only pick Humble when a critical dependency (a vendor driver, a specific MoveIt configuration, a customer-pinned Docker image) has not been ported. Avoid mixing distros inside a single workspace; the binary interfaces of `rcl`, `rclcpp`, and message packages are not stable across distros.

The official EOL schedule lives at [docs.ros.org/en/rolling/Releases.html](https://docs.ros.org/en/rolling/Releases.html) - sanity-check the dates above against that page when planning a multi-year deployment.

### What's in this section

* [Setup](setup.md) - installing ROS 2 on Ubuntu 22.04 / 24.04, colcon workspaces, overlays, and the Docker route.
* [DDS and QoS](dds-qos.md) - the part of ROS 2 that bites you first. RMW implementations, QoS profile components, compatibility rules, and tuning for real bandwidth.
* [Lifecycle and Composition](lifecycle-and-composition.md) - managed nodes for deterministic bringup, composable nodes for intra-process zero-copy.
* [Nav2 Deep Dive](nav2-deep-dive.md) - the modern navigation stack: bt\_navigator, controller\_server (DWB / MPPI / RPP), planners (Smac, NavFn), behavior trees, costmap layers, collision monitor, tuning.
* [MoveIt 2](moveit2.md) - manipulation: move\_group, OMPL, Pilz, ros2\_control integration, and when MoveIt is actually the right tool.
* [micro-ROS](micro-ros.md) - running real DDS on STM32 / ESP32 / RP2040 over DDS-XRCE.
* [Visualization](visualization.md) - rviz2, Foxglove, [Lichtblick](visualization.md#lichtblick), PlotJuggler, and the rqt family.

### Related reading

* [Polka](../authors-projects/polka.md) - my mobile platform running Humble + Jazzy side by side.
* [SLAM and State Estimation → LiDAR SLAM](../slam-and-state-estimation/lidar-slam.md) - the perception layer most ROS 2 navigation stacks rely on.
* [Optimization libraries](../mathematical-and-programming-foundations/optimization-libraries.md) - the math underneath MPPI, Smac, MoveIt, and most modern planners.
* [Legacy ROS 1](../ros-advanced/ros-1/README.md) - kept for archaeology only; do not start new projects there.

### How to read this section

These pages assume you already know what a topic, service, and action are at the conceptual level. If you don't, the official docs at [docs.ros.org/en/jazzy/Tutorials.html](https://docs.ros.org/en/jazzy/Tutorials.html) are the right starting point. What I cover here is the layer above the tutorials - the design decisions and production gotchas that the docs assume you'll learn the hard way.

I lean on production examples from my own work where they add signal. If you spot something that drifts out of date as new distros land, the GitHub history of this handbook is the source of truth.
