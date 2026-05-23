---
icon: gear
---

# Lifecycle and Composition

Two ROS 2 features that ROS 1 never really had, and that you will reach for the first time you have to make a multi-node bringup behave deterministically or shave latency off a perception pipeline. They are independent — you can have lifecycle nodes that aren't composed, and composable nodes that aren't lifecycle — but they pair extremely well.

## Lifecycle nodes (managed nodes)

A regular ROS 2 node starts when its process starts and stops when the process exits. There is no defined "ready" state. If node A publishes a topic that node B needs, and B happens to come up first, B silently misses the early messages.

A lifecycle node makes the state explicit. The node is created in `Unconfigured`, transitions through `Inactive` and `Active`, and can be cleanly torn down. An external "manager" (or a launch file) drives the transitions, so you can guarantee that every dependency is `Active` before downstream nodes start consuming.

### State machine

The states defined in [ROS Enhancement Proposal 2007](https://design.ros2.org/articles/node_lifecycle.html) \[verify]:

```
                  ┌─────────────────┐
                  │  Unconfigured   │  ← initial state after create
                  └────────┬────────┘
                           │ configure
                           ▼
                  ┌─────────────────┐
                  │    Inactive     │
                  └────────┬────────┘
                           │ activate
                           ▼
                  ┌─────────────────┐
                  │     Active      │  ← producing/consuming data
                  └────────┬────────┘
                           │ deactivate, cleanup, shutdown
                           ▼
                  ┌─────────────────┐
                  │    Finalized    │
                  └─────────────────┘
```

Plus four transient states (`Configuring`, `Activating`, `Deactivating`, `CleaningUp`, `ShuttingDown`, `ErrorProcessing`) that you implement callbacks for.

The callbacks you actually write:

| Callback         | Triggered by         | Use it for                                                  |
| ---------------- | -------------------- | ----------------------------------------------------------- |
| `on_configure`   | `configure` transition | Read parameters, create publishers/subscribers, allocate resources |
| `on_activate`    | `activate` transition  | Enable publishers (`->on_activate()`), start timers         |
| `on_deactivate`  | `deactivate` transition | Disable publishers, stop timers                            |
| `on_cleanup`     | `cleanup` transition  | Free resources you created in `on_configure`                |
| `on_shutdown`    | `shutdown` transition | Final cleanup before process exit                           |
| `on_error`       | Any callback failure  | Recover or transition to `Finalized`                        |

Each callback returns one of `SUCCESS`, `FAILURE`, or `ERROR`. `SUCCESS` proceeds to the next state. `FAILURE` returns to the previous state. `ERROR` triggers `on_error`.

### When to use lifecycle

Pretty much any production node benefits from lifecycle. Concretely:

* **Deterministic bringup order** — you want the IMU calibrated and publishing before EKF starts consuming.
* **Hot reconfig** — `deactivate`, change parameters, `activate` again without restarting the process.
* **Graceful shutdown** — `deactivate` lets you stop publishing without destroying state, useful for a "park the robot, don't crash" workflow.
* **Health management** — a watchdog can transition broken nodes through `cleanup` → `configure` → `activate` to restart them in-process.

Where lifecycle is overkill: throwaway scripts, simple bridge nodes, perception nodes you'll restart with `kill -9` if they break. Use your judgment.

### Python lifecycle node

```python
# my_pkg/lifecycle_talker.py
import rclpy
from rclpy.lifecycle import Node, State, TransitionCallbackReturn
from rclpy.lifecycle import Publisher
from rclpy.timer import Timer
from std_msgs.msg import String


class LifecycleTalker(Node):
    def __init__(self):
        super().__init__('lifecycle_talker')
        self._pub: Publisher | None = None
        self._timer: Timer | None = None
        self._count = 0

    def on_configure(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info('Configuring...')
        self.declare_parameter('rate_hz', 1.0)
        self._pub = self.create_lifecycle_publisher(String, '/chatter', 10)
        return TransitionCallbackReturn.SUCCESS

    def on_activate(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info('Activating...')
        rate = self.get_parameter('rate_hz').value
        self._timer = self.create_timer(1.0 / rate, self._tick)
        return super().on_activate(state)  # activates lifecycle publishers

    def on_deactivate(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info('Deactivating...')
        if self._timer is not None:
            self.destroy_timer(self._timer)
            self._timer = None
        return super().on_deactivate(state)

    def on_cleanup(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info('Cleaning up...')
        if self._pub is not None:
            self.destroy_publisher(self._pub)
            self._pub = None
        return TransitionCallbackReturn.SUCCESS

    def on_shutdown(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info('Shutting down...')
        return TransitionCallbackReturn.SUCCESS

    def _tick(self):
        if self._pub is None:
            return
        msg = String(data=f'hello {self._count}')
        self._pub.publish(msg)
        self._count += 1


def main():
    rclpy.init()
    node = LifecycleTalker()
    rclpy.spin(node)
    rclpy.shutdown()
```

Drive the transitions from the CLI:

```bash
ros2 lifecycle list /lifecycle_talker            # list available transitions
ros2 lifecycle set /lifecycle_talker configure   # Unconfigured → Inactive
ros2 lifecycle set /lifecycle_talker activate    # Inactive → Active
ros2 lifecycle get /lifecycle_talker             # show current state
```

### C++ lifecycle node

```cpp
// my_pkg/src/lifecycle_talker.cpp
#include <rclcpp/rclcpp.hpp>
#include <rclcpp_lifecycle/lifecycle_node.hpp>
#include <std_msgs/msg/string.hpp>

using rclcpp_lifecycle::LifecycleNode;
using rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface;
using CallbackReturn = LifecycleNodeInterface::CallbackReturn;

class LifecycleTalker : public LifecycleNode {
public:
    LifecycleTalker() : LifecycleNode("lifecycle_talker") {}

    CallbackReturn on_configure(const rclcpp_lifecycle::State&) override {
        RCLCPP_INFO(get_logger(), "Configuring...");
        declare_parameter("rate_hz", 1.0);
        pub_ = create_publisher<std_msgs::msg::String>("/chatter", 10);
        return CallbackReturn::SUCCESS;
    }

    CallbackReturn on_activate(const rclcpp_lifecycle::State& state) override {
        RCLCPP_INFO(get_logger(), "Activating...");
        LifecycleNode::on_activate(state);  // activates lifecycle publishers
        const double rate = get_parameter("rate_hz").as_double();
        const auto period = std::chrono::duration<double>(1.0 / rate);
        timer_ = create_wall_timer(period, [this] { tick(); });
        return CallbackReturn::SUCCESS;
    }

    CallbackReturn on_deactivate(const rclcpp_lifecycle::State& state) override {
        RCLCPP_INFO(get_logger(), "Deactivating...");
        timer_.reset();
        LifecycleNode::on_deactivate(state);
        return CallbackReturn::SUCCESS;
    }

    CallbackReturn on_cleanup(const rclcpp_lifecycle::State&) override {
        RCLCPP_INFO(get_logger(), "Cleaning up...");
        pub_.reset();
        return CallbackReturn::SUCCESS;
    }

private:
    void tick() {
        auto msg = std_msgs::msg::String();
        msg.data = "hello " + std::to_string(count_++);
        pub_->publish(msg);
    }

    rclcpp_lifecycle::LifecyclePublisher<std_msgs::msg::String>::SharedPtr pub_;
    rclcpp::TimerBase::SharedPtr timer_;
    size_t count_{0};
};

int main(int argc, char** argv) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<LifecycleTalker>()->get_node_base_interface());
    rclcpp::shutdown();
    return 0;
}
```

### Launch-driven activation

You almost never drive transitions manually in production — you wire up a launch file. The `nav2_lifecycle_manager` is the canonical example; it activates a list of nodes in order, with retries:

```python
from launch import LaunchDescription
from launch_ros.actions import Node, LifecycleNode
from launch.actions import EmitEvent, RegisterEventHandler
from launch_ros.events.lifecycle import ChangeState
from launch_ros.event_handlers import OnStateTransition
import lifecycle_msgs.msg


def generate_launch_description():
    talker = LifecycleNode(
        package='my_pkg',
        executable='lifecycle_talker',
        name='lifecycle_talker',
        namespace='',
    )

    configure_event = EmitEvent(
        event=ChangeState(
            lifecycle_node_matcher=lambda action: action == talker,
            transition_id=lifecycle_msgs.msg.Transition.TRANSITION_CONFIGURE,
        )
    )

    activate_on_inactive = RegisterEventHandler(
        OnStateTransition(
            target_lifecycle_node=talker,
            goal_state='inactive',
            entities=[EmitEvent(
                event=ChangeState(
                    lifecycle_node_matcher=lambda action: action == talker,
                    transition_id=lifecycle_msgs.msg.Transition.TRANSITION_ACTIVATE,
                )
            )],
        )
    )

    return LaunchDescription([talker, configure_event, activate_on_inactive])
```

For real bringup with multiple nodes, use the `nav2_lifecycle_manager` node — it takes a list of node names and walks them through transitions for you. Source: [github.com/ros-navigation/navigation2/tree/main/nav2\_lifecycle\_manager](https://github.com/ros-navigation/navigation2/tree/main/nav2_lifecycle_manager) \[verify].

## Composable nodes (component containers)

Lifecycle is about *when* a node runs. Composition is about *where* it runs.

A regular ROS 2 node is one process per node. Two nodes on the same machine talking via DDS still serialize messages, hand them to the kernel, copy them across loopback, and deserialize on the other side. For a 4K camera image, that round trip is real CPU.

A **composable node** is a node compiled as a shared library and loaded into a **component container** process at runtime. Multiple composable nodes in the same container share an address space — and when both endpoints opt in, ROS 2 uses **intra-process communication**: the publisher and subscriber pass a `shared_ptr` to the message instead of serializing. Zero-copy, single-digit microseconds.

### When composition pays off

* **Image / point cloud pipelines** — camera driver, rectification, debayer, perception network. Each stage hands a multi-megabyte message to the next. Intra-process is a 10–100x latency win.
* **Nav2 stack** — costmap, planner, controller all benefit. Nav2 ships a composable layout out of the box.
* **Any chain of small nodes that all run on the same robot.**

When composition doesn't help: nodes on different machines (still DDS), nodes that publish at low rates (overhead is irrelevant), or when you want process isolation for safety reasons (a crash in one composed node kills the container).

### Writing a composable node — C++

The class is just a regular `rclcpp::Node` (or `LifecycleNode`) with two extras: a `NodeOptions`-taking constructor and an `RCLCPP_COMPONENTS_REGISTER_NODE` macro.

```cpp
// my_pkg/src/image_filter_component.cpp
#include <rclcpp/rclcpp.hpp>
#include <rclcpp_components/register_node_macro.hpp>
#include <sensor_msgs/msg/image.hpp>

namespace my_pkg {

class ImageFilter : public rclcpp::Node {
public:
    explicit ImageFilter(const rclcpp::NodeOptions& options)
        : Node("image_filter", options)
    {
        sub_ = create_subscription<sensor_msgs::msg::Image>(
            "image_raw", rclcpp::SensorDataQoS(),
            [this](sensor_msgs::msg::Image::UniquePtr msg) {
                // Process in-place; with intra-process this is zero-copy
                pub_->publish(std::move(msg));
            });
        pub_ = create_publisher<sensor_msgs::msg::Image>(
            "image_filtered", rclcpp::SensorDataQoS());
    }

private:
    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr sub_;
    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr pub_;
};

}  // namespace my_pkg

RCLCPP_COMPONENTS_REGISTER_NODE(my_pkg::ImageFilter)
```

`CMakeLists.txt` builds it as a shared library and registers it as a component:

```cmake
find_package(rclcpp_components REQUIRED)

add_library(image_filter_component SHARED src/image_filter_component.cpp)
target_compile_definitions(image_filter_component PRIVATE COMPOSITION_BUILDING_DLL)
ament_target_dependencies(image_filter_component rclcpp rclcpp_components sensor_msgs)

rclcpp_components_register_nodes(image_filter_component "my_pkg::ImageFilter")

install(TARGETS image_filter_component
        ARCHIVE DESTINATION lib
        LIBRARY DESTINATION lib
        RUNTIME DESTINATION bin)
```

Load it into a container:

```bash
# Terminal 1: start a container
ros2 run rclcpp_components component_container

# Terminal 2: load the node
ros2 component load /ComponentManager my_pkg my_pkg::ImageFilter
```

### Loading multiple components from a launch file

This is how you actually use it in production:

```python
from launch import LaunchDescription
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode


def generate_launch_description():
    container = ComposableNodeContainer(
        name='perception_container',
        namespace='',
        package='rclcpp_components',
        executable='component_container_mt',  # multi-threaded container
        composable_node_descriptions=[
            ComposableNode(
                package='my_pkg',
                plugin='my_pkg::CameraDriver',
                name='camera_driver',
                extra_arguments=[{'use_intra_process_comms': True}],
            ),
            ComposableNode(
                package='my_pkg',
                plugin='my_pkg::ImageFilter',
                name='image_filter',
                extra_arguments=[{'use_intra_process_comms': True}],
            ),
            ComposableNode(
                package='my_pkg',
                plugin='my_pkg::ObjectDetector',
                name='object_detector',
                extra_arguments=[{'use_intra_process_comms': True}],
            ),
        ],
        output='screen',
    )
    return LaunchDescription([container])
```

The key flag is `use_intra_process_comms: True`. Without it the container still uses DDS between nodes in the same process — the address space sharing is wasted.

### Multi-threaded vs single-threaded containers

* `component_container` — one executor thread for the whole container. Callbacks serialize. Fine for low-rate or strictly-ordered work.
* `component_container_mt` — multi-threaded executor. Callbacks can run in parallel. What you want for a perception pipeline where you don't care about strict ordering between sensors.

Within a container, you can still control parallelism with callback groups (`MutuallyExclusive` vs `Reentrant`) on individual subscriptions.

### Intra-process zero-copy — the catch

The publisher must hand off a `unique_ptr` to a message, and the subscriber must take a `unique_ptr` (or `shared_ptr`). If either side copies, you lose the optimization. The signature in the example above:

```cpp
[this](sensor_msgs::msg::Image::UniquePtr msg) { ... }
```

is critical. If you switched to `const sensor_msgs::msg::Image::SharedPtr& msg`, you'd silently fall back to a copy.

Python composable nodes exist but the zero-copy story is weaker — Python objects have to round-trip through `pybind11`. For performance pipelines, write components in C++. Python is fine for orchestration nodes that don't move large data.

## Pattern: lifecycle + composition together

The combination is what Nav2 uses. Every Nav2 component (planner, controller, BT navigator, costmaps) is both a `LifecycleNode` and a `ComposableNode`. They are loaded into a single container, sequenced through configure → activate by `nav2_lifecycle_manager`, and exchange costmaps and paths intra-process.

The result: a multi-megabyte costmap moves from `costmap_2d` to `planner_server` to `controller_server` without ever being serialized. On a Jetson, that's the difference between holding 20 Hz control and dropping to 5.

## Production note — Lichtblick

At 10xConstruction.ai I worked on [Lichtblick](visualization.md#lichtblick), our fork of Foxglove. The 78% peak CPU reduction we shipped (120% → 26% vs upstream Foxglove) was a UI-side win, not a ROS one. But the *pattern* of composable nodes — keep related work in one process, use intra-process for the heavy data path, run the lifecycle layer underneath — is exactly how the rest of that robot's stack was built. Composable + lifecycle is the modern ROS 2 default for anything that has to actually run on a robot.

I have also used custom BT nodes in Nav2's `bt_navigator` (a composable lifecycle node itself) to gate behaviors on collision-monitor state — covered in [Nav2 Deep Dive](nav2-deep-dive.md).

## Pitfalls

* **Forgetting to call `LifecycleNode::on_activate(state)` from your override** — your lifecycle publishers stay inactive and silently drop messages.
* **Mixing intra-process and inter-process subscribers on the same topic** — works, but the intra-process optimization is disabled. Either commit fully or split topics.
* **`use_intra_process_comms` not set on every component** — needs to be on both publisher and subscriber.
* **Container crash kills every component** — useful for tight integration, painful for fault isolation. Don't bundle critical safety nodes (estop, watchdog) into the perception container.
* **Lifecycle state confusion in tests** — your test rig is `Unconfigured` by default. Either drive transitions in `setUp`, or override the constructor for test-only nodes that skip lifecycle. The `ros2_testing` skill in this repo has the pattern.

## Where to go next

* [Nav2 Deep Dive](nav2-deep-dive.md) — sees both features in production action.
* [Visualization → Lichtblick](visualization.md#lichtblick) — the project where the composition pattern paid off most.
* [DDS and QoS](dds-qos.md) — once you've cut intra-process traffic, the remaining inter-process traffic is what you tune next.
