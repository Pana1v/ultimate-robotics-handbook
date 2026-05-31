---
icon: android
---

# Humanoids

### **Humanoid Robots: A Comprehensive Guide** <a href="#undefined" id="undefined"></a>

<figure><img src="../.gitbook/assets/robofail.gif" alt=""><figcaption></figcaption></figure>

Humanoid robots, machines engineered to emulate the human body in both form and function, stand at the vanguard of robotic innovation . Their design, typically comprising a head, torso, two arms, and two legs, is strategically chosen to enable interaction with human-centric tools and environments, offering versatility across a multitude of applications . In contrast to conventional industrial robots-often stationary and confined to specific, repetitive tasks-humanoids are conceived for enhanced mobility, adaptability, and the capacity to operate within dynamic, human-populated spaces. This guide explores their fundamental definition, operational mechanics, pivotal capabilities, diverse applications, the organizations and research propelling their evolution, and avenues for deeper exploration.

***

### **1. What are Humanoid Robots? Definition and Core Characteristics**

A **humanoid robot** is a robot with its physical structure built to resemble the human body. This design philosophy serves functional purposes, such as enabling the robot to utilize tools and equipment designed for humans, navigate environments built for human occupancy, and engage in more intuitive interactions with people.

**Core Characteristics:**

* **Anthropomorphic Form:** Possesses a head, torso, arms, and legs, mirroring human anatomy.
* **Bipedal Locomotion:** The ability to walk on two legs is a defining and challenging characteristic .
* **Manipulation Capabilities:** Features arms and hands (end-effectors) designed for grasping and interacting with objects .
* **Sensor Integration:** Equipped with various sensors (vision, auditory, tactile, proprioceptive) to perceive and interpret the environment.
* **Interaction Potential:** Designed for interaction with humans and human-oriented settings, sometimes incorporating social cues and behaviors.

**How Humanoids Differ from Other Robots:**\
Most industrial robots are fixed and programmed for highly specific, repetitive tasks. Humanoid robots, however, are engineered for mobility and adaptability, aiming to handle a wider spectrum of tasks in less structured and evolving environments.

***

### **2. How Humanoid Robots Work: Key Technologies**

The complex functionality of humanoid robots stems from the sophisticated integration of several core technologies:

* **Actuators and Motors:** These are the "muscles and joints," enabling movement (e.g., electric, hydraulic). Some advanced designs like the iCub utilize tendon-driven joints for fine motor control .
* **Sensors and Perception Systems:**
  * **Cameras:** Provide visual input for object recognition, navigation (Visual SLAM), and facial recognition.
  * **Microphones:** Enable sound detection and speech recognition.
  * **Tactile Sensors:** Measure force and pressure for precise gripping and interaction. Tesla's Optimus Gen 2, for example, features tactile sensors on its fingers.
  * **Inertial Measurement Units (IMUs):** Help maintain balance and track orientation.
  * **Proprioceptive Sensors:** Provide feedback on the robot's own state (e.g., joint angles).
* **Control Systems:** Central Processing Units (CPUs) or distributed processors serve as the "brain," processing sensor data to control movements and make decisions .
* **Power Supply:** Typically rechargeable lithium-ion batteries, balancing energy density and weight.
* **Artificial Intelligence (AI) and Machine Learning:** AI underpins a humanoid's intelligence and adaptability .
  * **Machine Learning:** Refines movements and improves efficiency based on sensory feedback.
  * **Reinforcement Learning:** Enables learning complex tasks through trial and error.
  * **Natural Language Processing (NLP):** Facilitates voice interaction.
  * **Computer Vision:** Powers object recognition and scene understanding.

***

### **3. Key Capabilities of Humanoid Robots**

* **Locomotion (Walking and Balance):**\
  Bipedal locomotion is achieved by adjusting the center of mass and utilizing concepts like the Zero Moment Point (ZMP) for stability. Navigating uneven terrain is a significant challenge, addressed by real-time feedback systems in advanced robots.
* **Manipulation (Gripping and Precision):**\
  Humanoid arms and hands are designed for precise object interaction, often using tendon-driven systems. Machine learning is improving grip strength and adaptability.
* **Human-Robot Interaction (HRI):**\
  Effective interaction involves understanding human cues (gestures, voice, expressions) and communicating multimodally . Safety features are crucial for collaboration.
* **Planning and Control:**\
  This involves generating and executing motion trajectories, managing bipedal motion, path planning, obstacle avoidance, and self-collision detection. Whole-body control coordinates numerous joints for simultaneous tasks while maintaining balance .
* **Learning and Adaptability:**\
  Humanoids learn from experience through machine learning, reinforcement learning, and imitation learning to adapt to new situations.

***

### **4. Evolution and Recent Advancements**

The field has seen continuous innovation, with key platforms demonstrating growing sophistication.

| Robot Platform          | Developer/Company                      | Key Milestones / Noteworthy Features                                                                          |
| ----------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| **ASIMO** (legacy)      | Honda (Japan)                          | Early pioneer in advanced walking and human interaction.                                                      |
| **Atlas** (Electric)    | Boston Dynamics (USA, Hyundai-owned)   | New all-electric Atlas unveiled Apr 2024 replacing the hydraulic version; aimed at industrial deployment.     |
| **Digit**               | Agility Robotics (USA)                 | Logistics-focused; deployed in GXO and Amazon warehouses; v4 added head/manipulators.                         |
| **Optimus** (Gen 2/3)   | Tesla (USA)                            | Unveiled Oct 2022; Gen 2 (Dec 2023) added tactile fingers; "We Robot" event Oct 2024 demoed Gen 3 prototypes. |
| **Figure 02**           | Figure AI (USA)                        | Series B 2024; BMW factory pilot; integrated with OpenAI/Microsoft for reasoning.           |
| **NEO Beta / NEO Home** | 1X Technologies (Norway/USA)           | Soft-bodied home humanoid; OpenAI investor. Targeting consumer/home market.                                   |
| **Apollo**              | Apptronik (USA, ex-NASA Valkyrie team) | Industrial humanoid; Mercedes-Benz pilot 2024.                                                                |
| **Phoenix**             | Sanctuary AI (Canada)                  | General-purpose humanoid with manipulation-first design.                                                      |
| **Unitree G1 / H1**     | Unitree Robotics (China)               | G1 (May 2024) - sub-$20k humanoid democratizing access; H1 for higher-payload work.                           |
| **GR-1 / GR-2**         | Fourier Intelligence (China)           | GR-2 (2024) - rehabilitation roots, now general-purpose.                                                      |
| **Walker S**            | UBTECH Robotics (China)                | Deployed in BYD/Geely factories.                                                                              |
| **Iron**                | XPeng (China)                          | Auto-OEM-backed humanoid; first reveal Nov 2024.                                                    |
| **Booster T1**          | Booster Robotics (China)               | Lightweight humanoid, soccer/research focus.                                                                  |
| **Galbot G1**           | Galbot (China)                         | Foundation-model-driven manipulation.                                                               |
| **Ameca**               | Engineered Arts (UK)                   | Highly expressive face; advanced HRI.                                                                         |
| **HumanPlus**           | Stanford (USA)                         | Research prototype (Jun 2024) - shadow-learning whole-body humanoid skills via human video + RL.              |
| **iCub**                | Italian Inst. of Technology            | Open-source cognitive humanoid; long-standing research platform.                                              |
| **EngineAI Robot**      | EngineAI (China)                       | Demonstrated forward flip Feb 2025.                                                                           |

***

### **4.5. How modern humanoids learn (2024–2026)**

The post-2023 generation of humanoids - Figure, 1X, Tesla Optimus, Unitree G1, Apptronik Apollo - share a common stack underneath the marketing. Understanding it matters because _this_ is what differentiates a 2024+ humanoid from the ASIMO/Atlas-hydraulic era.

**The two-layer paradigm:**

1. **Low-level locomotion / whole-body control** - learned in simulation via reinforcement learning, then transferred to hardware.
2. **High-level manipulation / language conditioning** - driven by foundation models (VLAs) trained on teleoperated and internet-scale data.

**Key methods you'll see in 2024-2026 humanoid papers:**

| Method                                 | Origin                                     | What it does                                                                                          |
| -------------------------------------- | ------------------------------------------ | ----------------------------------------------------------------------------------------------------- |
| **PPO + privileged learning**          | ETH Zurich (ANYmal), MIT (Walk-These-Ways) | RL with privileged state in sim, distilled to a proprioception-only policy for real-world deployment. |
| **HumanPlus**                          | Stanford (2024)                            | Shadow-learning: humanoid mimics human pose from monocular video + RL refinement.                     |
| **OmniH2O**                            | CMU / CMU-CMU (2024)                       | Universal & dexterous human-to-humanoid whole-body teleop and learning.                               |
| **ExBody / ExBody2**                   | UCSD (2024)                                | Expressive whole-body control by tracking motion-capture references.                                  |
| **Diffusion Policy on humanoid hands** | Various                                    | Vision-conditioned diffusion policies for dexterous manipulation.                                     |
| **π0 / π0.5**                          | Physical Intelligence (2024–2025)          | Generalist VLA for cross-embodiment manipulation including humanoids.                                 |
| **RT-2 / OpenVLA on humanoids**        | Google DeepMind / Stanford                 | Vision-language-action models conditioned on natural-language goals.                                  |

For deep dives on all of the above, see the [Robot Learning](../robot-learning/robot-learning.md) section - specifically [Imitation Learning](../robot-learning/imitation-learning.md), [Reinforcement Learning](../robot-learning/reinforcement-learning-modern.md), and [Foundation Models / VLAs](../robot-learning/foundation-models-vla.md).

> **Field note.** The reason 2024+ humanoids look qualitatively better than 2018 humanoids is _not_ better mechatronics - Atlas-hydraulic was already mechanically impressive. It's that the locomotion controllers are now learned policies trained over billions of sim steps, and the manipulation stack is finally conditioned on language and vision foundation models rather than scripted state machines.

***

### **5. Applications of Humanoid Robots**

Humanoids are envisioned for diverse roles :

* **Research and Development:** Studying human biomechanics, cognition, and developing prosthetics.
* **Healthcare and Medicine:** Rehabilitation aids, robotic nurses, assistants for the elderly.
* **Industry and Manufacturing:** Assembly line tasks, material handling, inspection.
* **Service Sector:** Receptionists, caregivers, education, customer service.
* **Hazardous Environments:** Disaster response, tasks unsafe for humans.
* **Space Exploration:** Assisting astronauts, autonomous extraterrestrial tasks.
* **Companionship and Personal Assistance.**
* **Entertainment and Education.**

***

### **6. Current Challenges and Future Trends**

**Current Challenges** :

* Replicating the complexity and efficiency of biological motion.
* Improving structural design for strength and lightness.
* Developing advanced, efficient materials.
* Enhancing drive and control methods.
* Achieving greater energy efficiency and longer operational times.
* Matching human dexterity in manipulation.
* Reducing cost and improving scalability for mass production.
* Developing robust, general-purpose AI software.

**Future Trends** :

* More realistic and nuanced human interaction.
* Advanced mobility, dexterity, and safer navigation.
* Enhanced cognitive and emotional intelligence for roles in caregiving and education.
* Greater collaborative autonomy alongside humans.
* Holistic integration of bionics, brain-inspired intelligence, mechanics, and control.

***

### **7. Companies and Institutes Working on Humanoid Robots**

**Leading Global Companies & Platforms:**

| Company Name                              | Country      | Notable Humanoid Platform(s) / Focus Area                 |
| ----------------------------------------- | ------------ | --------------------------------------------------------- |
| **Boston Dynamics** (Hyundai)             | USA          | Atlas (Electric, 2024)                                    |
| **Tesla**                                 | USA          | Optimus Gen 2/3                                           |
| **Figure AI**                             | USA          | Figure 02 - BMW pilot, OpenAI/Microsoft partnership       |
| **1X Technologies**                       | Norway/USA   | NEO Beta / NEO Home - consumer humanoid; OpenAI-backed    |
| **Apptronik**                             | USA          | Apollo - Mercedes-Benz pilot                              |
| **Agility Robotics**                      | USA          | Digit - Amazon, GXO warehouse deployments                 |
| **Sanctuary AI**                          | Canada       | Phoenix - manipulation-first general-purpose              |
| **Physical Intelligence**                 | USA          | π0 / π0.5 foundation models for humanoid/cross-embodiment |
| **Skild AI**                              | USA          | Foundation models for robotic intelligence                |
| **Engineered Arts Ltd**                   | UK           | Ameca - expressive HRI                                    |
| **Unitree Robotics**                      | China        | G1 (sub-$20k), H1                                         |
| **Fourier Intelligence**                  | China        | GR-1 / GR-2                                               |
| **UBTECH Robotics**                       | China        | Walker S - BYD/Geely factory pilots                       |
| **XPeng**                                 | China        | Iron - auto-OEM backed                                    |
| **Booster Robotics**                      | China        | T1 - research/soccer focus                                |
| **Galbot**                                | China        | G1 - foundation-model-driven                              |
| **EngineAI**                              | China        | Forward-flip demo Feb 2025                                |
| **Honda** (legacy)                        | Japan        | ASIMO (retired)                                           |
| **Toyota**                                | Japan        | T-HR3, human support robots                               |
| **Italian Institute of Technology (IIT)** | Italy        | iCub (research)                                           |
| **SoftBank Robotics** (legacy)            | Japan/France | Pepper, Nao (social robots)                               |

**Key Research Institutes (Global):**

| Institute Name                                                        | Country     | Key Focus Areas in Humanoid Research               |
| --------------------------------------------------------------------- | ----------- | -------------------------------------------------- |
| **MIT (Massachusetts Institute of Technology)**                       | USA         | Locomotion, manipulation, AI, control              |
| **Stanford University**                                               | USA         | Learning (e.g., HumanPlus), HRI, perception        |
| **IHMC (Institute for Human & Machine Cognition)**                    | USA         | Bipedal locomotion, dynamic balance                |
| **KAIST (Korea Advanced Inst. of Science & Technology)**              | South Korea | Humanoid design, control, disaster response robots |
| **DFKI (German Research Center for Artificial Intel.)**               | Germany     | AI, HRI, cognitive robotics                        |
| **AIST (National Inst. of Advanced Industrial Science & Technology)** | Japan       | Long history in humanoid development and HRI       |
| **Beijing Institute of Technology**                                   | China       | BHR series humanoid robots                         |

**Presence in India:**

| Entity Name                                       | Type     | Relevance to Humanoid Robotics Ecosystem in India                                                                                                                                                                                                                                         |
| ------------------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Indian Institutes of Technology (IITs)**        | Academic | (e.g., Bombay, Kanpur, Madras, Delhi) Conduct robotics research relevant to humanoid components (actuation, sensors, control), AI, and machine learning.                                                                                                                                  |
| **Indian Institute of Science (IISc), Bangalore** | Academic | Active in fundamental and applied robotics research, including areas like biomechanics, AI, and control systems that are foundational for humanoid development.                                                                                                                           |
| **Addverb Technologies**                          | Company  | Focuses on AMRs, warehouse automation, and medical robotics (cobots, exoskeletons). While not primarily a humanoid manufacturer, their R\&D in AI, advanced manufacturing, and robotics contributes to the broader ecosystem.                                                             |
| _(Various Startups & Companies)_                  | Company  | Several Indian startups are emerging in robotics, AI, and automation. While direct development of advanced bipedal humanoids for commercial markets is still nascent, they contribute to component development, AI solutions, and service robotics which share foundational technologies. |

_(Note: The Indian landscape for commercial advanced humanoid development is evolving, with academic institutions currently playing a more significant role in foundational research relevant to humanoid systems.)_

***

### **8. Interesting Research Papers & Areas**

* **Comprehensive Reviews:**
  * Tong, Y., Liu, H., & Zhang, Z. (2024). "Advancements in Humanoid Robots: A Comprehensive Review and Future Prospects." _IEEE/CAA Journal of Automatica Sinica_, 11(2), 301–328.
    * _Focus:_ Holistic overview of status, advancements, key technologies, and challenges.
    * _Raw Link:_ `https://www.ieee-jas.net/article/doi/10.1109/JAS.2023.124140`
* **Bipedal Locomotion and Control:**
  * Yamamoto, K., Kamioka, T., & Sugihara, T. (2021). "Survey on model-based biped motion control for humanoid robots." _Advanced Robotics_, 35(2), 75-96.
    * _Focus:_ Reviews model-based control for bipedal motion (standing, walking, running).
    * _Raw Link (Original DOI):_ `https://doi.org/10.1080/01691864.2020.1837670`
* **Dexterous Manipulation:**
  * Rajeswaran, A., et al. (2017). "Learning Complex Dexterous Manipulation with Deep Reinforcement Learning and Demonstrations." _Robotics: Science and Systems XIV_.
    * _Focus:_ DRL for learning dexterous manipulation with human-like five-finger hands.
    * _Raw Link:_ `https://www.roboticsproceedings.org/rss14/p49.pdf`
* **Human-Robot Interaction (HRI):**
  * Ge, S. S., Wang, C., & Li, Y. (2013). "Human-Robot Interaction by Understanding Upper Body Gestures." _Journal of Human-Robot Interaction_, 2(3), 43-73.
    * _Focus:_ Gesture understanding for social humanoid robot interaction.
    * _Raw Link (NTU Repository):_ `https://dr.ntu.edu.sg/bitstream/10356/100584/1/Human-Robot%20Interaction%20by%20Understanding%20Upper%20Body%20Gestures.pdf`
* **Other Key Research Areas:** Planning and whole-body control, learning and AI in humanoids, structural design, and material applications .

***

### **9. Comprehensive Guides & Further Resources**

| Resource Title                        | Provider/Source    | Key Content                                                | Raw Link                                       |
| ------------------------------------- | ------------------ | ---------------------------------------------------------- | ---------------------------------------------- |
| Wikipedia - Humanoid Robot            | Wikipedia          | General information, history, links to specific robots     | `https://en.wikipedia.org/wiki/Humanoid_robot` |
| IEEE Spectrum Robotics                | IEEE Spectrum      | Articles and news on humanoid developments                 | `https://spectrum.ieee.org/robotics`           |
| Robohub.org                           | Robohub            | Non-profit platform for the robotics community             | `https://robohub.org/`                         |
| Google Scholar                        | Google             | Academic research search                                   | `https://scholar.google.com/`                  |
| arXiv                                 | Cornell University | Pre-print archive for research papers                      | `https://arxiv.org/`                           |
| IEEE/CAA Journal of Automatica Sinica | IEEE/CAA           | Research in automation and robotics (see paper link above) | `https://www.ieee-jas.net/`                    |

<br>
