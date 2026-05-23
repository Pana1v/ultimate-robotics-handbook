---
icon: code
---

# Modern C++ for Robotics

C++ is still the language you reach for when latency matters, when you need deterministic timing, or when you're talking to hardware. ROS 2 itself is C++ underneath — `rclpy` is a binding over `rcl`, which is C, which calls into `rcl_cpp` infrastructure for the heavy lifting. If you want to write a node that runs the control loop at 1 kHz without missing a beat, you write it in C++.

This page is the C++ I actually use in production robotics work, not the textbook tour. If you want the textbook, read Stroustrup. If you want to ship a robot, read this.

## C++17/20 features that actually matter

You should be on C++17 minimum. C++20 if your toolchain supports it (Humble defaults to C++17, Jazzy to C++17 but works fine with C++20 set in CMake). Here's what I use daily.

### Smart pointers — never `new`, almost never `delete`

```cpp
#include <memory>

// shared_ptr — ROS 2 uses these everywhere for nodes, publishers, subscribers
auto node = std::make_shared<rclcpp::Node>("my_node");

// unique_ptr — single-owner, zero overhead vs raw pointer
auto controller = std::make_unique<MotionController>(node);

// Pass by reference unless you need ownership semantics
void process(const PointCloud& cloud);  // GOOD
void process(std::shared_ptr<PointCloud> cloud);  // only if you store it
```

Rule of thumb: `unique_ptr` by default, `shared_ptr` when ROS 2 forces you (callbacks, lifecycle), raw pointer only as a non-owning observer that cannot outlive the owner.

### `std::optional` — say "maybe" without sentinel values

```cpp
#include <optional>

std::optional<Pose> lookup_transform(const std::string& target,
                                     const std::string& source) {
    try {
        auto tf = tf_buffer_->lookupTransform(target, source, tf2::TimePointZero);
        return tf_to_pose(tf);
    } catch (const tf2::TransformException& e) {
        return std::nullopt;  // No magic numbers, no out-params
    }
}

// At the call site:
if (auto pose = lookup_transform("map", "base_link")) {
    process(*pose);  // unwrap with * or ->
}
```

Stop returning `-1` or `(0,0,0)` to signal "no data." Use `std::optional`.

### `std::variant` — tagged unions done right

```cpp
#include <variant>

using SensorReading = std::variant<LaserScan, PointCloud2, Image>;

void handle(const SensorReading& reading) {
    std::visit([](const auto& msg) {
        using T = std::decay_t<decltype(msg)>;
        if constexpr (std::is_same_v<T, LaserScan>) {
            process_scan(msg);
        } else if constexpr (std::is_same_v<T, PointCloud2>) {
            process_cloud(msg);
        }
    }, reading);
}
```

Great for state machines, sensor fusion pipelines that handle heterogeneous data, and replacing inheritance hierarchies where you actually know the closed set of types.

### Structured bindings — unpack everything

```cpp
// Before C++17
auto result = compute_pose();
double x = std::get<0>(result);
double y = std::get<1>(result);

// C++17
auto [x, y, theta] = compute_pose();

// Range-based for over maps
for (const auto& [frame_id, transform] : transform_cache_) {
    publish(frame_id, transform);
}
```

### Concepts (C++20) — type constraints that don't hurt

```cpp
#include <concepts>

template <typename T>
concept FloatingPoint = std::floating_point<T>;

template <FloatingPoint T>
T wrap_angle(T angle) {
    while (angle > M_PI) angle -= 2 * M_PI;
    while (angle < -M_PI) angle += 2 * M_PI;
    return angle;
}
```

Error messages become readable. Template metaprogramming becomes legible.

### Ranges (C++20) — pipeline-style algorithms

```cpp
#include <ranges>
#include <algorithm>

// Get IDs of all valid detections within 5 meters
auto close_ids = detections
    | std::views::filter([](const auto& d) { return d.valid; })
    | std::views::filter([](const auto& d) { return d.distance < 5.0; })
    | std::views::transform([](const auto& d) { return d.id; });
```

Caveat: GCC's ranges implementation was rough before 11.2. On Humble (Ubuntu 22.04, GCC 11.4) you're fine. On older Iron deployments, check first.

## Eigen — your linear algebra workhorse

Eigen is header-only, expression-template-based, and almost certainly already in your dependency graph (tf2, OpenCV, PCL all use it). Learn it well. Docs: <https://eigen.tuxfamily.org/dox/>

### Fixed-size vs dynamic-size

```cpp
#include <Eigen/Dense>

// Fixed-size — stack-allocated, no heap, vectorized, FAST
Eigen::Vector3d position(1.0, 2.0, 3.0);     // 3-vector of doubles
Eigen::Matrix4d transform = Eigen::Matrix4d::Identity();  // 4x4 homogeneous

// Dynamic-size — heap-allocated, use when dimensions only known at runtime
Eigen::MatrixXd jacobian(rows, cols);
Eigen::VectorXd state(n_states);
```

**Rule:** if the size is known at compile time and is small (≤ 16 elements), use the fixed-size version. Always. The compiler can unroll loops, the data sits on the stack, no allocation in your hot loop.

### Expression templates — don't fight them

```cpp
// This does NOT compute three intermediate matrices.
// Eigen builds an expression tree and evaluates once into result.
Eigen::Matrix3d result = A * B + C * D - E;

// But beware: auto + Eigen = pain
auto bad = A * B;  // bad is an expression, NOT a matrix
// If A or B goes out of scope, bad becomes a dangling reference

Eigen::Matrix3d good = A * B;  // forces evaluation
```

The `auto` pitfall is real and has bitten me more than once. When in doubt, write the explicit type.

### Common pitfalls

```cpp
// 1. Alignment with fixed-size Eigen types in std::vector
// WRONG (pre-C++17, or with allocators not aware of alignment):
std::vector<Eigen::Matrix4d> poses;

// RIGHT (the Eigen-provided allocator):
std::vector<Eigen::Matrix4d, Eigen::aligned_allocator<Eigen::Matrix4d>> poses;

// In C++17, std::vector handles over-aligned types correctly if you use
// the default allocator AND compile with proper alignment support.
// I still use aligned_allocator out of paranoia.

// 2. Don't pass Eigen by value if it's dynamic-size
void process(Eigen::MatrixXd m);          // copies! allocates!
void process(const Eigen::MatrixXd& m);   // good
void process(const Eigen::Ref<const Eigen::MatrixXd>& m);  // best, accepts blocks too

// 3. Don't mix row-major and column-major silently
// Eigen is column-major by default. ROS messages often imply row-major.
// If you copy a raw buffer in, make sure layouts match.
```

See: <https://eigen.tuxfamily.org/dox/group__TopicPitfalls.html> [verify]

## Real-time considerations

If your code runs in a 1 kHz control loop, these are non-negotiable.

### No allocation in the hot path

Heap allocation is non-deterministic. `malloc` can block, defragment, page-fault. Pre-allocate everything outside the hot loop.

```cpp
class ControlLoop {
public:
    ControlLoop(size_t buffer_size) {
        // Reserve in constructor, NEVER in the loop
        recent_errors_.reserve(buffer_size);
        scratch_jacobian_.resize(6, 6);  // also pre-size Eigen matrices
    }

    void step(const State& s) {  // called at 1 kHz
        // No new, no make_shared, no resize-that-grows, no push_back-past-capacity
        scratch_jacobian_.noalias() = compute_jacobian(s);  // .noalias() avoids temp
        // ...
    }

private:
    std::vector<double> recent_errors_;
    Eigen::MatrixXd scratch_jacobian_;
};
```

### Lock-free queues for inter-thread comms

`std::mutex` can cause priority inversion. For producer/consumer between a real-time thread and a non-RT thread, use a lock-free SPSC queue.

- `boost::lockfree::spsc_queue` — single-producer single-consumer, header-only Boost. <https://www.boost.org/doc/libs/release/doc/html/boost/lockfree/spsc_queue.html> [verify]
- `folly::ProducerConsumerQueue` — Meta's version, similar API. <https://github.com/facebook/folly> [verify]
- `moodycamel::ReaderWriterQueue` — another popular choice. <https://github.com/cameron314/readerwriterqueue>

```cpp
#include <boost/lockfree/spsc_queue.hpp>

// RT thread pushes, GUI thread pops
boost::lockfree::spsc_queue<TelemetryFrame, boost::lockfree::capacity<1024>> queue;

// RT thread (producer):
TelemetryFrame frame = sample();
queue.push(frame);  // lock-free, wait-free for SPSC

// GUI thread (consumer):
TelemetryFrame frame;
while (queue.pop(frame)) {
    display(frame);
}
```

### No exceptions in real-time threads

Throwing an exception walks the stack and runs destructors — bounded in theory, unbounded in practice. For RT code, prefer `std::expected` (C++23) or `tl::expected` (header-only backport), or return error codes.

Also: `noexcept` on functions in the hot path. It lets the compiler emit better code and prevents accidental exception propagation across the RT boundary.

## Cache friendliness

Modern CPUs are starving for data, not arithmetic. A cache miss to main memory is ~100 ns. A cache hit is ~1 ns. That's two orders of magnitude.

### SoA vs AoS

```cpp
// Array of Structures (AoS) — intuitive but cache-unfriendly when iterating one field
struct ParticleAoS {
    Eigen::Vector3d position;
    Eigen::Vector3d velocity;
    double mass;
};
std::vector<ParticleAoS> particles;
// Iterating just positions wastes cache: each cache line carries unused velocity+mass

// Structure of Arrays (SoA) — what particle filters and SIMD want
struct ParticlesSoA {
    std::vector<double> x, y, z;
    std::vector<double> vx, vy, vz;
    std::vector<double> mass;
};
// Iterating positions = pure sequential reads = prefetcher's dream
```

For 1000 particles in a particle filter, SoA can be 3-5x faster on the resample step. Profile before refactoring, but know the pattern.

### Contiguous data structures

```cpp
std::vector<T>      // contiguous — cache-friendly, default choice
std::array<T, N>    // stack-allocated, fixed size, same cache properties
std::deque<T>       // chunked — okay
std::list<T>        // linked — almost always wrong
std::map<K, V>      // red-black tree — bad locality
std::unordered_map  // hash table — better, but still pointer-chasing on collisions
```

### `std::vector::reserve` is not optional

```cpp
std::vector<Detection> detections;
detections.reserve(expected_count);  // one allocation
for (...) {
    detections.push_back(...);  // no reallocs, no copies
}
```

Without reserve, vector doubles its capacity on growth — fine amortized, terrible for latency in a 1 kHz loop.

## When NOT to use STL containers

This is one of those "you grow into it" things. The STL is good, but the defaults are general-purpose, not robotics-tuned.

| You're tempted to use | But you probably want | Why |
|---|---|---|
| `std::list` | `std::vector` | List has terrible cache behavior; insertion-in-middle is rarely the bottleneck |
| `std::map<K,V>` (small N) | `std::vector<std::pair<K,V>>` + linear scan | For N < ~32, linear scan in cache beats tree traversal |
| `std::map<K,V>` (large N) | `boost::container::flat_map` | Sorted vector under the hood — log N lookup, cache-friendly |
| `std::string` for tiny labels | `std::string_view` or fixed-size buffer | SSO helps, but views avoid all allocation |
| `std::unordered_map` for hot lookups | `absl::flat_hash_map` or `robin_hood::unordered_map` | Open-addressing, ~2x faster in practice |

Pan's notes folder `/home/pan-navigator/Documents/claude-config/references/cpp_optimizations/` has detailed write-ups on `boost::flatmap`, `dont_need_map`, `no_lists`, `reserve`, `small_strings`, `small_vectors`, and PCL-specific gotchas. Read them before optimizing.

## PCL gotchas

PCL (Point Cloud Library, <https://pointclouds.org/>) is necessary for most LiDAR/depth work and miserable in equal measure.

```cpp
#include <pcl/point_cloud.h>
#include <pcl/point_types.h>
#include <pcl/filters/voxel_grid.h>

using Cloud = pcl::PointCloud<pcl::PointXYZ>;
auto cloud = std::make_shared<Cloud>();

pcl::VoxelGrid<pcl::PointXYZ> voxel;
voxel.setInputCloud(cloud);
voxel.setLeafSize(0.05f, 0.05f, 0.05f);
Cloud filtered;
voxel.filter(filtered);
```

Things to watch for:

- **Compile times.** Each PCL algorithm is a template on the point type. Including `<pcl/filters/voxel_grid.h>` in a header drags the entire template definition into every translation unit. Forward-declare and put PCL includes in `.cpp` files.
- **Linker errors.** PCL precompiles instantiations for the common types (`PointXYZ`, `PointXYZRGB`, `PointXYZI`, `PointNormal`). If you use a custom point type, you'll get unresolved symbols. Either stick to the common types or define `PCL_NO_PRECOMPILE` before includes.
- **`pcl_conversions::fromROSMsg` is slow.** It does a memcpy through an intermediate format. For high-rate clouds, write a direct conversion using the cloud's raw byte buffer. Pan's notes have a `pcl_fromROS.md` write-up.
- **PCL ships its own Eigen.** Sometimes a different version than the system one. ABI mismatches happen. Always rely on the system Eigen and let PCL pick it up.

## Threading

### `std::jthread` (C++20) — RAII threads with cancellation

```cpp
#include <thread>
#include <stop_token>

void worker(std::stop_token st) {
    while (!st.stop_requested()) {
        do_work();
    }
}

// jthread auto-joins on destruction AND supports cooperative cancellation
{
    std::jthread t(worker);
    // ... do stuff ...
}  // t.request_stop() then t.join() happens here automatically
```

Use `std::jthread` over `std::thread`. The destructor calling `request_stop()` + `join()` eliminates a whole class of bugs.

### `std::atomic` for small shared state

```cpp
std::atomic<bool> emergency_stop{false};

// Producer (any thread):
emergency_stop.store(true, std::memory_order_release);

// Consumer (control loop):
if (emergency_stop.load(std::memory_order_acquire)) {
    halt();
}
```

For booleans and small POD, `std::atomic` beats `std::mutex` every time. For larger state, use a mutex or, better, a lock-free queue.

### `std::shared_mutex` — multiple readers, one writer

```cpp
std::shared_mutex map_mutex_;
OccupancyGrid map_;

// Many readers
void planner_thread() {
    std::shared_lock lock(map_mutex_);
    plan_path(map_);
}

// One writer
void slam_thread() {
    std::unique_lock lock(map_mutex_);
    update_map(map_);
}
```

Don't use this in a 1 kHz loop — the reader-writer accounting has overhead. Use it for slower paths where reads vastly outnumber writes (map, parameter cache).

## rclcpp idioms

### Composition — multiple nodes in one process

```cpp
#include <rclcpp_components/register_node_macro.hpp>

class MyNode : public rclcpp::Node {
public:
    explicit MyNode(const rclcpp::NodeOptions& options)
        : Node("my_node", options) { /* ... */ }
};

RCLCPP_COMPONENTS_REGISTER_NODE(MyNode)
```

Then load into a container via `ros2 component load /component_container my_pkg my_pkg::MyNode`. Intra-process communication becomes a pointer pass instead of serialize/deserialize. For perception pipelines passing point clouds between nodes, this is 5-10x faster than separate processes. <https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Composition.html> [verify]

### Lifecycle nodes — managed state machines

```cpp
#include <rclcpp_lifecycle/lifecycle_node.hpp>

class SensorNode : public rclcpp_lifecycle::LifecycleNode {
public:
    SensorNode() : LifecycleNode("sensor") {}

    CallbackReturn on_configure(const State&) override {
        // open device, allocate buffers
        return CallbackReturn::SUCCESS;
    }
    CallbackReturn on_activate(const State&) override {
        LifecycleNode::on_activate(State{});  // activates publishers
        return CallbackReturn::SUCCESS;
    }
    // on_deactivate, on_cleanup, on_shutdown ...
};
```

Use lifecycle nodes whenever startup ordering or graceful shutdown matters — sensors, drivers, anything that touches hardware.

### Callback groups — control concurrency

```cpp
auto cb_group_sensors = create_callback_group(
    rclcpp::CallbackGroupType::Reentrant);
auto cb_group_control = create_callback_group(
    rclcpp::CallbackGroupType::MutuallyExclusive);

// Sensor callbacks can run in parallel
auto sub_lidar = create_subscription<LaserScan>("scan", 10,
    lidar_cb, opts_with_group(cb_group_sensors));
auto sub_camera = create_subscription<Image>("image", 10,
    image_cb, opts_with_group(cb_group_sensors));

// Control callbacks are serialized — never two at once
auto sub_cmd = create_subscription<Twist>("cmd_vel", 10,
    cmd_cb, opts_with_group(cb_group_control));
auto timer_ctrl = create_wall_timer(1ms, ctrl_step,
    cb_group_control);

// Required: spin with a multi-threaded executor for parallelism to actually happen
rclcpp::executors::MultiThreadedExecutor exec;
exec.add_node(node);
exec.spin();
```

The default `MutuallyExclusive` group on the default executor means *all* your callbacks serialize on one thread. Surprising amount of robotics C++ code is single-threaded by accident.

## Further reading

- `/home/pan-navigator/Documents/claude-config/references/cpp_optimizations/` — Pan's curated notes on C++ for robotics performance. Read `index.md` first.
- *Effective Modern C++* — Scott Meyers. Still the best book for getting modern C++ idioms right.
- *A Philosophy of Software Design* — John Ousterhout. Not C++ specific, but the chapter on minimizing exceptions matters for RT code.
- *C++ Concurrency in Action* — Anthony Williams. The threading reference.
- ROS 2 design docs: <https://design.ros2.org/> — read the executor and intra-process comms ones.
- `rclcpp` API: <https://docs.ros.org/en/jazzy/p/rclcpp/> [verify]

If you take one thing from this page: profile before you optimize, but know enough about the hardware (cache, allocator, scheduler) that your "vibes" optimizations are at least pointed in the right direction.
