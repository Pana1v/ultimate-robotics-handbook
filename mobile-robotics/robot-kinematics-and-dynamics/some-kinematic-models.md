# Some Kinematic Models

### **Differential Drive Robots**

A differential wheeled robot is a mobile robot whose movement is based on two independently driven wheels placed on a common axis, one on each side of the robot body. This is a very common and simple drive mechanism for mobile robots.

### **Principle of Operation**

The robot's motion is controlled by varying the relative speed and direction of its two drive wheels:

* **Straight Line Motion:** If both wheels are driven in the same direction and at the same speed, the robot moves in a straight line (forwards or backwards).
* **Rotation in Place:** If both wheels are driven at the same speed but in opposite directions, the robot will rotate about the central point of the axis connecting the wheels.
* **Curved Motion:** If the wheels are driven at different speeds or in different directions (but not perfectly opposite at the same speed), the robot will follow a curved path. The robot rotates about a point known as the Instantaneous Center of Curvature (ICC) or Instantaneous Center of Rotation (ICR), which lies along the common axis of the two wheels. The distance to this ICC determines the radius of the curve.

Differential drive robots typically have one or more passive caster wheels for balance and support.

### **Kinematics of Differential Drive Robots**

Let's define the parameters.

The radius of each drive wheel is denoted by r.

$$r$$\
The distance between the centers of the two drive wheels (the wheelbase or track width) is denoted by L.\
$$L$$\
The linear velocities of the left and right wheels along the ground, respectively, are denoted by V with subscripts L and R.

$$V_{L}  \\ V_{R}$$\
The angular velocities of the left and right wheels, respectively, are denoted by ω with subscripts L and R.

$$\omega_{L} \\ \omega_{R}$$\
Thus, the linear velocities of the wheels can be expressed in terms of their angular velocities and radius:\
$$V_{L} = \omega_{L} \cdot r \\ V_{R} = \omega_{R} \cdot r$$\
The linear velocity of the center point of the robot's axle is denoted by v.

$$v$$\
The angular velocity of the robot's body around the ICC is denoted by ω.

$$\omega$$\
The position of the robot's center in a global coordinate frame is represented by x and y coordinates.\
$$(x, y)$$\
The orientation (heading angle) of the robot with respect to the global X-axis is denoted by θ.\
$$\theta$$

**Forward Kinematics**\
Forward kinematics determines the robot's motion, specifically its linear velocity v and angular velocity ω, and the change in its pose (Δx, Δy, Δθ) given the wheel velocities.

1. **Robot's Linear and Angular Velocity:**\
   The linear velocity v of the robot (midpoint of the axle) and its angular velocity ω are given by the following formulae:\
   $$v = \frac{V_{R} + V_{L}}{2} = \frac{r(\omega_{R} + \omega_{L})}{2}$$\
   $$\omega = \frac{V_{R} - V_{L}}{L} = \frac{r(\omega_{R} - \omega_{L})}{L}$$
2. **Instantaneous Center of Curvature (ICC):**\
   The signed distance R from the ICC to the midpoint of the wheels along the wheel axis is given by:\
   $$R = \frac{L}{2} \frac{V_{R} + V_{L}}{V_{R} - V_{L}}$$\
   (Note: If the right wheel velocity equals the left wheel velocity, then the angular velocity ω is zero, the radius R is infinite, and the robot moves in a straight line. If the right wheel velocity is the negative of the left wheel velocity, then the linear velocity v is zero, the radius R is zero, and the robot spins in place.)
3. **Change in Pose (Odometry):**\
   Over a small time interval, denoted by δt,\
   \delta t\
   the robot's pose (x, y, θ) changes as follows:
   * If the angular velocity ω is approximately zero (indicating the robot is moving straight):\
     The change in the x-coordinate is Δx.\
     $$\Delta x \\ \Delta x = v \cdot \cos(\theta) \cdot \delta t$$\
     The change in the y-coordinate is Δy.\
     $$\Delta y \\ \Delta y = v \cdot \sin(\theta) \cdot \delta t$$\
     The change in orientation is Δθ.\
     $$\Delta \theta \\ \Delta \theta = 0$$
   * If the angular velocity ω is not equal to zero (indicating the robot is turning):\
     The new pose, denoted by (x', y', θ'), after the time interval δt can be calculated. The coordinates of the ICC, (x with subscript ICC, y with subscript ICC), relative to the global frame are:\
     $$x_{ICC}\\ x_{ICC} = x - R \sin(\theta)\\ y_{ICC}\\ y_{ICC} = y + R \cos(\theta)$$\
     The new pose after the time interval δt is then given by these formulae:\
     $$x' \\ x' = x - \frac{v}{\omega}(\sin(\theta) - \sin(\theta + \omega \delta t)) \\ y'\\ y' = y + \frac{v}{\omega}(\cos(\theta) - \cos(\theta + \omega \delta t)) \\ \theta' \\ \theta' = \theta + \omega \delta t \\$$\
     Alternatively, the instantaneous velocity components in the global frame are the time derivatives of x, y, and θ:\
     $$\dot{x} \\ \dot{x} = v \cos(\theta) \\ \dot{y}  \\ \dot{y} = v \sin(\theta) \\ dot{\theta} \\ \dot{\theta} = \omega$$\
     These can be integrated over the time interval δt to find the new pose.

**Inverse Kinematics**\
Inverse kinematics calculates the required individual wheel velocities (linear velocities V with subscripts L and R, or angular velocities ω with subscripts L and R) to achieve a desired robot linear velocity v and angular velocity ω.\
The required wheel ground velocities are:\
$$V_{R} = v + \frac{\omega L}{2} \\ V_{L} = v - \frac{\omega L}{2}$$\
And the required wheel angular velocities are:\
$$\omega_{R} = \frac{V_{R}}{r} = \frac{1}{r} \left(v + \frac{\omega L}{2}\right) \\ \omega_{L} = \frac{V_{L}}{r} = \frac{1}{r} \left(v - \frac{\omega L}{2}\right)$$

### **Advantages of Differential Drive:**

* **Simplicity:** Mechanically and conceptually simple.
* **Low Cost:** Fewer parts compared to more complex steering systems.
* **Maneuverability:** Can turn in place (zero turning radius), making it highly agile in constrained spaces.
* **Ease of Control:** The motion is relatively easy to program and control.

### **Disadvantages of Differential Drive:**

* **Slippage:** The kinematic model assumes no wheel slippage, which is not always true in real-world scenarios, leading to odometry errors.
* **Sensitivity:** Precise control of wheel speeds is necessary for accurate motion. Small differences in wheel speeds or diameters can cause deviation from a straight path.
* **Stability with Casters:** Depending on the number and placement of caster wheels, stability can sometimes be an issue, especially at higher speeds or on uneven surfaces.

***

### **Car-Like (Bicycle) Model Robots**

This model is kinematically equivalent to a bicycle, where typically the front wheel is steerable and one or both wheels can be driven. It's a common model for car-like robots.

### **Principle of Operation**

The robot moves by driving its wheel(s) and changes direction by steering the front wheel. The no-slip condition implies that the wheels' velocity vectors are perpendicular to their axes. The robot rotates around an Instantaneous Center of Rotation (ICR) which is located at the intersection of lines perpendicular to the axes of all wheels.

### **Kinematics of Car-Like (Bicycle) Model**

Let's define the parameters.\
The wheelbase (distance between the center of the front and rear wheels) is denoted by l.

$$l$$\
The steering angle of the front wheel (angle between the robot's longitudinal axis and the direction of the front wheel) is denoted by φ.\
$$\phi$$\
The linear velocity of the robot (often taken at the center of the rear axle for a rear-wheel drive model) is denoted by v.\
$$\phi$$\
The orientation (heading angle) of the robot's body with respect to the global X-axis is denoted by θ.\
$$\theta$$

**Forward Kinematics**\
Given the robot's velocity v (e.g., at the rear axle) and steering angle φ, the robot's motion, specifically the rates of change of its global position and orientation (time derivatives of x, y, and θ), is described by these formulae:\
$$\dot{x} = v \cos(\theta) \\ \dot{y} = v \sin(\theta) \\ \dot{\theta} = \frac{v}{l} \tan(\phi)$$

**Inverse Kinematics**\
Given a desired body twist (commanded linear velocity v with subscript cmd,\
$$v_{cmd}$$\
and commanded angular velocity ω with subscript cmd),\
$$\omega_{cmd}$$\
we need to find the steering angle φ and the driving wheel's velocity (e.g., v with subscript rear for rear-wheel drive).\
The steering angle φ is often a direct command input or can be derived from the desired angular velocity. From the forward kinematics equation for the time derivative of θ, we have:\
$$\tan(\phi) = \frac{\omega l}{v}$$\
So, the required steering angle is:\
$$\phi = \operatorname{atan2}(\omega_{cmd} l, v_{cmd})$$\
(using the $$f(x) = x * e^{2 pi i \xi x}$$ function for quadrant correctness, assuming v with subscript cmd is the robot's commanded forward speed at the reference point).

The velocity command for the driving wheel depends on which wheel is driven:

* **Rear-Wheel Drive:** The velocity of the rear wheel, denoted as v with subscript rear,\
  $$v_{rear}$$\
  is the commanded linear velocity v with subscript cmd of the robot's reference point (rear axle).\
  $$v_{rear} = v_{cmd}$$
* **Front-Wheel Drive:** If the front wheel is driven, its velocity, denoted as v with subscript front,\
  $$v_{front}$$\
  relates to the robot's reference point velocity v (at the rear axle) by the formula:\
  $$v = v_{front} \cos(\phi)$$\
  So, the required front wheel velocity is:\
  $$v_{front} = \frac{v_{cmd}}{\cos(\phi)}$$

### **Advantages of Car-Like Model:**

* **Stability:** Generally more stable at higher speeds than differential drive with casters.
* **Intuitive Control:** Steering is similar to how humans drive cars.

### **Disadvantages of Car-Like Model:**

* **Nonholonomic Constraints:** Cannot move directly sideways. Has a minimum turning radius (unless it's a special design like four-wheel steering).
* **Complexity:** Mechanically more complex than a simple differential drive due to the steering mechanism.
