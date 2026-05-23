---
icon: brain
---

# Foundation Models & Vision-Language-Action (VLA) Models

In 2022, the idea that you could pretrain one neural network on a giant mix of robot data and then fine-tune it for any task was speculative. In 2026, it is the default research direction across most major robotics labs. Whether it is the *production* default depends on who you ask and how patient your customers are.

This page covers the **VLA paradigm**: models that take vision + language as input and emit robot actions. It is the direction the field is most excited about and the direction most likely to be oversold.

## What is a VLA?

A Vision-Language-Action model is a single neural network that:

1. Takes one or more **images** (RGB, sometimes depth) as input.
2. Takes a **language instruction** ("pick up the red cup and put it on the plate").
3. Optionally takes **proprioception** (joint positions, gripper state).
4. Emits **robot actions** (end-effector deltas, joint targets, gripper commands).

Architecturally, almost all VLAs in 2026 follow the same template:

```
[Image] --[Vision Encoder, e.g. ViT, SigLIP]--> tokens
[Text]  --[Text Tokenizer]--> tokens
        --> [Transformer LLM backbone (Llama, PaLM-E, Pi base, etc.)]
        --> Action head (regression, autoregressive tokens, diffusion, or flow matching)
        --> [Action chunk for next ~1 second]
```

The "language model as policy backbone" framing is the big idea. You take a pretrained multimodal LLM and either:

- **Discretize actions into tokens** and let the LLM autoregress over them (RT-2 style), or
- **Replace the language head with an action decoder** (OpenVLA, π0 style), trained on robot demonstrations.

## A brief lineage

The order matters because each model fixed problems in the previous one.

### RT-1 (Google/Everyday Robots, 2022)

Brohan et al., *"RT-1: Robotics Transformer for Real-World Control at Scale"*. [https://arxiv.org/abs/2212.06817](https://arxiv.org/abs/2212.06817)

The first scaled-up version of "tokenize everything, transformer in the middle." 130k demonstrations across 700+ tasks, single policy, 35Hz inference. Not a foundation model in the modern sense (the encoder was not pretrained on web data), but the architectural ancestor.

### RT-2 (Google DeepMind, 2023)

Brohan et al., *"RT-2: Vision-Language-Action Models Transfer Web Knowledge to Robotic Control"*. [https://arxiv.org/abs/2307.15818](https://arxiv.org/abs/2307.15818)

The model that defined the term "VLA." Took a pretrained vision-language model (PaLI-X / PaLM-E), fine-tuned on robot data with actions encoded as text tokens. The big result: emergent capabilities from web pretraining transferred to manipulation (e.g., understanding "move the dinosaur to the red object" even when no demo showed dinosaurs).

### Open X-Embodiment / RT-X (2023)

Padalkar, Pooley et al., *"Open X-Embodiment: Robotic Learning Datasets and RT-X Models"*. [https://arxiv.org/abs/2310.08864](https://arxiv.org/abs/2310.08864)

Project: [https://robotics-transformer-x.github.io/](https://robotics-transformer-x.github.io/)

A collaboration of 30+ labs pooling robot data into one dataset (~1M trajectories across 22 embodiments). The dataset became the standard pretraining corpus for everything that followed. RT-X (RT-1-X, RT-2-X) was the demo: train a single model on all that data, get better cross-embodiment transfer.

### OpenVLA (Stanford, 2024)

Kim, Pertsch, Karamcheti et al. [https://openvla.github.io/](https://openvla.github.io/)
Paper: [https://arxiv.org/abs/2406.09246](https://arxiv.org/abs/2406.09246)

The first competitive open-weights VLA. 7B params, built on Llama-2 + SigLIP + DINOv2 fusion. Trained on Open X-Embodiment. Released weights, code, fine-tuning recipes.

OpenVLA is what most people in 2025–2026 actually start with because (a) weights are open, (b) the codebase is reasonable, (c) the LoRA fine-tuning recipes work on a single A100.

### Octo (Berkeley, 2024)

Octo Team. [https://octo-models.github.io/](https://octo-models.github.io/)
Paper: [https://arxiv.org/abs/2405.12213](https://arxiv.org/abs/2405.12213)

Berkeley's open VLA. Smaller (Octo-Base is ~93M params, Octo-Small ~27M), uses diffusion action heads instead of discrete tokens. Designed for fast fine-tuning and inference. Less flashy than OpenVLA but often a better default for hardware-constrained deployments.

### π0 / π0.5 / π0-FAST (Physical Intelligence, 2024–2025)

Black, Brown, Driess, Esmail, et al. [https://www.physicalintelligence.company/blog/pi0](https://www.physicalintelligence.company/blog/pi0)

π0 introduced **flow matching action heads** - instead of autoregressive token sampling or diffusion denoising, generate the action chunk via a single ODE solve. Order of magnitude faster inference at similar quality. Pretrained on a substantially larger and more diverse robot dataset than what was public at the time.

π0.5 (2025) [verify] extended to long-horizon mobile manipulation with open-ended language instructions ("clean the kitchen") - including some of the most impressive autonomous home demonstrations to date.

**OpenPi** [https://github.com/Physical-Intelligence/openpi](https://github.com/Physical-Intelligence/openpi) [verify] is the open release of π0-base + fine-tuning code. As of 2026 this is the strongest open-weights VLA and what I would build on if starting today.

### Other 2024–2026 VLAs worth knowing

| Model | Org | Distinguishing feature | Open weights? |
|---|---|---|---|
| **RDT-1B** | Tsinghua | 1B diffusion VLA, bimanual focus | Yes [verify] |
| **GR00T N1 / N1.5** | NVIDIA | Humanoid-first VLA, system-1 + system-2 split | Partial |
| **HPT** | MIT (Wang et al.) | Heterogeneous robot transformer | Yes [verify] |
| **CogACT** | Microsoft | VLM + diffusion action head | Yes [verify] |
| **Helix** | Figure AI | Humanoid VLA | No (closed) |
| **TinyVLA** | Various | Compressed VLAs <1B params | Some [verify] |

## How VLAs are trained

Three stages, all of which matter:

### Stage 1: Vision-language pretraining

Take an off-the-shelf vision-language model (Llama-2 + SigLIP for OpenVLA, PaLM-E for RT-2, internal model for π0). This is the bulk of the "world knowledge." Skip this and your VLA is just a slightly fancier ACT.

### Stage 2: Robot pretraining

Fine-tune on a large mix of robot data: Open X-Embodiment + DROID + internal data. ~1M+ trajectories. Action representation matters a lot here:

- **Discretized action tokens** (RT-2, OpenVLA) - easy to plug into LLM training, but lossy.
- **Continuous action diffusion** (Octo, CogACT) - better fidelity, slower inference.
- **Flow matching** (π0) - best of both, currently SOTA.

### Stage 3: Task-specific fine-tuning

You collect 50–500 demos of your specific task on your specific robot, fine-tune the base VLA. This is where you actually deploy.

LoRA fine-tuning works well - you do not need to update the full 7B params, a few hundred million LoRA params is enough for downstream tasks.

## Data scale, very roughly

For context - what "internet-scale robot data" actually means:

| Dataset / model | Trajectories | Robot-hours (approx) | Notes |
|---|---|---|---|
| RT-1 internal | 130k | ~17k | EveryDay Robots fleet, ~17 months |
| Open X-Embodiment | 1M+ | ~60k+ [verify] | Aggregated from 30+ labs |
| DROID | 76k | ~350 | Single-arm Franka, large scene diversity |
| BridgeData V2 | 60k | ~140 | Berkeley, WidowX |
| Physical Intelligence π0 internal | "millions" of trajectories [verify] | ??? | Largest non-public corpus as of 2025 |
| RT-2 / web pretraining contribution | ~9B image-text pairs (web) | n/a | The "magic" of VLAs is mostly here |

Compare to LLM scales (10T+ tokens) and you see why robot foundation models are still early. The "internet of robot data" is not a thing yet.

## What VLAs are good at (2026)

- **Language-conditioned manipulation** in moderately structured environments. Pick-and-place with arbitrary objects, simple kitchen tasks, sorting.
- **Cross-embodiment transfer.** Train on lots of arms, fine-tune on yours.
- **Multi-task policies.** One model, many tasks via language conditioning.
- **Few-shot adaptation** to new objects/scenes when the base task is in distribution.
- **Long-horizon tasks when paired with a planner** (LLM picks subgoals, VLA executes).

## What VLAs are bad at (2026)

- **Latency-critical control.** Even fast VLAs (π0 with flow matching) run at ~20-50Hz on an A100. Most cannot run on the robot's onboard compute at production frame rates.
- **Fine force control.** VLAs are trained on position/velocity demos. They mostly do not have a notion of compliance or force.
- **Truly novel tasks.** "In distribution" matters. A VLA fine-tuned on kitchen manipulation will not suddenly do circuit board assembly.
- **Dexterous manipulation.** OpenAI hand-cube rotation, in-hand tool use - not yet.
- **Tasks where the demonstrator was bad.** Garbage in, garbage out. VLAs amplify systematic demonstrator errors.

{% hint style="info" %}
**Field note.** The honest 2026 take on VLAs: they are a real capability advance for moderately-structured manipulation, *especially* when you need language conditioning. They are not yet the "GPT-3 of robotics." A bespoke ACT or Diffusion Policy fine-tuned on your specific task will still beat a fine-tuned VLA in narrow benchmarks - the VLA wins on *generalization* and *language instructability*. Pick the tool based on the deployment, not the demo video.
{% endhint %}

## Architectural details - a sketch

A representative modern VLA (OpenVLA-style) at a sketch level:

```
Input:
  - 2x RGB images (3rd person + wrist)
  - Language instruction (tokenized)
  - (Optional) proprioception

Encoders:
  - Image: SigLIP + DINOv2 fused, ViT-Large
  - Text: Llama tokenizer
  
Backbone:
  - Llama-2 7B (or similar)
  - Image patch tokens + text tokens + state tokens interleaved
  - Causal attention
  
Output:
  - Either: discretized action tokens (7 per step: dx, dy, dz, droll, dpitch, dyaw, gripper)
  - Or: diffusion/flow head on action chunks (k = 8 to 50 future actions)

Inference:
  - Predict action chunk (1 forward pass for autoregressive heads, multiple for diffusion)
  - Execute chunk
  - Re-plan at chunk boundary or earlier (receding horizon)
```

π0-style with flow matching:

```
Same encoders + backbone
Output: flow-matching head conditioned on hidden state
  - Sample noise z ~ N(0, I) in action space
  - Solve ODE dz/dt = v_θ(z, t, hidden) from t=0 to t=1
  - Resulting z is the predicted action chunk
  - Single ODE solve = ~10 function evaluations vs 50-100 for diffusion
```

## Where VLAs fit in your stack

A pragmatic 2026 architecture for a manipulation deployment:

```
[High-level planner / LLM]
        |
        | "pick up the red mug"
        v
[VLA: π0 or OpenVLA fine-tuned for kitchen tasks]
        |
        | end-effector delta + gripper command (10-20 Hz)
        v
[Inverse Kinematics + Cartesian impedance controller]
        |
        | joint torques (1 kHz)
        v
[Real robot]
        |
        | proprio + force/torque + images (varying rates)
        v
[Feedback to VLA + safety supervisor]
```

The VLA is not the only thing running. Force-sensitive primitives, safety stops, and IK still live as classical controllers. The VLA is a smart commander, not the whole stack.

## Fine-tuning recipes

For OpenVLA, the recipe that works:

```
1. Collect 50-500 demos of your task (teleop, kinesthetic, or both)
2. Convert to LeRobot or RLDS format
3. LoRA fine-tune OpenVLA-7B with:
   - rank 32, alpha 16
   - lr 5e-4
   - batch size 16 (single A100 80GB)
   - ~20k steps
4. Eval on held-out scene configurations
5. Iterate: more demos for failure modes, repeat
```

Time: ~1-2 days for data collection, ~6-12 hours for fine-tuning, ~1 day for eval. Faster than training a Diffusion Policy from scratch on the same task in most cases.

For π0 / OpenPi:

```
Similar pipeline. The OpenPi repo has reference fine-tuning scripts.
Flow matching head means inference is faster than diffusion, so this is preferred for higher-frequency control loops.
```

## Practical libraries

| Library | What it gives you | Notes |
|---|---|---|
| **OpenVLA** - [https://github.com/openvla/openvla](https://github.com/openvla/openvla) | OpenVLA training + inference + LoRA fine-tuning | The de-facto open VLA baseline. |
| **OpenPi** - [https://github.com/Physical-Intelligence/openpi](https://github.com/Physical-Intelligence/openpi) [verify] | π0 weights, fine-tuning, flow matching | The 2026 strongest open-weights VLA. |
| **Octo** - [https://github.com/octo-models/octo](https://github.com/octo-models/octo) [verify] | Octo-Small/Base + fine-tuning | Lighter weight, good for resource-constrained. |
| **LeRobot** - [https://github.com/huggingface/lerobot](https://github.com/huggingface/lerobot) | VLA fine-tuning recipes, dataset tooling | Has OpenVLA, π0 integrations. The integration layer. |
| **RDT-1B** - [https://github.com/thu-ml/RoboticsDiffusionTransformer](https://github.com/thu-ml/RoboticsDiffusionTransformer) [verify] | 1B bimanual diffusion VLA | If your task is bimanual. |
| **NVIDIA GR00T** - [https://github.com/NVIDIA/Isaac-GR00T](https://github.com/NVIDIA/Isaac-GR00T) [verify] | Humanoid-focused foundation model stack | New (2025), humanoid-specific. |

## Honest assessment of state of the art (early 2026)

What you can actually do today with off-the-shelf open VLAs:

- Fine-tune for a kitchen-scale manipulation task (~50-200 demos, single arm, single scene): ~70-85% success rate.
- Multi-scene generalization (same task, different rooms): ~50-70%.
- Cross-task generalization (related tasks unseen at fine-tune time): hit or miss, often <50%.
- Mobile manipulation: still early; π0.5 [verify] and Mobile ALOHA-derived work show promise but few open-weights baselines.
- Force-sensitive contact tasks: poor without specific force/torque conditioning.
- Sub-second precision tasks: poor due to inference latency.

For comparison: a Diffusion Policy or ACT trained from scratch on the *exact* task usually gets 85-95% success but does not generalize off-distribution.

## Further reading

- Brohan et al., *"RT-2: Vision-Language-Action Models Transfer Web Knowledge to Robotic Control"* - [https://arxiv.org/abs/2307.15818](https://arxiv.org/abs/2307.15818)
- Padalkar et al., *"Open X-Embodiment: Robotic Learning Datasets and RT-X Models"* - [https://arxiv.org/abs/2310.08864](https://arxiv.org/abs/2310.08864)
- Kim et al., *"OpenVLA: An Open-Source Vision-Language-Action Model"* - [https://arxiv.org/abs/2406.09246](https://arxiv.org/abs/2406.09246)
- Octo Team, *"Octo: An Open-Source Generalist Robot Policy"* - [https://arxiv.org/abs/2405.12213](https://arxiv.org/abs/2405.12213)
- Physical Intelligence, *"π0: A Vision-Language-Action Flow Model for General Robot Control"* - [https://www.physicalintelligence.company/blog/pi0](https://www.physicalintelligence.company/blog/pi0) [verify]
- CoRL 2024 and CoRL 2025 best papers - the VLA frontier is published here.
