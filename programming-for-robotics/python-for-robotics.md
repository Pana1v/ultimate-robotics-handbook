---
icon: code
---

# Python for Robotics

Python is the glue that holds modern robotics together. Perception models are trained in PyTorch. Calibration scripts are notebooks. Mission scripts are Python. Half your `rclpy` nodes are Python. The other half should probably be Python until you measure a real reason to port them.

But Python also gets misused. People write 1 kHz control loops in Python and then complain that their robot is jittery. So this page is about both - when Python is the right tool, and the idioms to use it well.

## When Python wins (and when it doesn't)

| Use case | Python | C++ |
|---|---|---|
| Prototyping a new algorithm | yes | no |
| Perception ML inference (Torch, ONNX, TensorRT wrapper) | yes | sometimes |
| Mission logic, behavior trees, scripting | yes | rarely |
| Calibration scripts | yes | no |
| Data analysis, rosbag post-processing | yes | no |
| Web/REST integration, dashboards | yes | rarely |
| 1 kHz+ control loop | no | yes |
| Hard-real-time anything | no | yes |
| Microcontroller / embedded | no (use C/C++/Rust) | sometimes |
| 100+ Hz callback in `rclpy` with heavy work | risky | yes |
| Driver for hardware over CAN/serial | sometimes | yes |

The honest version: if the latency budget is sub-millisecond and deterministic, write it in C++. If it's a script, a perception node, mission logic, or anything where readability matters more than nanoseconds, write it in Python.

## numpy idioms

The single most important Python-for-robotics skill is "don't write Python loops over numpy arrays."

### Vectorization

```python
import numpy as np

# BAD: explicit loop, 100x slower than vectorized
def distances_slow(points, target):
    out = np.zeros(len(points))
    for i in range(len(points)):
        out[i] = np.sqrt((points[i, 0] - target[0])**2 +
                         (points[i, 1] - target[1])**2 +
                         (points[i, 2] - target[2])**2)
    return out

# GOOD: vectorized
def distances(points, target):
    return np.linalg.norm(points - target, axis=1)
```

`points` is shape `(N, 3)`, `target` is shape `(3,)`. Broadcasting handles the subtract, and `np.linalg.norm` does the reduction in one BLAS call.

### Broadcasting

```python
# Compute pairwise distances between two sets of points
# A is (N, 3), B is (M, 3), want output (N, M)

# BAD:
D = np.zeros((N, M))
for i in range(N):
    for j in range(M):
        D[i, j] = np.linalg.norm(A[i] - B[j])

# GOOD: shape (N, 1, 3) - (1, M, 3) -> (N, M, 3) -> norm -> (N, M)
D = np.linalg.norm(A[:, None, :] - B[None, :, :], axis=2)
```

The `None` (a.k.a. `np.newaxis`) inserts a length-1 axis. Broadcasting then "stretches" the singleton dimensions. Internalize this pattern - you'll use it daily.

### `np.einsum` - when nothing else expresses what you want

```python
# Batch of N transforms (N, 4, 4) applied to N points (N, 4)
# Want output (N, 4)
out = np.einsum('nij,nj->ni', transforms, points_homogeneous)

# Compute (N, 3) point cloud transformed by a single (3, 3) rotation
# plus (3,) translation
out = np.einsum('ij,nj->ni', R, points) + t
```

`einsum` is read like a recipe: `'nij,nj->ni'` means "for each `n`, take indices `i,j` from arg 1 and `j` from arg 2, sum over `j`, output indexed by `n,i`." Once you read it fluently, it replaces a lot of `reshape`/`matmul`/`transpose` ceremony.

### Memory layout matters

```python
# Default numpy is row-major (C-order)
# OpenCV expects row-major; Eigen (and thus tf2) is column-major.

a = np.zeros((1000, 1000), dtype=np.float32)
print(a.flags['C_CONTIGUOUS'])  # True

# Slicing can break contiguity; .copy() fixes it
b = a[:, ::2]
print(b.flags['C_CONTIGUOUS'])  # False
c = b.copy()
print(c.flags['C_CONTIGUOUS'])  # True
```

If you're passing buffers to a C++ extension and it complains, contiguity is usually the reason.

## scipy.spatial.transform.Rotation

This class replaces 80% of the quaternion math you'd otherwise write. Don't reinvent it.

```python
from scipy.spatial.transform import Rotation as R
import numpy as np

# Construct from various conventions
r1 = R.from_quat([x, y, z, w])              # scipy uses xyzw order, ROS uses xyzw also
r2 = R.from_euler('xyz', [roll, pitch, yaw])
r3 = R.from_rotvec([0, 0, np.pi/4])         # axis-angle
r4 = R.from_matrix(rotation_matrix_3x3)

# Convert
quat = r1.as_quat()         # [x, y, z, w]
euler = r1.as_euler('zyx')  # roll-pitch-yaw conventions differ - pick one and stick
matrix = r1.as_matrix()

# Compose: r_total = r2 after r1
r_total = r2 * r1

# Apply to vectors (single or batch)
rotated = r1.apply(np.array([1, 0, 0]))         # shape (3,)
rotated_batch = r1.apply(points_Nx3)            # shape (N, 3)

# Interpolate between rotations (SLERP)
from scipy.spatial.transform import Slerp
times = [0, 1]
key_rots = R.from_quat([q0, q1])
slerp = Slerp(times, key_rots)
intermediate = slerp([0.25, 0.5, 0.75])
```

Quaternion order trap: ROS messages (`geometry_msgs/Quaternion`) use `(x, y, z, w)`. So does scipy. `tf2` Python helpers do too. But some older code (Eigen's `Quaterniond(w, x, y, z)` constructor) uses `wxyz`. Always check, always test with known values.

Docs: <https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.transform.Rotation.html>

## rclpy patterns

### Executors - single-threaded vs multi-threaded

```python
import rclpy
from rclpy.executors import MultiThreadedExecutor, SingleThreadedExecutor

def main():
    rclpy.init()
    node1 = SensorNode()
    node2 = PlannerNode()

    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(node1)
    executor.add_node(node2)

    try:
        executor.spin()
    finally:
        executor.shutdown()
        node1.destroy_node()
        node2.destroy_node()
        rclpy.shutdown()
```

`rclpy.spin(node)` uses a single-threaded executor by default. Every callback in every node runs on one thread, serialized. If one callback blocks (e.g., waits on a service call), nothing else runs. Switch to `MultiThreadedExecutor` the moment you have a blocking call, a long-running callback, or multiple sensors at different rates.

### Callback groups

```python
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup, ReentrantCallbackGroup

class MyNode(Node):
    def __init__(self):
        super().__init__('my_node')
        self.sensors_cb = ReentrantCallbackGroup()
        self.control_cb = MutuallyExclusiveCallbackGroup()

        # Sensor callbacks: can run concurrently
        self.create_subscription(LaserScan, 'scan', self.on_scan,
                                 10, callback_group=self.sensors_cb)
        self.create_subscription(Image, 'image', self.on_image,
                                 10, callback_group=self.sensors_cb)

        # Control: only ever one at a time
        self.create_subscription(Twist, 'cmd_vel', self.on_cmd,
                                 10, callback_group=self.control_cb)
        self.create_timer(0.01, self.control_step,
                          callback_group=self.control_cb)
```

- `MutuallyExclusiveCallbackGroup` - at most one callback in the group runs at a time. Safe default. Used when you want to avoid races on shared state.
- `ReentrantCallbackGroup` - any number of callbacks in the group can run in parallel. Use when callbacks are independent (e.g., sensor topics that update separate fields).

If you do a service call from inside a callback, that service callback **must** be in a different group than the calling callback - otherwise you deadlock. This is the single most common `rclpy` gotcha. <https://docs.ros.org/en/jazzy/Concepts/Intermediate/About-Executors.html> [verify]

### QoS profiles

```python
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy

# For sensors - match the publisher's QoS, usually BEST_EFFORT
sensor_qos = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    durability=DurabilityPolicy.VOLATILE,
    history=HistoryPolicy.KEEP_LAST,
    depth=5,
)

# For latched data - robot_description, map
latched_qos = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    depth=1,
)

self.create_subscription(LaserScan, 'scan', self.cb, sensor_qos)
```

If your subscription gets nothing, 80% of the time it's a QoS mismatch. Check with `ros2 topic info -v <topic>`.

### Lifecycle nodes in Python

```python
from rclpy.lifecycle import LifecycleNode, TransitionCallbackReturn, State

class SensorNode(LifecycleNode):
    def __init__(self):
        super().__init__('sensor')

    def on_configure(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info('Configuring...')
        # open hardware, allocate buffers
        return TransitionCallbackReturn.SUCCESS

    def on_activate(self, state: State) -> TransitionCallbackReturn:
        # start publishing
        return super().on_activate(state)

    def on_deactivate(self, state: State) -> TransitionCallbackReturn:
        return super().on_deactivate(state)
```

Python lifecycle support matured in Humble. Use it for anything touching hardware so launch can orchestrate startup order.

## asyncio with rclpy

Newer pattern, available since Humble. Lets you `await` on service calls and action goals naturally.

```python
import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger

class AsyncNode(Node):
    def __init__(self):
        super().__init__('async_node')
        self.client = self.create_client(Trigger, 'do_thing')

    async def call_service(self):
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('waiting...')
        request = Trigger.Request()
        future = self.client.call_async(request)
        response = await future  # no busy spinning, no nested executors
        return response

# In main:
async def amain(node):
    response = await node.call_service()
    node.get_logger().info(f'Got: {response.message}')
```

Caveats: as of early 2026 the asyncio-with-rclpy story is still evolving. The classic synchronous pattern with futures plus `spin_until_future_complete` works everywhere; asyncio works but watch out for executor interactions. <https://docs.ros.org/en/jazzy/How-To-Guides/Using-callback-groups.html> [verify]

## Type hints + mypy

Don't ship robotics Python without type hints. Bugs in robotics code are expensive (you may have just driven your robot into a wall), and the type system catches a real fraction of them for free.

```python
from typing import Optional
import numpy as np
import numpy.typing as npt

PointCloud = npt.NDArray[np.float32]  # shape (N, 3) by convention

def transform_cloud(cloud: PointCloud,
                    R: npt.NDArray[np.float64],
                    t: npt.NDArray[np.float64]) -> PointCloud:
    return (R @ cloud.T).T + t

def lookup_pose(frame: str) -> Optional[np.ndarray]:
    try:
        return self.tf_buffer.lookup_transform(...)
    except tf2_ros.LookupException:
        return None
```

Configure `mypy` with `--strict` for new code. For ROS messages, you can use `rosidl_runtime_py` types or just `Any` - the message classes themselves carry runtime type info.

## Debugging

```python
# Built-in debugger - set a breakpoint anywhere
breakpoint()  # Python 3.7+, drops into pdb

# Or use ipdb for nicer UI
import ipdb; ipdb.set_trace()

# rclpy log levels - set per-node from CLI
# ros2 run my_pkg my_node --ros-args --log-level my_node:=debug

# Throttled logging is essential at 100+ Hz
self.get_logger().info('still going', throttle_duration_sec=1.0)
```

When a node hangs, `py-spy dump --pid <pid>` shows you what each thread is doing without modifying the running process. <https://github.com/benfred/py-spy>

## Profiling

```python
# cProfile - overall hotspots
import cProfile, pstats
profiler = cProfile.Profile()
profiler.enable()
do_stuff()
profiler.disable()
pstats.Stats(profiler).sort_stats('cumulative').print_stats(20)
```

- `py-spy record -o flame.svg -- python my_node.py` - sampling profiler, produces flame graph, ~5% overhead. Best first-resort tool. <https://github.com/benfred/py-spy>
- `line_profiler` - decorate a function with `@profile`, get per-line timing. Use when cProfile points at a function but you need to know which line. <https://github.com/pyutils/line_profiler> [verify]
- `memory_profiler` - for memory leaks, which absolutely happen in long-running rclpy nodes. <https://github.com/pythonprofilers/memory_profiler> [verify]

If your `rclpy` node is eating CPU you didn't expect, 90% of the time it's one of: a callback in a tight loop with no rate limiting, a numpy operation that's looping in Python instead of vectorized, or a logging statement at high frequency without throttling.

## PyTorch + ROS 2

Perception models in PyTorch, deployed to ROS 2, is the standard 2026 stack.

```python
import torch
import torch.nn.functional as F
from cv_bridge import CvBridge

class DetectorNode(Node):
    def __init__(self):
        super().__init__('detector')
        self.model = torch.jit.load('detector.pt').cuda().eval()
        self.bridge = CvBridge()
        self.create_subscription(Image, 'camera/image_raw',
                                 self.on_image, sensor_qos)

    @torch.inference_mode()  # disables autograd, faster than torch.no_grad()
    def on_image(self, msg: Image):
        img = self.bridge.imgmsg_to_cv2(msg, 'rgb8')
        x = torch.from_numpy(img).permute(2, 0, 1).unsqueeze(0).cuda().float() / 255.0
        detections = self.model(x)
        # publish detections...
```

Deployment options, from most-portable to fastest:

1. **`torch.jit.script` / `torch.jit.trace`** - produces a `.pt` you can load without your model source code. First step. Easy.
2. **ONNX export** - `torch.onnx.export(model, dummy_input, 'model.onnx')`. Now your model is framework-agnostic; you can run it under ONNX Runtime, TensorRT, OpenVINO. <https://pytorch.org/docs/stable/onnx.html>
3. **TensorRT** - NVIDIA's inference engine. Convert ONNX to a TRT engine (`trtexec` or the `tensorrt` Python API). On Jetson and discrete NVIDIA GPUs, this is typically 2-5x faster than raw PyTorch. <https://developer.nvidia.com/tensorrt> [verify]
4. **`torch.compile` (PyTorch 2.x)** - JIT compilation. Sometimes great, sometimes flaky with dynamic shapes. Worth trying when ONNX export is painful.

Common production stack: train in PyTorch, export to ONNX, build TensorRT engine on the target hardware (Jetson Orin, RTX A4000, etc.), call from a Python `rclpy` node that handles I/O.

## Further reading

- *Effective Python* - Brett Slatkin. The Python equivalent of *Effective C++*.
- *High Performance Python* - Gorelick & Ozsvald. Profiling, vectorization, Cython.
- `rclpy` source: <https://github.com/ros2/rclpy> - reading the actual implementation clarifies more than any tutorial.
- ROS 2 Python style guide: <https://docs.ros.org/en/jazzy/The-ROS2-Project/Contributing/Code-Style-Language-Versions.html> [verify]
- numpy docs on broadcasting: <https://numpy.org/doc/stable/user/basics.broadcasting.html>

The rule I keep coming back to: write it in Python first. Measure. If a hot loop shows up in the profile, vectorize it. If that's not enough, port that one function to C++ via pybind11. Almost never do you need to rewrite the whole node.
