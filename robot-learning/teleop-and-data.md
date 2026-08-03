---
icon: brain
description: Teleop hardware, data quality, curation, cost, and scaling for imitation learning datasets.
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

Wu, Yang et al. [https://wuphilipp.github.io/gello_site/](https://wuphilipp.github.io/gello_site/)
Paper: [https://arxiv.org/abs/2309.13037](https://arxiv.org/abs/2309.13037)

A general-purpose, low-cost leader-follower kit. Same principle as ALOHA - kinematically similar leader arm copies joint angles to a follower - but designed to retrofit onto *any* arm (Franka, UR, xArm, etc.) rather than a fixed hardware spec.

A GELLO leader for a Franka arm is ~$300 in printed parts and Dynamixel servos. This was a step-change in accessibility: any lab with a Franka could now collect ALOHA-quality demos.

In 2026, GELLO + LeRobot + ACT/Diffusion Policy is the standard student-project recipe. You can get from "no IL setup" to "trained policy on real arm" in about $500 and a weekend.

## SO-100 / SO-101 / Koch / LeKiwi (HuggingFace + community)

LeRobot ecosystem hardware. [https://github.com/huggingface/lerobot](https://github.com/huggingface/lerobot)

- **SO-100 / SO-101** - TheRobotStudio's open-source 5-DOF arm + leader. ~$110 BOM each (so ~$220 for a leader-follower pair). [https://github.com/TheRobotStudio/SO-ARM100](https://github.com/TheRobotStudio/SO-ARM100)
- **Koch v1.1** - Alexander Koch's design, similar concept, ~$250.
- **LeKiwi** - wheeled mobile base for SO-100.

These are *the* hobbyist / educator hardware in 2026. Performance is below ALOHA (5 DOF vs 6, less rigidity, smaller payload), but the entry price is dramatically lower and the LeRobot dataset / model pipeline is excellent.

If you are an individual or a class setting up IL for the first time, start here.

## AnyTeleop (UC San Diego / NVIDIA, 2023)

Qin et al. [https://yzqin.github.io/anyteleop/](https://yzqin.github.io/anyteleop/)
Paper: [https://arxiv.org/abs/2307.04577](https://arxiv.org/abs/2307.04577)

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

- **Open-Television** (IIIS / MIT, 2024) - VR-based humanoid teleop with stereo passthrough. [https://github.com/OpenTeleVision/TeleVision](https://github.com/OpenTeleVision/TeleVision)
- **HOMIE** (Ben et al., 2025) - wearable exoskeleton for humanoid teleop. The exoskeleton locks the operator's joints to the robot's directly, closer to ALOHA's mechanical leader-follower philosophy than to camera-based tracking. The payoff is real proprioceptive feedback - the operator feels joint limits and loading, not just sees them on a screen - which no vision-based method above can replicate. The cost is donning time, a rig fitted per operator, and mechanical complexity (and failure modes) a webcam does not have.
- **DexCap** - wearable motion capture for dexterous manipulation. [https://dex-cap.github.io/](https://dex-cap.github.io/) The operator's hand is *instrumented* rather than mechanically constrained, which is the key distinction from an exoskeleton: you get five-finger pose data without needing a matching dexterous leader hand to exist at all. The tradeoffs are the ones every mocap rig has - a per-session calibration step, and pose quality that degrades whenever the capture system loses sight of what it is tracking.
- **UMI (Universal Manipulation Interface)** - Chi et al., 2024. Handheld grippers that record manipulation data *without a robot*. The operator just does the task; later you map it onto a robot. [https://umi-gripper.github.io/](https://umi-gripper.github.io/)
- **DOBB-E** (NYU / Hello Robot, 2023) - extension reacher with a camera; collect manipulation data via grocery-grabber. [https://dobb-e.com/](https://dobb-e.com/)

Exoskeletons and marker-based gloves sit on the same axis as AnyTeleop and VR hand-tracking above, just at the opposite end of it. Vision-based tracking is hardware-free and scales to as many operators as you have cameras, but it is noisy and latent. Worn hardware is precise and low-latency, but every operator needs a fitted rig and every session needs calibration. Neither wins outright - which one to use is a question of whether your bottleneck is operator throughput or demo precision, not a question of which is "better" in the abstract.

UMI deserves special attention: it dramatically reduces the cost of data collection by **decoupling demonstration from the robot**. You can record 100 hours of cooking demos with a UMI gripper for the cost of a few groceries; mapping those to a robot is a post-processing step. As of 2026 this is one of the more promising directions for *scaling* data collection.

## Egocentric human video as a data source

UMI already decouples demonstration from the robot - the operator does the task, mapping onto a robot happens later. Egocentric human video is the same idea taken to its logical extreme: no gripper at all, no markers, just a head-mounted or handheld camera recording a person doing the task with their own hands. It is not a teleop method - nobody is operating anything - but it belongs on this page because it competes with teleop for the same job: producing demonstrations to train a policy on.

The appeal is scale. Video of people cooking, cleaning, assembling, and manipulating objects exists in a volume no robot lab will ever match with teleop. Every hour of egocentric video anyone has ever recorded is, in principle, a demonstration.

The hard part is the embodiment gap, and it is severe:

- **No action labels.** Video shows what happened, not the control signal that caused it. There is no joint torque or end-effector velocity recorded in a video file - it has to be reconstructed after the fact.
- **Different kinematics.** A human hand has roughly two dozen degrees of freedom; most robot grippers have one. Mapping five-finger motion onto a parallel-jaw gripper throws most of that motion away, and there is no canonical way to decide what to keep.
- **Hands vs. grippers.** Human skin is compliant and grips via friction and conformance; most robot grippers are rigid and grip via force closure on a small number of contact points. A grasp that looks identical on video can be mechanically nothing alike once retargeted onto hardware.
- **Viewpoint mismatch.** Egocentric video is head-mounted; the deployment camera is usually wrist- or scene-mounted. Even the visual input distribution does not match.

What you get from the video is *observed*: hand and object pose in 3D, recoverable via pose estimation. What you need is *inferred*: the actual action, the grasp strategy, the contact forces, and often the subtask boundaries. All of that inference runs through the retargeting problem below, and today it is lossy enough that human video is mostly used to pretrain visual or representational backbones (see R3M, below) rather than to supply action labels directly. That is why, as of 2026, this remains a promising direction rather than a solved one: the data is abundant, but turning it into something a policy can act on is a research problem, not an engineering one.

## Multi-embodiment retargeting

Retargeting is the general problem both UMI and human video depend on: you have a demonstration recorded on one kinematic chain (a human hand, a UMI gripper, a leader arm) and you need it expressed in the action space of a different one - your robot.

**Joint-space retargeting** maps joint angles from source to target directly. This is why ALOHA and GELLO bother with mechanically similar leader-follower pairs in the first place (see above): when the two kinematic chains are close enough, joint-space retargeting is nearly the identity function, which is exactly why it is higher-bandwidth and immune to IK singularities.

**Task-space retargeting** maps the end-effector (or fingertip) pose and trajectory, then solves inverse kinematics on the target embodiment. This is unavoidable whenever source and target are kinematically dissimilar - a human hand mapped onto a parallel-jaw gripper, or one robot arm's demos reused on a differently sized arm.

What breaks in task-space retargeting, roughly in order of how often it bites:

- **Workspace limits.** The source trajectory can visit poses the target robot cannot reach at all. Naive retargeting either clips the trajectory (corrupting it) or fails outright.
- **Singularities.** An IK solver can produce discontinuous or ill-conditioned joint solutions near a singularity even when the source trajectory was perfectly smooth in task space.
- **Gripper geometry mismatch.** Finger length, aperture, and compliance differ between source (a human hand, a different gripper) and target. A grasp that closes cleanly on one geometry can miss, slip, or crush on another.
- **Dynamics differences.** Payload capacity, actuator bandwidth, and achievable joint velocity differ. A human hand's fast motion can be kinematically reachable on the target robot and still dynamically infeasible - the robot simply cannot move that fast.

When retargeting helps: when source and target are close in kinematics (matched leader-follower pairs, same-model robots across labs), or when the retargeted data only feeds a pretraining objective rather than being used directly as ground-truth actions.

When it silently poisons a dataset: when retargeting errors are systematic rather than random. An IK solver that consistently picks an unnatural elbow configuration, or a gripper mapping that gets contact timing subtly wrong, produces trajectories that are physically valid and look like normal training data - nothing in the schema or shape checks later on this page will catch them. Only a behavioral eval on the target robot will, and by then the bad data has already been trained on. This is the embodiment gap from the previous section, run at its hardest setting: human video retargeting, with no ground-truth robot action ever available to check the result against.

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

## Data curation and filtering at scale

The Field note above says to aggressively filter bad demos but does not say how to spot one in a dataset of a few hundred or a few thousand episodes where nobody has time to rewatch all of it. Some signals correlate with a bad demo well enough to be useful as a first pass:

- **Trajectory length outliers.** An episode much longer than the median often means hesitation, confusion, or a fumbled retry. One much shorter than the median often means a step got skipped.
- **Jerk and acceleration spikes.** Human teleop is never perfectly smooth, but a sudden, large spike in commanded jerk usually means a startled correction, not a deliberate motion.
- **Pauses mid-episode.** Long stretches of near-zero velocity in the middle of a task, not at a natural sub-goal, usually mean the operator stopped to think - which the policy has no reason to imitate.
- **Retries within an episode.** If the trajectory revisits a near-identical state it already passed through - the operator undoing and redoing the same sub-motion - that is usually a fumble being corrected, not a strategy.
- **Final-state verification failure.** Did the object actually end up where the task required? This needs a vision-based checker or a human glance, but it is the strongest signal of the group - the others are all proxies for this one.

None of these signals can tell you *why* the trajectory looks the way it does, and that is the catch: a long pause could be hesitation, or it could be the deliberate near-miss recovery this page told you earlier to keep ("Demonstrate the failure modes," above). A retry could be a fumble, or it could be exactly the contact-and-recover behavior that makes human demos worth collecting in the first place. Automated signals can flag candidates; they cannot adjudicate intent. The workable pipeline is automated flagging followed by human review of the flagged subset, not automated deletion - use the signals to make a few hundred demos reviewable, not to replace the reviewer.

Scoring a dataset for ranking, rather than a binary keep/discard, usually means computing these signals per episode, normalizing each into roughly comparable units, and combining them into a single score you sort by. Whether you then cut the bottom 10% or the bottom 40% is a threshold to treat as a hyperparameter validated against a held-out eval, not a fixed rule - a cutoff tuned on one task and robot will not transfer to the next. (More on why the eval split has to be frozen *before* you do any of this in "Dataset QA and regression testing," below.)

{% hint style="info" %}
**Field note.** Filter hard enough and you can turn a messy, multimodal dataset into a clean, unimodal one - and lose the thing that made human demonstrations better than scripted ones in the first place. A dataset where every demo takes the same path to the goal trains cleanly, but if the real task has two valid strategies (go around the obstacle left or right), filtering out the "noisier" of the two teaches the policy there is only one way to succeed. I do not have a clean rule for where the line is. Watch your held-out eval, not just your training loss, and be suspicious of any filtering pass that leaves your dataset looking *more* uniform than the task actually is.
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

## What a demo-hour actually costs

The demo counts above are not free, and the sticker price is not the operator's hourly wage. A demo-hour is composed of:

- **Operator wage** - what you pay the person driving the teleop rig.
- **Robot amortization** - hardware cost spread over its expected working life, plus the compute and infrastructure running alongside it.
- **Reset time between episodes** - moving objects back, re-homing the arm, clearing the workspace. This is usually the dominant cost and the one nobody budgets for up front: a task that takes 10 seconds to demonstrate can easily take a minute or more to reset for the next episode, so "task time" is a small fraction of the wall-clock time you actually pay for.
- **Hardware wear** - servos, cables, and gripper pads degrade under thousands of teleop cycles and eventually need replacing.
- **Discard rate** - the fraction of collected episodes that fail the curation pass above and never make it into training.

The number that actually matters is cost per *usable* demo, not cost per collected demo, and the discard rate is what separates them: if a quarter of what you collect gets filtered out, your real cost per usable demo is your collected-demo cost divided by 0.75, not 1. This is why "how aggressively should I filter" from the previous section is not purely a data-quality question - it is also a budget question. Filtering harder to tighten demo quality dispersion raises your discard rate, which raises your cost per usable demo, for a policy-quality benefit you can only confirm against a held-out eval. There is no formula that resolves this trade-off for you; there is only the arithmetic that tells you what each additional point of filtering is costing, which is worth knowing even if you decide to pay it.

| Cost component | Illustrative range - substitute your own values | Why it varies |
|---|---|---|
| Operator wage | Low to high, by region and skill | Student vs. contracted operator vs. domain specialist |
| Robot amortization | Small to moderate, per hour | Hardware cost divided by expected working lifetime hours |
| Reset overhead | Several times the task duration | Task complexity, workspace clutter, single- vs. multi-operator resets |
| Discard rate | Roughly a tenth to nearly half | Filtering aggressiveness, task difficulty, operator skill |
| Wear and consumables | Small but nonzero | Servo life, cable fatigue, gripper pad replacement |

This is also the calculation behind build-vs-buy. If a public dataset already covers your embodiment and task family - Open X-Embodiment, DROID, BridgeData V2, RoboSet, all covered on [Datasets & Benchmarks](datasets-and-benchmarks.md) - collecting a comparable volume yourself from scratch is usually the expensive path once reset time and discard rate are counted honestly. The reason to collect your own data anyway is that public datasets rarely match your exact camera setup, scene, or task ("Match the deployment camera," above), and that mismatch cost can outweigh the collection savings. The 2026 default is to lean on public data and VLA pretraining for general competence (see [Foundation Models & VLAs](foundation-models-vla.md) for the fine-tuning demo counts that assumes) and spend your own demo-hours narrowly, on the task-specific data nothing public can substitute for.

## Data formats and tooling

In 2026 there are basically two dominant formats:

- **LeRobot dataset format** - HuggingFace-hosted, Parquet + video, well-supported. [https://github.com/huggingface/lerobot](https://github.com/huggingface/lerobot)
- **RLDS** (Reinforcement Learning Datasets) - Google's format, TFDS-based, used by Open X-Embodiment and most VLA training. [https://github.com/google-research/rlds](https://github.com/google-research/rlds)

LeRobot is easier for individuals/small labs. RLDS is the standard for big VLA training. Tools exist to convert between them.

For your own datasets: just use LeRobot's format. Re-inventing data formats is a rite of passage and a waste of a week.

## Tooling for data collection workflows

- **LeRobot teleop scripts** - control rig + record + replay all in one. The 2026 default.
- **Foxglove** - visualize and replay teleop sessions. [https://foxglove.dev/](https://foxglove.dev/) Useful for QA-ing demos.

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

## Dataset QA and regression testing

"CI on the dataset, regression tests on the policy" above is doing a lot of work. Here is what it actually means in practice. Treat a dataset the way you would treat a codebase: it needs checks that run automatically, and a stable reference to compare against. A few checks matter specifically because this is robot data, not data in general:

- **Schema and shape validation.** Every episode should have the same keys, dtypes, and array shapes you expect (image resolution, action dimensionality, state vector length). Firmware updates and gripper encoding changes break this silently - catch it at ingestion, not at training time.
- **Timestamp monotonicity and dropped frames.** Check that every sensor stream's timestamps are strictly increasing and that the frame rate does not deviate far from nominal mid-episode. A camera stream that silently drops frames for half a second looks fine in aggregate statistics and produces a policy trained on corrupted temporal structure.
- **Camera dropouts mid-episode.** On multi-camera rigs sharing USB bandwidth, a camera can freeze and keep publishing its last frame instead of erroring out. This is invisible unless you specifically check for it - it will not show up as a missing frame, it will show up as a stale one, so check for runs of identical consecutive frames.
- **Calibration drift across a multi-day session.** Hand-eye and camera extrinsics can shift if a mount gets bumped between sessions. A dataset collected across a week where day 1-3 and day 4-5 have subtly different camera extrinsics is, from the policy's perspective, two different tasks glued together. Re-run a calibration check periodically during long collection campaigns and diff the result against the last one.

**Freeze your eval split before you filter, not after.** Pick and freeze a fixed set of initial conditions for evaluation first, exclude them from anything used for training, and only then apply the curation criteria from earlier on this page to what remains. Do it in the other order - filter first, carve the eval split out of the survivors - and your filtering criteria have already leaked into your eval set. Every policy comparison you run afterward is measuring your filter, not your policy.

**Version the dataset like you version code.** Tag what changed between dataset revisions (50 new demos added, 12 filtered out, one camera recalibrated) and record which dataset version a given policy checkpoint was trained on. Without this, "the new policy is better" and "the new dataset is different" become impossible to tell apart six months later.

## Further reading

- Zhao et al., *"Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware"* (ALOHA + ACT) - [https://arxiv.org/abs/2304.13705](https://arxiv.org/abs/2304.13705)
- Fu et al., *"Mobile ALOHA: Learning Bimanual Mobile Manipulation with Low-Cost Whole-Body Teleoperation"* - [https://arxiv.org/abs/2401.02117](https://arxiv.org/abs/2401.02117)
- Wu et al., *"GELLO: A General, Low-Cost, and Intuitive Teleoperation Framework for Robot Manipulators"* - [https://arxiv.org/abs/2309.13037](https://arxiv.org/abs/2309.13037)
- Chi et al., *"Universal Manipulation Interface: In-The-Wild Robot Teaching Without In-The-Wild Robots"* (UMI) - [https://umi-gripper.github.io/](https://umi-gripper.github.io/)
- Qin et al., *"DexMV: Imitation Learning for Dexterous Manipulation from Human Videos"* - [https://arxiv.org/abs/2108.05877](https://arxiv.org/abs/2108.05877)
- Nair et al., *"R3M: A Universal Visual Representation for Robot Manipulation"* - [https://arxiv.org/abs/2203.12601](https://arxiv.org/abs/2203.12601)
- Grauman et al., *"Ego4D: Around the World in 3,000 Hours of Egocentric Video"* - [https://arxiv.org/abs/2110.07058](https://arxiv.org/abs/2110.07058)
- LeRobot teleop documentation - [https://huggingface.co/docs/lerobot/](https://huggingface.co/docs/lerobot/)
