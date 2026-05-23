---
icon: gears
---

# Common Mechanisms

### Flywheel Shooter <a href="#flywheel-shooter" id="flywheel-shooter"></a>

<img src="https://www.vexforum.com/uploads/default/original/3X/1/2/1211f7d7e1a73c2e62dfa10fe5a3bdc97d5dc717.gif" alt="" data-size="original">

Construction

* Two counter-rotating wheels (often with compliant covers) mounted on motor shafts, spaced to pinch a round projectile.
* Motors may include encoders for closed-loop speed control.

Use Cases

* Rapid-fire launch of small, spherical game pieces (e.g., Power Cells, foam balls).

Advantages

* Continuous, high-rate firing-no reload cycle time needed.
* Velocity (and thus range) can be tuned on the fly by adjusting wheel speed.

Disadvantages

* Only handles round objects reliably-non-spherical items slip or jam. 2
* Motor speed (and shot consistency) falls off as battery voltage drops unless actively regulated by encoders. 2

### Striker (“Impact”) Shooter <a href="#striker-impact-shooter" id="striker-impact-shooter"></a>

<figure><img src="https://blogs.mathworks.com/student-lounge/files/2021/05/simvsactual_kicking.gif?file=2021/05/simvsactual_kicking.gif" alt=""><figcaption></figcaption></figure>

Construction

* Rigid striker arm or plate driven by a geared motor or spring, which impacts the projectile to launch it.
* Includes a pull-back mechanism (e.g., a torque motor with gear train) to reset the striker.

Use Cases

* Launching flat or irregular objects (pucks, square blocks) that cannot be gripped by wheels.

Advantages

* Compatible with a wide variety of shapes and sizes. 2
* Range adjustable by tuning spring tension or motor torque. 2

Disadvantages

* Energy loss to friction when the object slides against a surface reduces distance. 2
* High impact loads cause wear on linkages and mounting hardware. 2
* Reset mechanism adds cycle time and mechanical complexity. 2

### Catapult/Popper Shooter <a href="#catapultpopper-shooter" id="catapultpopper-shooter"></a>

![](https://media.tenor.com/V7SrMQFh3IwAAAAM/catapult-cat.gif)

Construction

* Elastic element (rubber band or spring) attached to an arm linkage, latched by a servo or pin.
* Release mechanism discharges stored energy to fling the projectile.

Use Cases

* Single-shot loops at moderate rate for uniform, repeatable distance (e.g., tennis-ball poppers, small foam ring launchers).

Advantages

* Very consistent shot energy and accuracy thanks to fixed spring tension. [6](https://www.reddit.com/r/FRC/comments/bienj1/shooter_mechanisms_introduction/)
* Simple control: prime once, trigger, then re-prime.

Disadvantages

* Fixed launch distance unless spring tension is manually adjusted between shots. [6](https://www.reddit.com/r/FRC/comments/bienj1/shooter_mechanisms_introduction/)
* Mechanical linkage must absorb high forces, leading to potential fatigue and breakage.&#x20;

### Linear Motion Guides <a href="#linear-motion-guides" id="linear-motion-guides"></a>

<figure><img src="https://i.makeagif.com/media/8-18-2016/4Qco1d.gif" alt="" width="375"><figcaption><p>Linear Travel Guide using Stepper motor and Timing belt</p></figcaption></figure>

<figure><img src="https://i.pinimg.com/originals/d9/00/e3/d900e36a1eba1cf95ecda87e681f17a6.gif" alt="" width="375"><figcaption><p>Whit Worth Mechanism</p></figcaption></figure>

**Construction:** Aluminum extrusion or steel rail profiles with rolling or plain bearings (linear slides, drawer slides, profile rails). [2](https://gm0.org/en/latest/docs/common-mechanisms/index.html)\
Use Cases

* Robot lifts, elevators, extendable arms, precise slide mechanisms\
  Advantages
* Recirculating bearings: smooth, low friction under load
* Profile rails: tight tolerances, long life\
  Disadvantages
* Adds weight and cost
* Requires precise alignment and mounting

### Arms & Elevators <a href="#arms--elevators" id="arms--elevators"></a>

<figure><img src="https://www.chiefdelphi.com/uploads/default/original/3X/4/f/4fb0d2a1f59cd99348127f762fa7b14bc2660981.gif" alt="" width="375"><figcaption><p>Continuous Elevator Mechanism</p></figcaption></figure>

<figure><img src="../.gitbook/assets/image (1).png" alt=""><figcaption><p>Retractable Elevator Arm</p></figcaption></figure>

**Construction:** Pivoting bars or telescoping frames driven by motors, winches, or actuators; may include cascade or continuous-loop rigging. [2](https://gm0.org/en/latest/docs/common-mechanisms/index.html)\
Use Cases

* Scoring at various heights, reaching over obstacles
* Gripper positioning and manipulator extension\
  Advantages
* Pivot arms: simple kinematics, compact stowage
* Telescopes: extendable range, rigid at full height\
  Disadvantages
* Pivot: limited vertical reach without long links
* Telescopes: mechanical complexity, potential binding

### Linkages <a href="#linkages" id="linkages"></a>

<figure><img src="https://i.pinimg.com/originals/1e/14/14/1e14141edc9ecb6942f91f9a99642fa4.gif" alt="" width="375"><figcaption><p>4-Bar Linkage Gripper</p></figcaption></figure>

<figure><img src="https://upload.wikimedia.org/wikipedia/commons/f/f4/ExtraSimpleWalkerBaseMechanism.gif" alt="" width="375"><figcaption><p>Simple Linkage Mechanism</p></figcaption></figure>

<figure><img src="https://codeavour.org/wp-content/uploads/2024/11/20240913-LR-Assembly-Linkage-Corner-Joint-2.gif" alt="" width="188"><figcaption><p>Rotary Linkage (Joint)</p></figcaption></figure>

<figure><img src="https://global.discourse-cdn.com/sketchup/original/3X/6/4/642148de48380d976973a66b396e700e01752966.gif" alt="" width="188"><figcaption><p>HInge</p></figcaption></figure>



**Construction:** Rigid links connected by revolute (pin) joints, forming Four-Bar, Parallel (pantograph), Scissor, Corner, or Cross linkages. [2](https://gm0.org/en/latest/docs/common-mechanisms/index.html)\
Use Cases

* Converting rotary motor motion into complex planar or vertical motion
* Lifts, level platforms, bilateral extension\
  Advantages
* Four-Bar: predictable motion path, adjustable leverage
* Scissor: large vertical extension in compact footprint
* Pantograph: maintain parallel output motion\
  Disadvantages
* Multiple joints: cumulative backlash and wear
* Scissor: linkage binding without precise fabrication

### Passive Intakes & Claws <a href="#passive-intakes--claws" id="passive-intakes--claws"></a>

<figure><img src="../.gitbook/assets/1586981532434-robot-handCloseClaw (2).gif" alt=""><figcaption><p>Servo Powered Gripper</p></figcaption></figure>

<figure><img src="https://d2t1xqejof9utc.cloudfront.net/screenshots/pics/df67d7efe51bab887a14ada8b844fe42/large.gif" alt=""><figcaption><p>Adaptive Claw</p></figcaption></figure>

**Construction:** Fixed mounting plates with compliant materials (rubber bands, foam), passive rollers or fingers. [2](https://gm0.org/en/latest/docs/common-mechanisms/index.html)\
Use Cases

* Gripping variable-shape game pieces without active actuation
* Centering objects against a backplate for further processing\
  Advantages
* Low complexity, minimal actuators required
* Gentle on game pieces, self-centering behavior\
  Disadvantages
* Limited gripping force, shape dependence
* No active release control

### Active Intakes <a href="#active-intakes" id="active-intakes"></a>

<figure><img src="https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEhynjJWX8LGjBu6D62DBff58kP03N6svu9xHzDssUexWyuW9OeWuGiwwTjUL97wEss8RBZ1f-ogMnfWyd5P8xiPfhaXPAdIaGN37Ws5k2udVBJOAuWXeW09M7sbshJNkDoFQeRqBLlB8rc/s1600/virtual+4+bar+gif+11in+cube.gif" alt=""><figcaption><p>Active Intake with Gripper</p></figcaption></figure>

<figure><img src="https://images.squarespace-cdn.com/content/v1/5ad3744596e76f5d16eb7704/1555726192057-L08JW1LDZKVKKMR7MQW1/cargo-intake.gif" alt=""><figcaption><p>Active Intake</p></figcaption></figure>

**Construction:** Powered rollers, wheels, or pneumatic fingers mounted on pivoting arms or frames. [2](https://gm0.org/en/latest/docs/common-mechanisms/index.html)\
Use Cases

* High-speed collection of balls, cubes, rings, or custom game pieces
* Feeding objects into indexers or shooters\
  Advantages
* Controlled grasping and ejection, high throughput
* Adjustable speed and torque for different materials\
  Disadvantages
* Additional motors or pneumatics add weight and draw current
* Complex timing and synchronization with downstream subsystems

### Transfers & Indexers <a href="#transfers--indexers" id="transfers--indexers"></a>

**Construction:** Belt or roller conveyors, pneumatic gates, channel guides, and staging shelves. [2](https://gm0.org/en/latest/docs/common-mechanisms/index.html)\
Use Cases

* Sequencing multiple game pieces, buffering under shooters or scoring mechanisms
* Automated stacking or batch delivery\
  Advantages
* Precise object positioning, continuous feeding
* Scalable to multiple game-piece types\
  Disadvantages
* Added length and mass on the robot
* Requires control logic to avoid jams

### Dead (Idle) Wheels <a href="#dead-idle-wheels" id="dead-idle-wheels"></a>

**Construction:** Free-spinning omni or traction wheels mounted on bearings, used as load-bearing supports. [2](https://gm0.org/en/latest/docs/common-mechanisms/index.html)\
Use Cases

* Reducing friction on non-driving corners
* Stabilizing mechanisms or gantry plates\
  Advantages
* Simple, passive way to carry loads without consuming motor power
* Minimal wear on drive motors\
  Disadvantages
* Adds drag if misaligned
* Does not contribute to motion

### Turrets <a href="#turrets" id="turrets"></a>

<figure><img src="https://i.ytimg.com/vi/9AV4Tij1c5I/maxresdefault.jpg?sqp=-oaymwEmCIAKENAF8quKqQMa8AEB-AH-CYAC0AWKAgwIABABGGUgXyhDMA8=&#x26;rs=AOn4CLAFdZk46ZJnbWWm08GL_xMtc7rAng" alt=""><figcaption><p>Turret Actuation</p></figcaption></figure>

<figure><img src="https://www.chiefdelphi.com/uploads/default/original/3X/b/d/bdcc7742fe29ba03d42eedc89f6ee95c3c1f8d8d.gif" alt=""><figcaption><p>Turret</p></figcaption></figure>

**Construction:** Rotating subplate on thrust bearings or lazy-Susans, driven by motors or servos. [2](https://gm0.org/en/latest/docs/common-mechanisms/index.html)\
Use Cases

* Aiming shooters or sensors independently of chassis orientation
* Multi-directional intake or scoring without turning the robot\
  Advantages
* Decouples turret and chassis control, rapid targeting
* Enables continuous rotation and precise angular positioning\
  Disadvantages
* Complex wiring management (slip rings or cable chains)
* Increased mass and higher center of gravity

### Forklift Mechanisms <a href="#forklift-mechanisms" id="forklift-mechanisms"></a>

<figure><img src="https://technologystudent.com/images3/rkpn4.gif" alt=""><figcaption><p>One of the implementations for lesser load, for higher loads a tension string is also reccomended</p></figcaption></figure>

![](https://i.makeagif.com/media/10-17-2019/kK6oQ-.gif)![](https://sc01.alicdn.com/kf/HTB1qvb8gYwrBKNjSZPc5jXpapXa8/231818923/HTB1qvb8gYwrBKNjSZPc5jXpapXa8.gif)

Above shown Screw and Belt Driven Linear Guides can also be used

**Construction**

* A rigid rectangular frame built from metal tubing or plates supports four drive motors with reduction gearing and a single H-bridge controller for traction and steering[6](https://blog.robotiq.com/bid/65794/magnetic-robot-end-effector-top-5-pros-and-cons).
* A vertical lift assembly uses profile rails or linear slide tracks on each side to guide motion, with a rack-and-pinion driven by a DC motor to raise and lower forks or a carriage2.
* Ultrasonic distance sensors mounted near the base detect shelf or object positions and trigger lift actions, all wired through a microcontroller (e.g., Arduino Uno) and soldered onto a breadboard for flexible I/O expansion2.

**Use Cases**

* Warehouse and warehouse-style competition challenges requiring precise fork positioning under pallets or blocks.
* Educational projects demonstrating pick-and-place automation, obstacle avoidance, and sensor integration.

**Advantages**

* High load capacity and stable vertical motion when properly counterbalanced.
* Precise height control via gear reduction and encoder feedback.
* Modular design allows easy adjustment of fork width and lift height.

**Disadvantages**

* Heavy lift assemblies can unbalance the drive base, requiring careful weight distribution or repositioning of components2.
* Increased mechanical complexity and part count raise build time and maintenance.
* Rack-and-pinion systems can bind if rails are misaligned or not lubricated.

### Robotic Grippers <a href="#robotic-grippers" id="robotic-grippers"></a>

**Mechanical Grippers**

![](https://media3.giphy.com/media/WQIN9lgizkXMgsftJ1/200w.gif?cid=6c09b952o2rbkwi508jkogf2thbv2hlplgtx2v8cdwmcdnjy\&ep=v1_gifs_search\&rid=200w.gif\&ct=g)![](https://i.pinimg.com/originals/09/50/eb/0950ebd72d7252cfca67b3a57c43279a.gif)![](https://makerworld.bblmw.com/makerworld/model/USaa761c0a98ea6b/design/2024-03-02_107745c8c8b61.gif)

* Construction: Two or more rigid fingers actuated by servos, motors, or linkages; often include compliant pads for better friction[3](http://engineering.nyu.edu/mechatronics/projects/ME7836/spring2018/Arduino_mini_project/AUTONOMOUSFORKLIFTBOT/report.pdf).
* Use Cases: General-purpose part handling, from small rigid game pieces to irregular objects in warehouses.
* Advantages: High grip force, adaptability to varied geometries, straightforward control.
* Disadvantages: Complex designs for large workpieces, increased weight, limited softness for fragile items[3](http://engineering.nyu.edu/mechatronics/projects/ME7836/spring2018/Arduino_mini_project/AUTONOMOUSFORKLIFTBOT/report.pdf).

**Vacuum Grippers**

<figure><img src="https://hips.hearstapps.com/popularmechanics/assets/17/38/1505931737-adhesive.gif" alt=""><figcaption><p>Vacuum Gripper</p></figcaption></figure>

* Construction: Suction cups linked to a vacuum pump or venturi generator, often with integrated pressure sensors[4](https://www.hvrmagnet.com/blog/robotic-grippers-advantages-and-disadvantages/).
* Use Cases: Handling flat, smooth panels, sheet goods, glass, and light game elements.
* Advantages: Simple design, fast pick-and-place cycles, low profile for tight spaces.
* Disadvantages: Only works on non-porous surfaces; rubber cups wear and require frequent replacement[3](http://engineering.nyu.edu/mechatronics/projects/ME7836/spring2018/Arduino_mini_project/AUTONOMOUSFORKLIFTBOT/report.pdf).

**Magnetic Grippers**

<figure><img src="https://www.hvrmagnet.com/blog/wp-content/uploads/2021/12/GIF-1.gif" alt=""><figcaption><p>Magnetic Gripper</p></figcaption></figure>

* Construction: Electromagnets, permanent magnets, or electro-permanent magnets embedded in a flat contact pad[3](http://engineering.nyu.edu/mechatronics/projects/ME7836/spring2018/Arduino_mini_project/AUTONOMOUSFORKLIFTBOT/report.pdf)[5](https://www.robots.com/articles/grippers-for-robots).
* Use Cases: Lifting ferrous parts, sheet metal handling, assembly tasks with metallic game pieces.
* Advantages: Single contact surface, rapid gripping, minimal structural components, energy-efficient (permanent/electro-permanent)[3](http://engineering.nyu.edu/mechatronics/projects/ME7836/spring2018/Arduino_mini_project/AUTONOMOUSFORKLIFTBOT/report.pdf)[5](https://www.robots.com/articles/grippers-for-robots).
* Disadvantages: Limited to ferrous materials, reduced holding force if surfaces are oily or covered in debris, parts may retain magnetism[3](http://engineering.nyu.edu/mechatronics/projects/ME7836/spring2018/Arduino_mini_project/AUTONOMOUSFORKLIFTBOT/report.pdf)[5](https://www.robots.com/articles/grippers-for-robots).

**Pneumatic Grippers**

![](https://i.makeagif.com/media/10-31-2021/FXU2PU.gif)![](https://i.makeagif.com/media/3-25-2016/BR1KiP.gif)![](https://d2t1xqejof9utc.cloudfront.net/screenshots/pics/3dc2efe423c1f55732962568aeb8d35a/large.gif)![](https://media1.giphy.com/media/Kz3x7cl4SN1zSeWPSm/giphy.gif?cid=6c09b952o2rbkwi508jkogf2thbv2hlplgtx2v8cdwmcdnjy\&ep=v1_gifs_search\&rid=giphy.gif\&ct=g)

* Construction: Parallel or angular jaw fingers driven by air cylinders, with flow control valves for speed and force tuning[4](https://www.hvrmagnet.com/blog/robotic-grippers-advantages-and-disadvantages/).
* Use Cases: High-speed pick-and-place, automated packaging, fluid-tight sealing in assembly.
* Advantages: High force-to-weight ratio, fast actuation, built-in compliance.
* Disadvantages: Requires compressed air infrastructure, noisy operation, potential air leaks.

**Servo-Electric Grippers**

![](https://d2t1xqejof9utc.cloudfront.net/screenshots/pics/7203e21784acae125abf0f5c62fb2cb9/large.gif)![](https://cdn.shopifycdn.net/s/files/1/0084/2799/5187/files/6_4d35b36a-1fb3-44b3-9e53-46cf1ddeb343.gif?v=1647564810)![](https://media.printables.com/media/prints/403482/images/3358009_e15a5169-52c2-4126-bcc0-fe2914e47cdf/thumbs/inside/1280x960/jpg/18db8080b42e32ebe3a4fd084945e65c.webp)

* Construction: Brushless or stepper motors with gearboxes driving finger linkages, often with integrated position and force sensors[4](https://www.hvrmagnet.com/blog/robotic-grippers-advantages-and-disadvantages/).
* Use Cases: Precision handling in electronics assembly, variable-force tasks in competition robots.
* Advantages: Precise position and force control, easy integration with digital controllers, low maintenance.
* Disadvantages: Higher cost, more complex control algorithms, potential heat generation in continuous use.
