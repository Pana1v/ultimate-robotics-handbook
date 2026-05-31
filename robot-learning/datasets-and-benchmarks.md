---
icon: brain
---

# Datasets & Benchmarks

A field's progress is measured by its benchmarks. Robotics has historically been bad at this - every paper claimed state of the art on a different real-robot setup that nobody else could reproduce. The 2023-2026 wave changed that, partially. There are now genuinely shared datasets and benchmarks, both real and simulated. This page surveys what to use and when.

The honest caveat: **no benchmark in robotics is as load-bearing as ImageNet was for vision or GLUE was for NLP**. A model that wins on LIBERO might fail on your physical robot. Use benchmarks for ablations and comparing techniques, not as a final verdict on capability.

## Real-robot datasets

These are collections of real demonstration trajectories from physical hardware. They are the substrate for VLA pretraining.

### Open X-Embodiment

Padalkar, Pooley et al., 2023. [https://arxiv.org/abs/2310.08864](https://arxiv.org/abs/2310.08864)

Project: [https://robotics-transformer-x.github.io/](https://robotics-transformer-x.github.io/)

The dataset that defines the era. A consortium of 30+ labs pooled their existing demo datasets into a unified format. Scale (approximate, the number keeps growing):

- 1M+ trajectories
- 22+ robot embodiments
- 300+ different tasks
- 100+ scenes
- RLDS format

This is the de facto pretraining corpus for any 2024+ VLA. If your paper claims competitive performance, it likely involved finetuning a model that was first pretrained on OXE.

### DROID

Khazatsky, Pertsch et al., 2024. [https://droid-dataset.github.io/](https://droid-dataset.github.io/)
Paper: [https://arxiv.org/abs/2403.12945](https://arxiv.org/abs/2403.12945)

The single biggest *consistent* real-robot dataset:

- 76k trajectories
- Single embodiment (Franka Panda)
- 564 scenes across 52 buildings, ~350 robot-hours
- Standardized hardware: Franka + ZED 2 stereo + ZED Mini wrist + Oculus Quest 2 teleop

The standardization is the point. Open X-Embodiment is heterogeneous; DROID is one robot in many scenes, which makes it a much better testbed for *scene generalization* studies.

### BridgeData V2

Walke, Black, Lee et al., 2023. [https://rail-berkeley.github.io/bridgedata/](https://rail-berkeley.github.io/bridgedata/)
Paper: [https://arxiv.org/abs/2308.12952](https://arxiv.org/abs/2308.12952)

- 60k trajectories
- WidowX arm
- 24 environments, 13 skills
- The "original" large-scale single-embodiment dataset that paved the way for DROID

Still widely used as a transfer-learning testbed.

### RH20T

Fang et al., 2023. [https://rh20t.github.io/](https://rh20t.github.io/)

110k+ sequences across 7 robots and 147 tasks. Strong on contact-rich tasks. Frequently cited for VLA pretraining mixes.

### RoboSet

Bharadhwaj et al., 2023.

A diverse multi-task manipulation dataset from CMU. ~28.5k trajectories. Less mainstream than DROID but worth knowing.

### LeRobot community datasets

HuggingFace hosts hundreds of community-contributed datasets in the LeRobot format. [https://huggingface.co/datasets?other=LeRobot](https://huggingface.co/datasets?other=LeRobot)

Quality is uneven - some are excellent (SO-100 demos from competent operators), some are unusable. As of 2026 this is the wild west of robotics data; useful for narrow tasks if you find the right one.

## Simulation benchmarks

### LIBERO

Liu et al., 2023. [https://libero-project.github.io/](https://libero-project.github.io/)
Paper: [https://arxiv.org/abs/2306.03310](https://arxiv.org/abs/2306.03310)

The de facto simulation benchmark for *lifelong learning* and *generalization* in manipulation IL. Built on robosuite.

- 130 language-conditioned tasks across 4 suites (Spatial, Object, Goal, Long)
- Designed to probe different generalization axes
- Standardized eval, low compute footprint

This is what most VLA papers benchmark on for sim evaluation. Beating LIBERO does not mean your policy works on a real robot. Failing on LIBERO is a strong signal you should not bother trying on real.

### RoboCasa

Nasiriany, Maddukuri, Zhang et al. (NVIDIA), 2024. [https://robocasa.ai/](https://robocasa.ai/)
Paper: [https://arxiv.org/abs/2406.02523](https://arxiv.org/abs/2406.02523)

The 2024 big-leap simulation benchmark for *household manipulation at scale*.

- 100+ household scenes (kitchens, mostly)
- 100+ object categories, 2500+ objects
- 100 atomic tasks
- Built on robosuite + procedurally generated scenes + AI-generated textures
- Designed to scale data via procedural generation

RoboCasa is the closest thing in 2026 to a "kitchen ImageNet." If you are training a VLA for household tasks, you train on RoboCasa.

### BEHAVIOR-1K

Li, Zhang et al. (Stanford), 2023. [https://behavior.stanford.edu/](https://behavior.stanford.edu/)
Paper: [https://arxiv.org/abs/2403.09227](https://arxiv.org/abs/2403.09227)

A simulation benchmark of 1000+ household activities. Built on OmniGibson (Isaac Sim + iGibson). More complex than RoboCasa - full mobile manipulation in cluttered homes, including soft bodies, fluids, cloth.

Strengths: scope. There is no other benchmark with this breadth of household tasks.
Weaknesses: hard to train on. The simulator is heavy, the activities are long-horizon, and many tasks involve deformables that no current learning approach handles well.

### Meta Habitat

[https://aihabitat.org/](https://aihabitat.org/)
Habitat 3.0 paper (2023): [https://arxiv.org/abs/2310.13724](https://arxiv.org/abs/2310.13724)

Meta's embodied AI platform. Strong on:

- Photorealistic indoor scenes (HM3D, Matterport)
- Multi-agent (human + robot) simulation in Habitat 3.0
- Navigation + social navigation benchmarks (PointNav, ObjectNav, ImageNav)

Habitat is less manipulation-focused than RoboCasa or BEHAVIOR. Its sweet spot is navigation, social navigation, and embodied QA.

### MetaWorld

Yu, Quillen et al., 2019. [https://meta-world.github.io/](https://meta-world.github.io/)
Paper: [https://arxiv.org/abs/1910.10897](https://arxiv.org/abs/1910.10897)

50 tabletop manipulation tasks for meta-RL and multi-task RL. Old but still cited. Built on MuJoCo. Useful baseline; do not use it as your only benchmark in 2026.

### robosuite / robomimic

[https://robosuite.ai/](https://robosuite.ai/)

The benchmark substrate that LIBERO and RoboCasa build on. A flexible MuJoCo-based manipulation framework with many standardized tasks. Pre-2023 IL papers often benchmark on robomimic's "Square," "Tool Hang," "Transport," etc.

### Isaac Lab task suites

[https://github.com/isaac-sim/IsaacLab](https://github.com/isaac-sim/IsaacLab)

Comes with built-in task suites:

- **legged_gym** (now part of Isaac Lab) - quadruped + humanoid locomotion
- **dexterous manipulation** - hand-cube reorientation, allegro tasks
- **Franka tabletop** - pick-and-place, stack, push

For RL benchmarking these are the canonical environments in 2026.

## Navigation benchmarks

Mobile robotics benchmarks have a different culture than manipulation.

### BARN Challenge

[https://www.cs.utexas.edu/~xiao/BARN_Challenge/BARN_Challenge.html](https://www.cs.utexas.edu/~xiao/BARN_Challenge/BARN_Challenge.html)

The Benchmark for Autonomous Robot Navigation. A simulation + real-world challenge run at ICRA each year. Tests local navigation through cluttered, narrow environments.

The "BARN" environments are procedurally generated obstacle fields between two walls; the robot must navigate from one end to the other without collisions. Brutally hard for purely reactive planners. Good ground truth for evaluating learned vs. classical local planners.

I (Pan) competed in BARN - see [BARN Challenge](../authors-projects/barn-challenge.md) for the project writeup.

### Habitat ObjectNav / SocialNav

Standardized navigation benchmarks within Meta Habitat:

- **PointNav** - go to a goal coordinate.
- **ObjectNav** - find an object by semantic label.
- **ImageNav** - find a location matching a goal image.
- **SocialNav** - navigate without colliding with humans / agents.

These have annual challenges and active leaderboards. The current SOTA mixes learned policies + classical SLAM + LLM planning.

### nuScenes / Waymo Open Dataset

For autonomous driving (not robot navigation in the indoor sense):

- **nuScenes** - [https://www.nuscenes.org/](https://www.nuscenes.org/) - 1000 driving scenes, multi-modal sensors.
- **Waymo Open Dataset** - [https://waymo.com/open/](https://waymo.com/open/) - 1000+ hours of driving, large-scale, well-maintained.

Both are foundational for autonomous-driving perception and prediction. The driving / robotics overlap is real but the benchmarks remain distinct.

## VLA-specific benchmarks

VLA papers in 2024-2026 typically benchmark on a combination of:

- **LIBERO** (sim, manipulation)
- **SimplerEnv** - [https://simpler-env.github.io/](https://simpler-env.github.io/) - a simulator designed to *match* real-robot evaluation distributions for OpenX-trained models. Letting you eval a real-trained VLA in sim with reasonable correlation.
- **Real-world Franka / WidowX evals** - manually scored, on the lab's own setup, often non-reproducible.
- **CALVIN** - [http://calvin.cs.uni-freiburg.de/](http://calvin.cs.uni-freiburg.de/) - long-horizon language-conditioned manipulation benchmark.

SimplerEnv is the most underrated of these - it provides a sim eval that actually correlates with real-robot results, which is more than LIBERO claims.

## Comparison table

| Dataset / Benchmark | Sim or Real | Scope | Best for | Notes |
|---|---|---|---|---|
| Open X-Embodiment | Real | Cross-embodiment manipulation | VLA pretraining | The pretraining corpus. |
| DROID | Real | Single-embodiment (Franka), many scenes | Scene generalization | Most consistent real dataset. |
| BridgeData V2 | Real | WidowX manipulation | Single-arm IL benchmarks | Pre-DROID standard. |
| LIBERO | Sim | Tabletop manipulation, generalization | Quick IL/VLA eval | Cheap, well-supported. |
| RoboCasa | Sim | Household kitchen | Scaling, procedural training | The 2024 leap forward. |
| BEHAVIOR-1K | Sim | Full household activity | Long-horizon ambition | Hard to train on. |
| Habitat | Sim | Indoor navigation + social | Navigation, embodied AI | Industry standard for navigation. |
| MetaWorld | Sim | Tabletop multi-task RL | Multi-task RL baselines | Older, still cited. |
| Isaac Lab tasks | Sim | Locomotion + manipulation | RL development | The 2026 RL default. |
| BARN | Sim + Real | Local navigation in clutter | Mobile robot benchmarking | Annual ICRA challenge. |
| nuScenes / Waymo | Real | Autonomous driving | Driving perception | AV-specific. |
| SimplerEnv | Sim | VLA eval matching real | Reproducible VLA evals | Most underrated. |
| CALVIN | Sim | Long-horizon lang-conditioned | Language IL eval | Solid mid-difficulty bench. |

## Benchmarks specifically for sim-to-real

Most "sim-to-real" papers do not use a shared benchmark - they show the same policy in sim and on their lab's robot, and report success rates. This is a real gap in the field.

A few attempts at shared sim-to-real benchmarks:

- **RoboHive** - [https://sites.google.com/view/robohive](https://sites.google.com/view/robohive) - a benchmark suite spanning sim + real for manipulation.
- **SimplerEnv** (above) - explicitly designed to predict real-robot performance from sim.

The reality is that sim-to-real claims still mostly need to be evaluated on the specific robot in the specific deployment. No benchmark substitutes for that.

## Choosing a benchmark

| If your work is about… | Use… |
|---|---|
| New IL algorithm | LIBERO + robomimic + real demos on your robot |
| VLA pretraining | Open X-Embodiment + DROID + SimplerEnv + real evals |
| Sim-to-real for locomotion | Isaac Lab terrains + real quadruped |
| Sim-to-real for manipulation | LIBERO + real Franka/WidowX |
| Long-horizon language tasks | CALVIN + RoboCasa |
| Household ambition | RoboCasa or BEHAVIOR-1K (the latter if you have time) |
| Navigation in clutter | BARN + Habitat |
| Driving perception | nuScenes + Waymo |

## Some honest limitations

1. **Benchmarks reward what they measure.** Most manipulation benchmarks measure short-horizon success in clean scenes. Real robots fail on long-horizon and on messy scenes. Your benchmark wins might not generalize.

2. **Real-robot reproducibility is still broken.** Even with shared hardware (Franka), different labs get different results because of lighting, room layout, operator skill, and ambient temperature.

3. **Sim benchmarks overfit fast.** LIBERO numbers crept from 30% to 90%+ in two years. Some of that is real progress, some is hyperparameter tuning to the benchmark.

4. **The Open X-Embodiment dataset is unbalanced.** Some embodiments dominate. A policy that "works on Open X" might just be a policy that works on Franka.

{% hint style="info" %}
**Field note.** I would much rather see a paper report "60% on a real robot you can buy for $30k" than "95% on LIBERO." The field is slowly drifting toward valuing real-world evals more. Help that drift along by always reporting both, and by being honest about the difference.
{% endhint %}

## Further reading

- Padalkar et al., *"Open X-Embodiment: Robotic Learning Datasets and RT-X Models"* - [https://arxiv.org/abs/2310.08864](https://arxiv.org/abs/2310.08864)
- Khazatsky et al., *"DROID: A Large-Scale In-The-Wild Robot Manipulation Dataset"* - [https://arxiv.org/abs/2403.12945](https://arxiv.org/abs/2403.12945)
- Liu et al., *"LIBERO: Benchmarking Knowledge Transfer for Lifelong Robot Learning"* - [https://arxiv.org/abs/2306.03310](https://arxiv.org/abs/2306.03310)
- Nasiriany et al., *"RoboCasa: Large-Scale Simulation of Everyday Tasks for Generalist Robots"* - [https://arxiv.org/abs/2406.02523](https://arxiv.org/abs/2406.02523)
- Li et al., *"BEHAVIOR-1K: A Human-Centered, Embodied AI Benchmark with 1,000 Everyday Activities and Realistic Simulation"* - [https://arxiv.org/abs/2403.09227](https://arxiv.org/abs/2403.09227)
