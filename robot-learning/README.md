---
icon: brain
---

# Robot Learning

Robot learning is the part of the field that exploded between 2022 and 2026. If you trained as a robotics engineer before the LLM era, this is the half of the discipline that probably did not exist when you took your first controls course. If you are just entering the field now, this is probably what drew you in.

This section covers the modern paradigm: how robots learn skills from data instead of being programmed with closed-form controllers. It is opinionated. The field moves fast and a lot of what gets shipped in demos does not survive contact with a real factory floor.

## The four (and a half) paradigms

There are roughly four ways to make a robot do a useful task in 2026. Pick the wrong one and you waste a year.

| Paradigm | Core idea | Data needs | Best for | Worst for |
|---|---|---|---|---|
| **Classical control** | Model the system, design a controller (PID, LQR, MPC) | None | Well-modeled rigid systems, safety-critical loops | Contact-rich manipulation, unstructured environments |
| **Model-based RL** | Learn dynamics, plan/optimize against the model | Medium (sim) | Locomotion, dexterous manipulation in sim | Tasks where dynamics are hard to learn (deformables) |
| **Model-free RL** | Learn a policy directly from rewards | High (sim, real if you can) | Locomotion (ANYmal, Spot), some manipulation | Tasks without dense reward signals |
| **Imitation learning** | Mimic human demonstrations | Medium-high (teleop) | Manipulation, mobile manipulation, anywhere a human can demo | Tasks humans cannot demo (faster-than-human, micro-scale) |
| **Foundation models / VLA** | Pretrain on internet-scale data, fine-tune for your task | Huge (pretrain), small (fine-tune) | Generalist tasks, language-conditioned behaviors | Anything needing <10ms cycle time, low-latency control |

The "half" paradigm is **hybrid stacks**: a foundation model picks high-level subgoals, a classical or learned low-level controller executes them. Most things that actually work in 2026 are hybrid.

{% hint style="info" %}
**Field note.** If a vendor is selling you "end-to-end learned" anything for a real production deployment in 2026, ask them what runs the safety stop. The answer is always a hand-written controller. Learning is for the parts of the problem that classical methods cannot express; do not use it for the parts they handle fine.
{% endhint %}

## When to use what

A decision tree that has saved me about a year of false starts:

1. **Can you write down the dynamics and constraints?** Use classical control. PID still wins most of the things people throw RL at.
2. **Is the task contact-rich (peg-in-hole, cloth manipulation, deformables)?** Skip analytic models. Go imitation learning or sim RL.
3. **Can a human teleoperate the task at decent quality?** Start with imitation learning. Diffusion Policy or ACT, ~50–500 demos, two days of work.
4. **Does the task generalize across many objects/scenes/instructions?** This is where VLAs (π0, OpenVLA, RT-2) earn their keep. But you still need task-specific demos for fine-tuning.
5. **Is the task a locomotion / whole-body control problem?** Sim-based PPO with privileged learning. The ANYmal/Walk-These-Ways recipe is the field standard.
6. **Do you have no demonstrations, no reward function, no simulator?** You do not have a robot learning problem. You have a problem.

## Subpages

- [Imitation Learning](imitation-learning.md) — BC, DAgger, ACT, Diffusion Policy. The most practical entry point for manipulation in 2026.
- [Modern Reinforcement Learning](reinforcement-learning-modern.md) — PPO for locomotion, SERL/HIL-SERL, Eureka, sim-to-real RL pipelines. The legged locomotion playbook.
- [Foundation Models & VLAs](foundation-models-vla.md) — RT-1/2/X, OpenVLA, π0, Octo. Where the field thinks it is going.
- [World Models](world-models.md) — DreamerV3, Cosmos, Genie, GAIA. Sample-efficiency and planning via learned simulators.
- [Sim-to-Real](sim-to-real.md) — Domain/dynamics randomization, Isaac Lab, MuJoCo MJX, Genesis. Why your sim-trained policy will fall over and what to do about it.
- [Teleoperation & Data Collection](teleop-and-data.md) — ALOHA, Mobile ALOHA, GELLO, AnyTeleop. The hardware that feeds the policies.
- [Datasets & Benchmarks](datasets-and-benchmarks.md) — Open X-Embodiment, DROID, LIBERO, RoboCasa, BEHAVIOR-1K, BARN.

## What does NOT belong here

A lot of robotics ML is just perception (detection, segmentation, depth estimation). That lives in [ML and Perception](../ml-and-perception/ml-and-perception.md). Robot learning is specifically about learning policies, dynamics, or world models — about closing the loop from sensors to actions, not just labeling pixels.

Classical reinforcement learning theory (MDPs, Bellman equations, DQN, the Sutton & Barto material) lives in [Reinforcement Learning](../ml-and-perception/reinforcement-learning.md). This section assumes you have at least skimmed that page.

## Reading order

If you are new to robot learning, here is the path I wish I had taken:

1. Read the Sutton & Barto Chapter 1 + the existing [RL page](../ml-and-perception/reinforcement-learning.md) so MDPs and policy gradients are not mysteries.
2. Read the [Imitation Learning](imitation-learning.md) page. Clone `lerobot`. Run the ACT tutorial on a sim arm. ~1 weekend.
3. Read the [Sim-to-Real](sim-to-real.md) page. Install Isaac Lab. Run the cartpole and quadruped tutorials. ~1 weekend.
4. Read the [Modern RL](reinforcement-learning-modern.md) page. Train a quadruped to walk in Isaac Lab. ~1 week if you have a GPU.
5. Read [Foundation Models](foundation-models-vla.md). Try OpenVLA fine-tuning if you have a teleop rig. Most readers will stop here.
6. [World Models](world-models.md) and the frontier stuff. Most of it is research-grade; do not bet a product on it yet.

## How fast is this moving?

Faster than this handbook. Treat anything in this section that is more than 18 months old as "probably still useful, but check what replaced it." I will try to date claims where I can.

State of play as of late 2025 / early 2026:

- **Diffusion Policy** is still the manipulation imitation default but **flow-matching policies** (π0, π0.5) are eating its lunch on long-horizon tasks.
- **OpenVLA** is the open-weights VLA baseline; **π0 / π0.5** is the commercial-ish SOTA with weights released.
- **Isaac Lab** has effectively replaced Isaac Gym; **Genesis** is the new fast-physics challenger.
- **GR00T** (NVIDIA) is the buzzword for humanoid foundation models but is still mostly a marketing umbrella over multiple research efforts.
- **Cosmos** dropped early 2025 as NVIDIA's bid for a video-pretrained world model for robotics. Real-world utility still being assessed.

## Further reading

- Sergey Levine, *"Understanding the World Through Action"* (2021) — old now but still the clearest framing of why learning matters for robotics: [https://arxiv.org/abs/2110.12543](https://arxiv.org/abs/2110.12543)
- Chelsea Finn's CS 224R course at Stanford, "Deep Reinforcement Learning" — lectures on YouTube, slides public.
- LeRobot blog series from HuggingFace ([https://huggingface.co/lerobot](https://huggingface.co/lerobot)) — practical, current, and the closest thing the field has to a textbook.
- The *Robotics: Science and Systems* (RSS) and *Conference on Robot Learning* (CoRL) proceedings — read the last two years' best papers.
- *State of Robot Learning* — annual review threads on Twitter/X by Sergey Levine, Chelsea Finn, and Pieter Abbeel are usually more current than any survey paper.
