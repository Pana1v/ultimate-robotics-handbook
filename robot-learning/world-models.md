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

The 2022–2024 wave (DreamerV3, IRIS, GAIA, Cosmos, Genie, DIAMOND, TD-MPC2) established that generative video models could serve as robot simulators and planners. The 2025–2026 wave goes further: models that plan in latent space without pixel reconstruction, video diffusion models repurposed as closed-loop action-conditioned simulators, cross-view 3D consistency, world foundation models spanning many robot bodies, world-action models that fuse world modeling with action output, and the first real-robot deployments of world-model-based policies. Quantified figures below come from arXiv abstracts, project pages, and third-party summaries; where a full paper was not opened, the figure is flagged as "details not surfaced."

### New architectures and paradigms (latent / pixel / hybrid)

**V-JEPA 2-AC** (Assran et al., Meta FAIR, June 2025, [arXiv:2506.09985](https://arxiv.org/abs/2506.09985)). Post-trains frozen V-JEPA 2 video encoders with a small action-conditioned predictor on ~62 hours of DROID robot video to do latent-space future-frame prediction, enabling zero-shot MPC-style planning on Franka arms at ~16 seconds per action (vs ~4 minutes for a Cosmos diffusion baseline). Real-robot: yes — zero-shot manipulation on Franka arms without per-environment data collection or task-specific training; success higher than the Cosmos baseline on every task tested.

**DINO-WM** (Zhou, Pan, LeCun, Pinto, v2 Feb 2025, [arXiv:2411.04983](https://arxiv.org/abs/2411.04983)). Learns visual dynamics without pixel reconstruction by using frozen DINOv2 patch features as latent state and a causal-attention ViT to predict future features from offline trajectories, then optimizes action sequences against a goal image at test time. Real-robot: no — simulation across mazes, PushT, Rope, and Granular scenes; strongest gains on PushT, Rope, Granular.

**DUET-DINO** (Nilavadi et al., Sep 2026, [arXiv:2609.10506](https://arxiv.org/abs/2609.10506)). Trains side- and wrist-camera action-conditioned predictors jointly with cross-attention for goal-conditioned 7-DoF planning on DROID and RoboArena trajectories. Real-robot: not reported / unconfirmed.

**VQ-WM** (Xu et al., Oct 2026, [arXiv:2610.25600](https://arxiv.org/abs/2610.25600)). Plans with shortest-path search over vector-quantized latent states using a controller-aware state codebook, then tracks each planned state with a learned continuous controller from visual feedback at a different rate, limiting compounding error. Real-robot: not reported.

**VLA-JEPA** (2602.10098). Latent world model bridging VLAs and JEPA-style predictive coding. Details not surfaced.

**DIAL** (2603.29844). Title only; details not surfaced.

**LeWorldModel** (2603.19312). Title only; details not surfaced.

**DreamDojo** (2602.06949). Generalist world model trained from human videos. Details not surfaced.

**VideoVLA** (2602.21157). Title only; details not surfaced.

**DiT4DiT** (2603.10448). Title only; details not surfaced.

**WoVR** (2602.13977). Simulator / RL world model. Details not surfaced.

**KineWorld** (2610.06349). Action-induced transport fields for embodied world modeling. Details not surfaced.

### World Action Models (WAMs) — world modeling fused with action output

A distinct 2025–2026 sub-genre: rather than a separate world model plus a separate policy, these models unify prediction of future world states and emission of robot actions in one network.

**Flex-π** (Yan et al., UW / Allen Institute, Aug 2026, [arXiv:2608.10860](https://arxiv.org/abs/2608.10860)). 6B model outputting future RGB, 3D pointmaps, DINOv3 semantics, and actions from one checkpoint; deployable as VLA, full world-action model, or intermediate points depending on compute; pointmaps encoded with a pretrained video world model's VAE encoder so geometry shares latents with RGB/DINO features; weights initialized from Wan, pre-trained on AGIBOT World. Real-robot: yes — up to 2–7× gains over baselines on real-world dexterous bimanual manipulation, runs faster than π0.5; beats strongest world-action baseline by 1.9× on RoboTwin with limited demonstrations.

**MotionWAM** (Zheng et al., Jun 2026, [arXiv:2606.09215](https://arxiv.org/html/2606.09215v1)). Replaces the VLM backbone of a VLA with a video world model whose intermediate denoising features condition the action policy; single egocentric camera input, whole-body motion tokens covering locomotion and torso, cross-embodiment action post-training in Stage 2. Real-robot: yes — Unitree G1, nine real-world tasks covering waist control, height regulation, squatting locomotion, foot interaction, body–hand coordination.

**HWAM** (Yan Yang et al., Oct 2026, [arXiv:2610.12026](https://arxiv.org/abs/2610.12026)). Humanoid world action model that generates state and action jointly, adding the post-execution proprioceptive state as a prediction target to close the gap between a policy's reference action and the whole-body controller's actual motion. Real-robot: yes — tested on three real tasks on the LimX OLI humanoid, reportedly beat every compared baseline.

**Being-M0.7** (Junpeng Yue et al., Oct 2026, [arXiv:2610.11283](https://arxiv.org/abs/2610.11283)). Latent WAM taking visual-motion priors from mixed-modality human data; training in three stages (pre-training, robot mid-training, action post-training). Real-robot: yes — best aggregate success on the SIMPLE benchmark; matched (did not beat) the top baseline on real Unitree G1 loco-manipulation.

**SelfWAM** (2608.00725). Self-grounded unified WAM for fast robot control. Details not surfaced.

**WAM-TTT** (2607.06988). Steers WAMs at test time by watching human play. Details not surfaced.

**R²-WAM** (2610.04913). Repair-and-reject post-training for world action models. Details not surfaced.

**OpenWAM** (2609.07398). Open, modular exploration of systematic WAM pretraining. Details not surfaced.

**Fast-WAM** (2603.16666). Title only; details not surfaced.

**EgoWAM** (2607.08436). WAMs beyond pixels using in-the-wild egocentric human data. Details not surfaced.

**GPC / Inference-Time Enhancement** (Qi et al., Feb 2025, [arXiv:2502.00622](https://arxiv.org/html/2502.00622)). Freezes a generative policy's weights and improves inference-time execution by sampling action proposals ranked/refined through short look-ahead rollouts in an action-conditioned world model. Real-robot: not reported — speed is the noted limitation (>3 s per decision cycle per a follow-up).

### Video diffusion world models for robotics

**Ctrl-World** (Guo, Shi, Chen, Finn, Oct 2025, [arXiv:2510.10125](https://arxiv.org/pdf/2510.10125)). Fine-tunes a pretrained video diffusion model on DROID to predict multiple camera views jointly and evaluates VLA policies entirely "in imagination," including an interactive keyboard-driven mode from a recorded starting observation. Real-robot: no — ranks policies without physical rollouts.

**GeniWorld** (Gu et al., Aug 2026, [arXiv:2608.06332](https://arxiv.org/abs/2608.06332)). Renders actions as visual representations so a policy or human operator drives an autoregressive Wan2.2 backbone in closed loop; claims robust transfer from fixed-scene demos to unseen scenes and beats Ctrl-World out of distribution. Real-robot: not reported — claims few-real-demonstration downstream policy improvement, but no quantitative real-robot figures surfaced.

**PAIWorld** (Huang et al., Jun 2026, [arXiv:2606.18375](https://arxiv.org/abs/2606.18375)). 3D-consistent multi-view world foundation model with Geometry-Aware Cross-View Attention, Geo-RoPE, and Latent 3D-REPA on a Wan2.1 backbone pretrained on 2.5M multi-view clips. Real-robot: benchmark-only (1st WorldArena EWMScore 72.31%; 2nd AgiBot-Challenge2026 EWMScore 82.45%, top Scene Consistency 90.41%); real deployment unconfirmed.

**DreamTrue** (Li et al., Oct 2026, [arXiv:2610.12468](https://arxiv.org/abs/2610.12468)). Edits recorded trajectories into actions that may fail, generates the resulting future videos across views and embodiments, and trains with embodied video rewards in a second stage with no extra real-robot data collection. Real-robot: challenge-track only — human-assessed interaction defects on AgiBot fell from 48.12% to 6.25% with state-of-the-art action following; 1st in the AgiBot World Challenge 2026 world-model track; hardware status unconfirmed.

**PhysGen** (Song et al., Mar 2026, [arXiv:2603.00110](https://arxiv.org/abs/2603.00110)). Uses a pretrained video generator (NOVA backbone) as a stand-in physics simulator; each step's token output yields both a robot action and a predicted video frame. Real-robot: partial — reported real-world Franka tasks at 75% success (per third-party summary, not verified against the paper); LIBERO 90.8%, ManiSkill 74%; 732M parameters; most of the gain (+13.2%) attributed to video-generation pretraining.

**Vid2World** (2505.14357, ICLR 2026). Uses "video diffusion causalization" to convert passive, full-sequence pretrained video diffusion models into action-conditioned interactive world models. Real-robot: yes — tested on real-robot manipulation, 3D game simulation, and open-world navigation.

**EVA** (2603.17808). Aligns video world models with executable robot actions using inverse dynamics rewards; a pretrained inverse dynamics model turns short windows of the generated rollout into actions. Real-robot: yes — tested on RoboTwin 2.0 simulation and a real bimanual robot; diffusion sampling cost still prevents high-frequency reactive control; authors point to distillation or fewer-step samplers.

**Vidarc** (2512.17661). Embodied video diffusion model for closed-loop control. Details not surfaced.

**Video2Act** (2512.03044). Dual-system video diffusion policy with robotic spatio-motional modeling. Details not surfaced.

**ProWorld** (2610.15294). Multi-view world model with proprioceptive feedback for closed-loop policy evaluation. Details not surfaced.

**DVG-WM** (2606.32028v1, June 2026). Disentangled video generation: splits the world model into dynamics learning and visual synthesis, carries dynamics into video latents via flow matching, and applies a latent degradation step to restore contact-rich detail. Real-robot: yes — better video quality and speedups up to 3.97× on LIBERO and real robots.

**PhysWorld** variants: "Robot Learning from a Physical World Model" (Mao et al., Nov 2025, [arXiv:2511.07416](https://arxiv.org/abs/2511.07416)) — zero-shot manipulation transfer via a reconstructed physical world model; real-robot: yes. "PhysWorld: From Real Videos to World Models of Deformable Objects" (Yang et al., Oct 2025, [arXiv:2510.21447](https://arxiv.org/abs/2510.21447)) — learns spatially-varying deformable-object properties from limited real video via an MPM digital twin plus a lightweight GNN world model; real-robot: unclear. "ABot-PhysWorld" (Chen et al., Mar 2026, [arXiv:2603.23376](https://arxiv.org/abs/2603.23376)) — 14B DiT with physics-aware DPO on ~3M clips from AgiBot, RoboCoin, RoboMind, Galaxea, and OXE; real-robot: unclear.

### Cosmos follow-ups and latent-video policies

**Cosmos Policy** (Kim et al., 2026). Encodes actions, future states, and values as extra latent "frames" in an otherwise unmodified pretrained video diffusion model, turning Cosmos into a unified world model + policy. Details not surfaced beyond the survey description.

**GE-Act** (Liao et al., 2026). A flow-matching action branch coupled to a video diffusion world model through cross-attention. Details not surfaced beyond the survey description.

**GreenWAM** (Sidorov et al., Oct 2026, [arXiv:2610.18774](https://arxiv.org/abs/2610.18774)). A single network (starting from Cosmos 3 Edge) acts as both world model and policy across 20 robot bodies via a 79-slot shared anatomical action space, with seven jointly trained modes spanning visual, action-conditioned, and world-action settings. Real-robot: yes — beats baselines adapted from π0.5 and Cosmos 3 Edge on a real humanoid; distilled single-step controller runs at 28.3 Hz on real hardware; scores above compared world-action models and video generators on WorldArena 1.0 (trajectory, depth, 3D accuracy); highest zero-shot LIBERO-plus success among compared methods. Code: GitHub greenvla/GreenWAM; HF SberRoboticsCenter/GreenWAM.

**GRAIL** (Xie et al., NVIDIA, Jun 2026, [arXiv:2606.05160](https://arxiv.org/abs/2606.05160)). Generates humanoid training data from video world models seeded by rendered 3D assets (known geometry, camera, metric scale), then recovers and refines trajectories via pose estimation/object tracking and joint optimization; no physical robot or motion capture needed before deployment. Real-robot: yes — Unitree G1 egocentric visual policies trained only on GRAIL data reached 84% success on object pick-up and 90% on stair-climbing. Dataset: 20,000+ sequences covering pick-up, whole-body manipulation, sitting, terrain traversal.

**Interactive World Simulator** (Wang et al., Mar 2026, [arXiv:2603.08546](https://arxiv.org/abs/2603.08546)). Action-conditioned video world model trained from a moderate-sized robot interaction dataset that supports stable >10-minute rollouts at 15 FPS on a single RTX 4090; predicted frames feed the policy and the policy's actions drive the next prediction in closed loop. Real-robot: yes (claimed validation) — simulator performance tracks real-world performance closely across several tasks; simulator-generated data roughly as useful as an equal amount of real data on rigid-object, deformable, and object-pile tasks. Prior world models score lower across its metrics (no numbers surfaced). Follow-up: HapticWorld (2609.31924) adds real-time joint-torque feedback; policies trained on its demonstrations succeeded 54/60 real-world trials vs 56/60 for real data and 19/60 for vision-only.

### World foundation models, simulators, and closed-loop evaluation

**GE-Sim 2.0** (Qiu et al., AgiBot, May 2026, [arXiv:2605.27491](https://arxiv.org/abs/2605.27491)). Closed-loop video world simulator extending view-only Genie Envisioner (v1, arXiv:2508.05635): a policy acts inside the simulator, receives generated frames as input for its next action chunk; trained on thousands of hours of real robot data (teleoperation, contact-rich interaction, on-robot deployment) including failures; a VL world-judge reward model scores rollouts frame-by-frame as automated referee and sparse reward for filtered BC and RL; diffusion distilled to few-step inference. Real-robot: unclear — pi05 policy served through openpi generates head + both wrist camera views in closed-loop rollouts; no quantitative policy-training results surfaced. Code: GitHub AgibotTech/GE-Sim-V2; HF agibot-world/Genie-Envisioner-Sim-v2.0 (checkpoint gesim_community_v2.0.1_g01op_distill_2B).

### Benchmarks and evaluation

**WorldArena** (Shang et al., Tsinghua, Feb 2026, [arXiv:2602.08971](https://arxiv.org/abs/2602.08971)). Evaluates three things — video perception quality, embodied task functionality (world model as data engine, policy evaluator, action planner), and human evaluation — via EWMScore, the arithmetic mean of 16 normalized video metrics across visual quality, motion quality, content consistency, physics adherence, 3D accuracy, and controllability. Real-robot: no — video and simulation benchmark (leaderboard: world-arena.ai); WorldArena 2.0 extends to 12 models and 3 modalities ([arXiv:2605.17912](https://arxiv.org/abs/2605.17912), May 2026), adding a test of world models as interactive RL environments for policy optimization plus real-robot settings and multiple embodiments.

**WorldEval** (Li et al., May 2025, [arXiv:2505.19017](https://arxiv.org/abs/2505.19017)). Automated pipeline evaluating real-robot policies inside a world model used as a simulator, adapting a video generation model with Policy2Vec so policy latent actions drive generated video; ranks policies/checkpoints and flags unsafe behavior from new robot models. Real-robot: yes — evaluates real-robot policies; reported to beat real-to-sim evaluation by MMRV and Pearson r correlation against real-world results.

**dWorldEval** (Apr 2026, [arXiv:2604.22152](https://arxiv.org/abs/2604.22152)). Discrete-diffusion world model for policy evaluation reporting gains over WorldEval, Ctrl-World, and WorldGym on LIBERO, RoboTwin, and real-robot tasks. Real-robot: yes (real-robot tasks included).

**H2R-Bench** (Rong et al., Aug 2026, [arXiv:2608.13049](https://arxiv.org/abs/2608.13049)). Tests cross-embodiment video transfer: given a first-person human manipulation clip, a video world model must generate video of a specified robot performing the same task — 240 transfer cases from 120 EgoDex test scenes across six manipulation families, each paired with parallel-jaw and dexterous-hand end-effectors. Real-robot: no — video-generation benchmark; human-to-robot transfer remains a weak spot even for leading video world models (no per-model scores surfaced).

**X2Real** (Ruan et al., Sep 2026, [arXiv:2609.27449](https://arxiv.org/abs/2609.27449)). Built on NVIDIA Isaac Lab-Arena to predict real-robot manipulation performance from simulated runs; 44 hierarchical long-horizon tasks across 10 capability dimensions; 73 runnable configurations on ArtiXon Arm-6A, Quanta X1, ARX R5, Franka; policies tested include Wall-OSS-0.5, DreamZero, π0.5, Wall-x-preview. Real-robot: yes (calibration) — simulated and real-robot scores correlate linearly at 0.84 after visual and physical calibration.

**RoboWM-Bench** (Apr 2026, [arXiv:2604.19092](https://arxiv.org/pdf/2604.19092)). Evaluates world models for manipulation by whether actions extracted from generated videos actually complete the task. Real-robot: unclear — details not surfaced.

**WorldSimProbe** (2608.09298). Diagnoses simulator faithfulness in action-conditioned world models for embodied manipulation. Details not surfaced.

**How Should World Models Be Evaluated for Embodied Decision-Making?** (2606.15032). Organizes the literature on an L0–L7 ladder from visual plausibility to policy-optimization utility; protocol stresses policy-ranking agreement and full-horizon outcome fidelity. Details not surfaced.

**Do World Models Make Better Robots?** (2609.29669). Catalogues 160 benchmarks; in 2025, open-loop world-model benchmarks outnumbered closed-loop ones 13 to 6. Details not surfaced.

**GigaWorld-1** (2607.02642) and **OSCAR** (2606.04463). Title only; details not surfaced.

### Surveys and tutorials

- **World Model for Robot Learning: A Comprehensive Survey** (2605.00080). Groups benchmarks into open-loop predictive quality, closed-loop task utility, policy evaluation, and physical-consistency diagnostics; cautions that convincing-looking rollouts can still break closed-loop control.
- **World Models for Robotic Manipulation: A Survey** (2606.00113).
- **From World Models to World Action Models: A Concise Tutorial for Robotics** (2607.00836).
- **World Models for Embodied Intelligence: From Plausible to Controllable to Actionable** (2609.16697).
- **Video Generation Models as World Models: Efficient Paradigms, Architectures and Algorithms** (2603.28489).
- **World-Action Models for Robot Learning and Control: A Survey** (2609.16074).
- **Robotic Video World Models: A Survey of Applications, Research Challenges, Future Directions** (2601.07823).

Quick reference:

| Model/Paper | arXiv | Date | Real-robot? |
|---|---|---|---|
| V-JEPA 2-AC | 2506.09985 | Jun 2025 | Yes (Franka) |
| DINO-WM | 2411.04983 | Feb 2025 | No (sim) |
| DUET-DINO | 2609.10506 | Sep 2026 | Unclear |
| VQ-WM | 2610.25600 | Oct 2026 | Not reported |
| VLA-JEPA | 2602.10098 | Feb 2026 | Details not surfaced |
| DIAL | 2603.29844 | Mar 2026 | Details not surfaced |
| LeWorldModel | 2603.19312 | Mar 2026 | Details not surfaced |
| DreamDojo | 2602.06949 | Feb 2026 | Details not surfaced |
| VideoVLA | 2602.21157 | Feb 2026 | Details not surfaced |
| DiT4DiT | 2603.10448 | Mar 2026 | Details not surfaced |
| WoVR | 2602.13977 | Feb 2026 | Details not surfaced |
| KineWorld | 2610.06349 | Oct 2026 | Details not surfaced |
| Flex-π | 2608.10860 | Aug 2026 | Yes (bimanual dexterous) |
| MotionWAM | 2606.09215 | Jun 2026 | Yes (Unitree G1) |
| HWAM | 2610.12026 | Oct 2026 | Yes (LimX OLI) |
| Being-M0.7 | 2610.11283 | Oct 2026 | Yes (Unitree G1, matched) |
| SelfWAM | 2608.00725 | Aug 2026 | Details not surfaced |
| WAM-TTT | 2607.06988 | Jul 2026 | Details not surfaced |
| R²-WAM | 2610.04913 | Oct 2026 | Details not surfaced |
| OpenWAM | 2609.07398 | Sep 2026 | Details not surfaced |
| Fast-WAM | 2603.16666 | Mar 2026 | Details not surfaced |
| EgoWAM | 2607.08436 | Jul 2026 | Details not surfaced |
| GPC / Inference-Time Enhancement | 2502.00622 | Feb 2025 | Not reported |
| Ctrl-World | 2510.10125 | Oct 2025 | No |
| GeniWorld | 2608.06332 | Aug 2026 | Unclear |
| PAIWorld | 2606.18375 | Jun 2026 | Benchmark only |
| DreamTrue | 2610.12468 | Oct 2026 | Challenge track only |
| PhysGen | 2603.00110 | Mar 2026 | Partial (Franka 75%) |
| Vid2World | 2505.14357 | May 2025 | Yes |
| EVA | 2603.17808 | Mar 2026 | Yes (bimanual) |
| Vidarc | 2512.17661 | Dec 2025 | Details not surfaced |
| Video2Act | 2512.03044 | Dec 2025 | Details not surfaced |
| ProWorld | 2610.15294 | Oct 2026 | Details not surfaced |
| DVG-WM | 2606.32028 | Jun 2026 | Yes (LIBERO + real) |
| PhysWorld (physical world model) | 2511.07416 | Nov 2025 | Yes |
| PhysWorld (deformable objects) | 2510.21447 | Oct 2025 | Unclear |
| ABot-PhysWorld | 2603.23376 | Mar 2026 | Unclear |
| Cosmos Policy | (2026) | 2026 | Details not surfaced |
| GE-Act | (2026) | 2026 | Details not surfaced |
| GreenWAM | 2610.18774 | Oct 2026 | Yes (humanoid) |
| GRAIL | 2606.05160 | Jun 2026 | Yes (Unitree G1) |
| Interactive World Simulator | 2603.08546 | Mar 2026 | Yes (claimed) |
| GE-Sim 2.0 | 2605.27491 | May 2026 | Unclear |
| WorldArena | 2602.08971 | Feb 2026 | No (benchmark) |
| WorldArena 2.0 | 2605.17912 | May 2026 | Real-robot settings added |
| WorldEval | 2505.19017 | May 2025 | Yes (evaluator) |
| dWorldEval | 2604.22152 | Apr 2026 | Yes (real-robot tasks) |
| H2R-Bench | 2608.13049 | Aug 2026 | No |
| X2Real | 2609.27449 | Sep 2026 | Yes (calibration 0.84) |
| RoboWM-Bench | 2604.19092 | Apr 2026 | Unclear |
| WorldSimProbe | 2608.09298 | Aug 2026 | Details not surfaced |
| Evaluation L0–L7 | 2606.15032 | Jun 2026 | Survey / position |
| 160-benchmark survey | 2609.29669 | Sep 2026 | Survey / position |
| GigaWorld-1 | 2607.02642 | Jul 2026 | Details not surfaced |
| OSCAR | 2606.04463 | Jun 2026 | Details not surfaced |

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
