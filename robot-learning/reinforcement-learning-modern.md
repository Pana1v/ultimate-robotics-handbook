---
icon: brain
---

# Reinforcement Learning (modern)

The [classical RL page](../perception-and-computer-vision/reinforcement-learning.md) covers MDPs, policy gradients, DQN, SAC, and the rest of the textbook canon. This page is about what actually works on real robots in 2026 - which is a much narrower slice than the textbook would suggest.

The short version: model-free RL on real robots is _still_ mostly impractical except for narrow domains. Where RL succeeds in production, it almost always means:

1. **Sim-trained PPO with privileged learning + domain randomization** (legged locomotion playbook), or
2. **Real-world sample-efficient RL with human-in-the-loop corrections** (SERL/HIL-SERL playbook for manipulation), or
3. **LLM-generated rewards + sim training** (Eureka and friends, for tasks where reward shaping was the bottleneck).

## Why "just train SAC on the real robot" does not work

Newcomers see Atari results, OpenAI's hand, and the original DeepMind quadruped work, and think model-free RL on real hardware is a solved problem. It is not.

Real robots have:

* **Slow data.** A 1kHz control loop gets you 3.6M samples in an hour. SAC needs \~1M for cartpole and 10–100M for anything interesting.
* **Hardware degradation.** You will break the robot before you finish training. Or your dataset will reflect a robot that no longer exists by the time you converge.
* **Resets.** "Move the arm back to the start" is itself a non-trivial policy. Autonomous resets are a whole research area.
* **Safety constraints.** You cannot let the policy go full random-exploration on a $50k arm.

So either you go to sim (and then have a sim-to-real problem), or you accept that you need a _sample-efficient_ algorithm + a human safety net, which is what SERL/HIL-SERL does.

## The legged locomotion playbook: PPO + privileged learning

This is the most successful real-world RL recipe in robotics, full stop. Every quadruped you have seen walking around in 2023–2026 - ANYmal, Spot, Unitree, etc. - uses some descendant of this pipeline.

The recipe, as established by:

* Lee et al., _"Learning quadrupedal locomotion over challenging terrain"_, Science Robotics 2020 - [https://arxiv.org/abs/2010.11251](https://arxiv.org/abs/2010.11251)
* Margolis & Agrawal, _"Walk These Ways"_, CoRL 2022 - [https://arxiv.org/abs/2212.03238](https://arxiv.org/abs/2212.03238)
* Kumar et al., _"RMA: Rapid Motor Adaptation for Legged Robots"_, RSS 2021 - [https://arxiv.org/abs/2107.04034](https://arxiv.org/abs/2107.04034)

The pipeline:

1. **Train a&#x20;**_**teacher**_**&#x20;policy in sim with privileged info.** The teacher sees ground-truth friction, terrain height, contact forces, base velocity - things the real robot will never have access to. This makes RL much easier; the teacher converges to good locomotion in a few hours on a GPU. Use PPO.
2. **Distill the teacher into a&#x20;**_**student**_**&#x20;policy that only uses proprioception + history.** Supervised learning from the teacher's actions, conditioned on the limited sensor inputs the real robot actually has.
3. **Deploy the student.** It implicitly identifies terrain parameters from the history of joint readings.

```
[Sim with privileged observations] -- PPO --> [Teacher policy π_teach(o_priv)]
[Sim with realistic observations]  -- BC  --> [Student policy π_stud(o_hist)]
[Real robot]                       -- run --> [Student policy]
```

**Why this works:**

* The teacher's RL problem is well-conditioned because the privileged observations make the world \~MDP.
* The student's problem is supervised learning (easy, sample-efficient).
* The history-conditioning lets the student infer environment parameters online.

**Walk-These-Ways extension:** Margolis & Agrawal showed you can condition the policy on commanded gait parameters (frequency, phase offset, step height, step width) so a single policy can do multiple gaits and you can change behavior at runtime without retraining. This is the basis for most modern multi-gait quadrupeds.

**Tools:**

* **Isaac Lab** - [https://github.com/isaac-sim/IsaacLab](https://github.com/isaac-sim/IsaacLab) - the de facto trainer. Replaced Isaac Gym in 2024.
* **rsl\_rl** - [https://github.com/leggedrobotics/rsl\_rl](https://github.com/leggedrobotics/rsl_rl) - clean PPO impl from ETH RSL, what ANYmal used.
* **legged\_gym** (now part of Isaac Lab) - task suite for quadruped/humanoid locomotion.

{% hint style="info" %}
**Field note.** People talk about "training a quadruped to walk with RL" like it's hard. With Isaac Lab and rsl\_rl you can train a passable walking policy in 30 minutes on a 4090. The hard part is the next 6 months of reward tuning, domain randomization, and sim-to-real debugging to get it to walk on _your_ terrain _robustly_ without bricking the robot.
{% endhint %}

## Reward shaping is 80% of the work

RL papers in robotics almost never publish their reward functions in full because they are page after page of `if-this-then-that-coefficient`. A typical quadruped locomotion reward has \~15-25 components:

* Track linear velocity (positive)
* Track angular velocity (positive)
* Penalize base height deviation
* Penalize roll/pitch
* Penalize joint accelerations (smoothness)
* Penalize torque (energy)
* Penalize action rate (smoothness)
* Penalize foot slip
* Reward foot clearance
* Reward periodic foot contact (gait shaping)
* Penalize self-collision
* Penalize joint limits
* ... and so on.

Each coefficient takes hours of sweeping to tune. This is the part nobody talks about and that nobody enjoys.

## Eureka: LLM-generated rewards

Ma et al., NVIDIA & UPenn, 2023. [https://arxiv.org/abs/2310.12931](https://arxiv.org/abs/2310.12931)

Project: [https://eureka-research.github.io/](https://eureka-research.github.io/)

Eureka uses GPT-4 to _write_ reward functions. You describe the task in natural language, GPT-4 outputs candidate Python reward functions, you train policies with each in parallel, and iterate based on which policies perform best.

For a class of tasks - primarily those where reward shaping was the bottleneck - Eureka generates rewards that beat human-engineered ones. It is particularly good at the "many small reward components I would not have thought of" problem.

**Caveats from someone who has used it:**

* It works best in _Isaac Gym / Isaac Lab_, where the simulation API is in the LLM's training data.
* It struggles with subtle physics (e.g., contact-dependent shaping) that requires actually running episodes to understand.
* The iteration loop is expensive (you train hundreds of policies).
* DrEureka (the sim-to-real successor) extends this to _generate_ the domain randomization ranges automatically: [https://eureka-research.github.io/dr-eureka/](https://eureka-research.github.io/dr-eureka/)

## SERL and HIL-SERL: real-world sample-efficient RL

Luo, Hu, Schaal et al., Berkeley, 2024. [https://serl-robot.github.io/](https://serl-robot.github.io/)

SERL (Sample-Efficient Robotic Reinforcement Learning) showed that with the right algorithmic stack you can do real-world RL on a manipulation task in 30 minutes to 2 hours of robot time. This was a watershed result - it shifted the conversation from "sim-to-real is the only path" to "actually maybe we can do real-world RL after all."

Key ingredients:

* **SAC with RLPD-style replay** - uses prior demonstrations + online data, off-policy critic learns fast.
* **Forward + backward policy.** Two policies - one to do the task, one to reset the workspace. This solves the reset problem.
* **Image encoder pretrained on the demo data.**
* **Sparse binary reward** ("did the gripper close on the object? did the part insert?"). No reward shaping.

**HIL-SERL** (Human-in-the-Loop SERL, 2024) [https://hil-serl.github.io/](https://hil-serl.github.io/) adds DAgger-style human corrections during training. When the policy is about to do something dumb, a human grabs a joystick and corrects. The correction goes into the buffer with high priority. This combines IL warm-start + RL refinement + human safety in one loop.

Results: trains contact-rich tasks (RAM insertion, dynamic flipping, cable routing) on real hardware in 1-3 hours total robot time.

{% hint style="info" %}
**Field note.** HIL-SERL is what I would actually deploy in 2026 if I needed real-world RL on a manipulation task. The combination of demo bootstrap + sparse reward + human correction is dramatically better than any pure-RL or pure-IL approach I have tried. Caveat: it requires a competent teleoperator who knows when to intervene. Untrained operators add noise that hurts.
{% endhint %}

## Curriculum learning

A curriculum is "start the task easy, make it progressively harder as the policy improves." For locomotion this looks like:

1. Train on flat ground with low commanded velocities.
2. Once tracking error drops below threshold, increase velocity range.
3. Add terrain randomization (stairs, slopes, gaps).
4. Add disturbances (random pushes).
5. Add payload variation.

Automatic curricula (where the system picks the next difficulty automatically) work well:

* **ALP-GMM** (Automatic Learning Progress / Gaussian Mixture Models) - Portelas et al.
* **Adaptive Curriculum** in Isaac Lab - grid-based terrain difficulty that promotes/demotes the robot based on success rate.

Use a curriculum on anything that does not converge in vanilla training. It often turns "does not work" into "works."

## Sim-to-real transfer (high level)

A whole page on this: [Sim-to-Real](sim-to-real.md). The TL;DR for RL specifically:

* Train with **domain randomization** (mass, friction, motor strength, latency, sensor noise, camera intrinsics).
* Train with **observation noise + action delay** that matches your real robot.
* Use **history-based policies** (recurrent or stack of past observations) so the policy can identify the dynamics online.
* For visual policies, randomize lighting, textures, distractors. Or use depth/segmentation as a more transferable representation.

## Multi-task and large-scale RL

The frontier in 2025–2026 is scaling RL to many tasks and many robots:

* **MTRL / multi-task PPO** - train one policy across many task variations.
* **PRO-X / Project GR00T** (NVIDIA) - humanoid foundation models trained partly with RL across simulated tasks.
* **RoboCasa + Isaac Lab combos** - large-scale procedural environments for RL pretraining.

These approaches blend into the VLA territory; see [Foundation Models & VLAs](foundation-models-vla.md).

## What about offline RL?

Offline RL (Q-learning from a static dataset, no environment interaction) - IQL, CQL, AWAC, etc. - looks great on paper for robotics: just use your demonstration data, no online interaction needed.

In practice for real robots in 2026:

* Offline RL on demonstration data alone _barely_ outperforms BC. The gain is small and the implementation pain is large.
* Offline RL pretraining + online RL fine-tuning (RLPD, Cal-QL) is a credible recipe and is what SERL effectively does.
* Pure offline RL on robot data is mostly a research curiosity right now. Use BC + ACT + Diffusion Policy instead unless you have a specific reason.

## Libraries

| Library                                                                                                                                       | Purpose                                                        | Notes                                                  |
| --------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------ |
| **Isaac Lab** - [https://github.com/isaac-sim/IsaacLab](https://github.com/isaac-sim/IsaacLab)                                                | Massively parallel sim for RL on Isaac Sim                     | The 2026 default for locomotion/manipulation RL.       |
| **rsl\_rl** - [https://github.com/leggedrobotics/rsl\_rl](https://github.com/leggedrobotics/rsl_rl)                                           | Clean PPO for legged robots                                    | What ETH/ANYmal uses.                                  |
| **MuJoCo MJX** - [https://github.com/google-deepmind/mujoco/tree/main/mjx](https://github.com/google-deepmind/mujoco/tree/main/mjx) | JAX-based MuJoCo, GPU-parallel                                 | Fastest option for many manipulation envs.             |
| **Brax** - [https://github.com/google/brax](https://github.com/google/brax)                                                                   | JAX-based physics + RL                                         | Differentiable, GPU-parallel. Older but solid.         |
| **Genesis** - [https://github.com/Genesis-Embodied-AI/Genesis](https://github.com/Genesis-Embodied-AI/Genesis)                      | Differentiable physics, claims to beat Isaac Gym in throughput | New (late 2024). Worth evaluating.                     |
| **Stable Baselines3** - [https://github.com/DLR-RM/stable-baselines3](https://github.com/DLR-RM/stable-baselines3)                            | PPO, SAC, TD3 in PyTorch                                       | Use for non-Isaac envs.                                |
| **CleanRL** - [https://github.com/vwxyzjn/cleanrl](https://github.com/vwxyzjn/cleanrl)                                                        | Single-file PPO/SAC implementations                            | Pedagogical, easy to fork.                             |
| **SERL/HIL-SERL** - [https://github.com/rail-berkeley/serl](https://github.com/rail-berkeley/serl)                                  | Real-world RL for manipulation                                 | The reference impl for real-world sample-efficient RL. |

## Practical pipeline I recommend (2026)

For someone tackling their first robot RL project:

1. **Pick a task you can simulate.** If you cannot simulate it cheaply, do IL instead.
2. **Use Isaac Lab.** Do not fight infrastructure.
3. **Start with a known-good task** (e.g., the cartpole, ant, or anymal env). Get it training.
4. **Modify incrementally.** Change one thing per training run.
5. **Use a curriculum from day 1.** Even a 2-stage curriculum helps.
6. **Domain randomize from day 1.** Cheaper than fixing sim-to-real gap later.
7. **Test in sim with the same domain randomization the real robot will face.** This is your validation set.
8. **Distill to a student policy** if you want to deploy with limited observations.
9. **Deploy with safety constraints in hardware** - torque limits, software E-stop, watchdogs. Do not trust the policy.

## Further reading

* Lee et al., _"Learning quadrupedal locomotion over challenging terrain"_ - [https://arxiv.org/abs/2010.11251](https://arxiv.org/abs/2010.11251)
* Margolis & Agrawal, _"Walk These Ways: Tuning Robot Control for Generalization with Multiplicity of Behavior"_ - [https://arxiv.org/abs/2212.03238](https://arxiv.org/abs/2212.03238)
* Kumar et al., _"RMA: Rapid Motor Adaptation for Legged Robots"_ - [https://arxiv.org/abs/2107.04034](https://arxiv.org/abs/2107.04034)
* Ma et al., _"Eureka: Human-Level Reward Design via Coding Large Language Models"_ - [https://arxiv.org/abs/2310.12931](https://arxiv.org/abs/2310.12931)
* Luo et al., _"SERL: A Software Suite for Sample-Efficient Robotic Reinforcement Learning"_ - [https://serl-robot.github.io/](https://serl-robot.github.io/)
* Schulman et al., _"Proximal Policy Optimization Algorithms"_ (PPO original) - [https://arxiv.org/abs/1707.06347](https://arxiv.org/abs/1707.06347)
