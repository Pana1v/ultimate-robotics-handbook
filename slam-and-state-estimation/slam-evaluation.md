---
icon: route
---

# SLAM Evaluation & Benchmarking

## Why evaluation is harder than people think

Every SLAM paper has a leaderboard. Every leaderboard has an asterisk. The reason: SLAM evaluation is *trajectory* evaluation against *ground truth*, and ground truth is hard.

This page covers:

* The canonical public datasets you should know.
* The metrics - ATE, RPE - and how to compute them correctly.
* `evo` (Grupp), the tool you actually use.
* Common pitfalls that turn a "we beat SOTA by 12%" result into "we forgot to align the trajectories."

If you publish a SLAM paper, your reviewers will check whether you ran on the right datasets with the right metrics aligned the right way. Get this part wrong and your contribution doesn't matter.

***

## The datasets

### KITTI Odometry - the autonomous-driving classic

Geiger, Lenz, Stiller, Urtasun (2013). [cvlibs.net/datasets/kitti](https://www.cvlibs.net/datasets/kitti/) `[verify]`.

* 22 sequences (11 with ground truth, 11 held out for the test server) of car-mounted stereo cameras + Velodyne HDL-64E + GPS/IMU through Karlsruhe.
* The reference benchmark for any LiDAR or visual SLAM that wants to be taken seriously in 2014-2020.
* Trajectory lengths ~0.5-5 km, urban + highway + residential.
* Ground truth: GPS/IMU post-processing (RTK), accurate to ~10 cm.

What it's good for: urban autonomous-driving SLAM, baseline against LOAM family, ORB-SLAM.

What it's not good for in 2026: it's solved. The leaderboard is saturated. Real challenges have moved elsewhere.

### TUM RGB-D - indoor visual SLAM

Sturm, Engelhard, Endres, Burgard, Cremers (2012). [cvg.cit.tum.de/data/datasets/rgbd-dataset](https://cvg.cit.tum.de/data/datasets/rgbd-dataset) `[verify]`.

* Indoor scenes captured with a Kinect (RGB-D), pose ground truth from a motion-capture system.
* Sequences range from "desk" (small, easy) to "long\_office" (drift-test) to "structure\_texture\_far" (hard).
* The de facto benchmark for RGB-D visual SLAM. Every dense-SLAM / neural-SLAM paper since NICE-SLAM reports on TUM.

What it's good for: indoor RGB-D SLAM, dense reconstruction.

What it's not good for: anything outdoor, anything with aggressive motion, anything LiDAR.

### EuRoC MAV - drone VIO benchmark

Burri et al. (2016). [projects.asl.ethz.ch/datasets/euroc](https://projects.asl.ethz.ch/datasets/doku.php?id=kmavvisualinertialdatasets) `[verify]`.

* Stereo visual + IMU, ground truth from Vicon (machine hall) or laser tracker (Vicon room).
* Sequences split by difficulty: easy / medium / hard. Hard = aggressive 6-DoF maneuvers.
* The benchmark for VIO. VINS-Mono, OKVIS, ORB-SLAM3 VI all report here.

What it's good for: visual-inertial odometry, aggressive motion, drone use cases.

What it's not good for: long traverses (the dataset is sub-100 m), LiDAR (no LiDAR in the sensor suite).

### Newer College - outdoor LiDAR-VIO

Ramezani et al. (2020), University of Oxford. [ori-drs.github.io/newer-college-dataset](https://ori-drs.github.io/newer-college-dataset/) `[verify]`.

* Handheld and quadruped sensor rig: Ouster OS0/OS1 LiDAR + stereo + IMU.
* Sequences across Oxford's New College quad - indoor + outdoor mix, structured + organic geometry.
* Ground truth: high-precision GNSS-INS post-processing.

What it's good for: outdoor LiDAR-VIO, robust SLAM in mixed environments, modern benchmark beyond KITTI.

### Hilti SLAM Challenge - the hardest public benchmark

Hilti + ETH + Oxford. Annual since 2021. [hilti-challenge.com](https://hilti-challenge.com/) `[verify]`.

* Construction-site sensor rig: 3D LiDAR + multiple cameras + IMU + GNSS.
* Real construction sites: stairwells, scaffolding, dust, dynamic objects, repetitive geometry.
* Ground truth from a survey-grade total station tracking the rig.
* Leaderboard competitive - typically 30-50 entries per year.

What it's good for: the hardest publicly available SLAM, *if* you want to publish against a 2026-era benchmark and not look two years out of date.

### Other datasets worth knowing

* **ICL-NUIM** (Handa et al. 2014) - synthetic indoor RGB-D with perfect ground truth. Good for noise-free baselines and dense reconstruction comparisons.
* **MH-LiDAR / MulRan** - South Korean urban LiDAR with global descriptors for place recognition. Heavy revisits - great for testing loop closure.
* **SubT (DARPA Subterranean Challenge) datasets** - tunnels, urban, cave. Hard for everything.
* **M2DGR / M2DGR-Plus** - multi-modal multi-platform Chinese campus dataset, 2022+.
* **Replica** (FAIR 2019) - high-quality synthetic indoor for neural-SLAM evaluation.
* **ScanNet / ScanNet++ / ScanNet200** - indoor RGB-D for neural / dense SLAM.

***

## Metrics - ATE, RPE, and pitfalls

### Absolute Trajectory Error (ATE)

After aligning the estimated trajectory to ground truth (more on alignment below), compute, for each timestamped pose:

$$
F_i = Q_i^{-1} \mathbf{T} P_i
$$

where $P_i$ is the estimated pose, $Q_i$ the ground-truth pose, and $\mathbf{T}$ the alignment transform. ATE is then the RMSE of the translation part of $F_i$ over the trajectory:

$$
ATE_{rmse} = \sqrt{ \frac{1}{N} \sum_i \| \mathrm{trans}(F_i) \|^2 }
$$

ATE captures the *global* trajectory accuracy - how close the estimated path is to the truth in absolute terms. It's dominated by drift accumulation. A SLAM with good loop closure will have much lower ATE than the same SLAM without.

### Relative Pose Error (RPE)

For a time window $\Delta$ (e.g., 1 m or 1 s):

$$
E_i = (Q_i^{-1} Q_{i+\Delta})^{-1} (P_i^{-1} P_{i+\Delta})
$$

RPE is the RMSE of translation and rotation parts of $E_i$ over the trajectory.

RPE captures the *local* accuracy - how well does the SLAM estimate motion between two nearby times. RPE is approximately invariant to drift; it measures the odometry quality, not the loop closure.

Both metrics are reported by virtually every modern SLAM paper. The convention is:

* **ATE for global accuracy.** When you want to know "did this SLAM produce a globally consistent map?" - ATE is your answer.
* **RPE for local accuracy.** When you want to know "is the front-end / odometry good?" - RPE.

### Trajectory alignment - the bit everyone gets wrong

Before you compute ATE, you have to *align* the estimated trajectory to ground truth. Three modes:

* **SE(3) alignment** - find the rigid 6-DoF transform that minimizes ATE. Standard for stereo / RGB-D / LiDAR SLAM (with known scale).
* **Sim(3) alignment** - also estimate a global scale. Required for *monocular* SLAM, which is scale-ambiguous. Reporting "ATE" on monocular without Sim(3) alignment is meaningless.
* **Per-segment alignment** - re-align every $k$ meters / seconds. Effectively reports something between ATE and RPE.

Two common alignment errors:

1. Reporting raw ATE on monocular SLAM (without Sim(3)) - your scale is arbitrary, so ATE means nothing.
2. Reporting Sim(3) ATE on stereo / RGB-D / LiDAR - you're hiding scale error that the system was supposed to estimate correctly.

Pick the alignment that matches what your system *is supposed to estimate*.

***

## evo - the tool

Michael Grupp's `evo` library is what everyone uses. Repo: [github.com/MichaelGrupp/evo](https://github.com/MichaelGrupp/evo) `[verify]`.

`pip install evo` and you have:

* `evo_ape` - Absolute Pose Error (ATE).
* `evo_rpe` - Relative Pose Error.
* `evo_traj` - visualize, summarize, convert trajectory files.
* `evo_res` - compare results across runs.
* Support for KITTI, TUM, and bag formats out of the box.

Typical usage:

```bash
# Align and compute ATE with Sim(3) for monocular SLAM
evo_ape tum ground_truth.txt estimated.txt -a -s --plot --save_results result.zip

# RPE with 1 m windows for LiDAR odometry
evo_rpe kitti ground_truth.txt estimated.txt -d 1 -u m --plot
```

The flags matter:
* `-a` - SE(3) alignment.
* `-s` - also estimate scale (Sim(3) alignment). Use for monocular.
* `-d` and `-u` - RPE window size and unit.
* `--plot` - open matplotlib plots; otherwise it runs headless.

> **Field notes:** save your `evo` zip files. When a reviewer asks "did you align with scale?" or "what was the RPE window?" - the zip has all the metadata. I've been burned by re-running an experiment six months later and forgetting which alignment mode I used.

***

## Common pitfalls in SLAM benchmarking

A list of things that have either bitten me or that I've seen in published papers.

### 1. Timing offset between estimated and ground truth

Your SLAM's poses are timestamped. Ground truth is timestamped. If they're off by 50 ms (common - different clocks, no PTP sync), then for fast motion the "alignment" is fitting a constant time offset rather than evaluating accuracy. `evo` has a `-t` flag for time alignment; use it carefully.

### 2. Pose vs body vs sensor frame

KITTI poses are in the *camera* frame. Your SLAM might publish poses in the *base\_link* or *LiDAR* frame. ATE will be artificially inflated by the extrinsic offset. Always convert to a common frame before comparing.

### 3. Failed sequences not reported

If your SLAM diverges on 2 of 11 KITTI sequences, you report numbers on the other 9 and say "comparable to SOTA on the sequences where our method runs." This is *common* in papers. Always demand: what fraction of sequences ran to completion? What was the failure mode?

### 4. Picking only the runs that worked

SLAM is stochastic (sometimes). Particle filters, random initialization, race conditions. If you run 10 trials and report only the best one, your reported ATE is not your *expected* ATE. Always report mean ± std over multiple seeds.

### 5. Loop closure inflation

A SLAM that closes the final loop *at the very last frame* will have a beautiful ATE. The intermediate trajectory might have drifted badly, but the alignment + loop closure puts the endpoint right. Always look at the trajectory plot, not just the number.

### 6. Train-test contamination in learned SLAM

Learned SLAM systems (DROID-SLAM, learned front-ends) are trained on subsets of these datasets. Make sure the evaluation sequences weren't in the training set. ScanNet and TUM RGB-D especially have this problem.

### 7. Computing ATE on a subset that's "interesting"

Some papers compute ATE only on the part of the trajectory where the system was tracking. Anything where tracking failed gets dropped. This systematically biases ATE downward. If your system failed for 30% of the sequence, *report that*.

### 8. Real-time but not really

A SLAM that reports 30 Hz might be running offline on a workstation with a fast SSD. "Real-time" should always be tested *online*, with a live data feed, on the hardware you actually intend to deploy on. The published numbers might be from a 64-core threadripper.

### 9. Benchmarking on your own data without disclosing how

Your warehouse SLAM beats LIO-SAM by 15% on your own dataset. Great. But did you tune your system on this dataset and use default parameters for LIO-SAM? Did you cherry-pick the run where your system worked? **Publish your data, your config files, and your evaluation scripts.** This is the single biggest robustness signal for SLAM contributions.

### 10. Compute / accuracy trade-offs not reported

A SLAM that gets 5% better ATE while using 4× the CPU is rarely an improvement in practice. Always report runtime + memory + CPU/GPU profile alongside accuracy.

***

## A reasonable evaluation protocol for a new SLAM

If you're building a new SLAM (or testing an existing one for your project), I'd run this:

1. **Sanity on a known-good system.** Run ORB-SLAM3 or LIO-SAM on TUM / EuRoC / KITTI and reproduce the published numbers. If you can't reproduce within 10%, your eval setup is broken.
2. **Your system on the same datasets.** Compare like-for-like. Same alignment, same metric, same trajectory length.
3. **Multiple seeds.** Report mean ± std.
4. **Real-time profile.** CPU usage, memory, latency. Measured on the deployment hardware, not a workstation.
5. **Your own data.** Whatever the public dataset doesn't capture about your use case (reflective floors, dust, dynamic forklifts, custom sensor rig) - record your own dataset with the best ground truth you can manage (total station, motion capture, GNSS-RTK).
6. **Ablations.** Turn off each component (loop closure, IMU, feature X). Show what each contributes.

> **Field notes:** if you're publishing, every reviewer will ask for ablations. Do them upfront. If you're shipping a product, ablations also tell you *what to cut if you need to run on less compute*. The component that costs 30% CPU and improves ATE by 2% is the one you remove first.

***

## Further reading

* Sturm, Engelhard, Endres, Burgard, Cremers (2012) - "A Benchmark for the Evaluation of RGB-D SLAM Systems." [IROS 2012](https://www.cvlibs.net/publications/Sturm2012IROS.pdf) `[verify]`. The TUM RGB-D paper; defined the ATE/RPE convention.
* Zhang & Scaramuzza (2018) - "A Tutorial on Quantitative Trajectory Evaluation for Visual(-Inertial) Odometry." [arxiv.org/abs/1810.08628](https://arxiv.org/abs/1810.08628) `[verify]`. The clearest tutorial on alignment, metrics, and pitfalls.
* `evo` documentation: [github.com/MichaelGrupp/evo/wiki](https://github.com/MichaelGrupp/evo/wiki) `[verify]`.

### Cross-references

* [Filter SLAM](filter-slam.md), [Graph SLAM](graph-slam.md) - what's being evaluated.
* [Visual SLAM](visual-slam.md), [LiDAR SLAM](lidar-slam.md), [Learned SLAM](learned-slam.md) - the systems benchmarked on the datasets above.
* [GO-SLAM (Pan's)](../authors-projects/go-slam.md) - benchmarked on KITTI sequences against ground truth as a from-scratch SLAM exercise.
