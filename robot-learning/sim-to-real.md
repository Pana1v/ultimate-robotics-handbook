---
icon: brain
---

# Sim-to-Real Transfer

Training a policy in simulation and deploying it on a real robot is the only way most robot learning happens at scale. The catch: simulators lie. Friction is wrong, latencies are wrong, sensors are wrong, the dynamics are slightly off, and physical contacts are *very* wrong. A policy that gets 100% in sim and 0% on the real robot is the rule, not the exception, for anyone doing this for the first time.

This page covers the techniques that close that gap.

## Why sim-to-real is hard

A non-exhaustive list of things that differ between your sim and your robot:

| Discrepancy | Typical impact |
|---|---|
| Motor torque constants (datasheet vs. real) | Velocity tracking errors of 10-30% |
| Joint backlash, friction, gearbox losses | Trajectory drift, oscillation |
| Sensor noise (IMU bias, encoder quantization) | Localization drift |
| Sensor latency + control latency | Policy oscillation, instability |
| Communication jitter (CAN, EtherCAT) | Inconsistent control frequencies |
| Mass/inertia mismatch | Wrong feedforward, wrong gains |
| Contact dynamics (collision models lie) | Locomotion failures, manipulation slipping |
| Camera calibration (intrinsics, extrinsics, color, exposure) | Vision policies fail entirely |
| Lighting, textures, distractors in the real world | Vision policies fail entirely |
| Wear and tear of the actual robot over time | Policies that worked yesterday fail today |

The strategies below address one or more of these.

## Strategy 1: Domain Randomization (DR)

Tobin et al., 2017. [https://arxiv.org/abs/1703.06907](https://arxiv.org/abs/1703.06907)

Train your policy across a *distribution* of simulated environments instead of a single fixed one. At each rollout, sample:

- Friction coefficients ($$\mu \in [0.5, 1.5] \times$$ nominal)
- Masses ($$m \in [0.8, 1.2] \times$$ nominal)
- Motor strengths ($$\tau_\text{max} \in [0.7, 1.3] \times$$ nominal)
- Latency ($$\Delta t \in [10, 50]$$ ms)
- Sensor noise levels
- (For vision) lighting, textures, camera pose, distractor objects

The policy learns to be robust across this whole distribution. If the real robot's parameters fall *inside* the randomized range, the policy should work.

This is the **single most important trick** in sim-to-real. Get this right and many other discrepancies stop mattering. Get it wrong and nothing else helps.

**Calibration of randomization ranges:**

- Too narrow: policy is brittle to real-world variation.
- Too wide: policy is overly conservative and underperforms (or worse, fails to train).
- Sweet spot: ranges that *contain* the real robot's true parameters plus 20-50% margin.

**Tips:**

- Randomize observations and actions, not just dynamics. Inject noise into proprioception. Add action-space noise.
- Randomize latency. The number one cause of sim-to-real failure on real robots is unmodeled delay.
- For vision, randomize hard: textures, lighting, distractors, camera pose, exposure, color jitter.

## Strategy 2: System Identification (SysID)

The complement to DR. Instead of randomizing blindly, *measure* your robot's parameters and match the simulator to them.

Typical SysID pipeline:

1. Apply known inputs to the robot (excitation trajectories, swept frequency, step inputs).
2. Measure the response.
3. Fit simulator parameters to minimize the discrepancy.

What you usually want to identify:

- Link masses, inertias, COM offsets
- Joint friction (Coulomb + viscous)
- Motor constants ($$K_t$$, gear ratio, peak torque)
- Latency (control + sensor)
- Backlash (per joint)

In 2026 you mostly want SysID *plus* DR - identify the nominal parameters and then randomize around them.

**Tools:**

- **MuJoCo's `mj_inverse`** + scipy optimizers for offline SysID.
- **Isaac Lab** has SysID utilities for actuator models.
- **Drake** has rich tooling for inertia identification.

## Strategy 3: Dynamics Randomization

A specific form of DR aimed at the *dynamics* of the system, popularized by:

OpenAI, *"Learning Dexterous In-Hand Manipulation"* (2018, the Rubik's Cube paper). [https://arxiv.org/abs/1808.00177](https://arxiv.org/abs/1808.00177)

OpenAI Rubik's Cube extension: [https://arxiv.org/abs/1910.07113](https://arxiv.org/abs/1910.07113)

They randomized a giant list of parameters (object mass, friction, hand dynamics, latency, vision parameters) and trained a recurrent policy that could *implicitly identify* the current environment from its history. At test time on a real hand, the policy did online identification and adapted.

This is the conceptual basis for the **history-based policy** trick used in legged locomotion. Stack 5-50 past observations as input, give the policy enough capacity (recurrent or transformer), and it will learn to estimate environment parameters from observation history.

## Strategy 4: Real-to-Sim (data-driven simulators)

Instead of trying to handcraft a simulator that matches reality, *learn the simulator* from real-world data.

Approaches:

- **Differentiable physics + parameter fitting.** Use a differentiable simulator (Brax, MuJoCo MJX, Genesis), backprop through rollouts to fit parameters to real trajectories.
- **Learned residual dynamics.** Run an analytic sim, learn a neural net that corrects the sim → real residual.
- **Full neural simulators.** Train a network to predict next state from current state + action, trained on real data. (This is "world models" - see [World Models](world-models.md).)

The 2024-2026 trend is **hybrid**: analytic physics for the broad strokes (Coriolis terms, kinematics) + learned corrections for the parts physics gets wrong (contact, deformables, friction).

## Strategy 5: Privileged Learning

The student-teacher pipeline from [Modern RL](reinforcement-learning-modern.md). The teacher in sim sees privileged information; the student is distilled to use only real-robot-available observations. This isolates the "hard RL" problem from the "limited observability" problem.

Combined with DR + history-based policies, this is the legged-locomotion sim-to-real recipe that has worked for ANYmal, Spot, Unitree, and most humanoids in 2026.

## The "Reality Gap" diagnostic

When your policy works in sim and fails on real, do these *in order*. Most teams skip steps and waste weeks.

1. **Does the sim policy work with the same observations/action timing the real robot will have?** If your sim runs at 1000Hz and your real robot at 100Hz, the policies will be different.
2. **Does the sim policy work with sim-injected noise matching the real robot's noise levels?** Add noise to sim observations matching the real IMU/encoder noise spec.
3. **Does the sim policy work with sim-injected latency matching real?** Critical for any high-rate control loop.
4. **What is the sim → real action discrepancy?** Run the policy in sim, capture the actions. Replay those actions open-loop on the real robot. Where does the trajectory diverge? That gap is your dynamics modeling gap, not your policy gap.
5. **Are your sensors calibrated?** Re-zero IMU. Re-calibrate cameras. Sanity-check encoder offsets.
6. **Is your URDF/MJCF actually matching the robot?** I have lost weeks to wrong inertia tensors.

{% hint style="info" %}
**Field note.** Open-loop replay is the underrated diagnostic. If you record actions from a sim rollout and replay them on the real robot, you isolate the *dynamics* gap from the *policy* gap. If the open-loop trajectory diverges immediately, your simulator is wrong. If it tracks well and only diverges after several seconds, your policy might just need better feedback. Different problems, different fixes.
{% endhint %}

## The simulators (2026 landscape)

| Sim | What it's for | GPU-parallel? | Differentiable? | Notes |
|---|---|---|---|---|
| **Isaac Lab** (NVIDIA) - [https://github.com/isaac-sim/IsaacLab](https://github.com/isaac-sim/IsaacLab) | RL, locomotion, manipulation | Yes (PhysX-GPU) | No | Replaced Isaac Gym (2024). Current default for RL. |
| **MuJoCo MJX** - [https://github.com/google-deepmind/mujoco](https://github.com/google-deepmind/mujoco) | RL, manipulation, MPC | Yes (JAX) | Yes | DeepMind's GPU MuJoCo. Excellent for fast iteration. |
| **MuJoCo (classic)** - same repo | MPC, controls research | No | Limited | Still the gold standard for contact dynamics. |
| **Genesis** - [https://github.com/Genesis-Embodied-AI/genesis-world](https://github.com/Genesis-Embodied-AI/genesis-world) | RL, diff physics | Yes | Yes | New (late 2024). Claims 80x speedup over Isaac Gym. Worth evaluating. |
| **Brax** - [https://github.com/google/brax](https://github.com/google/brax) | RL, differentiable physics | Yes (JAX) | Yes | Older, well-tested. |
| **Drake** - [https://drake.mit.edu/](https://drake.mit.edu/) | Trajectory opt, MPC, planning | No | Yes | High-fidelity multibody. The "controls people" simulator. |
| **Gazebo / Ignition** - [https://gazebosim.org/](https://gazebosim.org/) | Multi-robot, ROS integration | No | No | Standard for system integration testing. Slow for RL. |
| **Webots** - [https://cyberbotics.com/](https://cyberbotics.com/) | Education, classical robotics | No | No | Lightweight, easy to use. |
| **PyBullet** - [https://pybullet.org/](https://pybullet.org/) | Manipulation, learning | No (CPU) | Partial | Old default for IL/RL research. Still used. |
| **Isaac Sim** (NVIDIA) - [https://developer.nvidia.com/isaac-sim](https://developer.nvidia.com/isaac-sim) | High-fidelity, USD-based scenes | GPU rendering | No | The "visuals" sibling of Isaac Lab. Use for synthetic data. |
| **NVIDIA Cosmos** - see [World Models](world-models.md) | Synthetic video, eval | GPU | No | Generative, not physics-based. |

### Isaac Gym → Isaac Lab

If you read anything written before 2024 about NVIDIA's RL stack, it probably says "Isaac Gym." Isaac Gym is deprecated. Use **Isaac Lab** instead. It is built on Isaac Sim, supports more rigorous physics, integrates with USD, and is what NVIDIA actively maintains.

Migration is mostly straightforward - most reward functions and environment configs port over with minor changes.

### MuJoCo and MJX

MuJoCo is the gold standard for contact-rich rigid-body dynamics. Always has been, still is. The contact solver is more robust than PhysX in many regimes.

**MJX** is the JAX-based, GPU-parallelizable, differentiable version. It is fast enough that you can train manipulation policies on a single GPU with hundreds of parallel environments. For pure manipulation RL in 2026, MJX is a strong default. For locomotion with complex terrain, Isaac Lab tends to be easier.

### Genesis (CMU + collaborators, late 2024)

Genesis claims dramatic speedups over Isaac Gym for RL (80x in published benchmarks). It is differentiable, GPU-parallel, supports rigid + soft body + fluids in one framework. Too new to have a confident "is it production-ready" verdict (early 2026), but worth evaluating for new projects.

[https://github.com/Genesis-Embodied-AI/genesis-world](https://github.com/Genesis-Embodied-AI/genesis-world)

## Case studies - what actually worked

### ANYmal (ETH RSL)

The reference sim-to-real success story for legged robots. Lee et al. 2020 trained ANYmal entirely in Isaac Gym (now Isaac Lab) with:

- Domain randomization on friction, masses, motor params, latency
- Privileged-info teacher policy
- Student policy distilled to use only history-based proprioception
- Sim-trained policy deployed *zero-shot* on real hardware
- Robust to terrain not seen in training

Total robot data used for training: zero. The whole pipeline is sim.

### OpenAI Rubik's Cube (2019)

The poster child for dynamics randomization. Trained a Shadow hand to solve a Rubik's cube in sim with extensive parameter randomization (object size, friction, hand calibration, latency). Deployed on real hardware with non-trivial success.

In retrospect, the policy was less robust than the demos implied, and the approach has been superseded by more targeted DR + IL hybrids. But it was the first big sim-to-real-from-pure-RL success and established many of the techniques still used in 2026.

[https://arxiv.org/abs/1910.07113](https://arxiv.org/abs/1910.07113)

### Vision sim-to-real (general)

The most reliable trick for visual sim-to-real in 2026: **don't trust your renderer**. Either:

- Train on depth/segmentation/point clouds (more transferable than RGB), or
- Use heavy domain randomization on textures, lighting, distractors, or
- Use a pretrained visual encoder (DINOv2, CLIP, SigLIP) and only learn the policy head. Encoders trained on internet data transfer well.

The "render photorealistic sim, hope it generalizes" approach generally underperforms one of the above three.

## A starter recipe for a new robot

If you are bringing up sim-to-real on a new platform for the first time:

1. **Get the URDF right.** Validate masses, inertias, joint limits against the CAD. Walk through every link.
2. **Identify nominal motor / actuator parameters.** Calibrate $$K_t$$, gear ratios, max torque from real data.
3. **Identify control + sensor latency.** Step inputs, measure delay. Bake into sim.
4. **Build the simplest possible task** (stand still, hold position) and verify sim and real agree.
5. **Add domain randomization** around the identified nominal parameters. Start with ±20%.
6. **Train your policy with history-based observations** so it can adapt.
7. **Open-loop replay sim policy actions on real** as a diagnostic.
8. **Deploy with safety constraints in hardware** - torque limits, software E-stop.
9. **Iterate.** Real-world failures tell you what to randomize next.

## Common failure modes

- **"My policy oscillates on real but not in sim."** → Latency mismatch. Add 20-50ms control latency to sim and retrain.
- **"My policy stalls / refuses to move on real."** → Probably motor saturation. Real motors hit limits sim did not. Add torque randomization.
- **"My vision policy works in sim, fails on real."** → Render gap. Domain randomize harder, or switch to depth/segmentation, or use pretrained encoders.
- **"My policy works on day 1 of a new robot, fails on day 30."** → Hardware degradation. Retrain with wider DR.
- **"Sim policy is conservative on real, leaves performance on the table."** → DR ranges were too wide. Narrow them via SysID and retrain.

## Further reading

- Tobin et al., *"Domain Randomization for Transferring Deep Neural Networks from Simulation to the Real World"* - [https://arxiv.org/abs/1703.06907](https://arxiv.org/abs/1703.06907)
- OpenAI et al., *"Solving Rubik's Cube with a Robot Hand"* - [https://arxiv.org/abs/1910.07113](https://arxiv.org/abs/1910.07113)
- Peng et al., *"Sim-to-Real Transfer of Robotic Control with Dynamics Randomization"* - [https://arxiv.org/abs/1710.06537](https://arxiv.org/abs/1710.06537)
- Lee et al., *"Learning quadrupedal locomotion over challenging terrain"* - [https://arxiv.org/abs/2010.11251](https://arxiv.org/abs/2010.11251)
- Isaac Lab documentation - [https://isaac-sim.github.io/IsaacLab/](https://isaac-sim.github.io/IsaacLab/)
- *"Sim-to-Real in Robotics: A Survey"* - Zhao, Queralta, Westerlund. [https://arxiv.org/abs/2009.13303](https://arxiv.org/abs/2009.13303)
