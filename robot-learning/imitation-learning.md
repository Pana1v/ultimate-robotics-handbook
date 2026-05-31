---
icon: brain
---

# Imitation Learning

Imitation learning (IL) is the most practical way to make a robot do a real task in 2026. If you have a teleop rig, a few hundred demonstrations, and a GPU, you can ship something useful in a week. The math is not deep - the engineering is in the data.

## The setup

You have demonstrations: a dataset of (observation, action) pairs collected from an expert. Usually the expert is a human teleoperating the robot. You want a policy $$\pi_\theta(a \mid o)$$ that imitates the expert.

In its simplest form this is supervised learning. The observation $$o$$ is your input, the action $$a$$ is your target, you minimize some loss. That is **Behavior Cloning** (BC), and it has been around since the 90s (ALVINN, NVIDIA's end-to-end driving paper, etc.). Everything modern is a variation on this theme that handles the failure modes BC has.

## Behavior Cloning (BC)

The vanilla recipe:

$$
\mathcal{L}_\text{BC}(\theta) = \mathbb{E}_{(o, a) \sim \mathcal{D}} \left[ \| \pi_\theta(o) - a \|^2 \right]
$$

Minimize MSE between your policy's predicted action and the expert action. Done.

**Where BC actually works:**

- Short-horizon tasks (<5 seconds, <100 timesteps)
- Tasks where the state distribution at test time matches the demonstrations
- Tasks where small errors do not compound into catastrophic ones

**Where BC catastrophically fails: compounding errors.** This is the central pathology. At training time the policy sees states from expert trajectories. At test time, the first small error puts the policy in a state slightly off the expert distribution. The next action is now slightly worse. After 50 timesteps you are in a state the policy has never seen and it falls over.

Formally: if your one-step error is $$\epsilon$$, your $$T$$-step regret is $$O(T^2 \epsilon)$$, not $$O(T \epsilon)$$. This is the **covariate shift** problem (Ross & Bagnell, 2010): [https://arxiv.org/abs/1011.0686](https://arxiv.org/abs/1011.0686)

## DAgger (Dataset Aggregation)

Ross, Gordon & Bagnell, AISTATS 2011. The simplest fix to BC's compounding errors.

The idea: roll out your current policy, get into the weird off-distribution states, ask the expert what they would do there, add those (state, expert action) pairs to your dataset, retrain. Repeat.

```
1. Train π_0 on expert demos D_0
2. For i = 1...N:
     a. Roll out π_{i-1} in the environment, collect visited states S_i
     b. Query expert for actions on S_i, get (S_i, expert(S_i))
     c. D_i = D_{i-1} ∪ (S_i, expert(S_i))
     d. Train π_i on D_i
```

**Where DAgger works in practice:** simulation, where querying the expert is cheap. Almost never on real robots because you cannot pause a robot mid-failure and ask the human "what would you have done here?" - by the time the human responds the moment is gone.

{% hint style="info" %}
**Field note.** DAgger is conceptually the right idea but operationally a nightmare on real hardware. The 2024-era successor is **HG-DAgger** and **HIL-SERL** style approaches where the human intervenes in real-time during policy rollouts. We cover those on the [Modern RL](reinforcement-learning-modern.md) page.
{% endhint %}

## Action Chunking Transformer (ACT)

Zhao et al., 2023. The ALOHA paper. [https://arxiv.org/abs/2304.13705](https://arxiv.org/abs/2304.13705)

ACT is what made low-cost bimanual manipulation actually work. Two key ideas:

1. **Action chunking.** Predict $$k$$ future actions at once (typically $$k=100$$, ~1 second at 100Hz) instead of one. This compresses the effective horizon by a factor of $$k$$, which directly reduces compounding error.
2. **Temporal ensembling.** At each timestep, ensemble overlapping predictions from previous chunks. This smooths the action stream and reduces jitter.

Architecturally: a CVAE-style encoder produces a latent $$z$$ from the demonstration's action sequence (used only at training), a transformer decoder predicts $$k$$ actions conditioned on multiple camera views + proprioception + $$z$$. At inference $$z = 0$$.

```python
# Pseudocode for ACT inference loop
for t in range(T):
    if t % chunk_size == 0:
        action_chunk = policy(obs_t)  # predicts k actions
    # Temporal ensemble: weighted avg of overlapping chunk predictions
    action_t = ensemble(action_chunks_covering_t)
    execute(action_t)
```

**Why it works:** action chunking is doing two things - reducing the effective horizon (so error compounds less) and making the policy commit to a multi-step plan (so it does not stutter on contact-rich subtasks).

**Practical pointers:**

- Original code: [https://github.com/tonyzhaozh/act](https://github.com/tonyzhaozh/act)
- LeRobot has a maintained, clean ACT implementation: [https://github.com/huggingface/lerobot](https://github.com/huggingface/lerobot)
- Works great on ALOHA, SO-100, SO-101, Koch, GELLO setups
- ~50–200 demos is enough for simple tasks, ~500–1000 for harder ones
- Trains in a few hours on a single 4090

## Diffusion Policy

Chi et al., RSS 2023. [https://arxiv.org/abs/2303.04137](https://arxiv.org/abs/2303.04137)

Project page: [https://diffusion-policy.cs.columbia.edu/](https://diffusion-policy.cs.columbia.edu/)

The other 2023 paper that changed the field. Same problem (BC + manipulation), different solution.

**Core idea:** instead of regressing to the expert's action directly, model the action distribution with a diffusion model. The policy is a denoising network that, conditioned on observations, samples from the posterior $$p(a \mid o)$$.

Why this beats BC:

1. **Multimodal actions.** If the human demonstrator sometimes goes around an obstacle on the left and sometimes on the right, MSE BC will regress to the mean and try to go *through* the obstacle. A diffusion model captures both modes.
2. **Action sequence modeling.** Like ACT, predicts a chunk of future actions, not a single step.
3. **High-dimensional action spaces handled gracefully.** Important for bimanual or dexterous setups.

**The math, briefly.** Train a network $$\epsilon_\theta(a^k, o, k)$$ to predict the noise added at diffusion step $$k$$ to a clean action sequence $$a^0$$. At inference, start from Gaussian noise $$a^K$$ and iteratively denoise:

$$
a^{k-1} = \alpha_k \big( a^k - \gamma_k \epsilon_\theta(a^k, o, k) \big) + \sigma_k z
$$

Use DDIM or DDPM scheduler. 10-100 denoising steps per action chunk. The slow inference is the only real downside.

**Diffusion Policy vs ACT in practice (my opinion):**

| Aspect | ACT | Diffusion Policy |
|---|---|---|
| Inference latency | ~5 ms (single forward pass) | ~50–200 ms (denoising loop) |
| Handles multimodal demos | Poorly (CVAE helps a bit) | Yes, this is the point |
| Sample efficiency | Higher | Slightly lower |
| Implementation complexity | Medium | Medium-high |
| Best for | Short-horizon, low-latency, single-mode behaviors | Long-horizon, multi-modal, contact-rich |

{% hint style="info" %}
**Field note.** In production, ACT still wins for short-horizon pick-place at 100Hz because diffusion inference latency is brutal. Diffusion Policy wins anywhere the task is multimodal (e.g., bimanual manipulation where the same goal can be achieved with either hand leading). Most real deployments I have seen in 2025 use ACT or one of its descendants for the low-level controller and reserve diffusion for slower high-level skill selection. New work like consistency-distilled diffusion policies is closing the latency gap.
{% endhint %}

## Recent work (2024-2026)

The field has not stood still. A non-exhaustive list of what is worth knowing:

- **3D Diffusion Policy (DP3)** - Ze et al., RSS 2024. Diffusion Policy with point cloud inputs instead of RGB. Generalizes much better across scenes. [https://3d-diffusion-policy.github.io/](https://3d-diffusion-policy.github.io/)
- **Flow Matching Policies** - used in π0 / π0.5. Replaces the diffusion denoising loop with a single ODE solve. Order of magnitude faster inference at similar quality. The π0 paper: [https://www.physicalintelligence.company/blog/pi0](https://www.physicalintelligence.company/blog/pi0)
- **VQ-BeT / BeT (Behavior Transformer)** - Shafiullah et al., NeurIPS 2022. Discrete action tokens via VQ-VAE + transformer. Handles multimodality cheaply. [https://arxiv.org/abs/2206.11251](https://arxiv.org/abs/2206.11251)
- **HPT (Heterogeneous Pre-trained Transformers)** - Wang et al., NeurIPS 2024. Pretrain on heterogeneous robot data, then fine-tune. [https://liruiw.github.io/hpt/](https://liruiw.github.io/hpt/)
- **RDT-1B** - Robotics Diffusion Transformer. Scaled diffusion policy to 1B params, pretrained on Open X-Embodiment. [https://rdt-robotics.github.io/rdt-robotics/](https://rdt-robotics.github.io/rdt-robotics/)

For language-conditioned IL and full VLAs (RT-1, RT-2, OpenVLA, π0), see [Foundation Models & VLAs](foundation-models-vla.md).

## Data collection - the actual hard part

The math above takes a weekend to understand. Getting good data takes months. This is where most projects fail.

**Demonstration count rule of thumb (2026):**

| Task complexity | Minimum demos | Diminishing returns | Notes |
|---|---|---|---|
| Pick-and-place, fixed object/pose | 50 | 200 | Easy. Both ACT and BC work. |
| Pick-and-place, varied objects | 200 | 1000 | Need visual diversity in demos. |
| Insertion / contact-rich (USB, peg-in-hole) | 100 | 500 | Force feedback in demos helps a lot. |
| Bimanual coordination | 200 | 1500 | This is where ACT shines. |
| Long-horizon (>30s, multiple subtasks) | 500 | 5000+ | Use chunked/hierarchical policies. |
| Mobile manipulation | 500 | 5000+ | Mobile ALOHA-style. Hard. |

**Quality > quantity.** 200 clean demonstrations beat 2000 sloppy ones. A bad demo where the human collided, recovered, and finished is worse than nothing - the policy will learn the collision-and-recover habit.

**Diversity matters more than count.** Vary object positions, lighting, distractors, starting poses. 200 diverse demos > 1000 from the same starting state.

**Demo-to-task-time ratio.** Rough heuristic: budget 100x the task duration in data collection time. A 10-second task needs ~1000 seconds of demos to do well, which after the overhead of setup and resets is ~3-5 hours of human teleop.

For the teleop hardware side, see [Teleoperation & Data Collection](teleop-and-data.md).

## Code & libraries to start with

| Library | What it gives you | When to use it |
|---|---|---|
| **LeRobot** (HuggingFace) - [https://github.com/huggingface/lerobot](https://github.com/huggingface/lerobot) | ACT, Diffusion Policy, VQ-BeT implementations, datasets, training scripts | First stop. Best maintained IL codebase as of 2026. |
| **Diffusion Policy** (Columbia) - [https://github.com/real-stanford/diffusion_policy](https://github.com/real-stanford/diffusion_policy) | Reference impl, faithful to paper | If you want to dig into the original. |
| **ACT** (Stanford) - [https://github.com/tonyzhaozh/act](https://github.com/tonyzhaozh/act) | Reference ACT + ALOHA stack | If running on ALOHA hardware specifically. |
| **Robomimic** (Stanford) - [https://robomimic.github.io/](https://robomimic.github.io/) | BC, BC-RNN, hierarchical IL, benchmarks | Older but well-engineered. Good for ablations. |
| **OpenPi** - [https://github.com/Physical-Intelligence/openpi](https://github.com/Physical-Intelligence/openpi) | π0 weights and fine-tuning code | For VLA-style flow matching policies. |

## Connection to graph-based policies

For tasks with structured spatial reasoning (e.g., multi-object manipulation, articulated objects), GNN-based imitation policies are an underexplored but powerful direction.

## Common pitfalls

1. **Training on demos that include the human's recovery from mistakes.** The policy will learn to make the mistake. Filter or re-collect.
2. **Using state inputs in sim, expecting it to transfer to images in real.** Train on images from day one if you intend to deploy on a real robot.
3. **Forgetting proprioception.** Vision-only policies are brittle. Concatenate joint positions, velocities, gripper state.
4. **Action space mismatch.** End-effector pose vs. joint position vs. delta poses - each changes the difficulty of the IL problem. Delta end-effector pose with a separate gripper head is the 2026 default for arms.
5. **Camera placement changes between data collection and deployment.** Even 1cm of shift can tank a policy. Use mounted, not handheld, cameras.

## Further reading

- Chi et al., *"Diffusion Policy: Visuomotor Policy Learning via Action Diffusion"* - [https://arxiv.org/abs/2303.04137](https://arxiv.org/abs/2303.04137)
- Zhao et al., *"Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware"* (ACT/ALOHA) - [https://arxiv.org/abs/2304.13705](https://arxiv.org/abs/2304.13705)
- Ross, Gordon & Bagnell, *"A Reduction of Imitation Learning and Structured Prediction to No-Regret Online Learning"* (DAgger) - [https://arxiv.org/abs/1011.0686](https://arxiv.org/abs/1011.0686)
- LeRobot blog post series: [https://huggingface.co/blog/lerobot](https://huggingface.co/blog/lerobot) [verify]
- Pieter Abbeel & Andrew Ng, *"Apprenticeship Learning via Inverse Reinforcement Learning"* (2004) - the classic IRL paper, useful for context on what IL is *not*.
