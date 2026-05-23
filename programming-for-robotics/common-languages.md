---
icon: subtitles
---

# Common Languages

### The 2026 landscape

In production robotics in 2026, three languages cover ~95% of the work:

* **C++** - every performance-critical ROS 2 node, every real-time control loop, every SLAM/perception backbone (Nav2, MoveIt 2, ORB-SLAM3, FAST-LIO2 - all C++).
* **Python** - every glue script, every ML/perception model, every rapid prototype, plus a large fraction of ROS 2 nodes that aren't on the hot path. `rclpy` is fully featured.
* **Rust** - a rising third. The official `rclrs` client library is maturing, and adoption is growing for safety-critical and embedded robotics. Worth learning if you're building greenfield systems in 2026.

Everything else is niche. Deep dives for each:

* **[C++ for Robotics](cpp-for-robotics.md)** - Eigen, real-time idioms, rclcpp composition, cache-friendly code.
* **[Python for Robotics](python-for-robotics.md)** - numpy idioms, rclpy patterns, PyTorch + ROS 2.

***

### Common Robotics Languages

* **C++**\
  Direct memory and hardware control, deterministic performance, wide RT and embedded support. The backbone of ROS 2 (`rclcpp`).\
  – Pros: high speed, extensive libraries (Eigen, PCL, OpenCV, Boost), fine-grained control.\
  – Cons: steep learning curve, careful memory management, slow compile times.\
  – Use when: any hot loop, drivers, SLAM, perception, controllers.
* **Python**\
  Rapid prototyping, scripting, AI/vision integration. Huge ecosystem (NumPy, SciPy, PyTorch, OpenCV).\
  – Pros: readable, massive ML ecosystem, fast iteration. `rclpy` is full-featured in ROS 2.\
  – Cons: GIL prevents true threading, slower than C++ in tight loops, packaging can be painful.\
  – Use when: ML inference nodes, dashboards, behaviors, anywhere off the hot path.
* **Rust**\
  Memory-safe systems language with C++-comparable performance. Official ROS 2 client library is `rclrs` (in active development).\
  – Pros: no segfaults, fearless concurrency, modern tooling (cargo).\
  – Cons: smaller robotics ecosystem than C++/Python, learning curve, `rclrs` API still evolving.\
  – Use when: greenfield systems where safety matters; safety-critical drivers; if your team is Rust-fluent already.
* **MATLAB / Simulink**\
  Model-based design for kinematics, dynamics, control, and vision. Automatic code generation to embedded targets or ROS nodes.\
  – Pros: integrated toolboxes (Robotics System Toolbox, Computer Vision), built-in plotting.\
  – Cons: commercial licensing, less flexible for custom drivers, awkward for production deployment.\
  – Use when: control system design, simulation, academic research.
* **Hardware Description Languages (VHDL / Verilog / SystemVerilog)**\
  For FPGAs: ultra-low-latency sensor interfaces, custom co-processors (e.g., event-camera processing).\
  – Pros: cycle-accurate, parallel hardware acceleration.\
  – Cons: very steep learning curve, specialized domain.
* **Embedded C (with vendor SDKs)**\
  For bare-metal MCU work: motor controllers, sensor drivers. Often paired with FreeRTOS or Zephyr.\
  – Use when: writing firmware for the robot's microcontrollers, often bridged to ROS 2 via [micro-ROS](../ros-2/micro-ros.md).

Older/niche languages - **C#/.NET** (Windows-only, Microsoft Robotics Developer Studio is effectively dead), **Java** (rare in robotics), **Lisp** (historical AI planning) - you'll encounter only in legacy systems.

### Picking Your First Robotics Language

| Goal | Start with |
|---|---|
| Real-time control, drivers, SLAM | **C++** |
| ML/vision, scripting, rapid prototyping | **Python** |
| Greenfield with safety focus | **Rust** |
| Embedded MCU firmware | **Embedded C** (often with [micro-ROS](../ros-2/micro-ros.md)) |
| Model-based control design | **MATLAB/Simulink** |
| FPGA sensor co-processor | **VHDL/Verilog** |

> **Field note.** In my production robotics work the actual ratio has been: ~60% C++, ~30% Python, ~10% Bash/CMake/launch-file glue. Rust is on the radar but hasn't replaced any C++ yet.

### Study Resources <a href="#study-resources" id="study-resources"></a>

* 4 Best Programming Languages For Robotics-GUVI blog\
  [https://www.guvi.in/blog/best-programming-languages-for-robotics/](https://www.guvi.in/blog/best-programming-languages-for-robotics/)
* What Is the Best Programming Language for Robotics?-Robotiq\
  [https://blog.robotiq.com/what-is-the-best-programming-language-for-robotics](https://blog.robotiq.com/what-is-the-best-programming-language-for-robotics)
* Top 8 Robotic Programming Languages-Built In\
  [https://builtin.com/robotics/robotic-programming-language](https://builtin.com/robotics/robotic-programming-language)
* Exploring 5 Types of Robot Programming Languages-Augmentus\
  [https://www.augmentus.tech/blog/are-all-robot-programming-languages-the-same/](https://www.augmentus.tech/blog/are-all-robot-programming-languages-the-same/)
* Robot Programming Language: 5 Options Explored-Bota Systems\
  [https://www.botasys.com/post/robot-programming-language](https://www.botasys.com/post/robot-programming-language)
* Learn ROS & Robotics Online-The Construct (incl. Python for Robotics)\
  [https://www.theconstruct.ai/home/](https://www.theconstruct.ai/home/)\
  [https://www.theconstruct.ai/robotigniteacademy\_learnros/ros-courses-library/python-robotics/](https://www.theconstruct.ai/robotigniteacademy_learnros/ros-courses-library/python-robotics/)
* ROS Official Documentation & Tutorials\
  [https://www.ros.org/](https://www.ros.org/)
* Discussion: “What’s the best language for getting into robotics?”-Reddit\
  [https://www.reddit.com/r/robotics/comments/vhkzti/whats\_the\_best\_language\_for\_getting\_into\_robotics/](https://www.reddit.com/r/robotics/comments/vhkzti/whats_the_best_language_for_getting_into_robotics/)
