---
description: The algorithms robots actually run - spatial indexing, nearest-neighbor search, heuristic and sampling-based planning, dynamic programming, and real-time complexity.
icon: code-branch
---

# Advanced Algorithms

## Beyond LeetCode: the algorithms robots actually run

Interview prep teaches you to reverse linked lists. Robotics will never ask you to. What it asks instead, constantly:

* **"Which of these 100k points is closest to this one?"** - nearest-neighbor search, the inner loop of every ICP variant and every costmap lookup.
* **"What's the shortest path through this grid, and can you update it when the map changes?"** - heuristic search and incremental replanning.
* **"Find me *any* collision-free path through a 7-DoF configuration space"** - sampling-based planning, because grids die above ~4 dimensions.
* **"What's the optimal action from every state?"** - dynamic programming, which is the skeleton inside both Dijkstra and modern RL.

The common thread: all of these run inside a control loop with a deadline. An algorithm that is asymptotically optimal but misses its 20 ms budget is worse than a greedy hack that always answers in 5 ms. That tension - optimality vs. bounded time - is the actual subject of this page.

***

## Spatial data structures: KD-trees, octrees, voxel hashing

Every perception and mapping pipeline is built on one of three structures. Know all three and when each wins.

**KD-trees** recursively split space along axis-aligned hyperplanes. Build in $$O(n \log n)$$, query in $$O(\log n)$$ average for low dimensions. The workhorse implementation in C++ is [nanoflann](https://github.com/jlblancoc/nanoflann) - header-only, fast, used by half the SLAM systems on GitHub. Two caveats that bite in practice:

1. **They're static.** Inserting points degrades balance; the textbook answer is "rebuild," which is fine offline and brutal at sensor rate. The engineering fix is the **ikd-Tree** (Cai, Xu, Zhang 2021) - incremental insert/delete/rebalance in one structure. This single data structure is arguably the reason FAST-LIO2 runs on one CPU core.
2. **They die in high dimensions.** Beyond roughly 15-20 dimensions, backtracking visits most of the tree and you're doing brute force with extra steps. For descriptor matching (128-d+) use approximate methods (FLANN's randomized trees, HNSW) instead.

**Octrees** recursively split 3D space into 8 children. The classic robotics use is [OctoMap](https://octomap.github.io/): probabilistic occupancy at multiple resolutions, with unknown space explicitly represented. Great for mapping and collision queries ("is this 0.5 m box free?"), mediocre for nearest-neighbor - a KD-tree beats it for NN almost always.

**Voxel hashing** skips the tree entirely: hash the integer voxel coordinate into a flat hash map. $$O(1)$$ insert and lookup, no rebalancing, memory proportional to *occupied* space only. This is what modern LiDAR odometry actually uses - KISS-ICP keeps its local map in a voxel hash with a handful of points per voxel, and the VDB family (OpenVDB, nvblox) is the same idea industrialized for TSDFs.

| Structure | Insert | NN query | Memory | Use it for |
| --- | --- | --- | --- | --- |
| KD-tree (static) | rebuild | $$O(\log n)$$ | tight | one-shot registration, fixed maps |
| ikd-Tree | $$O(\log n)$$ amortized | $$O(\log n)$$ | tight | odometry local maps at sensor rate |
| Octree (OctoMap) | $$O(\log n)$$ | poor | compact, multi-res | occupancy mapping, box collision queries |
| Voxel hash | $$O(1)$$ | $$O(1)$$ to ~27 neighbor voxels | occupied-only | LiDAR odometry maps, TSDF fusion |

My default in 2026: voxel hash for anything that updates at sensor rate, KD-tree for anything static, octree only when I genuinely need the unknown-space semantics.

***

## Nearest-neighbor search and the inner loop of ICP

ICP is covered properly in [LiDAR SLAM](../slam-and-state-estimation/lidar-slam.md), but here's the algorithmic skeleton: every iteration finds, for each of ~10k-100k source points, its nearest neighbor in the target. The alignment math (SVD or a small Gauss-Newton solve) is nearly free by comparison. **Correspondence search is 80-90% of ICP's runtime**, which means your registration speed is a data-structure decision, not a math decision.

Three practical consequences:

* **Approximate is fine.** ICP correspondences are wrong at the start anyway - that's why it iterates. An approximate NN that returns *a* close point instead of *the* closest point barely changes convergence. Don't pay for exactness the algorithm doesn't need.
* **Amortize the build.** Scan-to-map ICP queries the same target map for many iterations across many scans. An incremental structure (ikd-Tree, voxel hash) that persists across scans beats rebuilding a perfect KD-tree every frame.
* **Voxel-hash correspondences are often enough.** Look up the query point's voxel plus its 26 neighbors, take the best point found. Constant time, cache-friendly, and the basis of KISS-ICP's speed.

When I built [GO-SLAM](../authors-projects/go-slam.md) - a from-scratch GICP + pose-graph pipeline - the first working version spent most of its frame time in correspondence search. Every meaningful speedup came from the NN layer, none from the solver. That experience generalizes: if your registration is slow, profile the NN search before touching the optimization.

***

## Heuristic search: A* variants, anytime planners, D* Lite for replanning

A* is Dijkstra plus an admissible heuristic: expand nodes by $$f(n) = g(n) + h(n)$$. If $$h$$ never overestimates, the result is optimal. On a 2D costmap with an L2 heuristic, this is fast enough that you rarely need anything cleverer for global planning. Nav2's planners are exactly this family - NavFn (Dijkstra/A* on the grid) and the Smac planners (Hybrid-A* and state lattice for car-like kinematics, where node expansion follows feasible motion primitives instead of grid edges).

The variants worth knowing:

* **Weighted A*** - inflate the heuristic: $$f = g + w \cdot h$$ with $$w > 1$$. You lose optimality but gain a *bounded* suboptimality (cost ≤ $$w$$ times optimal) and the search gets dramatically greedier and faster. This one-line change is the highest value-per-effort trick in search.
* **ARA*** (Anytime Repairing A*, Likhachev et al.) - start with large $$w$$, get a feasible path fast, then decrease $$w$$ and reuse previous search effort to refine. The right shape for planning under a deadline: you always have *some* answer, and it improves if time allows.
* **D* Lite** (Koenig & Likhachev 2002) - incremental replanning. When edge costs change (an obstacle appears in the costmap), it repairs only the affected part of the search instead of replanning from scratch. The win is real when changes are local and the map is big; for small grids (~200x200), honestly, replanning A* from scratch is so cheap that D* Lite's bookkeeping isn't worth it. Measure before committing.

***

## Sampling-based planning: RRT, RRT*, PRM

Grid search dies with dimension: a 7-DoF arm at 1° resolution is ~$$360^7$$ cells. Sampling-based planners sidestep this by never discretizing - they sample random configurations, keep the collision-free ones, and connect them.

* **RRT** grows a tree from the start: sample a random configuration, extend the nearest tree node toward it, repeat. Probabilistically complete (finds a path if one exists, eventually), but the paths are jagged and arbitrarily suboptimal. Fast at finding *a* solution.
* **RRT*** adds rewiring: when adding a node, check nearby nodes and reconnect them through the new node if that lowers their cost. Asymptotically optimal - the path converges to optimal as samples → ∞. The catch: convergence is slow, and the NN queries for rewiring (note: spatial data structures again) dominate runtime. **Informed RRT*** prunes sampling to the ellipsoid that could improve the current solution, and **BIT*** batches samples with a heuristic ordering - both converge much faster in practice.
* **PRM** (Probabilistic Roadmap) is the multi-query answer: sample and connect a roadmap *offline*, then answer many start/goal queries with cheap graph search on it. Right choice when the environment is static and you plan repeatedly in it - a workcell manipulator, not a mobile robot in a warehouse.

| Planner | Optimal? | Best for |
| --- | --- | --- |
| RRT | No | Fast feasibility in high-DoF spaces |
| RRT* / Informed RRT* / BIT* | Asymptotically | When path quality matters and you have ~100 ms+ |
| PRM | Asymptotically (PRM*) | Static environments, many queries |
| Hybrid-A* / lattice | Resolution-optimal | Car-like kinematics, 2D-3D state spaces |

Two things every newcomer misses. First, the sampling-based output is a *path*, not a trajectory - it has no timing, and feeding raw RRT waypoints to a controller produces robot dance. Smoothing and time-parameterization are mandatory; that's the subject of [Trajectory Planning](../mobile-robotics/trajectory-planning.md). Second, in low dimensions (2D-3D mobile robots), search-based planners usually beat sampling-based ones - sampling earns its keep above ~4-5 DoF.
***

## Dynamic programming and value iteration

Dynamic programming is the principle underneath half this page: optimal solutions decompose into optimal sub-solutions. Dijkstra is DP on a graph. The Bellman equation is DP on an MDP:

$$
V_{k+1}(s) = \max_a \sum_{s'} P(s' \mid s, a)\left[ R(s,a,s') + \gamma V_k(s') \right]
$$

**Value iteration** just sweeps this update over all states until convergence, then the policy is the greedy argmax. Each sweep is $$O(|S| \cdot |A| \cdot |S'|)$$ where $$|S'|$$ is the number of reachable successors - cheap per state, but $$|S|$$ explodes exponentially with state dimension. Practically, exact value iteration tops out around 3-4 discretized state dimensions before the table stops fitting in anything.

Where you actually meet it in robotics:

* **Coarse global guidance** - a value function over a 2D grid is exactly the "potential field done right": no local minima, because it's globally optimal by construction.
* **As the ancestor of RL.** Q-learning is value iteration with sampled transitions instead of a known model; actor-critic methods are DP with function approximation standing in for the table. If value iteration makes sense to you, half of [modern RL](../robot-learning/reinforcement-learning-modern.md) is notation.
* **Trajectory optimization** - DDP/iLQR are local dynamic programming along a trajectory, which is how the idea survives in continuous high-dimensional spaces.

If you implement one algorithm from this page by hand, make it value iteration on a gridworld. It's ~40 lines of Python and it permanently demystifies the Bellman equation.

***

## Real-time budgets: complexity that matters at 50 Hz

Big-O analysis assumes $$n \to \infty$$. Your control loop assumes $$t \leq 20\,\text{ms}$$. These are different regimes, and the second one is where robots live.

A rough budget picture for a mobile robot stack:

| Loop | Rate | Budget | What runs there |
| --- | --- | --- | --- |
| Control | 50-100 Hz | 10-20 ms | controller step, costmap lookups, safety checks |
| Local planning | 10-20 Hz | 50-100 ms | DWA/MPPI rollouts, local trajectory optimization |
| Global planning | ~1 Hz / on demand | ~1 s | A*, RRT*, value sweep |
| Mapping / SLAM | 1-10 Hz | 100 ms-1 s | registration, pose-graph optimization |

Hard-won rules for staying inside those budgets:

1. **Constants beat asymptotics at robot scale.** At $$n \approx 10^4$$, a cache-friendly $$O(n)$$ scan over a flat array routinely beats an $$O(\log n)$$ pointer-chasing tree. Profile before believing the textbook.
2. **Never allocate in the loop.** Preallocate buffers, `reserve()` vectors, avoid `std::map`/`std::list` in hot paths - every node is a heap allocation and a cache miss.
3. **Worst case is the only case.** A planner that averages 8 ms but spikes to 80 ms at the worst possible moment - the cluttered corner, the doorway - fails exactly when it matters. Bound the worst case (iteration caps, anytime cutoffs) and accept the suboptimal answer.
4. **Prefer anytime algorithms at the boundary.** ARA*, RRT* and MPPI all share the property that interrupting them yields a valid (if suboptimal) answer. That property is worth more than optimality in any loop with a deadline.

My [BARN Challenge](../authors-projects/barn-challenge.md) entry drove this home: in dense randomized obstacle fields, the navigation stack lives or dies on whether the tight loop *always* produces a sane command in time, not on whether the path was optimal. Optimality is a luxury; latency is a constraint.

***

## Where to go next

* [LiDAR SLAM](../slam-and-state-estimation/lidar-slam.md) - see KD-trees, ikd-Tree, and voxel hashing earning their keep inside real registration pipelines.
* [Trajectory Planning](../mobile-robotics/trajectory-planning.md) - turning planner paths into time-parameterized trajectories a controller can actually follow.
* [Modern RL](../robot-learning/reinforcement-learning-modern.md) - where value iteration goes when the state space stops fitting in a table.
