---
icon: trophy
---

# BARN Challenge 2026 — Mapless Navigation, Solo Submission

> IEEE ICRA BARN Challenge 2026. Clearpath Jackal, Gazebo, ROS 2. I built a **Breadcrumb Explorer** architecture (solo-developed) instead of the standard SLAM-based baselines — **mapless navigation without SLAM or laser odometry** in dynamic obstacle fields. First submission scored **0.3682 / 0.5** on the official leaderboard — the **highest score by an Indian team since the benchmark began in 2022**.

**Role:** Solo entrant
**Platform:** Clearpath Jackal in Gazebo + (later) physical hardware
**Stack:** ROS 2 `[verify Humble or Jazzy]`, custom Python/C++ stack
**Timeline:** Jan 2026 - Present
**Validation:** 300 randomly generated Gazebo courses, 76% zero-shot goal reach
**Finals:** Physical event in **Vienna**

***

## BARN Challenge background

The **B**enchmark **A**utonomous **R**obot **N**avigation Challenge (BARN) was created in 2022 by the LARG group at UT Austin (Xuesu Xiao, Peter Stone, et al.) to evaluate navigation in highly constrained, randomized environments — narrow gaps, tight corners, dense obstacles. The benchmark generates **300 procedurally varied Gazebo worlds** of increasing difficulty and scores each entry by:

* Whether it reaches the goal
* How fast it reaches the goal
* How safely it does so (collisions kill the run)

The metric is bounded between 0 and 0.5. A score of 0.5 means perfect, instant traversal across all 300 worlds with zero collisions. Scores above 0.3 are competitive — the leaderboard's top teams in past years have hovered around 0.4 - 0.45.

> **Why BARN matters:** real navigation stacks (Nav2, move_base, etc.) work great on the easy 70% of environments and fall apart on the long-tail 30% — narrow gaps, U-shapes, dead-ends in dynamic clutter. BARN is engineered specifically to expose that long tail.

***

## Why mapless — no SLAM, no laser odometry

Almost every BARN baseline runs the same template:

```
LiDAR → SLAM (Cartographer / SLAM Toolbox) → costmap → planner (DWA / TEB) → cmd_vel
```

This is the standard ROS navigation playbook. It works. It's also slow to start, sensitive to wheel-slip and IMU drift, and it accumulates state that's a liability when the environment changes between trials.

I chose to skip SLAM and laser odometry entirely for three specific reasons:

1. **The Jackal has terrible odometry in tight BARN courses.** Its skid-steer kinematics produce heavy wheel-slip during the kind of in-place rotations narrow gaps demand. Encoder-derived velocity diverges from true velocity by 20-40% during turns `[verify]`. SLAM that depends on `/odom` as a motion prior gets confused.
2. **BARN courses are static-within-trial but vary across trials.** Building a SLAM map is wasted work — you'll never see the same map again. A map-free policy generalizes across all 300 worlds with zero retraining.
3. **The 270° LiDAR coverage gap matters.** The Jackal's stock Hokuyo UST-10LX has a 270° field of view (not 360°). There's a 90° dead zone behind the robot. Any laser-based odometry has to handle this gap, which is a brittle problem.

So instead: **only the local LiDAR scan + IMU + a memory of where I've been in the odom frame**. No global map. No SLAM-derived pose. Just a fading trail of breadcrumbs.

***

## Breadcrumb memory algorithm

The core idea is borrowed loosely from how foraging insects mark territory — a pheromone trail that decays over time. In navigation terms:

1. As the robot moves, **drop a breadcrumb** in the odom frame at every fixed distance (e.g., 0.25 m).
2. Each breadcrumb stores its position, the timestamp it was dropped, and a flag for whether the trajectory it belongs to ended in success or failure.
3. When planning the next motion, **bias** the planner toward breadcrumbs labeled "tasty" (succeeded historically) and **away from** breadcrumbs labeled "stale" (led to a dead-end, oscillation, or collision recovery).

Pseudocode:

```python
class BreadcrumbExplorer:
    def __init__(self):
        self.crumbs = []   # list of (pos, t, label) tuples
        self.last_drop = None

    def on_odom(self, odom):
        if self.last_drop is None or dist(odom.pos, self.last_drop) > 0.25:
            self.crumbs.append(Crumb(pos=odom.pos, t=now(), label='neutral'))
            self.last_drop = odom.pos

    def label_recent_as(self, label, lookback_sec=2.0):
        """Called when we know the recent trajectory was good or bad."""
        cutoff = now() - lookback_sec
        for c in self.crumbs:
            if c.t > cutoff:
                c.label = label

    def planning_bias(self, candidate_pos):
        """Score adjustment for a candidate next position."""
        score = 0.0
        for c in nearby_crumbs(candidate_pos, radius=1.0):
            if c.label == 'tasty':
                score += weight_decay(c.t) * +1.0
            elif c.label == 'stale':
                score += weight_decay(c.t) * -2.0
        return score
```

The planner is a simple **sampling-based reactive local planner** — it draws N candidate motion primitives at each step, scores each by `(progress_toward_goal + breadcrumb_bias + obstacle_clearance)`, and executes the winner.

### Why this works on BARN

* **Tight corridors**: when the robot enters a U-shape that looks promising but is actually a dead-end, the recovery code labels that trajectory as stale. The *same* exploration on the next try (or after a failed forward attempt) immediately routes around it.
* **No SLAM means no state to corrupt**: even if odom drifts 30 cm over a 10 m run, the breadcrumb memory is locally self-consistent. The breadcrumbs drift with the robot.
* **Decay handles dynamism**: in BARN's dynamic-obstacle worlds, a "stale" label from 30 seconds ago is much less authoritative than one from 3 seconds ago. The decay function downweights old information automatically.

***

## Tasty vs stale trajectories

The labeling logic is the key learning signal. Without it, breadcrumbs are just a history — with it, they're a self-improving policy.

| Event | Label applied | Lookback window |
| --- | --- | --- |
| Reached goal | `tasty` | Entire trajectory |
| Reached a checkpoint (intermediate progress milestone) | `tasty` | Since last checkpoint |
| Oscillated in place (no progress for >3 s) | `stale` | Last 5 s |
| Triggered recovery behavior (e.g., backup-and-rotate) | `stale` | Last 3 s |
| Collided | `stale` | Last 2 s |

Labels are applied **retroactively** — the robot doesn't know at the moment of dropping a breadcrumb whether the path was good. It only knows in hindsight, once it sees the outcome.

This is functionally similar to Monte-Carlo style temporal-difference reinforcement, except all values are categorical (`tasty`, `stale`, `neutral`) and decay over time. No reward function. No neural network. No training phase.

> **Note:** because BARN restarts the world between trials, "memory across trials" only makes sense for repeated attempts on the *same* world. The decay constant is tuned so that breadcrumbs from the previous trial on the same world are still informative, but breadcrumbs from a different world (a different geometry) are quickly stale.

***

## Recovery from drift

The 270° sensor coverage gap means the robot is **blind behind itself**. Combined with skid-steer odometry that drifts 20-40% during sharp turns, you can imagine how this fails: the robot turns to clear an obstacle, the odometry says it turned 90° but actually it turned 75°, and now the breadcrumb map is rotated relative to reality.

Three pieces of the system handle this:

1. **IMU integration as the primary heading estimator.** The Jackal IMU is high-quality enough that yaw drift over a 30-second BARN run is well under 5°. I use IMU yaw and only use encoder yaw as a sanity check.
2. **Local scan-matching for short-horizon refinement.** Every 1 s, the latest LiDAR scan is matched against the scan from 1 s ago using a fast 2D ICP. The relative pose correction is folded back into the odom estimate as a soft prior.
3. **Breadcrumb pruning on disagreement.** If the IMU heading and odom heading disagree by more than 10° at any point, all breadcrumbs older than 3 seconds are downweighted (their decay is accelerated). The memory shrinks back to the local window where geometry is still trustworthy.

This is not as good as a full SLAM solution — but it's *good enough* for a 30-60 second BARN run, where the world is bounded and the planning horizon is short.

***

## Results

### First submission

| Metric | Value |
| --- | --- |
| Overall score | **0.3682 / 0.5** |
| Worlds solved (out of 300) | `[verify exact count]` |
| Zero-shot goal-reach rate | **76%** |
| Mean time-to-goal | `[verify]` |
| Collision rate | `[verify]` |
| Submission rank | Highest score by an Indian team since the benchmark began (2022) |

### Across the 300 randomized Gazebo courses

The breadcrumb explorer's 76% zero-shot goal-reach rate (no retraining, no per-world tuning) is the headline statistic. For comparison, vanilla Nav2 with DWA on the same courses lands in the 50-60% range `[verify]` — the gap is precisely on the long-tail "narrow gap + dead-end" worlds where map-free reactive planning has an inherent edge.

### Improvement over successive trials

Because the breadcrumb memory persists across trials on the same world, the score is *not* a one-shot measurement. On worlds where the first attempt fails, the system typically converges within 2-4 retries — labels accumulate, dead-ends get marked stale, and the explorer routes around them. This is the "learning-from-repetition" property that makes the architecture interesting beyond the BARN context.

***

## Roadmap to Vienna finals

The physical BARN finals are at ICRA 2026 in Vienna. Between now and then:

1. **Score floor:** push the simulated score from 0.3682 toward 0.40. The remaining ~25% of unsolved worlds are dominated by very narrow gaps (<1.2× robot width) where the reactive planner needs better sampling. I'm experimenting with directional motion primitive sets biased toward the goal direction.
2. **Speed:** the time-to-goal component of the score is currently dragged down by conservative velocity limits. I want to add a confidence-modulated speed controller — when breadcrumb labels are unanimous about a direction being tasty, push speed up; when labels are mixed, slow down.
3. **Hardware transfer:** Gazebo's LiDAR model is too clean. The real Hokuyo on the physical Jackal has more noise, dropouts on dark surfaces, and varying scan rates under battery droop. The first physical bring-up will tell me what survives.
4. **Recovery behaviors:** the current "stuck → backup-and-rotate" recovery is crude. A learned recovery policy (small policy network trained on simulated stuck states) could shave time on the hard worlds.
5. **Submission cycle:** the BARN leaderboard updates monthly `[verify]`. I'm targeting one submission per month with measurable improvements until the finals.

***

## Why I'm writing this up

There's a school of thought in robotics that says "you have to use SLAM, otherwise you're not doing serious navigation." This project is a small piece of evidence against that. For a class of problems — bounded environments, short-horizon planning, repeated trials with feedback — **map-free reactive policies with a learned memory beat map-based stacks on both speed and robustness**.

I'm not claiming this generalizes to large-scale warehouse navigation (it doesn't — see [Polka](polka.md) and [GO-SLAM](go-slam.md) for what I actually use at production scale). But the BARN benchmark is engineered to be a worst-case for map-based methods, and a best-case for what the breadcrumb explorer does well.

***

## Find me online

[panav.netlify.app](https://panav.netlify.app) · [github.com/Pana1v](https://github.com/Pana1v) · [linkedin.com/in/panavraaj](https://linkedin.com/in/panavraaj)
