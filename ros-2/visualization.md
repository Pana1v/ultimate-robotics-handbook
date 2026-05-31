---
icon: gear
---

# Visualization

Visualization in ROS 2 is the difference between "the robot is broken" and "the lidar driver is publishing zeros." You will spend more time staring at rviz2, Foxglove, and PlotJuggler than at logs. This page is my opinionated tour - which tool to reach for, when each one earns its keep, and where I have spent real production engineering effort.

The tools I'll cover:

* **rviz2** - 3D scene visualizer. The workhorse.
* **Foxglove Studio** - browser-based, MCAP-native, license changed in 2024.
* **Lichtblick** - fork of Foxglove I've contributed to; significantly cheaper on CPU, MoveIt 2 / Android support.
* **PlotJuggler** - time-series plotting and analysis. I am a contributor.
* **rqt\_* family** - graph, plot, console, parameter editor, image view.

## rviz2

Successor to ROS 1's rviz. Same shape (a 3D scene with pluggable display panels), rebuilt on Qt 5/6 and OpenGL, sourced as ROS 2 packages.

The repo: [github.com/ros2/rviz](https://github.com/ros2/rviz). Ships as `ros-jazzy-rviz2` (or your distro).

### What rviz2 is good at

* **3D scene** - TF tree, URDF, point clouds, occupancy grids, marker arrays. Rendering is fast enough to view a multi-million-point cloud at 30+ Hz on a modern GPU.
* **Native ROS integration** - you point it at a topic, pick the message type, and you see the data. No extra serialization.
* **Display plugins** - write your own in C++ if you need to visualize a custom message type. Pretty mature API.
* **Localhost first** - rviz2 talks DDS directly. No bridge, no JSON.

### What rviz2 is bad at

* **Remote viewing** - rviz2 over X11 forwarding is painful; rviz2 connected to a remote robot via DDS works but is bandwidth-heavy. You're sending serialized point clouds over Wi-Fi. This is where Foxglove / Lichtblick win.
* **Time-series plots** - `rviz_default_plugins` has some chart-like displays but they are awful. Use PlotJuggler.
* **Recording / replay UX** - you record with `ros2 bag`, replay with `ros2 bag play`, and rviz2 just sees the topics. No built-in seek bar or annotation layer.
* **Browser access** - there's no web-based rviz2 (there were experimental versions, none mainline). For browser viewing, Foxglove / Lichtblick.

### Useful rviz2 workflow tips

* **Save configs**: `File → Save Config As`. Per-launch rviz config files in your `bringup` package mean you don't reconfigure every time.

  ```python
  Node(
      package='rviz2',
      executable='rviz2',
      arguments=['-d', os.path.join(pkg_share, 'rviz', 'nav2.rviz')],
  )
  ```

* **TF debugging**: enable the TF display, then enable "Show Names" and "Show Axes." If a frame is grayed out you don't have a transform.

* **Fixed frame trap**: rviz2 shows everything relative to "Fixed Frame." If `map` is your fixed frame but you haven't built one yet, every display is broken until you switch to `odom` or `base_link`.

* **Point cloud QoS**: rviz2 defaults to RELIABLE for most topics. If your camera publishes `BEST_EFFORT` (most do), set the display's QoS to match - otherwise it silently shows nothing. The display's properties panel has a QoS dropdown.

## Foxglove Studio

[Foxglove Studio](https://foxglove.dev) is an Electron/web app for visualizing robotics data. It started as a modern alternative to rviz with a focus on remote viewing and bag analysis.

### Why teams reach for it

* **Web-native** - runs in the browser. Connect to a robot over WebSocket bridge (`foxglove_bridge`), no X11.
* **MCAP-native** - Foxglove is the company behind [MCAP](https://mcap.dev), a modern bag format that supplanted `.bag`/`.db3` for many teams.
* **Layouts** - multi-panel layouts (3D, plot, image, raw, log) that you can save and share.
* **TypeScript extensions** - you write panels in TypeScript, not C++. Way faster iteration than rviz2 plugins.

### The license change

In 2024, Foxglove relicensed Studio under the **Business Source License (BUSL-1.1)** \[verify]. Practically, this means:

* The source is still on GitHub, you can still build it.
* Commercial use *as a product* (selling Foxglove-derived tools) requires a paid license.
* Internal use by an end-user robotics team is generally fine, but read the terms carefully if you're a vendor.

The license change triggered several forks, including Lichtblick.

### Connection patterns

Two ways Foxglove (or Lichtblick) talks to a robot:

| Mode               | What it is                              | When to use                          |
| ------------------ | --------------------------------------- | ------------------------------------ |
| **Foxglove WebSocket** | A node (`foxglove_bridge`) running on the robot that exposes topics over WebSocket. | Live viewing.                        |
| **MCAP file**       | Pre-recorded bag file                   | Offline analysis, debugging post-incident. |
| **Rosbridge (legacy)** | The older JSON-over-WebSocket bridge | Compatibility only; foxglove\_bridge is leaner. |

`foxglove_bridge` is a single node:

```bash
ros2 run foxglove_bridge foxglove_bridge --ros-args -p port:=8765
```

Then in the browser app, "Open Connection → Foxglove WebSocket → ws\://robot.local:8765".

## Lichtblick

A fork of Foxglove Studio I've contributed to. The original Foxglove had three problems for our use case:

1. **Heavy CPU usage** when rendering live data, which would steal cycles from the perception pipeline on the same machine.
2. **No mobile / Android support** - our operators wanted to monitor robots from tablets.
3. **MoveIt 2 visualization** was awkward - no first-class planning-scene panel.

Lichtblick exists to fix these. The repo: [github.com/Lichtblick-Suite/lichtblick](https://github.com/Lichtblick-Suite/lichtblick). License is Apache 2.0.

### What I worked on

Headline results from my work:

* **Peak CPU usage cut by 78%** - from 120% on a single core down to 26% on the same workload (rendering a live robot view with point clouds, costmaps, BT visualization, and several plots). The wins came from a combination of:
  * Throttling render passes to actual display refresh.
  * Reusing GPU resources across frame updates instead of reallocating.
  * A smarter dirty-rectangle approach for plot panels.
  * Coalescing redundant tree-update events from the BT view.

* **MoveIt 2 support for Android** - a planning scene panel and trajectory preview that works on tablet form factors. The challenge wasn't the renderer (Three.js is fine on mobile GPUs) but the touch interaction model - selecting a link, dragging a goal pose, scrubbing through a trajectory all needed redesign.

* **Custom TypeScript / ROS 2 interface** - extension API for our domain-specific panels (machine state, jobsite map, operator approvals).

Both efforts paid for themselves quickly: operators stopped complaining about laggy UIs, and the perception team got their CPU budget back.

### When to use Lichtblick vs Foxglove

* **Use Lichtblick** when you care about CPU on the device running the UI (laptops in the field, tablets), when you want Apache 2.0 licensing, or when you need the MoveIt 2 / mobile panels.
* **Use Foxglove** when you're already paying for it, when you want the official cloud platform integration, or when you need a feature that hasn't landed in the fork yet.

Both speak the same `foxglove_bridge` protocol, so switching is a same-day operation.

## PlotJuggler

[PlotJuggler](https://github.com/facontidavide/PlotJuggler) is the time-series plotting tool in ROS 2. Authored by Davide Faconti; I have contributed upstream as well.

If you have ever tried to plot a topic in rviz2's "Plot" panel and given up: PlotJuggler is the alternative. It is purpose-built for the "I want to see how this number changes over time, alongside three other numbers, with annotations" workflow that you do constantly.

### What PlotJuggler is good at

* **Drag-and-drop** - drag a topic onto the canvas, get a plot. Drag another, drop onto the same plot, get an overlay.
* **Live and replay** - `ros2 bag play` straight into PlotJuggler; play with the scrub bar; mark events.
* **Math channels** - define `error = setpoint - measured` directly in the UI. Differentiation, integration, FFT all built-in.
* **Layouts** - save the layout of plots, panels, and math channels. Re-open with one click.
* **Cross-bag comparison** - load two bags side by side. Genuinely useful for "was the controller better last week?"

The single thing it does not do is 3D - for that, rviz2 / Foxglove. The two tools complement each other.

### Typical workflow

```bash
# Install
sudo apt install ros-jazzy-plotjuggler ros-jazzy-plotjuggler-ros

# Run
ros2 run plotjuggler plotjuggler
```

Then `Streaming → Start ROS Topic Subscriber`, pick the topics you care about, and drag.

For replay:

```bash
ros2 bag play my_bag.mcap
ros2 run plotjuggler plotjuggler
```

PlotJuggler subscribes to whatever the bag is republishing.

## rqt\_* family

Old guard from ROS 1, ported to ROS 2 with minor changes. Still useful for specific tasks.

| Tool             | What it does                                       | Use it when                              |
| ---------------- | -------------------------------------------------- | ---------------------------------------- |
| `rqt_graph`      | Visualizes the node + topic graph                  | Debugging "who is publishing what"       |
| `rqt_console`    | Filterable log viewer                              | Reading logs across many nodes           |
| `rqt_reconfigure` | Live parameter editor                             | Tuning gains, thresholds at runtime      |
| `rqt_plot`       | Basic plotting                                     | Almost never - use PlotJuggler           |
| `rqt_image_view` | Camera image viewer                                | Verifying a camera is publishing         |
| `rqt_bag`        | Bag file inspector                                 | Mostly replaced by Foxglove for analysis |
| `rqt_tf_tree`    | TF tree viewer                                     | Visualizing parent → child relationships |
| `rqt_topic`      | Topic monitor with rates                           | Quick "is this topic alive" check        |

Run any of them with `ros2 run rqt_* rqt_*`. They all run in a unified `rqt` shell too: `ros2 run rqt_gui rqt_gui`, then add plugins from the menu.

### `rqt_graph`

Underrated. When you join a new project and want to understand the wiring, this is the first command I run. Pick "Nodes/Topics (active)" from the dropdown, hide the TF noise, and you have a system diagram.

### `rqt_reconfigure`

For nodes that declare their parameters with `descriptor` set up correctly, this gives you sliders and dropdowns. Useful for tuning controller gains live without restarting nodes. Less useful for nodes that just use raw `declare_parameter` without descriptors.

## Tool selection - the cheat sheet

| Task                                       | Reach for                                |
| ------------------------------------------ | ---------------------------------------- |
| 3D scene of robot + map + sensors           | rviz2                                    |
| 3D scene from a tablet or laptop in the field | Lichtblick (or Foxglove)               |
| Time-series of any numeric topic           | PlotJuggler                              |
| Quick "is this camera alive" check         | `rqt_image_view`                         |
| Live parameter tuning                      | `rqt_reconfigure`                        |
| Filtered log viewer                        | `rqt_console`                            |
| Topology of the node graph                 | `rqt_graph`                              |
| Replay analysis of a bag                   | Foxglove / Lichtblick + PlotJuggler      |
| Custom domain-specific panels              | Lichtblick (TypeScript) or rviz2 plugin (C++) |
| Post-incident video for stakeholders       | Lichtblick screen recording from bag     |

## Production lessons

A few things I've learned the hard way:

* **Save your rviz2 configs to version control.** A `.rviz` file is plain XML. Check it in. Otherwise everyone reinvents the layout daily.

* **Avoid running rviz2 on the robot's main compute.** It steals cycles from your perception pipeline. Run a `foxglove_bridge` on the robot and view from a separate machine.

* **Throttle high-rate topics in the visualizer.** A 60 FPS render is plenty; subscribing to a 200 Hz IMU and rendering every sample is a waste. Foxglove / Lichtblick handle this automatically; rviz2 doesn't.

* **Per-topic QoS in the visualizer.** Almost every "I don't see anything" report I've debugged has been a QoS mismatch - usually a sensor publisher on `BEST_EFFORT` and rviz2 subscribing on `RELIABLE`.

* **Record before you debug.** If you're chasing an intermittent bug, run `ros2 bag record` as a systemd service. Cheap; saves you the next time it reproduces.

* **MCAP over db3.** ROS 2's default bag format is SQLite (`.db3`). MCAP is faster, more compact, and natively supported by every modern tool. `ros2 bag record --storage mcap ...`.

## Where to go next

* [Setup](setup.md) - installing the visualization tools alongside the rest of the distro.
* [DDS and QoS](dds-qos.md) - the source of most "I see no data" symptoms.
* [Nav2 Deep Dive](nav2-deep-dive.md) - the stack I usually visualize with this tooling.
* [Polka](../authors-projects/polka.md) - my own platform, used as the canvas for most of this work.
* [Lichtblick on GitHub](https://github.com/Lichtblick-Suite/lichtblick) - if you want to read the actual CPU-reduction commits.
* [PlotJuggler on GitHub](https://github.com/facontidavide/PlotJuggler) - Davide's repo, where I contribute.
