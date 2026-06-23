---
description: A cross-handbook index of the datasets and benchmarks that actually matter, with pointers to the deep dives
icon: database
---

# Datasets & Benchmarks

{% hint style="info" %}
This page is an **index**, not a deep dive. The full treatments live elsewhere in the handbook: [Robot Learning - Datasets & Benchmarks](../robot-learning/datasets-and-benchmarks.md) for manipulation/VLA data, and [SLAM Evaluation & Benchmarking](../slam-and-state-estimation/slam-evaluation.md) for trajectory datasets and metrics. Use this page to figure out *which* benchmark you need, then jump to the deep dive.
{% endhint %}

## Why benchmarks matter (and how they lie)

Benchmarks are how a field agrees on what "better" means. Without KITTI there is no way to claim your LiDAR odometry beats LOAM; without LIBERO every IL paper is "we tried it on our robot and it worked." Shared datasets are the only mechanism robotics has for reproducible comparison, and you should use them for every ablation you run.

But every benchmark lies in a predictable way, and you should know the failure modes before trusting a leaderboard:

* **Saturation.** Once a benchmark is solved, ranking on it measures tuning effort, not capability. KITTI odometry has been saturated for years - a top-10 entry tells you almost nothing about how that system handles a dusty warehouse.
* **Distribution lock-in.** Methods overfit to the benchmark's sensor rig, environment, and quirks. A visual SLAM system tuned for TUM RGB-D's slow handheld Kinect motion will faceplant on a drone.
* **Proxy gap.** Sim benchmarks measure sim performance. Beating LIBERO does not mean your policy works on hardware; failing LIBERO is a strong signal it won't. Treat sim benchmarks as a *necessary* filter, never a *sufficient* one.
* **Metric gaming.** Any single number can be optimized at the expense of what you actually care about. mAP says nothing about latency; ATE says nothing about map quality; success rate says nothing about how violently the robot moved.

My rule: benchmark to compare techniques against each other, then validate on your own hardware in your own environment before believing anything.

Quick routing table if you already know what you're building:

| You are building | Benchmark on | Deep dive |
| --- | --- | --- |
| LiDAR/visual odometry or SLAM | KITTI (baseline) + Newer College or Hilti (credibility) | [SLAM Evaluation](../slam-and-state-estimation/slam-evaluation.md) |
| VIO for a drone | EuRoC MAV | [SLAM Evaluation](../slam-and-state-estimation/slam-evaluation.md) |
| A 2D/3D detector for a robot | COCO for sanity, then your own data | [Object Detection & Tracking](../perception-and-computer-vision/object-detection-and-tracking.md) |
| An AV perception stack | nuScenes + Waymo Open | [3D Perception](../perception-and-computer-vision/3d-perception.md) |
| A manipulation policy (IL/VLA) | LIBERO in sim, then real-robot trials | [Robot Learning Datasets](../robot-learning/datasets-and-benchmarks.md) |
| An AMR navigation stack | BARN environments | [BARN Challenge](../authors-projects/barn-challenge.md) |

## SLAM & odometry

Full coverage with metrics, alignment pitfalls, and the `evo` workflow: [SLAM Evaluation & Benchmarking](../slam-and-state-estimation/slam-evaluation.md).

| Dataset | Sensors | What it tests | Status in 2026 |
| --- | --- | --- | --- |
| **KITTI Odometry** | Stereo + Velodyne HDL-64E + GPS/IMU (car) | Urban driving SLAM, 0.5-5 km trajectories | Saturated, but still the lingua franca baseline |
| **EuRoC MAV** | Stereo + IMU (drone), Vicon/laser-tracker GT | VIO under aggressive 6-DoF motion | The VIO benchmark; every VINS/ORB-SLAM3 number you see comes from here |
| **TUM RGB-D** | Kinect RGB-D, mocap GT | Indoor dense / neural SLAM | Default for RGB-D and NeRF/Gaussian-splat SLAM papers |
| **Newer College** | Ouster LiDAR + stereo + IMU (handheld/quadruped) | Outdoor-indoor LiDAR-VIO, modern rigs | The "post-KITTI" LiDAR benchmark worth reporting on |

If you want a current-generation challenge instead of a solved one, look at the Hilti SLAM Challenge - construction sites, dust, stairwells - covered in the [SLAM evaluation deep dive](../slam-and-state-estimation/slam-evaluation.md). For the neural end of the spectrum (Replica, ScanNet), see [Learned SLAM](../slam-and-state-estimation/learned-slam.md) and the author's [GO-SLAM](../authors-projects/go-slam.md) work.

## Perception

Detection and segmentation benchmarks live in the perception chapter - see [Object Detection & Tracking](../perception-and-computer-vision/object-detection-and-tracking.md) and [3D Perception](../perception-and-computer-vision/3d-perception.md).

| Dataset | Domain | What it tests | Notes |
| --- | --- | --- | --- |
| **COCO** | 2D images, ~330k images, 80 classes | Detection, segmentation, keypoints | Still the default pretraining/eval set for 2D detectors; saturated at the top but the mAP numbers remain the common currency |
| **nuScenes** | AV, 1000 scenes, 6 cameras + LiDAR + radar | 3D detection, tracking, prediction | The benchmark for camera-based 3D detection (BEV methods); uses NDS, a composite of mAP plus translation/scale/orientation errors |
| **Waymo Open** | AV, ~1150 segments, 5 LiDARs + 5 cameras | 3D detection and tracking at scale | Larger and harder than nuScenes; APH (heading-weighted AP) is the headline metric |

Also worth knowing, briefly:

* **SemanticKITTI** - per-point semantic labels on KITTI's LiDAR scans; the benchmark for LiDAR semantic segmentation.
* **ScanNet / ScanNet++** - indoor RGB-D scans with dense 3D annotations; doubles as a neural-SLAM and a 3D segmentation benchmark.
* **LVIS** - COCO images, ~1200 categories with a long tail; the better test if your robot needs rare-object vocabulary.

The honest caveat for robotics people: COCO-style mAP is a weak proxy for "my robot's grasping pipeline finds the object." Indoor manipulation scenes look nothing like COCO - different viewpoints, clutter, lighting, and object distributions. Expect a noticeable accuracy drop and plan to fine-tune on your own data - or reach for open-vocabulary models, covered in [Foundation Vision Models](../perception-and-computer-vision/foundation-vision-models.md).

## Manipulation & robot learning

This is the fastest-moving area, and the full survey - including DROID, BridgeData V2, RoboCasa, BEHAVIOR-1K - is at [Robot Learning - Datasets & Benchmarks](../robot-learning/datasets-and-benchmarks.md). The three you must know:

| Benchmark | Type | What it tests | One-line verdict |
| --- | --- | --- | --- |
| **Open X-Embodiment** | Real-robot dataset, ~1M+ trajectories, 22+ embodiments | VLA pretraining at scale | The de facto pretraining corpus for every 2024+ VLA |
| **LIBERO** | Sim benchmark, 130 language-conditioned tasks | IL generalization and lifelong learning | What VLA papers report; cheap to run, weak transfer guarantee |
| **RoboMimic** | Sim benchmark + framework, human demos of varying quality | Offline IL/RL algorithm comparison | Older but well-engineered; great for clean ablations of BC variants |

Runners-up you will see cited constantly, all covered in the deep dive:

* **DROID** - ~76k trajectories, single Franka embodiment across hundreds of scenes; the testbed for scene generalization.
* **BridgeData V2** - ~60k WidowX trajectories; the original large single-embodiment corpus.
* **RoboCasa** - procedurally generated household sim at scale; the closest thing to a "kitchen ImageNet."
* **BEHAVIOR-1K** - 1000+ household activities with fluids and deformables; impressive scope, heavy to train on.

The pattern in 2026: pretrain on Open X-Embodiment (or use a model that did), ablate on LIBERO or RoboCasa, then collect ~100-500 of your own demos for the real task. See [Imitation Learning](../robot-learning/imitation-learning.md) for the demo-count heuristics and [Foundation Models & VLAs](../robot-learning/foundation-models-vla.md) for what the pretrained models actually buy you.

One opinionated warning: the manipulation benchmark landscape churns fast. A leaderboard position from 18 months ago is archaeology. Check the dates on any comparison table before you trust it - including the ones in this handbook.

## Navigation

Navigation benchmarking is less standardized than SLAM or manipulation - most labs still demo on their own buildings. The notable exception:

* **BARN (Benchmark Autonomous Robot Navigation)** - ~300 procedurally generated cluttered obstacle courses, run as an annual competition at ICRA on standardized Jackal robots. It tests exactly the thing classical nav stacks are bad at: tight, cluttered spaces where the default DWA/TEB parameters give up. Scoring combines success rate and traversal time. I competed in it - notes and lessons at [BARN Challenge](../authors-projects/barn-challenge.md).
* **Habitat challenges** - embodied AI navigation (PointNav, ObjectNav) in photorealistic indoor scans. Success weighted by Path Length (SPL) is the headline metric. Strongly sim-flavored; transfer to real robots is an open question.

What BARN gets right is the thing most navigation "benchmarks" get wrong: identical hardware, identical compute budget, unseen test environments. If you are building an AMR nav stack, running it through BARN environments in sim is a cheap and genuinely informative stress test - see [Trajectory Planning](../mobile-robotics/trajectory-planning.md) for the planner side.

## Metrics cheat sheet

The numbers you will be asked to report, in one table:

| Metric | Domain | What it measures | Gotchas |
| --- | --- | --- | --- |
| **ATE** (Absolute Trajectory Error) | SLAM | RMSE of pose error after aligning estimate to ground truth | Alignment method (SE(3) vs Sim(3) vs SE(2)) changes the number; monocular SLAM *must* use Sim(3). Dominated by loop-closure quality |
| **RPE** (Relative Pose Error) | SLAM / odometry | Drift over fixed time/distance deltas | The honest odometry metric; report both ATE and RPE, they answer different questions |
| **mAP** | 2D/3D detection | Mean average precision over classes at IoU thresholds | COCO mAP averages IoU 0.5:0.95; older papers report mAP@0.5 only - numbers are not comparable |
| **NDS / APH** | AV 3D detection | mAP composited with translation/orientation quality (nuScenes); heading-weighted AP (Waymo) | Designed because plain mAP ignores orientation, which matters when predicting where a car is going |
| **Success rate** | Manipulation / navigation | Fraction of trials achieving the goal | Meaningless without trial count and confidence intervals; ~20-50 trials per condition is the floor for a believable claim |
| **SPL** | Embodied navigation | Success weighted by path efficiency | Penalizes wandering; standard in Habitat, rare on real robots |

Two habits worth stealing from the SLAM community: always state your alignment and your tooling (`evo` has become the standard precisely so numbers are comparable), and always report distributions, not just means - a policy with 80% success and violent failures is worse than one at 75% that fails gently.

And a minimal reporting checklist that will save you from the most common reviewer (or teammate) objections:

1. Name the exact dataset version and split - "KITTI" alone is ambiguous, "KITTI odometry sequences 00-10" is not.
2. State the metric definition and any alignment/threshold choices.
3. Give trial counts and variance for anything stochastic - one seed is an anecdote.
4. Report compute and latency alongside accuracy if the system is meant to run on a robot. A detector at 2 Hz is a different product than the same detector at 30 Hz.

## Where to go next

* [Robot Learning - Datasets & Benchmarks](../robot-learning/datasets-and-benchmarks.md) - the full manipulation/VLA dataset survey this page summarizes.
* [SLAM Evaluation & Benchmarking](../slam-and-state-estimation/slam-evaluation.md) - ATE/RPE computed correctly, `evo` workflow, and the pitfalls that invalidate results.
* [BARN Challenge](../authors-projects/barn-challenge.md) - first-hand account of competing in the navigation benchmark mentioned above.
* [Foundation Models & VLAs](../robot-learning/foundation-models-vla.md) - what pretraining on these datasets actually produces.
