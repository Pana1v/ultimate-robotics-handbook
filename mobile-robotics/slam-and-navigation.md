---
icon: map-location
---

# SLAM and Navigation

{% hint style="info" %}
**This is the introductory SLAM page.** For the full treatment — modern visual / LiDAR / learned SLAM, sensor fusion, graph optimization, ICP variants, and benchmarking — see the dedicated [SLAM & State Estimation](../slam-and-state-estimation/) section. Pan's case study on building [GO-SLAM from scratch](../authors-projects/go-slam.md) is over there too.
{% endhint %}

### **Simultaneous Localization and Mapping (SLAM)**

SLAM is the computational problem of a robot constructing a map of an unknown environment while simultaneously keeping track of its own location (pose: position and orientation) within that map [1](https://www.flyability.com/blog/simultaneous-localization-and-mapping)[11](https://en.wikipedia.org/wiki/Simultaneous_localization_and_mapping). It's like waking up in an unfamiliar place and trying to draw a map while also figuring out where you are on that map [15](https://ouster.com/insights/blog/introduction-to-slam-simultaneous-localization-and-mapping).

### **How SLAM Works**

The SLAM process generally involves these key steps:

1. **Sensing:** The robot uses sensors (e.g., LiDAR, cameras, sonar, IMUs) to gather data about its surroundings and its own movement [1](https://www.flyability.com/blog/simultaneous-localization-and-mapping)[3](https://www.surveyinggroup.com/what-is-slam-and-how-does-it-works/).
   * **LiDAR (Light Detection and Ranging):** Provides precise distance measurements, creating a point cloud of the environment. Excellent for accuracy but can be expensive [5](https://arxiv.org/pdf/1611.09436.pdf).
   * **Cameras (Visual SLAM - VSLAM):** Use visual features from images to map and localize. Cost-effective but sensitive to lighting conditions and can struggle in featureless environments [13](https://milvus.io/ai-quick-reference/what-is-visual-slam-and-how-is-it-used-in-robotics)[18](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2024.1347985/full). ORB-SLAM is a popular VSLAM method [17](https://www.linkedin.com/pulse/type-slam-robotics-prakash-thangavel).
   * **IMU (Inertial Measurement Unit):** Measures orientation and motion, helping to reduce drift and improve pose estimation [8](https://milvus.io/ai-quick-reference/how-do-robots-use-slam-simultaneous-localization-and-mapping-algorithms-for-navigation).
2. **Landmark Extraction/Feature Detection:** The system identifies distinctive, stationary features or landmarks in the sensor data (e.g., corners, edges, distinct objects) [1](https://www.flyability.com/blog/simultaneous-localization-and-mapping)[19](https://dspace.mit.edu/bitstream/handle/1721.1/119149/16-412j-spring-2005/contents/projects/1aslam_blas_repo.pdf).
3. **Data Association:** The robot determines if currently observed landmarks are new or have been seen before. This is crucial for correcting position estimates and closing loops [19](https://dspace.mit.edu/bitstream/handle/1721.1/119149/16-412j-spring-2005/contents/projects/1aslam_blas_repo.pdf).
4. **State Estimation & Map Update:** Using probabilistic algorithms (like Kalman Filters, Particle Filters, or Graph-based optimization), SLAM estimates the robot's current pose and updates the map. This is an iterative process [9](https://www.sciencedirect.com/science/article/abs/pii/S0926580524000803)[11](https://en.wikipedia.org/wiki/Simultaneous_localization_and_mapping).
   * **Extended Kalman Filter (EKF-SLAM):** One of the earliest approaches, updates robot pose and landmark positions [19](https://dspace.mit.edu/bitstream/handle/1721.1/119149/16-412j-spring-2005/contents/projects/1aslam_blas_repo.pdf).
   * **Particle Filter (PF-SLAM / Gmapping):** Uses a set of particles to represent possible robot poses, good for non-linear problems [8](https://milvus.io/ai-quick-reference/how-do-robots-use-slam-simultaneous-localization-and-mapping-algorithms-for-navigation)[14](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2021.618268/full).
   * **GraphSLAM:** Represents the problem as a graph where nodes are robot poses and landmarks, and edges are constraints from observations. Optimizes the entire trajectory and map [11](https://en.wikipedia.org/wiki/Simultaneous_localization_and_mapping).
5. **Loop Closure:** When a robot re-observes a previously mapped area, it "closes the loop." This significantly reduces accumulated errors (drift) in the map and pose estimates, leading to a more consistent global map [8](https://milvus.io/ai-quick-reference/how-do-robots-use-slam-simultaneous-localization-and-mapping-algorithms-for-navigation)[10](https://www.linkedin.com/advice/3/what-pros-cons-using-slam-navigation-skills-ros).

### **Types of SLAM**

* **LiDAR SLAM:** Relies on laser scanners for high-precision mapping [1](https://www.flyability.com/blog/simultaneous-localization-and-mapping).
* **Visual SLAM (VSLAM):** Uses cameras as the primary sensor. Can be monocular (one camera), stereo (two cameras), or RGB-D (color + depth) [13](https://milvus.io/ai-quick-reference/what-is-visual-slam-and-how-is-it-used-in-robotics).
* **Multi-Robot SLAM:** Multiple robots collaborate to build a map, which presents challenges in data fusion and scalability [14](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2021.618268/full).

### **Pros of SLAM**

* Enables navigation in unknown or dynamic environments without pre-existing maps [10](https://www.linkedin.com/advice/3/what-pros-cons-using-slam-navigation-skills-ros).
* Can create detailed maps for various applications (e.g., 3D model reconstruction, path planning) [9](https://www.sciencedirect.com/science/article/abs/pii/S0926580524000803)[15](https://ouster.com/insights/blog/introduction-to-slam-simultaneous-localization-and-mapping).
* Adapts to changes in the environment by updating the map in real-time [10](https://www.linkedin.com/advice/3/what-pros-cons-using-slam-navigation-skills-ros).
* Sensor fusion can lead to robust and accurate localization [8](https://milvus.io/ai-quick-reference/how-do-robots-use-slam-simultaneous-localization-and-mapping-algorithms-for-navigation).

### **Cons of SLAM**

* Computationally intensive, especially for large environments or high-resolution maps [10](https://www.linkedin.com/advice/3/what-pros-cons-using-slam-navigation-skills-ros).
* Sensitive to sensor noise, poor lighting (for VSLAM), or featureless environments, which can lead to map drift or failure [10](https://www.linkedin.com/advice/3/what-pros-cons-using-slam-navigation-skills-ros).
* Loop closure detection can be challenging and critical for long-term accuracy [14](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2021.618268/full).
* Dynamic objects (e.g., moving people) can confuse the mapping process if not handled properly [6](https://scholar9.com/publication/e46a210422dfb207baa1149a38d4118a.pdf)[13](https://milvus.io/ai-quick-reference/what-is-visual-slam-and-how-is-it-used-in-robotics).

***

### **Navigation in Robotics**

Navigation encompasses the ability of a robot to determine its own position and then plan and follow a path to a goal location while avoiding obstacles [6](https://scholar9.com/publication/e46a210422dfb207baa1149a38d4118a.pdf)[7](https://algocademy.com/blog/algorithms-in-robotics-pathfinding-and-navigation/). SLAM provides the map and localization, which are crucial inputs for navigation algorithms [10](https://www.linkedin.com/advice/3/what-pros-cons-using-slam-navigation-skills-ros).

The navigation process typically involves:

1. **Perception:** Using sensors to understand the environment, detect obstacles, and identify navigable paths [6](https://scholar9.com/publication/e46a210422dfb207baa1149a38d4118a.pdf)[20](https://www.sciencedirect.com/topics/computer-science/robot-navigation). This is where SLAM-generated maps are used.
2. **Localization:** Determining the robot's current position and orientation on the map (often provided by the SLAM system) [7](https://algocademy.com/blog/algorithms-in-robotics-pathfinding-and-navigation/)[20](https://www.sciencedirect.com/topics/computer-science/robot-navigation). Algorithms like AMCL (Adaptive Monte Carlo Localization) are commonly used for localization on a pre-existing map [10](https://www.linkedin.com/advice/3/what-pros-cons-using-slam-navigation-skills-ros).
3. **Path Planning:** Calculating an optimal or feasible path from the robot's current location to a target destination, considering the map and avoiding obstacles [4](https://www.tandfonline.com/doi/full/10.1080/23311916.2019.1632046)[6](https://scholar9.com/publication/e46a210422dfb207baa1149a38d4118a.pdf).
   * **Global Path Planning:** Finds a path using the entire known map. Algorithms include:
     * **Dijkstra's Algorithm:** Finds the shortest path in a graph [16](https://www.slideshare.net/slideshow/robotics-navigation-238327631/238327631).
     * **A\* (A-star):** A heuristic search algorithm, often more efficient than Dijkstra's for finding the shortest path [5](https://arxiv.org/pdf/1611.09436.pdf)[16](https://www.slideshare.net/slideshow/robotics-navigation-238327631/238327631).
   * **Local Path Planning:** Reacts to immediate surroundings and dynamic obstacles, making real-time adjustments to the global path. Algorithms include:
     * **Potential Field Method:** Treats the robot as a particle in a field of forces, attracted to the goal and repelled by obstacles [7](https://algocademy.com/blog/algorithms-in-robotics-pathfinding-and-navigation/)[16](https://www.slideshare.net/slideshow/robotics-navigation-238327631/238327631).
     * **Dynamic Window Approach (DWA):** Samples velocities and predicts trajectories to choose a safe and efficient motion.
4. **Motion Control:** Executing the planned path by sending commands to the robot's actuators (e.g., motors) [5](https://arxiv.org/pdf/1611.09436.pdf). This involves feedback control to correct for errors and ensure the robot stays on track.
5. **Obstacle Avoidance:** Detecting and maneuvering around unexpected or dynamic obstacles not present in the initial map or global path [5](https://arxiv.org/pdf/1611.09436.pdf)[6](https://scholar9.com/publication/e46a210422dfb207baa1149a38d4118a.pdf). This is often handled by local planners.

### **Key Elements of Robot Navigation**

* **Environment Mapping:** Creating a representation of the surroundings (often from SLAM) [7](https://algocademy.com/blog/algorithms-in-robotics-pathfinding-and-navigation/).
* **Localization:** Knowing where the robot is [7](https://algocademy.com/blog/algorithms-in-robotics-pathfinding-and-navigation/).
* **Path Planning:** Deciding where to go [7](https://algocademy.com/blog/algorithms-in-robotics-pathfinding-and-navigation/).
* **Obstacle Avoidance:** Safely moving without collisions [7](https://algocademy.com/blog/algorithms-in-robotics-pathfinding-and-navigation/).
* **Real-time Decision Making:** Adapting to changes and unforeseen events [7](https://algocademy.com/blog/algorithms-in-robotics-pathfinding-and-navigation/).

***

### **Applications of SLAM and Navigation**

* **Autonomous Vehicles:** Self-driving cars use SLAM and navigation to perceive roads, plan routes, and avoid obstacles [2](https://www.mathworks.com/discovery/slam.html)[7](https://algocademy.com/blog/algorithms-in-robotics-pathfinding-and-navigation/).
* **Robotic Vacuums:** Home cleaning robots map rooms and navigate efficiently using SLAM [1](https://www.flyability.com/blog/simultaneous-localization-and-mapping)[2](https://www.mathworks.com/discovery/slam.html).
* **Warehouse Robots:** Automated Guided Vehicles (AGVs) and Autonomous Mobile Robots (AMRs) use these technologies for logistics and material handling [2](https://www.mathworks.com/discovery/slam.html)[7](https://algocademy.com/blog/algorithms-in-robotics-pathfinding-and-navigation/).
* **Drones (UAVs):** Navigate indoors (where GPS is unavailable) or explore unknown areas for tasks like inspection, delivery, or search and rescue [7](https://algocademy.com/blog/algorithms-in-robotics-pathfinding-and-navigation/)[13](https://milvus.io/ai-quick-reference/what-is-visual-slam-and-how-is-it-used-in-robotics).
* **Planetary Rovers & Exploration:** Robots exploring Mars or other hazardous environments rely on SLAM to map and navigate terrain where no prior maps exist [1](https://www.flyability.com/blog/simultaneous-localization-and-mapping)[7](https://algocademy.com/blog/algorithms-in-robotics-pathfinding-and-navigation/)[15](https://ouster.com/insights/blog/introduction-to-slam-simultaneous-localization-and-mapping).
* **Augmented Reality (AR) / Virtual Reality (VR):** SLAM helps track device pose for overlaying digital information onto the real world or creating immersive virtual experiences [11](https://en.wikipedia.org/wiki/Simultaneous_localization_and_mapping).

***

### **Challenges and Future Directions**

* **Dynamic Environments:** Handling moving obstacles, changing layouts, and other dynamic elements remains a significant challenge [7](https://algocademy.com/blog/algorithms-in-robotics-pathfinding-and-navigation/)[14](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2021.618268/full).
* **Scalability:** Applying SLAM and navigation to very large-scale environments or with many robots requires efficient algorithms and distributed processing [7](https://algocademy.com/blog/algorithms-in-robotics-pathfinding-and-navigation/)[14](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2021.618268/full).
* **Robustness & Reliability:** Ensuring consistent performance across diverse conditions (lighting, weather, sensor noise) is crucial for real-world deployment [10](https://www.linkedin.com/advice/3/what-pros-cons-using-slam-navigation-skills-ros).
* **Sensor Fusion:** Effectively combining data from multiple heterogeneous sensors to get a more complete and reliable understanding of the environment [6](https://scholar9.com/publication/e46a210422dfb207baa1149a38d4118a.pdf).
* **Deep Learning:** Integrating machine learning and deep learning for improved perception, semantic understanding of scenes, and more adaptive navigation strategies [6](https://scholar9.com/publication/e46a210422dfb207baa1149a38d4118a.pdf)[7](https://algocademy.com/blog/algorithms-in-robotics-pathfinding-and-navigation/).
