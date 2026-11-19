---
icon: brain
---

# World Models

A *world model* is a learned simulator: a neural network that, given an observation and an action, predicts the next observation. If you have a good world model you can do imagination-based planning, sample-efficient RL, and counterfactual reasoning without ever touching the real environment.

World models have been around since Schmidhuber's RNN-based controllers in the early 90s and the Ha & Schmidhuber 2018 "World Models" paper. What changed in the 2022-2026 period is two things:

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

Code: [https://github.com/eloialonso/iris](https://github.com/eloialonso/iris)

IRIS replaces the latent RSSM with a discrete VQ-VAE tokenizer + autoregressive transformer (think GPT-2 over image tokens). The policy is then trained inside an imagination rolled out by the transformer.

Strong on Atari at very low sample counts (2 hours of game time vs. weeks for SAC/Rainbow). Architecturally important because it bridges latent world models and pixel-space transformers.

## GAIA-1 / GAIA-2 (Wayve)

GAIA-1: [https://arxiv.org/abs/2309.17080](https://arxiv.org/abs/2309.17080)

GAIA-2: [https://wayve.ai/thinking/gaia-2/](https://wayve.ai/thinking/gaia-2/)

Wayve's autonomous-driving world models. Conditioned on video + actions + text + ego-vehicle state, they generate plausible driving futures. GAIA-2 (2024) added multi-camera, multi-modal conditioning and is used internally for closed-loop policy evaluation - train a policy, evaluate it inside GAIA-2 before putting it on a real car.

**Why it matters for non-driving robotics:** GAIA established the playbook of "pretrain a video model on web-scale driving footage, condition on actions, use as a closed-loop sim." Cosmos and Genie are direct intellectual descendants.

## Cosmos (NVIDIA, 2025)

[https://www.nvidia.com/en-us/ai/cosmos/](https://www.nvidia.com/en-us/ai/cosmos/)

Paper: [https://arxiv.org/abs/2501.03575](https://arxiv.org/abs/2501.03575)

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

Genie 2 [https://deepmind.google/discover/blog/genie-2-a-large-scale-foundation-world-model/](https://deepmind.google/discover/blog/genie-2-a-large-scale-foundation-world-model/)

DeepMind's foundation world model. The key trick: trained *unsupervised* on internet video, learns latent action representations *automatically* (no need for ground-truth actions in the training data). You can then prompt it with an image and a (learned) action to generate plausible futures.

For robotics this is less directly useful than Cosmos (Genie's actions are abstract, not robot actions), but Genie 2's emergent capabilities (object permanence, physics, multi-step interactions) hint at what video-only pretraining can give you.

## Diffusion world models for RL

**DIAMOND** - Alonso et al., NeurIPS 2024. [https://arxiv.org/abs/2405.12399](https://arxiv.org/abs/2405.12399) - trains an Atari policy entirely inside a diffusion world model. The model generates the game frames; the policy plays the game it imagines. State of the art on Atari 100k at the time.

This is conceptually significant: if a 100M-param diffusion model can simulate Atari well enough to train a policy, what does a 100B-param model trained on robot video give us?

## TD-MPC2

Hansen, Su, Wang, 2024. [https://arxiv.org/abs/2310.16828](https://arxiv.org/abs/2310.16828)

Code: [https://github.com/nicklashansen/tdmpc2](https://github.com/nicklashansen/tdmpc2)

A specific kind of world model + planner combo that has held up well in 2024-2026. Learns a latent dynamics model + a value function, then does *MPC in the latent space* at decision time. Combines the planning-time guarantees of MPC with the learned representations of model-based RL.

For continuous control benchmarks (DMControl, MetaWorld) TD-MPC2 is one of the strongest model-based baselines. The single set of hyperparameters across 80+ tasks is a Dreamer-style win.

## New world models, 2025–2026

The 2022–2024 wave (DreamerV3, IRIS, GAIA, Cosmos, Genie, DIAMOND, TD-MPC2) established that generative video models could serve as robot simulators and planners. The 2025–2026 wave goes further: models that plan in latent space without pixel reconstruction, video diffusion models repurposed as closed-loop action-conditioned simulators, cross-view 3D consistency, world foundation models spanning many robot bodies, and the first real-robot deployments of world-model-based policies. Quantified figures below come from arXiv abstracts, project pages, and third-party summaries; where a full paper was not opened, the figure is flagged.

### New architectures and paradigms

**V-JEPA 2-AC** (Assran et al., Meta FAIR, June 2025, [arXiv:2506.09985](https://arxiv.org/abs/2506.09985)). Post-trains frozen V-JEPA 2 video encoders with a small action-conditioned predictor on ~62 hours of DROID robot video to do latent-space future-frame prediction, enabling zero-shot MPC-style planning on Franka arms at ~16 seconds per action (vs ~4 minutes for a Cosmos diffusion baseline). Real-robot: yes — zero-shot manipulation on Franka arms without per-environment data collection or task-specific training.

**DINO-WM** (Zhou, Pan, LeCun, Pinto, v2 Feb 2025, [arXiv:2411.04983](https://arxiv.org/abs/2411.04983)). Learns visual dynamics without pixel reconstruction by using frozen DINOv2 patch features as latent state and a causal-attention ViT to predict future features from offline trajectories, then optimizes action sequences against a goal image at test time. Real-robot: no — simulation across mazes, PushT, Rope, and Granular scenes; strongest gains on PushT, Rope, Granular.

**DUET-DINO** (Nilavadi et al., Sep 2026, [arXiv:2609.10506](https://arxiv.org/abs/2609.10506)). Trains side- and wrist-camera action-conditioned predictors jointly with cross-attention for goal-conditioned 7-DoF planning on DROID and RoboArena trajectories. Real-robot: not reported / unconfirmed.

**VQ-WM** (Xu et al., Oct 2026, [arXiv:2610.25600](https://arxiv.org/abs/2610.25600)). Plans with shortest-path search over vector-quantized latent states using a controller-aware state codebook, then tracks each planned state with a learned continuous controller from visual feedback at a different rate, limiting compounding error. Real-robot: not reported.

### Generative video world models for robotics

**Ctrl-World** (Guo, Shi, Chen, Finn, Oct 2025, [arXiv:2510.10125](https://arxiv.org/pdf/2510.10125)). Fine-tunes a pretrained video diffusion model on DROID to predict multiple camera views jointly and evaluates VLA policies entirely "in imagination," including an interactive keyboard-driven mode. Real-robot: no — ranks policies without physical rollouts.

**GeniWorld** (Gu et al., Aug 2026, [arXiv:2608.06332](https://arxiv.org/abs/2608.06332)). Renders actions as visual representations so a policy or human operator drives an autoregressive Wan2.2 backbone in closed loop; claims robust transfer from fixed-scene demos to unseen scenes. Real-robot: not reported.

**PAIWorld** (Huang et al., Jun 2026, [arXiv:2606.18375](https://arxiv.org/abs/2606.18375)). 3D-consistent multi-view world foundation model with Geometry-Aware Cross-View Attention, Geo-RoPE, and Latent 3D-REPA on a Wan2.1 backbone pretrained on 2.5M multi-view clips. Real-robot: benchmark-only (1st WorldArena, 2nd AgiBot-Challenge2026); real deployment unconfirmed.

**DreamTrue** (Li et al., Oct 2026, [arXiv:2610.12468](https://arxiv.org/abs/2610.12468)). Edits recorded trajectories into actions that may fail, generates the resulting future videos across views and embodiments, and trains with embodied video rewards. Real-robot: challenge-track only (1st, AgiBot World Challenge 2026 world-model track); hardware status unconfirmed.

**PhysGen** (Song et al., Mar 2026, [arXiv:2603.00110](https://arxiv.org/abs/2603.00110)). Uses a pretrained video generator (NOVA backbone) as a stand-in physics simulator; each step yields both a robot action and a predicted video frame. Real-robot: partial — reported real-world Franka tasks at 75% success (per third-party summary).

**PhysWorld** variants: "Robot Learning from a Physical World Model" (Mao et al., Nov 2025, [arXiv:2511.07416](https://arxiv.org/abs/2511.07416)) — zero-shot manipulation transfer via a reconstructed physical world model; real-robot: yes. "PhysWorld: From Real Videos to World Models of Deformable Objects" (Yang et al., Oct 2025, [arXiv:2510.21447](https://arxiv.org/abs/2510.21447)) — real-robot: unclear. "ABot-PhysWorld" (Chen et al., Mar 2026, [arXiv:2603.23376](https://arxiv.org/abs/2603.23376)) — 14B DiT with physics-aware DPO on ~3M robot clips; real-robot: unclear.

### World models with measured real-robot deployment

**GreenWAM** (Sidorov et al., Oct 2026, [arXiv:2610.18774](https://arxiv.org/abs/2610.18774)). A single network (from Cosmos 3 Edge) acts as both world model and policy across 20 robot bodies via a 79-slot shared anatomical action space. Real-robot: yes — beats π0.5- and Cosmos 3 Edge-adapted baselines on a real humanoid; distilled controller runs at 28.3 Hz.

**GRAIL** (Xie et al., NVIDIA, Jun 2026, [arXiv:2606.05160](https://arxiv.org/abs/2606.05160)). Generates humanoid training data from video world models seeded by rendered 3D assets; no physical robot or motion capture needed before deployment. Real-robot: yes — Unitree G1 egocentric visual policies trained only on GRAIL data reached 84% pick-up and 90% stair-climbing.

**Interactive World Simulator** (Wang et al., Mar 2026, [arXiv:2603.08546](https://arxiv.org/abs/2603.08546)). Action-conditioned video world model supporting stable >10-minute rollouts at 15 FPS on a single RTX 4090; policy and simulator drive each other in closed loop. Real-robot: yes (claimed) — simulator performance tracks real hardware; simulator-generated data roughly as useful as real data on rigid/deformable/pile tasks.

**MotionWAM** (Zheng et al., Jun 2026, [arXiv:2606.09215](https://arxiv.org/html/2606.09215v1)). Replaces the VLM backbone of a VLA with a video world model whose denoising features condition the action policy; whole-body motion tokens for locomotion and torso. Real-robot: yes — Unitree G1, nine real-world tasks.

**Flex-π** (Yan et al., Aug 2026, [arXiv:2608.10860](https://arxiv.org/abs/2608.10860)). 6B model outputting future RGB, 3D pointmaps, DINOv3 semantics, and actions from one checkpoint; deployable as VLA, full world-action model, or intermediate points. Real-robot: yes — up to 2–7× gains over baselines on real-world dexterous bimanual manipulation.

### Latent / pixel / hybrid models for robot control

**GPC / Inference-Time Enhancement** (Qi et al., Feb 2025, [arXiv:2502.00622](https://arxiv.org/html/2502.00622)). Freezes a generative policy's weights and improves inference-time execution by sampling action proposals ranked/refined through short look-ahead rollouts in an action-conditioned world model. Real-robot: not reported — speed is the noted limitation (>3 s per decision cycle per a follow-up).

### World foundation models, simulators, and closed-loop evaluation

**GE-Sim 2.0** (Qiu et al., AgiBot, May 2026, [arXiv:2605.27491](https://arxiv.org/abs/2605.27491)). Closed-loop video world simulator: a policy acts inside the simulator, receives generated frames as its next input; trained on thousands of hours of real robot data including failures; a VL world-judge reward scores rollouts frame-by-frame. Real-robot: unclear — no quantitative policy-training results surfaced.

**Benchmarks.** WorldArena (Shang et al., Feb 2026, [arXiv:2602.08971](https://arxiv.org/abs/2602.08971)) — unified benchmark scoring video perception, task functionality, and human evaluation via EWMScore. WorldEval (Li et al., May 2025, [arXiv:2505.19017](https://arxiv.org/abs/2505.19017)) — evaluates real-robot policies inside a world model; correlates with real-world results. dWorldEval (Apr 2026, [arXiv:2604.22152](https://arxiv.org/abs/2604.22152)) — discrete-diffusion world model for policy evaluation on LIBERO, RoboTwin, and real-robot tasks. H2R-Bench (Rong et al., Aug 2026, [arXiv:2608.13049](https://arxiv.org/abs/2608.13049)) — human-to-robot video transfer benchmark. X2Real (Ruan et al., Sep 2026, [arXiv:2609.27449](https://arxiv.org/abs/2609.27449)) — Isaac Lab-Arena-based benchmark predicting real-robot performance from simulated runs (sim/real correlation 0.84). RoboWM-Bench (Apr 2026, [arXiv:2604.19092](https://arxiv.org/pdf/2604.19092)) — evaluates world models by whether actions extracted from generated videos complete tasks.

Quick reference:

| Model/Paper | arXiv | Date | Real-robot? |
|---|---|---|---|
| V-JEPA 2-AC | 2506.09985 | Jun 2025 | Yes (Franka) |
| DINO-WM | 2411.04983 | Feb 2025 | No (sim) |
| DUET-DINO | 2609.10506 | Sep 2026 | Unclear |
| Ctrl-World | 2510.10125 | Oct 2025 | No |
| GeniWorld | 2608.06332 | Aug 2026 | Unclear |
| PAIWorld | 2606.18375 | Jun 2026 | Benchmark only |
| DreamTrue | 2610.12468 | Oct 2026 | Challenge track only |
| PhysGen | 2603.00110 | Mar 2026 | Partial (Franka 75%) |
| PhysWorld (physical world model) | 2511.07416 | Nov 2025 | Yes |
| ABot-PhysWorld | 2603.23376 | Mar 2026 | Unclear |
| GreenWAM | 2610.18774 | Oct 2026 | Yes (humanoid) |
| GRAIL | 2606.05160 | Jun 2026 | Yes (Unitree G1) |
| Interactive World Simulator | 2603.08546 | Mar 2026 | Yes (claimed) |
| GPC / Inference-Time Enhancement | 2502.00622 | Feb 2025 | Not reported |
| VQ-WM | 2610.25600 | Oct 2026 | Not reported |
| MotionWAM | 2606.09215 | Jun 2026 | Yes (Unitree G1) |
| Flex-π | 2608.10860 | Aug 2026 | Yes (bimanual dexterous) |
| GE-Sim 2.0 | 2605.27491 | May 2026 | Unclear |
| WorldArena | 2602.08971 | Feb 2026 | No (benchmark) |
| WorldEval | 2505.19017 | May 2025 | Yes (evaluator) |
| dWorldEval | 2604.22152 | Apr 2026 | Yes (real-robot tasks) |
| H2R-Bench | 2608.13049 | Aug 2026 | No |
| X2Real | 2609.27449 | Sep 2026 | Yes (calibration) |
| RoboWM-Bench | 2604.19092 | Apr 2026 | Unclear |

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
- NVIDIA, *"Cosmos World Foundation Model Platform"* - [https://arxiv.org/abs/2501.03575](https://arxiv.org/abs/2501.03575)
- Hansen, Wang, Su, *"TD-MPC2: Scalable, Robust World Models for Continuous Control"* - [https://arxiv.org/abs/2310.16828](https://arxiv.org/abs/2310.16828)
- Bruce et al., *"Genie: Generative Interactive Environments"* - [https://arxiv.org/abs/2402.15391](https://arxiv.org/abs/2402.15391)
