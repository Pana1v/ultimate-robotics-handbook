---
icon: brain
---

# World Models

A *world model* is a learned simulator: a neural network that, given an observation and an action, predicts the next observation. If you have a good world model you can do imagination-based planning, sample-efficient RL, and counterfactual reasoning without ever touching the real environment.

World models have been around since Schmidhuber's RNN-based controllers in the early 90s and the Ha & Schmidhuber 2018 "World Models" paper. What changed in the 2022–2026 period is two things:

1. **Diffusion and transformer-based generative models** scaled to the point where you can predict realistic future *images* given past frames + actions, not just low-dimensional latents.
2. **Video pretraining** at internet scale gives you a strong "world prior" before you even see robot data.

The result: the line between "world model" and "generative video model" has blurred, and the same architectures that power Sora and Veo are showing up as planning components in robotics stacks.

## Why world models matter for robotics

Two main motivations:

### 1. Sample efficiency

If you have a world model, you can roll out imaginary trajectories cheaply on a GPU instead of expensive real (or even simulated) ones. DreamerV3 trains an Atari policy in under 30M environment steps; the equivalent model-free SAC takes 200M+. Same idea scales (in principle) to robot data.

### 2. Planning over learned dynamics

Classical MPC uses analytic dynamics. With a world model you can do MPC over a *learned* model that captures contact, deformables, and other phenomena that analytic models struggle with. This is the basis of recent work like **TD-MPC2** and **DreamerV3**'s planning variants.

### 3. (Bonus) Simulation of the real world

If your world model is good enough, you can train policies *entirely inside it*. This is the Cosmos / Genie 2 / GAIA dream: train a self-driving or robotics policy in a video-generated world that captures real-world distribution shifts you could not put in a hand-built sim.

## The architecture landscape

World models come in flavors. The taxonomy that matters:

| Type | What it predicts | Examples |
|---|---|---|
| **Latent (RSSM-style)** | Compressed latent state | Dreamer V1-V3, PlaNet |
| **Pixel-space autoregressive** | Next frame as patches | GAIA-1, IRIS, Genie |
| **Pixel-space diffusion** | Next frames via diffusion | Cosmos, GAIA-2, DIAMOND |
| **Hybrid (latent diffusion)** | Latents via diffusion | Cosmos-Predict |

Latent models are smaller, faster, harder to interpret. Pixel models are huge, slow, but visually inspectable and benefit directly from video pretraining.

## DreamerV3

Hafner et al., 2023. [https://arxiv.org/abs/2301.04104](https://arxiv.org/abs/2301.04104)

Code: [https://github.com/danijar/dreamerv3](https://github.com/danijar/dreamerv3)

DreamerV3 is the model-based RL benchmark you compare against in 2026. Three components:

1. **Recurrent State-Space Model (RSSM)** - encodes observations into a discrete latent state $$z_t$$ and predicts future latents conditioned on actions: $$p(z_{t+1} \mid z_t, a_t)$$.
2. **Reward / continue heads** - predict reward and episode termination from latent state.
3. **Actor-critic** - trained on imagined rollouts in the latent space.

The big result: a *single* set of hyperparameters works across 150+ tasks (Atari, DMC, MineCraft, etc.) and DreamerV3 hits expert performance with dramatically less environment data than model-free RL.

For robotics specifically, DreamerV3 has been applied to:

- Locomotion (Wu et al. 2022, Daydreamer) - real-world quadruped learns to walk in 1 hour.
- Manipulation in simulation - competitive with PPO at lower sample counts.
- Drone control.

**Where it falls short:**

- The latent state is low-dimensional; high-frequency contact-rich dynamics get blurred.
- Pretraining on world data is awkward - the RSSM is task-specific.
- Visualization / debugging is hard because the latents are not interpretable.

**DayDreamer** (Wu, Escontrela, Hafner, Abbeel, 2022) - applied DreamerV3 to *real* robots (Sphero, UR5, A1 quadruped). [https://arxiv.org/abs/2206.14176](https://arxiv.org/abs/2206.14176) - a quadruped learning to walk from scratch on hardware in ~1 hour. Still the most impressive demonstration of model-based RL on real robots.

## IRIS (Imagination with Retrieval and State)

Micheli et al., ICLR 2023. [https://arxiv.org/abs/2209.00588](https://arxiv.org/abs/2209.00588)

Code: [https://github.com/eloialonso/iris](https://github.com/eloialonso/iris) [verify]

IRIS replaces the latent RSSM with a discrete VQ-VAE tokenizer + autoregressive transformer (think GPT-2 over image tokens). The policy is then trained inside an imagination rolled out by the transformer.

Strong on Atari at very low sample counts (2 hours of game time vs. weeks for SAC/Rainbow). Architecturally important because it bridges latent world models and pixel-space transformers.

## GAIA-1 / GAIA-2 (Wayve)

GAIA-1: [https://arxiv.org/abs/2309.17080](https://arxiv.org/abs/2309.17080)

GAIA-2: [https://wayve.ai/thinking/gaia-2/](https://wayve.ai/thinking/gaia-2/) [verify]

Wayve's autonomous-driving world models. Conditioned on video + actions + text + ego-vehicle state, they generate plausible driving futures. GAIA-2 (2024) added multi-camera, multi-modal conditioning and is used internally for closed-loop policy evaluation - train a policy, evaluate it inside GAIA-2 before putting it on a real car.

**Why it matters for non-driving robotics:** GAIA established the playbook of "pretrain a video model on web-scale driving footage, condition on actions, use as a closed-loop sim." Cosmos and Genie are direct intellectual descendants.

## Cosmos (NVIDIA, 2025)

[https://www.nvidia.com/en-us/ai/cosmos/](https://www.nvidia.com/en-us/ai/cosmos/) [verify]

Paper: [https://arxiv.org/abs/2501.03575](https://arxiv.org/abs/2501.03575) [verify]

NVIDIA's bid for a *world foundation model for robotics*. Released early 2025. Architecturally similar to Sora-style diffusion video models, but trained on ~20 million hours of physical-world video curated to emphasize manipulation, locomotion, and embodied scenes.

Variants:

- **Cosmos-Predict** - generative model, predicts future video given past video + action / camera trajectory.
- **Cosmos-Transfer** - controllable generation (lighting, weather, object placement) for synthetic data.
- **Cosmos-Reason** - multimodal LLM for reasoning over Cosmos-generated scenes.

Stated use cases:

- Generating synthetic training data for VLAs and perception models.
- Closed-loop evaluation of robot policies.
- Pretraining encoders for downstream robot tasks.

{% hint style="info" %}
**Field note.** Cosmos is the most ambitious world model release in robotics to date and worth following. As of early 2026 my honest read is: the *generated videos* are impressive, the *measured downstream gains* on real robot policies are less established than the marketing implies. NVIDIA released the weights and the toolchain (Cosmos-Tokenizer in particular is genuinely useful as a standalone encoder), but "Cosmos as your training sim" is not yet a turn-key thing. Watch the next 12 months.
{% endhint %}

## Genie 1 / Genie 2 (DeepMind)

Genie 2 [https://deepmind.google/discover/blog/genie-2-a-large-scale-foundation-world-model/](https://deepmind.google/discover/blog/genie-2-a-large-scale-foundation-world-model/) [verify]

DeepMind's foundation world model. The key trick: trained *unsupervised* on internet video, learns latent action representations *automatically* (no need for ground-truth actions in the training data). You can then prompt it with an image and a (learned) action to generate plausible futures.

For robotics this is less directly useful than Cosmos (Genie's actions are abstract, not robot actions), but Genie 2's emergent capabilities (object permanence, physics, multi-step interactions) hint at what video-only pretraining can give you.

## Diffusion world models for RL

**DIAMOND** - Alonso et al., NeurIPS 2024. [https://arxiv.org/abs/2405.12399](https://arxiv.org/abs/2405.12399) [verify] - trains an Atari policy entirely inside a diffusion world model. The model generates the game frames; the policy plays the game it imagines. State of the art on Atari 100k at the time.

This is conceptually significant: if a 100M-param diffusion model can simulate Atari well enough to train a policy, what does a 100B-param model trained on robot video give us?

## TD-MPC2

Hansen, Su, Wang, 2024. [https://arxiv.org/abs/2310.16828](https://arxiv.org/abs/2310.16828)

Code: [https://github.com/nicklashansen/tdmpc2](https://github.com/nicklashansen/tdmpc2)

A specific kind of world model + planner combo that has held up well in 2024–2026. Learns a latent dynamics model + a value function, then does *MPC in the latent space* at decision time. Combines the planning-time guarantees of MPC with the learned representations of model-based RL.

For continuous control benchmarks (DMControl, MetaWorld) TD-MPC2 is one of the strongest model-based baselines. The single set of hyperparameters across 80+ tasks is a Dreamer-style win.

## When to actually use a world model (2026)

Be honest with yourself. World models are oversold in research and undershipped in production. Cases where they genuinely earn their keep:

| Use case | Worth it? | Notes |
|---|---|---|
| Sample-efficient sim RL | Maybe | DreamerV3 helps if your sim is slow. With Isaac Lab, model-free PPO is fast enough that the world model rarely wins on wall-clock. |
| Sample-efficient *real* RL | Yes | DayDreamer-style. Especially for legged real-world RL. |
| Closed-loop policy eval | Yes if you have one | Cosmos / GAIA-2 style. Beats running on the real robot for every iteration. |
| Synthetic data generation | Maybe | Quality is improving, but real demos are still better per-dollar. |
| Replacing your simulator entirely | Not yet | The "Cosmos as your training environment" pitch is not yet operational for most teams. |
| Mental model / counterfactuals during planning | Yes if you can afford the latency | TD-MPC2 style - model-based MPC at decision time. |

## Practical recipes

### DreamerV3 for a real robot task

1. Use the official DreamerV3 repo: [https://github.com/danijar/dreamerv3](https://github.com/danijar/dreamerv3).
2. Wrap your robot as a Gym(nasium)-compatible env.
3. Use the default hyperparams. Do not tune them. The whole point is that they generalize.
4. Run for 1-2M environment steps. Expect 1-3 hours of real robot time for simple manipulation, longer for locomotion.
5. Compare against your model-free baseline. If Dreamer is not winning by 2-3x sample efficiency, something is wrong.

### TD-MPC2 for a manipulation task

1. Repo: [https://github.com/nicklashansen/tdmpc2](https://github.com/nicklashansen/tdmpc2).
2. Same Gymnasium wrapper.
3. Default hyperparams again.
4. Run for ~500k steps in sim.
5. Deploy with MPC planning at execution time; you can vary the horizon based on compute budget.

### Cosmos for synthetic data (early 2026)

1. Get the Cosmos weights from NVIDIA (Cosmos-Predict-7B or 14B variants).
2. Use the Cosmos-Transfer pipeline to render scene variations.
3. Use generated videos to augment your real demo set for VLA fine-tuning.
4. Measure downstream task success - do not trust visual fidelity as a proxy.

## Limitations of world models in 2026

- **Contact dynamics.** Generative video models still hallucinate when fingers grip surfaces or objects collide. The "physics-y" details are exactly where you would most want a world model and exactly where they are weakest.
- **Long-horizon coherence.** Most models drift after ~5 seconds of generation. Long-horizon planning needs hierarchical structure.
- **Action conditioning fidelity.** Models trained on "video-only" or weakly-conditioned data do not respond strongly to action inputs.
- **Compute.** Cosmos-Predict-14B inference is GPU-hours per minute of video. Not deployable on-robot.
- **Eval.** "Did the world model predict the right next frame?" is not the right metric. "Did training a policy in this world model produce a policy that works in reality?" is the metric, and it is brutally expensive.

## Further reading

- Ha & Schmidhuber, *"World Models"* - [https://arxiv.org/abs/1803.10122](https://arxiv.org/abs/1803.10122) (the modern starting point)
- Hafner et al., *"Mastering Diverse Domains through World Models"* (DreamerV3) - [https://arxiv.org/abs/2301.04104](https://arxiv.org/abs/2301.04104)
- Wu et al., *"DayDreamer: World Models for Physical Robot Learning"* - [https://arxiv.org/abs/2206.14176](https://arxiv.org/abs/2206.14176)
- NVIDIA, *"Cosmos World Foundation Model Platform"* - [https://arxiv.org/abs/2501.03575](https://arxiv.org/abs/2501.03575) [verify]
- Hansen, Wang, Su, *"TD-MPC2: Scalable, Robust World Models for Continuous Control"* - [https://arxiv.org/abs/2310.16828](https://arxiv.org/abs/2310.16828)
- Bruce et al., *"Genie: Generative Interactive Environments"* - [https://arxiv.org/abs/2402.15391](https://arxiv.org/abs/2402.15391)
