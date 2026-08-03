---
icon: plug
description: A solo entry to Intrinsic's AI for Industry Challenge - fiber-optic cable insertion with ACT and SmolVLA, a ladder of perception approaches, and the data wall that separates a 286/300 ground-truth score from a real-world one.
---

# Intrinsic AI for Industry Challenge - Learning to Plug a Cable

> Intrinsic's (Alphabet) **AI for Industry Challenge**: autonomously plug a fiber-optic cable into a port reachable by a robot arm. I worked through the full stack of approaches - hand-coded state machines, classical CV, learned perception, and finally imitation learning - and ran straight into **the data wall**. Scored **286 / 300** with perfect pose information; the real-world evaluation was a different animal entirely.

**Role:** Solo entrant
**Platform:** UR5e arm + Robotiq gripper, force/torque sensing
**Stack:** Python, ResNet18, U-Net, YOLO, ACT (Action Chunking Transformer), SmolVLA
**Task:** Fiber-optic cable insertion into a board-mounted port
**Source:** Full write-up - [A Journey Through the Intrinsic AI for Industry Challenge](https://pana1v.substack.com/p/a-journey-through-the-intrinsic-ai) (May 2026)

***

## The task

Insert a fiber-optic cable into a small port mounted on a board in front of a UR5e arm. It sounds trivial - it is the kind of thing a human does without thinking - and that is exactly why it is a good benchmark. Contact-rich insertion under perception uncertainty is the long-standing hard problem in manipulation: the tolerances are tight, the cable is compliant, and "close enough" fails the insertion.

The challenge ran in two regimes:

* **Ground-truth mode** - you get the exact pose of the port. The problem reduces to motion planning and contact handling.
* **Perception mode** - you get camera images and have to figure out where the port is yourself, including with distractor ports and a randomized board pose.

These are not two difficulty settings on the same problem - they stress entirely different parts of the stack:

| | Ground-truth mode | Perception mode |
|---|---|---|
| What's actually being tested | Motion planning + contact handling | All of that, *plus* perceiving the port under distractors and board-pose randomization |
| Main bottleneck | Force/torque-guided insertion quality | Demonstration coverage of the scene distribution |
| What carries over from the other mode | - | The insertion primitive itself (approach/align/insert) transfers; the perception problem does not |
| Score reached | **286 / 300** (scripted FSM: 280+) | <!-- AUTHOR: insert final perception-mode score --> |

***

## Why cable insertion is a hard manipulation problem

It looks trivial because a human does it without conscious thought, and that gap - trivial for a human, hard for a robot - is exactly what makes it a useful benchmark rather than a toy one. Three things stack against you:

1. **Sub-millimeter tolerance.** A fiber connector has to align to the port within a fraction of a millimeter, along the correct insertion axis, before it will seat. Vision alone, even good vision, typically localizes a small connector to a few millimeters of accuracy once you account for camera calibration error, depth noise, and the connector's own geometric ambiguity. That is not good enough. The last few millimeters of this task cannot be a purely visual servoing problem.
2. **The object is compliant, not rigid.** The cable itself flexes, and its exact pose right before insertion depends on how it was grasped, how it is hanging, and residual strain from the approach motion - none of which is fully observable from an image. A rigid-body pose estimate for the connector does not capture the cable's state.
3. **The task is force-dominated near contact, not vision-dominated.** Once the connector tip is near the port, the meaningful signal shifts from "where is it" (vision) to "what does contact feel like" (force/torque) - is the connector cocked at an angle, is it catching on the port's lip, is it seated. A policy that only looks and never feels is trying to solve the hardest 5% of the task blind.

The dominant sensing modality actually changes over the course of the motion, which is easy to say and easy to miss in practice:

```
[Approach]                  [Align]                        [Insert]
vision-dominant       -->   vision + coarse force    -->    force-dominant
"get near the port"         "correct residual pose"         "feel for seating, catch snags"
```

A policy - or a person - that treats this as one uniform motion instead of three regimes with different dominant senses is going to either overshoot on approach (too cautious, using force cues too early) or miss the seating feel on insert (too visual, ignoring force cues too late). This is the general reason contact-rich insertion tasks - USB, peg-in-hole, board connectors, this fiber port - show up again and again as manipulation benchmarks: they force a policy to combine coarse visual reaching with fine, force-aware contact behavior in one continuous motion, and getting only one of those right is not enough.

***

## The progression (and why each step happened)

I did not start with learning. I climbed the ladder of increasing sophistication, and each rung failed for a reason that pushed me to the next.

1. **Hand-coded finite state machine, ground-truth mode.** With perfect pose, a scripted approach-align-insert FSM with a force/torque guard scored **280+**. This is the baseline that proves the task is solvable when perception is free.
2. **Classical CV - blob detection.** The first attempt at real perception. Threshold, find the port-shaped blob, estimate pose. Brittle the moment lighting, distractors, or board pose moved - classical CV has no built-in invariance to any of that, and hand-tuning thresholds for one lighting condition is not a generalizable strategy.
3. **Learned perception - ResNet18 / U-Net.** Regress the port location, or segment the port mask. Better than blobs, but hungry for labeled data and still wobbly out of distribution - a detector trained on the scenes I happened to collect is not the same thing as a detector that has seen the scene the evaluator will actually generate.
4. **YOLO-based detection.** Treat the port as an object-detection target. Cleaner, but detection accuracy did not translate to insertion-grade pose accuracy. This is the classic gap between "the box is roughly right" and "the pose is precise enough to insert" - object detection and precision pose estimation are different problems wearing the same bounding box.
5. **Imitation learning - ACT and SmolVLA.** End-to-end: learn the insertion policy from teleoperated demonstrations. This is the modern answer, and where the real lesson lived.

As a quick reference, the same progression compressed:

| Stage | Approach | Why it moved on | Score |
|---|---|---|---|
| 1 | Hand-coded FSM, ground-truth mode | Baseline - proves the task is solvable with free perception | **280+** |
| 2 | Classical CV, blob detection | Brittle to lighting, distractors, board-pose changes | - |
| 3 | Learned perception (ResNet18 / U-Net) | Data-hungry, wobbly out of distribution | - |
| 4 | YOLO-based detection | Detection accuracy did not translate to insertion-grade pose accuracy | - |
| 5 | Imitation learning (ACT, SmolVLA) | End-to-end, learns contact behavior directly instead of bolting a primitive onto perception | **286/300** (ground-truth) |

***

## ACT vs SmolVLA - two answers to the data wall

By the time I got to imitation learning, the lesson from stages 1-4 was already clear: perception could get me *close* to the port, but "close" is not "inserted," and closing that last gap needed something that could learn contact behavior end-to-end rather than a hand-tuned insertion primitive bolted onto a perception pipeline. ACT and SmolVLA are both credible answers to that, but they trade off differently, and the trade-off matters for a task this contact-sensitive.

**ACT (Action Chunking Transformer)** - see [Imitation Learning](../robot-learning/imitation-learning.md) for the full mechanism - predicts a chunk of future actions at once instead of one step at a time, which compresses the effective control horizon. That is exactly the property you want for a fast, contact-rich insertion motion: low inference latency (a single forward pass, single-digit milliseconds), good sample efficiency, and a policy that commits to a short multi-step plan instead of dithering at the moment of contact. The cost is that ACT is narrow - it is trained for this task, on this setup, and does not carry language conditioning or broad visual generalization with it.

**SmolVLA** - a compact, open vision-language-action model built by Hugging Face for the LeRobot ecosystem, designed to fine-tune and run on modest, consumer-grade hardware rather than requiring a datacenter GPU - brings the opposite trade-off. It carries language conditioning and whatever general visual competence its pretraining bought it (see [Foundation Models & VLAs](../robot-learning/foundation-models-vla.md) for the VLA paradigm it belongs to), at the cost of being a bigger, slower-to-run model than a from-scratch ACT policy, with base competence spread across many tasks rather than concentrated on this one.

Neither model choice fixed the actual problem. **Both are bounded by the same demonstration coverage**, and that is the whole thesis of this page: the model was not what determined whether the policy generalized to the evaluator's randomized scenes. The data was.

| | ACT | SmolVLA |
|---|---|---|
| Inference latency | Single forward pass, low milliseconds | Higher - a larger VLA backbone, not built for this control rate |
| Language conditioning | None | Yes |
| Visual generalization | Only what this task's demos taught it | Inherits some breadth from VLA pretraining |
| Compute to fine-tune | Modest, single consumer GPU territory | Modest for a VLA - designed for consumer-grade hardware, per its authors |
| What it needed from me | Task-specific demos, nothing else | Same demos, plus whatever its pretraining already covered |

<!-- AUTHOR: insert comparative success rates / behavior differences observed between the ACT and SmolVLA policies once finalized -->

***

## The data wall

The binding constraint was never the model architecture. It was **data** - specifically, collecting enough diverse teleop demonstrations to cover the distribution the evaluator would throw at me: distractor ports, board-pose randomization, multiple NICs in the scene, lighting variation.

> With perfect pose information I hit **286 / 300**. The same policy in the randomized real-world evaluation fell apart - not because the policy was wrong, but because my demonstrations did not cover the multi-NIC, randomized-board scenes the evaluator generated.

<!-- AUTHOR: insert the actual perception-mode / randomized-evaluation score here once finalized -->

[Imitation Learning](../robot-learning/imitation-learning.md) puts the general principle bluntly: diversity matters more than count, and 200 diverse demonstrations beat 1000 collected from the same starting state. My demonstration set did not have enough coverage of the distractor-port and board-pose randomization the evaluator generated - which is a data problem, not a model problem, and no amount of swapping ACT for SmolVLA (or back) was going to fix it.

<!-- AUTHOR: insert total demo count collected, and the split between the ACT and SmolVLA training sets -->

This is the gap the [Robot Learning](../robot-learning/robot-learning.md) section of this handbook keeps coming back to: imitation learning is only as good as its demonstration coverage, and collecting that coverage is the actual job. Domain randomization in *simulation* is cheap; domain randomization in *teleop data* is expensive human time. See [Teleoperation and Data Collection](../robot-learning/teleop-and-data.md) for the techniques this project leaned on.

***

## What I would do differently

* **Budget the data, not the model.** I spent too long swapping perception backbones (ResNet to U-Net to YOLO) when the leverage was in demonstration diversity.
* **Randomize the demos, not just the sim.** Coverage of distractors and board pose at *collection* time would have closed most of the sim-to-eval gap.
* **Keep the FSM as a fallback.** The 280+ scripted baseline is a real safety net; a learned policy that can hand off to a scripted insert under uncertainty is more robust than either alone.
* **Budget reset time and discard rate honestly.** [Teleoperation & Data Collection](../robot-learning/teleop-and-data.md) makes the point that the real cost of a demo is reset overhead and discard rate, not the wage of the person driving the rig. In hindsight I was collecting to a demo-count target instead of a coverage target, which is the wrong unit to optimize.

The full narrative - with the dead ends, the scores at each stage, and the SmolVLA experiments - is in the [Substack post](https://pana1v.substack.com/p/a-journey-through-the-intrinsic-ai).

{% hint style="info" %}
**Field note.** The most useful thing this project taught me is that "which model" is usually the wrong question until "which data" has been answered honestly. I climbed four rungs of perception sophistication before touching imitation learning, and every one of those rungs was a real improvement - and every one of them still hit the same wall, because none of them changed how much of the task distribution I had actually demonstrated. If I had spent the ResNet/U-Net/YOLO weeks collecting board-pose-randomized teleop demos instead, I suspect I would have shipped a better policy with a worse perception stack.
{% endhint %}

## Further reading

- Zhao et al., *"Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware"* (ACT/ALOHA) - [https://arxiv.org/abs/2304.13705](https://arxiv.org/abs/2304.13705)
- Shukor et al., *"SmolVLA: A Vision-Language-Action Model for Affordable and Efficient Robotics"* - [https://arxiv.org/abs/2506.01844](https://arxiv.org/abs/2506.01844)

***

## Find me online

[panav.netlify.app](https://panav.netlify.app) · [github.com/Pana1v](https://github.com/Pana1v) · [linkedin.com/in/panavraaj](https://linkedin.com/in/panavraaj)
