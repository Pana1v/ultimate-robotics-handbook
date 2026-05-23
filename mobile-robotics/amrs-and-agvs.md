---
icon: user-robot-xmarks
---

# AMR's and AGV's

### **Autonomous Mobile Robots (AMRs) vs. Automated Guided Vehicles (AGVs): A Comprehensive Guide** <a href="#undefined" id="undefined"></a>

<figure><img src="../.gitbook/assets/X5vcEh.gif" alt=""><figcaption></figcaption></figure>

In the realm of industrial automation and logistics, two key technologies are transforming how materials and goods are transported within facilities: **Automated Guided Vehicles (AGVs)** and **Autonomous Mobile Robots (AMRs)**. While both aim to automate internal transport tasks, they differ significantly in their navigation, flexibility, and operational capabilities . Understanding these differences is crucial for businesses looking to optimize their intralogistics operations . This guide delves into the definitions, core technologies, key differences, applications, leading companies, and resources for both AMRs and AGVs.

***

### **1. Understanding AGVs and AMRs**

### **1.1. What are Automated Guided Vehicles (AGVs)?**

**Automated Guided Vehicles (AGVs)** are material handling systems or load carriers that travel autonomously along predefined paths or routes within a facility . They have been a staple in manufacturing and warehouses for decades, typically used for repetitive, point-to-point material transport .

**Key Characteristics of AGVs :**

* **Guided Navigation:** Rely on fixed infrastructure for guidance, such as magnetic stripes on the floor, wires embedded in the concrete, optical sensors following painted lines, or reflective tape markers. Some modern AGVs use laser triangulation or vision guidance for more flexibility but still typically follow programmed paths.
* **Predefined Routes:** Operate on fixed, pre-programmed paths. Deviations require reprogramming or infrastructure changes.
* **Obstacle Detection (Basic):** Can detect obstacles in their path but usually stop and wait for the obstacle to be removed rather than navigating around it. They do not typically reroute themselves.
* **Centralized Control:** Often managed by a centralized fleet management system that dictates routes and schedules.

### **1.2. What are Autonomous Mobile Robots (AMRs)?**

**Autonomous Mobile Robots (AMRs)** are a more advanced generation of automated material handling solutions. AMRs use sophisticated sensors, artificial intelligence (AI), and onboard mapping capabilities to understand their environment and navigate dynamically without fixed infrastructure guides .

**Key Characteristics of AMRs :**

* **Autonomous Navigation:** Utilize technologies like SLAM (Simultaneous Localization and Mapping) to build maps of their environment and navigate independently, adapting to changes . They "learn" their surroundings.
* **Dynamic Path Planning:** Can intelligently plan and adjust their routes in real-time to avoid obstacles and find the most efficient path to their destination. If an obstacle is detected, an AMR will attempt to navigate around it .
* **Infrastructure-Free:** Do not require physical guides like magnetic stripes or wires, allowing for quicker deployment and greater flexibility in changing layouts .
* **Collaborative:** Often designed to work safely alongside humans in shared workspaces (can be considered a type of cobot in some contexts).
* **Intelligence & Adaptability:** Can make decisions based on real-time conditions, contributing to optimized workflows and improved operational efficiency .

***

### **2. AGVs vs. AMRs: Key Differences Tabulated**

| Feature                            | Automated Guided Vehicles (AGVs)                                                                         | Autonomous Mobile Robots (AMRs)                                                                               |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| **Navigation Technology**          | Guided by fixed infrastructure (magnetic stripes, wires, lasers on reflectors, vision following lines) . | Autonomous via onboard sensors (LiDAR, cameras, etc.), SLAM, AI, and pre-loaded or self-created maps .        |
| **Path Flexibility**               | Fixed, predefined paths. Changes require reprogramming/infrastructure modification .                     | Dynamic path planning; can navigate around obstacles and find alternative routes in real-time .               |
| **Obstacle Avoidance**             | Typically stops when an obstacle is detected; waits for removal .                                        | Intelligently navigates around obstacles by re-routing .                                                      |
| **Infrastructure Needs**           | Requires installation of guidance infrastructure (wires, tapes, reflectors) .                            | Minimal infrastructure changes; navigates using existing facility features .                                  |
| **Deployment Time & Cost**         | Longer deployment, higher initial infrastructure cost and disruption .                                   | Faster deployment, lower initial infrastructure cost .                                                        |
| **Scalability & Flexibility**      | Less flexible to layout changes; scalability can be disruptive .                                         | Highly flexible; easily adapts to new layouts or scales up by adding more units .                             |
| **Intelligence & Decision Making** | Limited onboard intelligence; relies on central control for routing .                                    | High onboard intelligence; makes independent navigation decisions based on real-time data .                   |
| **Workflow Integration**           | Best for simple, repetitive, point-to-point tasks .                                                      | Adaptable to complex, dynamic workflows; can optimize routes and tasks .                                      |
| **Cost (Overall)**                 | Higher initial setup cost, potentially lower unit cost for very simple AGVs.                             | Potentially lower initial setup, unit cost can vary. Total Cost of Ownership (TCO) needs careful evaluation . |
| **Human Collaboration**            | Typically operates in dedicated zones or requires significant safety measures.                           | Often designed for safe collaboration with humans in shared spaces .                                          |

***

### **3. How They Work: Core Technologies**

### **3.1. AGV Technology**

* **Guidance Systems :**
  * **Magnetic Tape/Wire Guidance:** Sensors follow magnetic tapes adhered to or wires embedded in the floor.
  * **Laser Guidance (Laser Triangulation):** Uses rotating lasers that reflect off targets mounted on walls/objects to determine position.
  * **Optical/Vision Guidance:** Follows painted lines or uses cameras to recognize features along a path.
  * **Inertial Guidance:** Uses gyroscopes and odometry; often needs periodic referencing.
* **Control System:** Centralized fleet manager assigns tasks and routes. Onboard controllers execute movements along these paths.
* **Safety Sensors:** Bumpers, proximity sensors to detect obstacles and trigger a stop.

### **3.2. AMR Technology**

* **Sensing & Perception :**
  * **LiDAR:** For 3D mapping and obstacle detection.
  * **3D Cameras/Depth Sensors:** For object recognition, environmental understanding.
  * **IMUs:** For motion tracking and localization.
  * **Encoders:** Measure wheel rotation for odometry.
* **SLAM (Simultaneous Localization and Mapping):** AMR builds a map of the facility as it moves (or uses a pre-loaded CAD drawing) and simultaneously determines its location within that map.
* **AI & Path Planning Algorithms:** Process sensor data to understand the environment, identify obstacles, and calculate the most efficient collision-free path to the destination. Algorithms like A\*, D\*, or DWA are common.
* **Fleet Management System (FMS):** While AMRs navigate autonomously, an FMS optimizes task allocation, manages traffic flow for multiple AMRs, and interfaces with Warehouse Management Systems (WMS) or Manufacturing Execution Systems (MES) .

***

### **4. Applications of AGVs and AMRs**

Both AGVs and AMRs are primarily used for automating internal logistics and material handling.

| Application Sector             | AGV Use Cases                                                                                                     | AMR Use Cases                                                                                                                                      |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Manufacturing**              | Transporting raw materials, work-in-progress (WIP) between production lines, finished goods to storage/shipping . | Flexible material transport in dynamic production environments, line-side replenishment, moving components to assembly stations, kitting .         |
| **Warehousing & Distribution** | Moving pallets in and out of storage, long-distance transport between fixed points (e.g., receiving to racking) . | Order picking (goods-to-person, person-to-goods), sorting, packing, putaway, replenishment, cross-docking in dynamic and high-traffic warehouses . |
| **Logistics & E-commerce**     | Repetitive pallet movements, bulk transport .                                                                     | Efficient order fulfillment, managing fluctuating demand, supporting sortation centers .                                                           |
| **Healthcare**                 | Transporting meals, linens, medical supplies, waste within hospitals along fixed routes .                         | Delivering medications, lab samples, supplies in complex hospital layouts; assisting staff with material transport .                               |
| **Food & Beverage**            | Moving ingredients, packaging materials, finished products in production and storage .                            | Handling diverse product types, managing cold chain logistics within facilities .                                                                  |
| **Automotive**                 | Line-side delivery of parts, assembly line movement of vehicle bodies .                                           | Flexible parts delivery to assembly lines, supporting just-in-time (JIT) manufacturing, transporting tools and equipment .                         |
| **Retail (Backroom)**          | Transporting goods from receiving to storage.                                                                     | Restocking shelves, moving inventory in dynamic retail backrooms.                                                                                  |

**General Trend:** AGVs are suited for stable, high-volume, repetitive tasks with fixed routes. AMRs excel in dynamic, complex environments requiring flexibility, intelligent obstacle navigation, and collaboration with humans .

***

### **5. Companies and Institutes (AGVs & AMRs)**

### **Leading Global AGV/AMR Manufacturers & Solution Providers**

| Company Name                                  | Type (Primarily)          | Notable Products/Focus                                                                                            | Raw Link (Example)                                               |
| --------------------------------------------- | ------------------------- | ----------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| **KUKA AG**                                   | AMR & AGV                 | KMP series (AMRs), extensive range of AGVs for manufacturing and logistics .                                      | `https://www.kuka.com/`                                          |
| **OMRON Corporation (Adept Technology)**      | AMR                       | LD Series, HD Series AMRs for industrial and logistics applications, Fleet Operations Workspace (FLOW) software . | `https://automation.omron.com/`                                  |
| **Mobile Industrial Robots (MiR) (Teradyne)** | AMR                       | Wide range of AMRs (MiR100 to MiR1350) for various payloads, MiR Fleet software .                                 | `https://www.mobile-industrial-robots.com/`                      |
| **Geekplus Technology Co., Ltd.**             | AMR                       | Goods-to-Person picking, sorting, moving robots; comprehensive AMR solutions for warehouses .                     | `https://www.geekplus.com/`                                      |
| **ABB**                                       | AGV & AMR                 | AGVs for manufacturing, Flexley AMRs for flexible material handling .                                             | `https://global.abb/`                                            |
| **Fetch Robotics (Zebra Technologies)**       | AMR                       | Cloud robotics platform, AMRs for warehouse and manufacturing logistics.                                          | `https://www.zebra.com/us/en/solutions/robotics-automation.html` |
| **Locus Robotics**                            | AMR                       | Collaborative AMRs primarily for order fulfillment in e-commerce and warehouses.                                  | `https://locusrobotics.com/`                                     |
| **GreyOrange**                                | AMR & AGV                 | AI-powered fulfillment automation, Ranger series (AMRs/AGVs) for sorting, goods-to-person .                       | `https://www.greyorange.com/`                                    |
| **IAM Robotics**                              | AMR                       | Autonomous picking and material handling robots, Swift (mobile picking robot) .                                   | `https://www.iamrobotics.com/`                                   |
| **Seegrid**                                   | AMR (Vision-guided)       | Palion AMRs using vision-based navigation for enterprise-wide automation.                                         | `https://www.seegrid.com/`                                       |
| **Dematic (KION Group)**                      | AGV & AMR                 | AGV systems for manufacturing and distribution, integrating AMRs in broader solutions .                           | `https://www.dematic.com/`                                       |
| **JBT Corporation**                           | AGV                       | Long history in AGV systems for various industries including manufacturing, food & beverage, healthcare .         | `https://www.jbtc.com/automated-systems/`                        |
| **Daifuku Co., Ltd.**                         | AGV                       | Material handling solutions including AGVs for manufacturing and logistics.                                       | `https://www.daifuku.com/`                                       |
| **Murata Machinery (Muratec)**                | AGV                       | AGV systems for cleanroom environments (semiconductor) and general manufacturing.                                 | `https://www.muratec.net/`                                       |
| **BALYO**                                     | AMR (Infrastructure-free) | Technology transforming standard forklifts into AMRs using SLAM navigation.                                       | `https://www.balyo.com/`                                         |

### **AMR/AGV Ecosystem in India**

| Company Name             | Type (Primarily) | Key Offerings/Focus in India | Raw Link (Example) |
| ------------------------ | ---------------- | ---------------------------- | ------------------ |
| **Addverb Technologies** | AMR & AGV        |                              |                    |
