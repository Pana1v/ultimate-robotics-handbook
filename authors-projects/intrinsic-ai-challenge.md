---
icon: plug
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

***

## The progression (and why each step happened)

I did not start with learning. I climbed the ladder of increasing sophistication, and each rung failed for a reason that pushed me to the next.

1. **Hand-coded finite state machine, ground-truth mode.** With perfect pose, a scripted approach-align-insert FSM with a force/torque guard scored **280+**. This is the baseline that proves the task is solvable when perception is free.
2. **Classical CV - blob detection.** The first attempt at real perception. Threshold, find the port-shaped blob, estimate pose. Brittle the moment lighting, distractors, or board pose moved.
3. **Learned perception - ResNet18 / U-Net.** Regress the port location / segment the port mask. Better than blobs, but hungry for labeled data and still wobbly out of distribution.
4. **YOLO-based detection.** Treat the port as an object-detection target. Cleaner, but detection accuracy did not translate to insertion-grade pose accuracy.
5. **Imitation learning - ACT and SmolVLA.** End-to-end: learn the insertion policy from teleoperated demonstrations. This is the modern answer, and where the real lesson lived.

***

## The data wall

The binding constraint was never the model architecture. It was **data** - specifically, collecting enough diverse teleop demonstrations to cover the distribution the evaluator would throw at me: distractor ports, board-pose randomization, multiple NICs in the scene, lighting variation.

> With perfect pose information I hit **286 / 300**. The same policy in the randomized real-world evaluation fell apart - not because the policy was wrong, but because my demonstrations did not cover the multi-NIC, randomized-board scenes the evaluator generated.

This is the gap the [Robot Learning](../robot-learning/robot-learning.md) section of this handbook keeps coming back to: imitation learning is only as good as its demonstration coverage, and collecting that coverage is the actual job. Domain randomization in *simulation* is cheap; domain randomization in *teleop data* is expensive human time. See [Teleoperation and Data Collection](../robot-learning/teleop-and-data.md) and [Imitation Learning](../robot-learning/imitation-learning.md) for the techniques this project leaned on.

***

## What I would do differently

* **Budget the data, not the model.** I spent too long swapping perception backbones (ResNet → U-Net → YOLO) when the leverage was in demonstration diversity.
* **Randomize the demos, not just the sim.** Coverage of distractors and board pose at *collection* time would have closed most of the sim-to-eval gap.
* **Keep the FSM as a fallback.** The 280+ scripted baseline is a real safety net; a learned policy that can hand off to a scripted insert under uncertainty is more robust than either alone.

The full narrative - with the dead ends, the scores at each stage, and the SmolVLA experiments - is in the [Substack post](https://pana1v.substack.com/p/a-journey-through-the-intrinsic-ai).
