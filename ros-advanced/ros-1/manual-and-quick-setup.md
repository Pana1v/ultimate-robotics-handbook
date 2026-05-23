# Manual and Quick Setup

{% tabs %}
{% tab title="ROS 1" %}
**ROS 1 Installation Full Guide :** [**https://wiki.ros.org/noetic/Installation**](https://wiki.ros.org/noetic/Installation)

### ROS 1 Manual Installation & Learning Playlists <a href="#ros-1-manual-installation--learning-playlists" id="ros-1-manual-installation--learning-playlists"></a>

### **Manual Installation (ROS 1 Noetic Example)**

Follow the official ROS Wiki for a step-by-step manual installation:

1.  **Update package index:**

    ```
    sudo apt update
    ```
2.  **Install ROS Noetic (Desktop-Full):**

    ```
    sudo apt install ros-noetic-desktop-full
    ```

    * For lighter installs, use:
      * Desktop: `sudo apt install ros-noetic-desktop`
      * Base: `sudo apt install ros-noetic-ros-base`2.
3.  **Initialize rosdep:**

    ```
    sudo apt install python3-rosdep
    sudo rosdep init
    rosdep update
    ```
4.  **Environment setup:**

    ```
    echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc
    source ~/.bashrc
    ```
5.  **Test installation:**

    ```
    roscore
    ```

    *   Open a new terminal and run:

        ```
        rosnode list
        ```

        You should see `/rosout` if everything is working.

**Full guide:** [ROS Noetic Installation (wiki.ros.org)](http://wiki.ros.org/noetic/Installation/Ubuntu)2\
**Beginner tutorials:** [ROS Wiki Tutorials](http://wiki.ros.org/ROS/Tutorials)6

### **Top ROS 1 Video Playlists & Learning Resources**

* [**Beginner ROS Tutorials Playlist – YouTube**](https://www.youtube.com/playlist?list=PLAjUtIp46jDdv1U7I0tJlJTmjnYcczJSN)[4](https://robocademy.com/2020/04/28/top-free-tutorials-to-learn-ros-robot-operating-system/)
* [**Justin Huang’s ROS Tutorials**](https://www.youtube.com/watch?v=nKIOb6lyrlI\&list=PLn8PRpmsu08pzi6EMiYnR-076Mh-q3tWr)[5](https://www.youtube.com/playlist?list=PLAjUtIp46jDdv1U7I0tJlJTmjnYcczJSN)
* [**ROBOTIS Free ROS Video Tutorials & Book**](https://robocademy.com/2020/04/28/top-free-tutorials-to-learn-ros-robot-operating-system/)\
  Includes videos and a free ebook for beginners[3](http://wiki.ros.org/noetic/Installation/Ubuntu).
* [**Programming for Robotics: ROS Tutorials (ETH Zurich)**](https://robocademy.com/2020/04/28/top-free-tutorials-to-learn-ros-robot-operating-system/)\
  Structured, university-level lectures[3](http://wiki.ros.org/noetic/Installation/Ubuntu).
* [**The Construct: ROS in 5 Days**](https://robocademy.com/2020/04/28/top-free-tutorials-to-learn-ros-robot-operating-system/)\
  Fast-paced, hands-on video series[3](http://wiki.ros.org/noetic/Installation/Ubuntu).

### Quick Setup for ROS 1 (Automated Script) <a href="#quick-setup-for-ros-1-automated-script" id="quick-setup-for-ros-1-automated-script"></a>

For a fast installation using scripts (recommended for repeatable setups):

1.  **Clone the script repository:**

    ```
    git clone https://github.com/Pana1v/ros-install-scripts.git
    cd ros-install-scripts
    chmod -R +x .
    ```
2.  **Run the install script for your ROS 1 version:**

    | Ubuntu Version | ROS 1 Version | Desktop-Full Install Command         |
    | -------------- | ------------- | ------------------------------------ |
    | 16.04          | Kinetic (EOL) | `./ros1/ros-kinetic-desktop-full.sh` |
    | 18.04          | Melodic       | `./ros1/ros-melodic-desktop-full.sh` |
    | 20.04          | Noetic        | `./ros1/ros-noetic-desktop-full.sh`  |

    Example for Noetic:

    ```
    ./ros1/ros-noetic-desktop-full.sh
    ```
3. **Follow the post-install steps above (rosdep, environment setup).**

**Repository:** [Pana1v/ros-install-scripts](https://github.com/Pana1v/ros-install-scripts)

**Recommendation:**\
Manual installation is best for learning and understanding the process. Use the automated script for quick, repeatable setups or when deploying to multiple machines. For in-depth learning, follow the playlists and official tutorials referenced above
{% endtab %}

{% tab title="ROS 2" %}
**ROS 2 Installation Full Guide :** [**https://docs.ros.org/en/humble/Installation.html**](https://docs.ros.org/en/humble/Installation.html)

### ROS 2: Manual and Quick Setup <a href="#ros-2-manual-and-quick-setup" id="ros-2-manual-and-quick-setup"></a>

### **Manual Installation (Example: ROS 2 Humble on Ubuntu 22.04)**

1.  **Set up sources and keys:**

    ```
    sudo apt update && sudo apt install curl gnupg2 lsb-release
    sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
    sudo apt update
    ```
2.  **Install ROS 2 (Desktop):**

    ```
    sudo apt install ros-humble-desktop
    ```
3.  **Environment setup:**

    ```
    echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
    source ~/.bashrc
    ```
4.  **Install dependencies for building packages:**

    ```
    sudo apt install python3-colcon-common-extensions python3-rosdep
    sudo rosdep init
    rosdep update
    ```
5.  **Test installation:**

    ```
    ros2 run demo_nodes_cpp talker
    # In another terminal:
    ros2 run demo_nodes_cpp listener
    ```

**Official guide:** [ROS 2 Installation Guide](https://docs.ros.org/en/ros2_installation.html)

### **Quick Setup Using Automated Script**

**Using** [**Pana1v/ros-install-scripts**](https://github.com/Pana1v/ros-install-scripts)**:**

1.  **Clone and prepare scripts:**

    ```
    git clone https://github.com/Pana1v/ros-install-scripts.git
    cd ros-install-scripts
    chmod -R +x .
    ```
2.  **Run the install script for your ROS 2 version:**

    | Ubuntu Version | ROS 2 Version | Desktop Install Command           |
    | -------------- | ------------- | --------------------------------- |
    | 20.04          | Foxy          | `./ros2/ros2-foxy-desktop.sh`     |
    | 20.04          | Galactic      | `./ros2/ros2-galactic-desktop.sh` |
    | 22.04          | Humble        | `./ros2/ros2-humble-desktop.sh`   |

    Example for Humble:

    ```
    ./ros2/ros2-humble-desktop.sh
    ```
3. **Follow post-install steps (environment setup, rosdep).**

**Recommendation:**\
Use the manual method to understand the process and dependencies. Use the quick script for rapid, repeatable installations or multiple deployments. For learning, explore the concepts and popular packages section, and refer to official tutorials and community playlists.
{% endtab %}
{% endtabs %}
