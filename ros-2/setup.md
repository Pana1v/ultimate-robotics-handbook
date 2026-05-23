---
icon: gear
---

# Setup

This page is the install-and-bootstrap guide I wish someone had handed me on day one. The official docs at [docs.ros.org/en/jazzy/Installation.html](https://docs.ros.org/en/jazzy/Installation.html) \[verify] cover the happy path. What you get here is the same path with the failure modes called out, plus the colcon workspace pattern I use on every project.

## Pick your distro and OS pair

ROS 2 binaries are pinned to specific Ubuntu versions. Do not try to install Jazzy on 22.04 or Humble on 24.04 — you will spend a day fighting glibc and Python version mismatches. The pairs you actually want:

| Distro | Ubuntu       | Python | Notes                                        |
| ------ | ------------ | ------ | -------------------------------------------- |
| Humble | 22.04 Jammy  | 3.10   | Conservative choice, mature third-party support |
| Jazzy  | 24.04 Noble  | 3.12   | Default for new work                         |

ARM64 (Jetson, Raspberry Pi 4/5) builds exist for both — same `apt` flow, just on `arm64`.

## Binary install via apt

This is what you use on a developer machine or a robot in production. Source builds are only for distro contributors or people patching `rcl`.

The official instructions are at [docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html) \[verify]. The condensed flow for Jazzy on Ubuntu 24.04:

```bash
# Locale — ROS 2 assumes UTF-8
sudo apt update && sudo apt install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# Enable universe repo
sudo apt install -y software-properties-common
sudo add-apt-repository universe

# Add the ROS 2 apt source
sudo apt update && sudo apt install -y curl gnupg lsb-release
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
| sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# Install the desktop metapackage (rviz2, demos, tutorials)
sudo apt update
sudo apt install -y ros-jazzy-desktop
```

For Humble, replace `jazzy` with `humble` and run on 22.04. For a headless robot you may prefer `ros-jazzy-ros-base` instead of `ros-jazzy-desktop` to skip rviz2 and the demo packages.

Always install the dev tools — you need them the first time you build any workspace:

```bash
sudo apt install -y \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    python3-argcomplete \
    build-essential \
    git
```

### What you actually get

After `ros-jazzy-desktop` you have:

* `/opt/ros/jazzy/` — the installed distro (immutable, do not edit)
* `ros2` CLI on your `PATH` once sourced
* `rclcpp`, `rclpy`, `rmw_cyclonedds_cpp` (default RMW for Jazzy), demo packages, rviz2

## rosdep — initialize once per machine

`rosdep` resolves the `<depend>` tags in `package.xml` into apt packages. It is a one-time setup, and it bites you the first time you build a workspace if you forget.

```bash
sudo rosdep init   # writes /etc/ros/rosdep/sources.list.d/20-default.list
rosdep update      # user-level, fetches the YAML manifests into ~/.ros/rosdep/

# Inside a workspace, resolve all package.xml dependencies
rosdep install --from-paths src --ignore-src -r -y
```

If `rosdep init` complains that the file already exists, you ran it before — that is fine, just skip to `rosdep update`. If `rosdep update` fails behind a proxy, set `ROSDISTRO_INDEX_URL` to a local mirror.

## colcon workspace setup

You do not run your code from `/opt/ros/jazzy/`. You build it in an overlay workspace that layers on top of the installed distro. The minimum useful structure:

```
~/ros2_ws/
├── src/
│   ├── my_package/
│   │   ├── package.xml
│   │   ├── setup.py            # or CMakeLists.txt
│   │   └── my_package/
│   └── third_party/            # vendored sources via vcs import
├── build/                      # colcon scratch — gitignore this
├── install/                    # build artifacts — gitignore this
└── log/                        # build logs — gitignore this
```

Create and build it:

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws

# Source the underlay (installed distro) BEFORE building
source /opt/ros/jazzy/setup.bash

# Pull dependencies from package.xml
rosdep install --from-paths src --ignore-src -r -y

# Build. --symlink-install lets you edit Python files without rebuilding.
colcon build --symlink-install

# Source the overlay
source install/setup.bash
```

A few flags you will want often:

```bash
# Build just one package and its dependencies
colcon build --packages-up-to my_package

# Build with Release optimization (default is no optimization for CMake)
colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release

# Run tests
colcon test --packages-select my_package
colcon test-result --verbose

# Clean a single package
rm -rf build/my_package install/my_package
```

### The overlay / underlay pattern

A *workspace* is a directory with `src/`, `build/`, `install/`. When you `source install/setup.bash` of a workspace that was built on top of another, the result is an *overlay* — your local packages shadow the underlay's packages by name.

A common production layout has three layers:

1. **Distro underlay**: `/opt/ros/jazzy/setup.bash` — the installed binaries
2. **Vendor underlay**: `~/vendor_ws/install/setup.bash` — third-party packages built once, rarely touched (Nav2 patches, custom drivers)
3. **Workspace overlay**: `~/ros2_ws/install/setup.bash` — your day-to-day code

Source them in that order — each `source` extends `AMENT_PREFIX_PATH` and friends. If you accidentally source out of order you may see "package not found" for things that are clearly built; usually the fix is `unset` everything and start a fresh shell.

## .bashrc setup

What you put in `.bashrc` is mostly a question of how many distros you juggle. My pattern:

```bash
# ~/.bashrc

# Don't auto-source ROS into every shell — pollutes PATH for other work.
# Use a function instead.
function ros2-jazzy() {
    source /opt/ros/jazzy/setup.bash
    if [ -f ~/ros2_ws/install/setup.bash ]; then
        source ~/ros2_ws/install/setup.bash
    fi
    export ROS_DOMAIN_ID=42
    export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
    echo "ROS 2 Jazzy active, DOMAIN=42, RMW=cyclonedds"
}

function ros2-humble() {
    source /opt/ros/humble/setup.bash
    if [ -f ~/humble_ws/install/setup.bash ]; then
        source ~/humble_ws/install/setup.bash
    fi
    export ROS_DOMAIN_ID=42
    export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
    echo "ROS 2 Humble active, DOMAIN=42, RMW=cyclonedds"
}
```

If you only ever use one distro, sure, source it unconditionally in `.bashrc`. The day you need to evaluate a new release you will regret it.

### ROS\_DOMAIN\_ID

`ROS_DOMAIN_ID` partitions DDS traffic. Two ROS 2 systems on the same LAN with the same `ROS_DOMAIN_ID` will discover each other; with different IDs they will not. Valid range is roughly `0–101`, default is `0`.

Pick a non-zero value per project so you do not accidentally talk to your office mate's robot during testing. Document it in your robot's setup script.

## Source install (development only)

You should not do a source install of the full distro unless you are patching the middleware itself. If you are, the flow is roughly:

```bash
mkdir -p ~/ros2_jazzy/src
cd ~/ros2_jazzy
vcs import --input https://raw.githubusercontent.com/ros2/ros2/jazzy/ros2.repos src
rosdep install --from-paths src --ignore-src -r -y \
    --skip-keys "fastcdr rti-connext-dds-6.0.1 urdfdom_headers"
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
```

This takes 30–90 minutes on a fast workstation. The result is a workspace in `~/ros2_jazzy/install/` that you source instead of `/opt/ros/jazzy/setup.bash`. Authoritative source: [docs.ros.org/en/jazzy/Installation/Alternatives/Ubuntu-Development-Setup.html](https://docs.ros.org/en/jazzy/Installation/Alternatives/Ubuntu-Development-Setup.html) \[verify].

In practice, when I need to patch a single Nav2 package I clone just that package into my workspace's `src/` and let colcon's overlay shadow the binary version. Much faster than a full source build.

## Docker as an alternative

If your host OS is not on the right Ubuntu version, or you want CI parity with the robot, Docker is the cleanest path. The Open Source Robotics Foundation maintains official images at [hub.docker.com/r/osrf/ros](https://hub.docker.com/r/osrf/ros) \[verify].

Useful tags:

| Image                              | Contents                              |
| ---------------------------------- | ------------------------------------- |
| `osrf/ros:jazzy-ros-core`          | Minimal — just `rcl` and CLI tools    |
| `osrf/ros:jazzy-ros-base`          | + common deps, no GUI                 |
| `osrf/ros:jazzy-desktop`           | + rviz2, demo packages                |
| `osrf/ros:jazzy-desktop-full`      | + Gazebo bridge, simulation tools     |

A minimal Dockerfile for a development workspace:

```dockerfile
FROM osrf/ros:jazzy-desktop

RUN apt-get update && apt-get install -y \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ws
COPY src/ src/

RUN . /opt/ros/jazzy/setup.sh \
    && rosdep update \
    && rosdep install --from-paths src --ignore-src -r -y

RUN . /opt/ros/jazzy/setup.sh \
    && colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release

CMD ["/bin/bash"]
```

For GUI tools (rviz2) and GPU passthrough (Isaac ROS, perception), see the `docker-ros2-development` patterns in the skills directory — they cover X11 forwarding, NVIDIA Container Toolkit, and DDS discovery across containers.

## Verifying the install

The fastest end-to-end check:

```bash
# Terminal 1
ros2 run demo_nodes_cpp talker

# Terminal 2
ros2 run demo_nodes_py listener
```

If you see "I heard: [Hello World: N]" the install works, and your two terminals are talking via DDS. If they don't, check:

1. `ROS_DOMAIN_ID` matches in both terminals
2. `RMW_IMPLEMENTATION` matches (or both are unset — uses default)
3. Loopback / multicast is not blocked by `iptables` or `ufw`

`ros2 topic list` and `ros2 node list` should also show the demo talker and listener.

## Common pitfalls

These are the ones I see junior engineers hit weekly.

* **Mixed distros sourced in one shell** — `source /opt/ros/humble/setup.bash` followed by `source /opt/ros/jazzy/setup.bash` puts you in a half-broken state. Symptoms range from cryptic CMake errors to silent ABI corruption at runtime. Always start a fresh shell when switching distros.

* **Sourcing the underlay AFTER your overlay** — your overlay's `setup.bash` extends `AMENT_PREFIX_PATH` based on what was set when it was built. Source the underlay first, every time.

* **Forgetting `ROS_DOMAIN_ID`** — your robot and your laptop are both on domain `0` by default. The first time you run a multi-robot lab demo you will see ghost topics from your colleague's machine.

* **`rosdep install` skipped** — `colcon build` will fail with missing system packages and the error message rarely points to the missing apt package. Always run `rosdep install --from-paths src --ignore-src -r -y` after pulling new sources.

* **`--symlink-install` with C++** — symlink install symlinks Python files into `install/`, but C++ binaries are still copied. Editing Python works without rebuilding; editing C++ still needs `colcon build`. Easy to forget.

* **Building in Debug mode by accident** — `colcon build` defaults to no `-DCMAKE_BUILD_TYPE`, which on most compilers means no optimization. Your code will be 5–20x slower than necessary. Always pass `--cmake-args -DCMAKE_BUILD_TYPE=Release` for anything you'll measure.

* **Stale `build/` after a `package.xml` change** — colcon caches dependency graphs. After changing `package.xml`, sometimes `colcon build` doesn't pick up the new dep. Nuke `build/<pkg>/` and rebuild that package.

* **`use_sim_time` mismatch** — when you launch alongside a simulator (Gazebo, Isaac Sim), every node needs `use_sim_time: True` or the clocks drift. The launch parameter is `use_sim_time`; the env variable does nothing.

* **Cyclone vs Fast DDS discovery** — they will technically interop, but discovery times can blow up. Pin `RMW_IMPLEMENTATION` to one across all nodes on the network. See [DDS and QoS](dds-qos.md).

## Where to go next

* [DDS and QoS](dds-qos.md) — the part of ROS 2 that will bite you next.
* [Lifecycle and Composition](lifecycle-and-composition.md) — once you have a multi-node bringup that needs determinism.
* The official tutorials at [docs.ros.org/en/jazzy/Tutorials.html](https://docs.ros.org/en/jazzy/Tutorials.html) \[verify] are still the right place to learn the CLI muscle memory.
