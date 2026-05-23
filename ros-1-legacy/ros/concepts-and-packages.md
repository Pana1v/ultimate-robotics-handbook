# Concepts and Packages (ROS 1)

{% hint style="warning" %}
**ROS 1 is deprecated.** Noetic — the final ROS 1 distro — reached End of Life on **May 2025**. For any new robotics project in 2026, use **ROS 2 Humble** (LTS, EOL May 2027) or **ROS 2 Jazzy** (LTS, EOL May 2029). This page is preserved for legacy/maintenance work only.

→ For current content see the [ROS 2 section](../../ros-2/ros-2.md).
{% endhint %}

{% tabs %}
{% tab title="ROS 1" %}
### **Core Concepts of ROS 1**

{% embed url="https://www.youtube.com/playlist?list=PLAjUtIp46jDdv1U7I0tJlJTmjnYcczJSN" %}
Playlist encapsualting important concepts
{% endembed %}

**Tutorials:** [**https://wiki.ros.org/ROS/Tutorials**](https://wiki.ros.org/ROS/Tutorials)

ROS 1 is structured around several key concepts that enable modular, distributed, and scalable robot software development. The main ideas are organized at different levels2[5](https://www.reddit.com/r/ROS/comments/17eh6px/most_important_parts_packages_for_ros/):

### **1. Nodes**

* **Definition:** Nodes are independent processes that perform computation. Each node is typically responsible for a single task (e.g., reading sensor data, controlling motors, localization).
* **Implementation:** Nodes are written using ROS client libraries such as `roscpp` (C++) or `rospy` (Python).
* **Communication:** Nodes communicate with each other using topics, services, or the parameter server, and are managed at runtime by the ROS Master2[3](http://wiki.ros.org/ROS/Concepts)[5](https://www.reddit.com/r/ROS/comments/17eh6px/most_important_parts_packages_for_ros/).

### **2. Master**

* **Role:** The ROS Master provides name registration and lookup for nodes, topics, and services, enabling nodes to discover and connect with each other.
* **Operation:** Nodes register themselves and their communication interfaces with the Master, which acts like a DNS server for the ROS network. After discovery, nodes communicate directly2[5](https://www.reddit.com/r/ROS/comments/17eh6px/most_important_parts_packages_for_ros/).

### **3. Parameter Server**

* **Purpose:** Stores global parameters (key-value pairs) accessible at runtime by all nodes. Used for configuration and tuning of nodes without code changes2[5](https://www.reddit.com/r/ROS/comments/17eh6px/most_important_parts_packages_for_ros/).

### **4. Topics**

* **Mechanism:** Topics are named message buses for asynchronous, many-to-many communication. Nodes publish messages to topics, and other nodes subscribe to receive those messages.
* **Strong Typing:** Each topic enforces a specific message type for data consistency.
* **Transport:** Default is TCPROS (reliable TCP/IP), with UDPROS (UDP-based, low-latency) for specific use cases2[3](http://wiki.ros.org/ROS/Concepts)[5](https://www.reddit.com/r/ROS/comments/17eh6px/most_important_parts_packages_for_ros/).

### **5. Messages**

* **Definition:** Strictly defined data structures used to communicate over topics. Defined in `.msg` files and can include primitive types or nested messages[3](http://wiki.ros.org/ROS/Concepts)[5](https://www.reddit.com/r/ROS/comments/17eh6px/most_important_parts_packages_for_ros/).

### **6. Services**

* **Mechanism:** Synchronous, request/response interactions for tasks that require confirmation or a result (e.g., requesting a sensor reading).
* **Definition:** Defined in `.srv` files with request and response fields[5](https://www.reddit.com/r/ROS/comments/17eh6px/most_important_parts_packages_for_ros/).

### **7. Bags**

* **Purpose:** Files (with `.bag` extension) for recording and replaying topic data. Essential for debugging, simulation, and development[5](https://www.reddit.com/r/ROS/comments/17eh6px/most_important_parts_packages_for_ros/).

### **8. Filesystem Level**

* **Packages:** The basic unit of ROS software organization, containing nodes, libraries, configuration files, and more.
* **Workspaces:** Directories for building and managing multiple packages together[5](https://www.reddit.com/r/ROS/comments/17eh6px/most_important_parts_packages_for_ros/).

### **Popular and Essential ROS 1 Packages**

While the importance of a package depends on your application, the following are widely used and considered essential in most ROS 1 projects[4](https://foxglove.dev/blog/the-building-blocks-of-ros1)[6](https://www.packtpub.com/en-us/learning/how-to-tutorials/ros-architecture-and-concepts)[7](https://gist.github.com/DLu/0ce75ef609f78d0bf171b9dc6bcf0477):

| Package Name                                | Purpose/Description                                               |
| ------------------------------------------- | ----------------------------------------------------------------- |
| **tf / tf2**                                | Coordinate frame transforms (essential for robot kinematics)      |
| **rviz**                                    | 3D visualization tool for sensor data, robot models, and planning |
| **ros\_control**                            | Framework for controller management and hardware abstraction      |
| **moveit**                                  | Motion planning and manipulation for robotic arms                 |
| **navigation**                              | Autonomous navigation stack for mobile robots                     |
| **gazebo\_ros\_pkgs**                       | Integration between ROS and Gazebo simulator                      |
| **urdf**                                    | Unified Robot Description Format for robot models                 |
| **robot\_localization**                     | State estimation from multiple sensors                            |
| **rosbag**                                  | Data recording and playback                                       |
| **sensor\_msgs, geometry\_msgs, std\_msgs** | Standard message types for sensors, geometry, etc.                |
| **image\_transport, cv\_bridge**            | Tools for handling images and computer vision                     |
| **robot\_state\_publisher**                 | Publishes robot joint states to tf                                |
| **actionlib**                               | Tools for asynchronous task execution                             |
| **ros\_perception**                         | Perception stack for vision and point cloud processing            |
| **rosparam, rosnode, rostopic, rosservice** | Core tools for managing ROS system                                |
| **ROS Industrial**                          | Packages for industrial robot support                             |
| **rqt**                                     | GUI plugins for introspection, plotting, and debugging            |

**Other Notable Packages (from usage statistics)**[**6**](https://www.packtpub.com/en-us/learning/how-to-tutorials/ros-architecture-and-concepts)**:**

* `cv_bridge`, `image_transport` (vision)
* `robot_state_publisher`, `joint_state_publisher` (robot state)
* `dynamic_reconfigure` (runtime parameter tuning)
* `catkin` (build system)
* `roslaunch`, `rosbag`, `rosmsg`, `rostopic`, `rosservice`, `rosnode` (core utilities)
* `urdf_tutorial`, `turtlesim` (learning and demos)

### **References and Further Reading**

* [ROS Concepts (wiki.ros.org)](http://wiki.ros.org/ROS/Concepts)2
* [The Building Blocks of ROS 1 (Foxglove)](https://foxglove.dev/blog/the-building-blocks-of-ros1)[3](http://wiki.ros.org/ROS/Concepts)
* [Effective Robotics Programming with ROS (Packt)](https://www.packtpub.com/en-us/learning/how-to-tutorials/ros-architecture-and-concepts)[5](https://www.reddit.com/r/ROS/comments/17eh6px/most_important_parts_packages_for_ros/)
* [Most Important ROS Packages (Reddit)](https://www.reddit.com/r/ROS/comments/17eh6px/most_important_parts_packages_for_ros/)[4](https://foxglove.dev/blog/the-building-blocks-of-ros1)
* [Top ROS Packages (GitHub Gist)](https://gist.github.com/DLu/0ce75ef609f78d0bf171b9dc6bcf0477)[6](https://www.packtpub.com/en-us/learning/how-to-tutorials/ros-architecture-and-concepts)
* [Trossen Robotics: ROS 1 Open Source Packages](https://docs.trossenrobotics.com/interbotix_xsarms_docs/ros1_packages.html)
{% endtab %}

{% tab title="ROS 2" %}
{% embed url="https://www.youtube.com/playlist?list=PLAjUtIp46jDdv1U7I0tJlJTmjnYcczJSN" %}
Playlist encapsualting important concepts
{% endembed %}

### ROS 2 Concepts and Popular Packages <a href="#ros-2-concepts-and-popular-packages" id="ros-2-concepts-and-popular-packages"></a>

ROS 2 Tutorials: [https://docs.ros.org/en/humble/Tutorials.html](https://docs.ros.org/en/humble/Tutorials.html)

### **Core Concepts of ROS 2**

ROS 2 is a modern, distributed robotics middleware designed for flexibility, scalability, and real-time performance. It builds on the lessons of ROS 1 and introduces several key architectural and functional improvements.

### **1. Nodes**

* **Definition:** Nodes are independent, modular processes that perform computation. Each node can handle a specific function, such as sensor reading, data processing, or actuator control.
* **Types:**
  * **Standard Node:** Basic node with minimal state management.
  * **Lifecycle Node:** Supports managed states (e.g., unconfigured, inactive, active, finalized), enabling robust startup, shutdown, and error handling[4](https://www.reddit.com/r/ROS/comments/17eh6px/most_important_parts_packages_for_ros/)[7](https://docs.ros.org/en/humble/Concepts.html).
* **Features:** Nodes are more modular in ROS 2, can be composed into a single process, and support advanced lifecycle management for reliability[4](https://www.reddit.com/r/ROS/comments/17eh6px/most_important_parts_packages_for_ros/)[7](https://docs.ros.org/en/humble/Concepts.html).

### **2. Topics**

* **Mechanism:** Topics are named channels for asynchronous, many-to-many publish/subscribe communication. Nodes publish messages to topics, and other nodes subscribe to receive them2[4](https://www.reddit.com/r/ROS/comments/17eh6px/most_important_parts_packages_for_ros/)[6](https://husarion.com/tutorials/ros2-tutorials/ros2/).
* **DDS Integration:** ROS 2 uses the Data Distribution Service (DDS) middleware, enabling automatic discovery, decentralized communication, and advanced Quality of Service (QoS) controls[6](https://husarion.com/tutorials/ros2-tutorials/ros2/)[7](https://docs.ros.org/en/humble/Concepts.html).
* **QoS Policies:** Fine-grained control over reliability, durability, deadline, and resource usage, crucial for real-time and safety-critical applications[4](https://www.reddit.com/r/ROS/comments/17eh6px/most_important_parts_packages_for_ros/)[7](https://docs.ros.org/en/humble/Concepts.html).

### **3. Services**

* **Definition:** Services provide synchronous, request/response communication. A client sends a request to a service server and waits for a response, suitable for tasks that require confirmation or a result[4](https://www.reddit.com/r/ROS/comments/17eh6px/most_important_parts_packages_for_ros/)[6](https://husarion.com/tutorials/ros2-tutorials/ros2/).
* **Implementation:** Defined using `.srv` files specifying request and response types.

### **4. Actions**

* **Purpose:** Actions allow for asynchronous, long-running tasks with feedback and the ability to cancel (e.g., navigation goals, manipulation tasks).
* **Structure:** Built on top of topics and services, actions provide goal, feedback, and result channels[4](https://www.reddit.com/r/ROS/comments/17eh6px/most_important_parts_packages_for_ros/)[6](https://husarion.com/tutorials/ros2-tutorials/ros2/).

### **5. Parameters**

* **Role:** Store configuration and runtime values for nodes. Parameters can be dynamically updated, allowing for flexible system tuning[4](https://www.reddit.com/r/ROS/comments/17eh6px/most_important_parts_packages_for_ros/)[6](https://husarion.com/tutorials/ros2-tutorials/ros2/).

### **6. Quality of Service (QoS)**

* **Importance:** QoS policies (enabled by DDS) let developers specify message delivery guarantees, reliability, and resource constraints for each topic or service, enhancing real-time and distributed performance[4](https://www.reddit.com/r/ROS/comments/17eh6px/most_important_parts_packages_for_ros/)[7](https://docs.ros.org/en/humble/Concepts.html).

### **7. Launch System**

* **Advancement:** ROS 2 uses Python-based launch files, allowing for programmable, flexible system startup and orchestration[4](https://www.reddit.com/r/ROS/comments/17eh6px/most_important_parts_packages_for_ros/)[6](https://husarion.com/tutorials/ros2-tutorials/ros2/).

### **8. Security**

* **Features:** Built-in support for authentication, encryption, and access control, making ROS 2 suitable for commercial and safety-critical deployments[4](https://www.reddit.com/r/ROS/comments/17eh6px/most_important_parts_packages_for_ros/)[7](https://docs.ros.org/en/humble/Concepts.html).

### **9. Tools and Ecosystem**

* **Developer Tools:** ROS 2 offers a suite of tools for introspection, debugging, visualization (e.g., RViz2), plotting, logging, and playback, accelerating development and troubleshooting[5](https://learnopencv.com/robot-operating-system-introduction/)[7](https://docs.ros.org/en/humble/Concepts.html).
* **Community:** A vibrant, global community contributes to a rich repository of open-source packages, ensuring continuous improvement and innovation[7](https://docs.ros.org/en/humble/Concepts.html).

### **Popular and Essential ROS 2 Packages**

The following packages are widely used and form the backbone of most ROS 2 applications. Your choice may vary depending on your robot and application, but these are considered foundational:

| Package Name                                | Purpose/Description                                                        |
| ------------------------------------------- | -------------------------------------------------------------------------- |
| **rclcpp / rclpy**                          | Core C++ and Python client libraries for node development                  |
| **tf2**                                     | Coordinate frame transformations for robot kinematics and sensor fusion    |
| **RViz2**                                   | 3D visualization tool for sensor data, robot models, and planning          |
| **ros2\_control**                           | Modular, extensible robot control framework                                |
| **Nav2**                                    | Navigation stack for autonomous mobile robots                              |
| **MoveIt 2**                                | Advanced motion planning and manipulation for robotic arms                 |
| **Gazebo / Ignition**                       | High-fidelity robot simulation environments                                |
| **sensor\_msgs, geometry\_msgs, std\_msgs** | Standard message types for sensors, geometry, and basic data               |
| **image\_tools, camera\_info\_manager**     | Vision and sensor integration tools                                        |
| **rosbag2**                                 | Data recording and playback for ROS 2 messages                             |
| **robot\_state\_publisher**                 | Publishes robot joint states to tf2                                        |
| **action\_msgs, lifecycle\_msgs**           | Standard messages for actions and node lifecycle management                |
| **rqt, RViz2 plugins**                      | GUI tools for introspection, plotting, debugging, and visualization        |
| **slam\_toolbox**                           | SLAM (Simultaneous Localization and Mapping) for mapping and localization  |
| **navigation2 (Nav2)**                      | Advanced navigation and path planning for mobile robots                    |
| **Perception packages**                     | Includes packages for vision, point cloud processing, and object detection |

**Other Notable Packages:**

* `micro_ros` (ROS 2 for microcontrollers)
* `ament_cmake` (build system)
* `colcon` (build tool)
* `ros2launch` (launch management)
* `ros2param` (parameter management)
* `ros2topic`, `ros2service`, `ros2bag` (core CLI tools)

### **References and Further Reading**

* [ROS 2 Concepts (docs.ros.org, Foxy)](https://docs.ros.org/en/foxy/Concepts.html)2
* [ROS 2 Concepts (docs.ros.org, Humble)](https://docs.ros.org/en/humble/Concepts.html)[6](https://husarion.com/tutorials/ros2-tutorials/ros2/)
* [Introduction to ROS 2 (LearnOpenCV)](https://learnopencv.com/robot-operating-system-introduction/)[4](https://www.reddit.com/r/ROS/comments/17eh6px/most_important_parts_packages_for_ros/)
* [ROS 2 Tutorials (Husarion)](https://husarion.com/tutorials/ros2-tutorials/ros2/)[5](https://learnopencv.com/robot-operating-system-introduction/)
* [Introduction to ROS 2 (MathWorks)](https://www.mathworks.com/help/ros/gs/robot-operating-system-ros2-basic-concepts.html)[7](https://docs.ros.org/en/humble/Concepts.html)
* [Most Important ROS Packages (Reddit)](https://www.reddit.com/r/ROS/comments/17eh6px/most_important_parts_packages_for_ros/)
{% endtab %}
{% endtabs %}
