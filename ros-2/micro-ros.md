---
icon: gear
---

# micro-ROS

micro-ROS is how you get a real ROS 2 node - same QoS, same DDS semantics, same `rclc` API - running on a microcontroller. It is the modern answer to ROS 1's `rosserial`, and it is a complete rebuild rather than a port. If you have ever tried to wedge `rosserial_arduino` into a project with serious sensor traffic, micro-ROS is a relief.

The project lives at [micro.ros.org](https://micro.ros.org). Source: [github.com/micro-ROS](https://github.com/micro-ROS).

I've used micro-ROS in production for ESP32-based motor controllers and sensor interfaces in mobile platforms - wheel encoders, ESC interfaces, IMU shims. It is also what I would reach for if I were building [Polka](../authors-projects/polka.md) again today, instead of the custom serial protocol I started with.

## Why micro-ROS exists

Microcontrollers can't run full DDS. The implementations (Cyclone, Fast DDS) assume a host OS, multi-threading, dynamic memory, network stacks with megabytes of buffer space. An STM32F4 has 128 KB of RAM total.

The OMG already had an answer in spec form: **DDS-XRCE** (eXtremely Resource-Constrained Environments). It defines a tiny binary protocol with a single TCP/UDP connection to an *agent* running on a host, which then bridges into the full DDS network.

micro-ROS implements DDS-XRCE on the MCU side, exposes it through `rclc` (a C API that mirrors `rclcpp`'s shape), and ships a Linux-side `micro-ROS Agent` (built on Fast DDS) that translates between XRCE and full DDS.

## Architecture

```
        ┌───────────────────────────┐
        │       MCU (Client)        │
        │  ┌─────────────────────┐  │
        │  │  Your application   │  │
        │  └──────────┬──────────┘  │
        │             │ rclc API    │
        │  ┌──────────▼──────────┐  │
        │  │  micro-ROS client   │  │
        │  │  (rclc / rmw_uxrce) │  │
        │  └──────────┬──────────┘  │
        └─────────────┼─────────────┘
                      │ DDS-XRCE over UART / UDP / CAN
        ┌─────────────▼─────────────┐
        │   micro-ROS Agent (Linux) │
        │   (eProsima Micro XRCE-DDS Agent) │
        └─────────────┬─────────────┘
                      │ full DDS (RTPS)
        ┌─────────────▼─────────────┐
        │   Regular ROS 2 nodes     │
        │   (rclcpp, rclpy on host) │
        └───────────────────────────┘
```

From the host's perspective, the MCU appears as a normal ROS 2 node - same topics, services, parameters. From the MCU's perspective, it talks to an agent over a serial or network link.

### The agent

The agent is a regular ROS 2 node you run on your robot's main computer:

```bash
# Install
sudo apt install ros-jazzy-micro-ros-agent

# Run, listening on UART
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyUSB0 -b 115200

# Or UDP
ros2 run micro_ros_agent micro_ros_agent udp4 --port 8888
```

A single agent can host multiple MCU clients. In practice I run one agent per MCU; cheaper to debug.

## Supported MCUs

micro-ROS targets a long list of hardware. The ones I actually see in the field:

| MCU family       | RAM range    | Notes                                          |
| ---------------- | ------------ | ---------------------------------------------- |
| **STM32 F4 / F7 / H7** | 192 KB – 1 MB | The industrial workhorse. STM32CubeIDE integration. |
| **ESP32** (Xtensa) | 320–520 KB  | Wi-Fi + Bluetooth on board. My go-to for prototypes. |
| **ESP32-S3 / C3 / C6** | varies    | Newer ESP variants, all supported.            |
| **RP2040** (Raspberry Pi Pico) | 264 KB | Cheap, dual-core, decent toolchain.    |
| **Teensy 4.0 / 4.1** | 1 MB        | Arduino-compatible, very fast (Cortex-M7 @ 600 MHz). |
| **Arduino UNO R4 (Minima / WiFi)** | 32 KB | Lower bound. Renesas RA4M1, ESP32-S3 co-processor on WiFi variant. |
| Nuttx, Zephyr, FreeRTOS, ThreadX | - | RTOSes supported alongside bare-metal. |

The official list is at [micro.vulcanexus.org/docs/overview/hardware/](https://micro.vulcanexus.org/docs/overview/hardware/). The official Arduino integration is `micro_ros_arduino` ([github.com/micro-ROS/micro\_ros\_arduino](https://github.com/micro-ROS/micro_ros_arduino)).

### Practical RAM minimum

You can technically run micro-ROS on the Arduino UNO R4 (32 KB), but in practice anything below ~64 KB of usable RAM is painful - you'll spend more time tuning memory pool sizes than writing application code. ESP32 and Teensy 4.x are the sweet spot.

## Transport options

| Transport     | Pros                                    | Cons                                   |
| ------------- | --------------------------------------- | -------------------------------------- |
| **UART / Serial** | Simple, deterministic, no network stack | Single client per port, 115 200 baud default is slow. Bump to 921 600 or 4 000 000. |
| **USB CDC**   | Looks like serial to the host           | Same throughput limits.                |
| **UDP (Wi-Fi / Ethernet)** | High throughput, multiple clients | Wi-Fi flakiness on busy networks.   |
| **CAN bus**   | Native to automotive / industrial       | Tiny payload per frame, custom integration. |
| **BLE**       | Wireless without IP stack               | Bandwidth limited, mostly for telemetry. |

For a typical "wheel encoder + IMU + ESC control" node I run on ESP32: UART to the main computer. Reliable, predictable, no Wi-Fi politics.

## Build flow

There are two main toolchains. Pick based on what your team already uses.

### Option A: PlatformIO + micro\_ros\_platformio

If you're already using PlatformIO ([platformio.org](https://platformio.org)) for embedded work, this is the cleanest path. The `micro_ros_platformio` library handles all the build wiring.

`platformio.ini` for an ESP32:

```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
lib_deps =
    https://github.com/micro-ROS/micro_ros_platformio.git
board_microros_distro = jazzy
board_microros_transport = serial
```

`src/main.cpp`:

```cpp
#include <Arduino.h>
#include <micro_ros_platformio.h>
#include <rcl/rcl.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>
#include <std_msgs/msg/int32.h>

rcl_publisher_t publisher;
std_msgs__msg__Int32 msg;
rclc_executor_t executor;
rclc_support_t support;
rcl_allocator_t allocator;
rcl_node_t node;
rcl_timer_t timer;

void timer_callback(rcl_timer_t* timer, int64_t /*last_call_time*/) {
    (void) timer;
    msg.data++;
    rcl_publish(&publisher, &msg, NULL);
}

void setup() {
    set_microros_serial_transports(Serial);
    delay(2000);

    allocator = rcl_get_default_allocator();
    rclc_support_init(&support, 0, NULL, &allocator);
    rclc_node_init_default(&node, "esp32_node", "", &support);
    rclc_publisher_init_default(
        &publisher, &node,
        ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32),
        "esp32/counter");
    rclc_timer_init_default(&timer, &support, RCL_MS_TO_NS(100), timer_callback);
    rclc_executor_init(&executor, &support.context, 1, &allocator);
    rclc_executor_add_timer(&executor, &timer);

    msg.data = 0;
}

void loop() {
    rclc_executor_spin_some(&executor, RCL_MS_TO_NS(100));
}
```

The PlatformIO library builds the micro-ROS static library for you the first time you compile. After that it's just a regular embedded build.

### Option B: ESP-IDF or STM32CubeIDE

For when you're not on Arduino and want full control. The micro-ROS source tree provides component modules for ESP-IDF, makefile snippets for STM32 HAL, and CMake integration for Zephyr.

The flow is roughly:

1. Clone the micro-ROS firmware repo for your platform (e.g., `micro_ros_espidf_component`).
2. Drop it into your IDF project as a component.
3. Add `colcon meta` files describing which packages you want (every message type in your firmware has to be pre-compiled).
4. Build the static library once.
5. Link your firmware against it.

This is fiddly the first time and routine afterward.

## API patterns

micro-ROS' `rclc` is intentionally similar in shape to `rclcpp`, but without exceptions or RAII. Everything is C, everything checks return codes.

### Publishing

```cpp
rcl_publisher_t publisher;
rclc_publisher_init_default(
    &publisher, &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Float32),
    "imu/temperature");

std_msgs__msg__Float32 msg;
msg.data = 23.5;
rcl_publish(&publisher, &msg, NULL);
```

### Subscribing

```cpp
rcl_subscription_t subscriber;
geometry_msgs__msg__Twist cmd_vel_msg;

void cmd_vel_callback(const void* msgin) {
    const auto* msg = (const geometry_msgs__msg__Twist*) msgin;
    set_motor_velocity(msg->linear.x, msg->angular.z);
}

rclc_subscription_init_default(
    &subscriber, &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Twist),
    "cmd_vel");

rclc_executor_add_subscription(
    &executor, &subscriber, &cmd_vel_msg,
    cmd_vel_callback, ON_NEW_DATA);
```

### Services and parameters

Supported, but heavier in code and memory than publishers. Use sparingly. A 32-bit parameter takes more code-space than a `Float32` publisher.

## Memory tuning

Every message type has a pre-allocated buffer. The defaults in `colcon.meta` are conservative - fine for small messages, wasteful for sensors.

The knobs that matter, set in `colcon.meta` and rebuilt:

```yaml
names:
  rmw_microxrcedds:
    cmake-args:
      - -DRMW_UXRCE_MAX_NODES=1
      - -DRMW_UXRCE_MAX_PUBLISHERS=10
      - -DRMW_UXRCE_MAX_SUBSCRIPTIONS=5
      - -DRMW_UXRCE_MAX_SERVICES=2
      - -DRMW_UXRCE_MAX_CLIENTS=1
      - -DRMW_UXRCE_MAX_HISTORY=4
      - -DRMW_UXRCE_STREAM_HISTORY=4
      - -DRMW_UXRCE_MAX_INPUT_BEST_EFFORT_STREAMS=1
      - -DRMW_UXRCE_MAX_OUTPUT_BEST_EFFORT_STREAMS=1
      - -DRMW_UXRCE_MAX_OUTPUT_RELIABLE_STREAMS=1
      - -DRMW_UXRCE_MAX_INPUT_RELIABLE_STREAMS=1
```

If you're running out of memory: turn `MAX_NODES`, `MAX_PUBLISHERS`, `MAX_HISTORY` down. If sessions are dropping under load: turn `STREAM_HISTORY` up.

Each `ROSIDL_GET_MSG_TYPE_SUPPORT` you reference also costs flash (the message struct's metadata). For unused message types, don't include them - `colcon` will skip building them if they're not in your dependencies.

## micro-ROS vs rosserial - short version

| Feature           | rosserial (ROS 1)     | micro-ROS (ROS 2)        |
| ----------------- | --------------------- | ------------------------ |
| Protocol          | Custom binary         | DDS-XRCE (OMG standard)  |
| QoS               | None                  | Full DDS QoS             |
| Multiple clients per agent | No           | Yes                      |
| Transport         | UART only             | UART / UDP / CAN / custom |
| Message size limit | ~512 bytes           | Up to RAM budget (~few KB practical) |
| Status            | EOL with ROS 1 (May 2025) | Active, primary embedded path for ROS 2 |

rosserial does not exist on ROS 2. If someone tells you to use it for a new ROS 2 project, they are about five years out of date. The migration story is "rewrite the MCU firmware in micro-ROS."

## Practical limits

A few things that don't fit on an MCU at all, no matter how much you tune:

* **Large messages** - A 1 MP image is bigger than most MCU RAM. Strip down to the data you actually need. Send raw uint8 arrays for short telemetry, point-to-point IK calls, joint positions. Cameras and LiDARs are not MCU territory.

* **High-rate transient\_local topics** - Latching needs buffer memory. Use sparingly; one or two transient\_local topics is fine, ten will exhaust your RAM.

* **Cross-network discovery** - The MCU does not participate in DDS discovery directly. It connects to one agent; the agent fans out. Multi-machine setups need careful agent placement.

* **Hot reconfiguration** - micro-ROS clients don't gracefully resync if the agent restarts. Wrap your `rclc_support_init` in a reconnection loop.

## Reconnection pattern

The default examples assume the connection never drops. In a real robot the agent process, the USB cable, or the Wi-Fi will hiccup. Always wrap initialization:

```cpp
enum states { WAITING_AGENT, AGENT_AVAILABLE, AGENT_CONNECTED, AGENT_DISCONNECTED };
states state = WAITING_AGENT;

void loop() {
    switch (state) {
        case WAITING_AGENT:
            EXECUTE_EVERY_N_MS(500, state = (RMW_RET_OK == rmw_uros_ping_agent(100, 1))
                                            ? AGENT_AVAILABLE : WAITING_AGENT;);
            break;
        case AGENT_AVAILABLE:
            state = create_entities() ? AGENT_CONNECTED : WAITING_AGENT;
            if (state == WAITING_AGENT) destroy_entities();
            break;
        case AGENT_CONNECTED:
            EXECUTE_EVERY_N_MS(200, state = (RMW_RET_OK == rmw_uros_ping_agent(100, 1))
                                            ? AGENT_CONNECTED : AGENT_DISCONNECTED;);
            if (state == AGENT_CONNECTED) {
                rclc_executor_spin_some(&executor, RCL_MS_TO_NS(100));
            }
            break;
        case AGENT_DISCONNECTED:
            destroy_entities();
            state = WAITING_AGENT;
            break;
    }
}
```

This is verbose but bulletproof. The examples folder in `micro_ros_arduino` has cleaner versions; copy from there.

## Common pitfalls

* **Agent and client distro mismatch** - Humble agent can't talk to Iron client and vice versa. Match versions.

* **Forgetting to set the transport** - `set_microros_serial_transports(Serial)` must run *before* `rclc_support_init`. Otherwise the client tries to use a null transport.

* **Calling `rclc_executor_spin_some` from inside an ISR** - don't. micro-ROS is not interrupt-safe. Spin from the main loop, set flags from ISRs.

* **Stack overflow on FreeRTOS** - micro-ROS tasks need ~10 KB of stack. The default FreeRTOS task stack is 1–2 KB. Bump it.

* **Power-cycling the MCU without restarting the agent** - sometimes the agent doesn't notice the client is gone and refuses to accept a new session. Restart the agent.

* **Custom messages without rebuilding** - if you add a new `.msg` file you must rebuild the micro-ROS static library against the new IDL. There's no runtime registration.

* **Trying to run RVIZ visualization of a sensor on the MCU** - the message size budget will kill you. Push raw values to the agent and let a host node compose visualization markers.

## Where to go next

* [micro.ros.org](https://micro.ros.org) - official docs, tutorials, supported boards.
* [github.com/micro-ROS/micro\_ros\_arduino](https://github.com/micro-ROS/micro_ros_arduino) - pre-built Arduino library, easiest path for ESP32 / Teensy / Portenta.
* [DDS and QoS](dds-qos.md) - the QoS settings work the same on micro-ROS, with caveats about reliable streams.
* [Setup](setup.md) - installing the agent on your robot's main computer.
* [Polka](../authors-projects/polka.md) - my mobile platform, candidate for a micro-ROS firmware rewrite.
