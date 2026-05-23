---
icon: brain
---

# Teleoperation & Data Collection

The 2023+ wave of imitation learning is the wave it is because three things happened in parallel:

1. **Algorithms** (ACT, Diffusion Policy) that work with hundreds, not millions, of demos.
2. **Cheap, capable hardware** (ALOHA, GELLO, SO-100/101) that let small labs collect data on a budget.
3. **Teleop interfaces** that produce *high-quality* demonstrations human operators can actually generate.

This page is about the third pillar. The algorithms eat the data your teleop rig produces. Garbage in, garbage out.

## Why teleop > scripted demos

Pre-2022 IL papers often used scripted demonstrations - written analytic controllers that solved the task, generating "expert" trajectories. This is great for ablations and toy environments but **does not generalize**:

- Scripted demos do not capture human intuition about contact, force, and recovery.
- Scripted demos are unimodal - they always do the task the same way. Real humans do it many ways.
- Scripted demos cannot show *how to recover* from off-distribution states.
- Scripted demos require you to already have solved the task you are trying to learn. If you can script it, why are you using IL?

Human teleop demos have:

- Natural multimodality (different humans, different strategies, even one human in different moods)
- Force-aware behavior (humans implicitly modulate force based on feel)
- Recovery from near-failures (priceless for robustness)
- Distribution covering what a human-controlled robot actually does

The cost: humans are slow, expensive, and inconsistent. Hence the engineering challenge of making teleop fast, accurate, and ergonomic.

## ALOHA (Stanford / Google, 2023)

Zhao et al., *"Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware"*. [https://arxiv.org/abs/2304.13705](https://arxiv.org/abs/2304.13705)

Project: [https://tonyzhaozh.github.io/aloha/](https://tonyzhaozh.github.io/aloha/)

The breakthrough hardware. Two ViperX 300 arms as "followers," two smaller WidowX arms as "leaders." Operator manipulates the leaders; the followers copy joint positions. Bimanual, ~20kg payload, ~$25k BOM.

Key design choices that mattered:

- **Joint-space leader-follower mapping** rather than end-effector tracking. Much higher bandwidth, no IK singularities.
- **Mechanical similarity** between leader and follower so the operator's proprioception transfers.
- **3rd-person + wrist cameras** for both arms.
- **Standardized data format** (which became the seed of the LeRobot data format).

ALOHA became the de facto benchmark hardware for bimanual IL. The paper itself was the first ACT paper.

## Mobile ALOHA (Stanford / Google, 2024)

Fu et al. [https://mobile-aloha.github.io/](https://mobile-aloha.github.io/)
Paper: [https://arxiv.org/abs/2401.02117](https://arxiv.org/abs/2401.02117)

ALOHA on a mobile base. Operator drives + teleoperates the arms simultaneously. The data collection demos that got everyone excited about home robots in 2024 came from this rig - folding clothes, cooking, watering plants, etc.

What it actually proved:

- Mobile manipulation IL is feasible with reasonable data scales (~50-100 demos per task).
- Co-training across multiple tasks helps generalization.
- A wheeled base + bimanual arm is enough for impressive home demos.

What it did *not* prove:

- That those demos generalize beyond the demonstrated scene configurations. Most do not, robustly.

## GELLO (Berkeley, 2023)

Wu, Yang et al. [https://wuphilipp.github.io/gello_site/](https://wuphilipp.github.io/gello_site/) [verify]
Paper: [https://arxiv.org/abs/2309.13037](https://arxiv.org/abs/2309.13037) [verify]

A general-purpose, low-cost leader-follower kit. Same principle as ALOHA - kinematically similar leader arm copies joint angles to a follower - but designed to retrofit onto *any* arm (Franka, UR, xArm, etc.) rather than a fixed hardware spec.

A GELLO leader for a Franka arm is ~$300 in printed parts and Dynamixel servos. This was a step-change in accessibility: any lab with a Franka could now collect ALOHA-quality demos.

In 2026, GELLO + LeRobot + ACT/Diffusion Policy is the standard student-project recipe. You can get from "no IL setup" to "trained policy on real arm" in about $500 and a weekend.

## SO-100 / SO-101 / Koch / LeKiwi (HuggingFace + community)

LeRobot ecosystem hardware. [https://github.com/huggingface/lerobot](https://github.com/huggingface/lerobot)

- **SO-100 / SO-101** - TheRobotStudio's open-source 5-DOF arm + leader. ~$110 BOM each (so ~$220 for a leader-follower pair). [https://github.com/TheRobotStudio/SO-ARM100](https://github.com/TheRobotStudio/SO-ARM100) [verify]
- **Koch v1.1** - Alexander Koch's design, similar concept, ~$250. [verify]
- **LeKiwi** - wheeled mobile base for SO-100. [verify]

These are *the* hobbyist / educator hardware in 2026. Performance is below ALOHA (5 DOF vs 6, less rigidity, smaller payload), but the entry price is dramatically lower and the LeRobot dataset / model pipeline is excellent.

If you are an individual or a class setting up IL for the first time, start here.

## AnyTeleop (CMU, 2023)

Qin et al. [https://anyteleop.com/](https://anyteleop.com/) [verify]
Paper: [https://arxiv.org/abs/2307.04577](https://arxiv.org/abs/2307.04577) [verify]

Vision-based teleop. Use a camera + hand pose estimation to drive the robot end-effector. Operator does not need any physical leader hardware.

Strengths:

- Hardware-free for the operator.
- Generalizes across robot embodiments.
- Good for dexterous hands where mechanical leader-follower is hard.

Weaknesses (in my experience):

- Latency. The pose estimation pipeline is slow enough to introduce 50-100ms lag that operators find disorienting.
- Precision. Hand-tracking is noisier than encoders on a mechanical leader. Fine manipulation suffers.
- Force awareness - none. You can't feel what you're touching.

I mention it because it shows up in many recent humanoid demos, especially the ones where the robot has a dexterous hand and a mechanical leader is impractical.

## VR-based teleop

Use a Meta Quest, Vision Pro, or similar headset + controllers to drive the robot. The Tesla Optimus and many Figure / 1X / Apptronik demos use VR teleop.

Pros:

- Operator sees what the robot sees (stereoscopic camera passthrough).
- Hand tracking via VR controllers is decent.
- Spatial awareness from VR is hard to replicate with screen-based teleop.

Cons:

- Latency budget is tight. Network or rendering hiccups kill the experience.
- Expensive operator hardware compared to GELLO.
- Operator fatigue is higher (try wearing a Quest for 4 hours).

For humanoid teleop, this is arguably the dominant paradigm in 2026. For arm-only manipulation, GELLO-style is usually better.

## Other teleop approaches worth knowing

- **Open-Television** (IIIS / MIT, 2024) - VR-based humanoid teleop with stereo passthrough. [https://github.com/OpenTeleVision/TeleVision](https://github.com/OpenTeleVision/TeleVision) [verify]
- **HOMIE** (Han et al., 2024) - wearable exoskeleton for humanoid teleop. [verify]
- **DexCap** - wearable motion capture for dexterous manipulation. [https://dex-cap.github.io/](https://dex-cap.github.io/) [verify]
- **UMI (Universal Manipulation Interface)** - Chi et al., 2024. Handheld grippers that record manipulation data *without a robot*. The operator just does the task; later you map it onto a robot. [https://umi-gripper.github.io/](https://umi-gripper.github.io/)
- **DOBB-E** (NYU / Hello Robot, 2023) - extension reacher with a camera; collect manipulation data via grocery-grabber. [https://dobb-e.com/](https://dobb-e.com/) [verify]

UMI deserves special attention: it dramatically reduces the cost of data collection by **decoupling demonstration from the robot**. You can record 100 hours of cooking demos with a UMI gripper for the cost of a few groceries; mapping those to a robot is a post-processing step. As of 2026 this is one of the more promising directions for *scaling* data collection.

## Comparison table

| Rig | Cost (USD) | DOF | Hands? | Mobile? | Best for |
|---|---|---|---|---|---|
| **ALOHA** | ~$25k | 6+6 | No (parallel grippers) | Static | Bimanual research, ACT baseline |
| **Mobile ALOHA** | ~$32k | 6+6 + base | No | Yes | Mobile manipulation research |
| **GELLO + Franka pair** | ~$30k (mostly Franka) | 7+7 | Optional | Static | Industrial-grade arm IL |
| **SO-100 / Koch** | ~$200-300 | 5 | No | No | Education, hobbyist, classroom |
| **SO-100 + LeKiwi** | ~$600 | 5 + base | No | Yes | Mobile teleop on a budget |
| **AnyTeleop** | ~$500 (camera + robot) | Robot-dependent | Yes (hand-tracked) | Robot-dependent | Hardware-free, dexterous hands |
| **VR (Quest + arm)** | ~$1k + arm | Robot-dependent | Optional | Robot-dependent | Humanoids, immersive |
| **UMI gripper** | ~$200 (handheld) | Effective 6 | No | "Yes" (you walk) | Scaling data without a robot |

## Data quality is everything

You can have the best teleop rig in the world and still collect bad data. The fundamentals:

### Reset diversity

Vary the starting configuration. If every demo starts with the cup at exactly $$(x_0, y_0)$$, your policy will only work there.

### Demonstrate the failure modes

If you want the robot to *not* knock things over while reaching, include demos where the operator nearly knocks something over and recovers. The policy needs to see what recovery looks like.

### Don't include bad demos

If you screw up a demo (mis-press a button, hit a singularity, drop the object), delete it. Do not include it as "a recovery." It is noise, not signal.

### Match the deployment camera

Whatever camera setup the policy will use at deployment, use the *same* camera setup at data collection. Resolution, position, intrinsics, lighting. Even small mismatches hurt.

### Demonstrate at deployment speed

If your robot will execute at 10cm/s, demonstrate at 10cm/s. If you demo at 30cm/s and deploy at 10cm/s, the policy will be confused.

### Multiple operators

Single-operator data is biased toward that person's quirks. Multi-operator data is more diverse and generalizes better. Even 2-3 operators is better than 1.

{% hint style="info" %}
**Field note.** I have come to believe that *demo quality dispersion* - how different the best and worst demos in your dataset are - is one of the most important variables and one of the least talked about. A dataset where all demos are 80% as good as the best demo trains a far better policy than one where the best is 100% and the worst is 30%. Aggressively filter the bad ones.
{% endhint %}

## Dataset scale, in practice (2026)

How many demos is "enough" depends on the task, the algorithm, and the robot. Empirical rules of thumb (single-task, fine-tuning a strong base policy):

| Task type | Demos for first signal | Demos for "works most of the time" | Demos for "robust" |
|---|---|---|---|
| Single fixed-pose pick-place | 10 | 50 | 200 |
| Varied pose pick-place | 50 | 200 | 1000 |
| Insertion / contact-rich | 100 | 300 | 1000+ |
| Bimanual coordination | 100 | 300 | 1500 |
| Long-horizon / multi-step | 200 | 1000 | 5000+ |
| Mobile manipulation | 200 | 1000 | 5000+ |

For VLA fine-tuning the numbers are roughly half - the pretraining does heavy lifting.

## Data formats and tooling

In 2026 there are basically two dominant formats:

- **LeRobot dataset format** - HuggingFace-hosted, Parquet + video, well-supported. [https://github.com/huggingface/lerobot](https://github.com/huggingface/lerobot)
- **RLDS** (Reinforcement Learning Datasets) - Google's format, TFDS-based, used by Open X-Embodiment and most VLA training. [https://github.com/google-research/rlds](https://github.com/google-research/rlds)

LeRobot is easier for individuals/small labs. RLDS is the standard for big VLA training. Tools exist to convert between them.

For your own datasets: just use LeRobot's format. Re-inventing data formats is a rite of passage and a waste of a week.

## Tooling for data collection workflows

- **LeRobot teleop scripts** - control rig + record + replay all in one. The 2026 default.
- **Foxglove** - visualize and replay teleop sessions. [https://foxglove.dev/](https://foxglove.dev/) Useful for QA-ing demos.
- **OpenLeap** - open-source ALOHA-compatible record/replay tooling. [verify]

## Practical workflow

```
Day 1: Set up hardware + verify teleop ergonomics. 
        Test simple movements. Run a sanity-check task (push a block).

Day 2: Collect 50 demos of your target task across varied initial conditions.
        Watch every demo back. Delete the bad ones.

Day 3: Train ACT or Diffusion Policy on the cleaned 30-40 demos.
        Eval on the real robot. Identify failure modes.

Day 4-5: Collect 50-200 more demos targeted at the failure modes.
         Re-train. Iterate.

Day 6+: Robust deployment, edge case collection, etc.
```

A real production-grade pipeline is more elaborate (CI on the dataset, regression tests on the policy, etc.), but the above is the unit of iteration.

## Further reading

- Zhao et al., *"Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware"* (ALOHA + ACT) - [https://arxiv.org/abs/2304.13705](https://arxiv.org/abs/2304.13705)
- Fu et al., *"Mobile ALOHA: Learning Bimanual Mobile Manipulation with Low-Cost Whole-Body Teleoperation"* - [https://arxiv.org/abs/2401.02117](https://arxiv.org/abs/2401.02117)
- Wu et al., *"GELLO: A General, Low-Cost, and Intuitive Teleoperation Framework for Robot Manipulators"* - [https://arxiv.org/abs/2309.13037](https://arxiv.org/abs/2309.13037) [verify]
- Chi et al., *"Universal Manipulation Interface: In-The-Wild Robot Teaching Without In-The-Wild Robots"* (UMI) - [https://umi-gripper.github.io/](https://umi-gripper.github.io/)
- LeRobot teleop documentation - [https://huggingface.co/docs/lerobot/](https://huggingface.co/docs/lerobot/) [verify]
