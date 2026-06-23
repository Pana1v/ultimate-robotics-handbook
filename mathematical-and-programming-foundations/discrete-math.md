---
description: Graphs, search, trees, state machines, and combinatorics - the discrete structures every robotics stack secretly runs on.
icon: diagram-project
---

# Discrete Mathematics & Graph Theory

## Why discrete math is the robotics math nobody teaches you

Robotics curricula drill linear algebra and calculus into you for years, and rightly so - kinematics and state estimation live there. But open up any deployed robot stack and the *structure* of the software is discrete: a TF tree, a pose graph, a costmap grid being searched by A\*, a behavior tree ticking at 10 Hz, a state machine guarding the e-stop. The continuous math fills in the edge weights; the discrete math decides what's connected to what.

I'd put it this way: continuous math tells you *where* the robot is, discrete math tells you *how the problem is organized*. You can survive with a fuzzy memory of the Jacobian chain rule. You cannot survive without knowing what a graph, a tree, and a search frontier are, because you'll be staring at them in `rqt_graph`, RViz, and your planner logs every single day.

This page is the working subset. No proofs, no pigeonhole-principle party tricks - just the structures that show up in real stacks and where they show up.

***

## Graphs: the data structure robots run on

A graph $$G = (V, E)$$ is a set of vertices and a set of edges connecting them. Directed or undirected, weighted or not. That's the whole definition, and it's everywhere:

| Robotics object             | Vertices              | Edges                                  | Type                |
| --------------------------- | --------------------- | -------------------------------------- | ------------------- |
| Pose graph (SLAM back-end)  | Robot poses           | Odometry + loop-closure constraints    | Sparse, weighted    |
| PRM roadmap                 | Sampled free configs  | Collision-free local connections       | Undirected, weighted |
| TF tree (`tf2`)             | Coordinate frames     | Rigid transforms                       | Directed **tree**   |
| ROS 2 node graph            | Nodes                 | Topics / services / actions            | Directed            |
| Occupancy grid for search   | Cells                 | 4- or 8-connectivity                   | Implicit, uniform   |
| Topological map             | Rooms / waypoints     | Traversability                         | Undirected          |

Three of these deserve a closer look.

**Pose graphs.** Modern SLAM is literally nonlinear least squares *on a graph* - poses are variable nodes, measurements are edges, and the sparsity of the information matrix is exactly the adjacency structure of the graph. That sparsity is the entire reason graph SLAM beat EKF-SLAM. The full story is in [graph-slam.md](../slam-and-state-estimation/graph-slam.md); I also built a pose-graph back-end from scratch in [GO-SLAM](../authors-projects/go-slam.md), which I'd recommend as an exercise to anyone - nothing teaches you graph sparsity like writing the solver yourself.

**TF trees.** `tf2` enforces that the frame graph is a *tree*: every frame has exactly one parent, no cycles. This is not pedantry - a tree guarantees a unique path (and therefore a unique composed transform) between any two frames. The moment two nodes publish conflicting parents for the same frame, you don't have a tree anymore and you get the classic "TF_REPEATED_DATA / jumping robot" symptoms. When you debug TF, you are debugging a graph-theory invariant.

**Roadmaps.** PRM-style planners reduce continuous motion planning to graph construction (sample, connect) plus graph search (below). Once the roadmap exists, every query is just shortest-path.

> **Field notes:** when a system misbehaves, my first instinct is to draw it as a graph - frames, nodes, topics, whatever. About half of "mysterious" robot bugs turn out to be a structural problem you can see instantly in the picture: a cycle where a tree was assumed, a disconnected component, two subgraphs running on different clocks.

***

## Graph search you will actually use

You need exactly three algorithms in muscle memory. Everything else is a variation.

| Algorithm | Edge weights | Heuristic | Complexity        | Use it for                                  |
| --------- | ------------ | --------- | ----------------- | ------------------------------------------- |
| BFS       | None (uniform) | No      | $$O(V + E)$$      | Reachability, flood fill, frontier exploration |
| Dijkstra  | Non-negative | No        | $$O(E \log V)$$   | Shortest path, all-goals cost fields (NavFn) |
| A\*       | Non-negative | Yes       | Same worst case, far fewer expansions | Single start-goal queries with a decent heuristic |

A\* is just Dijkstra with a priority bias: expand by $$f(n) = g(n) + h(n)$$, cost-so-far plus estimated cost-to-go. Two properties carry all the weight:

* **Admissible** $$h$$ (never overestimates) ⟹ A\* returns the optimal path.
* **Consistent** $$h$$ (triangle inequality) ⟹ no node is ever re-expanded.

On a grid, Euclidean distance is admissible and consistent, so A\* on a costmap is both correct and fast. Nav2's planners are exactly this family: NavFn runs Dijkstra/A\* on the global costmap, and the Smac planners run Hybrid-A\*-style search over motion primitives when you need kinematic feasibility.

Things that bite in practice:

* **Inflated heuristics** ($$f = g + \epsilon h$$) trade optimality for speed. Often the right trade on big maps - just know you made it.
* **8-connected grids with Euclidean $$h$$** produce paths that hug obstacles diagonally. That's the costmap inflation layer's job to fix, not the search's.
* **Replanning** - D\* Lite and friends reuse the previous search when a few edge costs change. Worth knowing they exist; rarely worth implementing yourself in 2026.

Don't just read this - run it. The [interactive widgets](../widgets/widgets.md) page has an A\*-vs-Dijkstra grid pathfinder where you can paint obstacles and watch the expansion frontiers side by side. Watching Dijkstra's circular wavefront versus A\*'s directed cone is worth a thousand words of Big-O.

***

## Trees, spanning structures, and sampling-based planners

A tree is a connected acyclic graph - $$n$$ vertices, $$n-1$$ edges, unique path between any pair. Robots are full of them:

* **TF trees** (above) - the acyclicity is the feature.
* **Search trees** - the explored portion of A\* with parent pointers *is* a tree; that's why path reconstruction is just "follow parents to the root."
* **RRTs** - Rapidly-exploring Random Trees grow a tree through configuration space by sampling a random point and extending the nearest tree node toward it. RRT\* adds rewiring so path cost converges toward optimal as samples increase. The RRT\* widget on the [widgets page](../widgets/widgets.md) lets you watch the rewiring happen - the moment a shorter branch steals children from a longer one is the whole algorithm.
* **Behavior trees** - next section.

The tree-vs-graph distinction maps cleanly onto the two big sampling-based planner families:

| Planner | Structure | Best for |
| ------- | --------- | -------- |
| RRT / RRT\* / RRT-Connect | Tree, single query | One-shot planning in high-DOF spaces (arms) |
| PRM / PRM\* | Graph (roadmap), multi-query | Static environments, repeated queries |

**Spanning trees** earn a mention for one practical reason: spanning-tree coverage (STC) algorithms, which drive a lot of cleaning and inspection robots, work by building a spanning tree over a coarse grid and circumnavigating it - guaranteed full coverage, no cell visited more than roughly twice. And in SLAM, spanning-tree-based graph sparsification (keep a max-weight spanning structure, drop weak edges) is a standard trick for long-term map maintenance.

Cluttered-navigation benchmarks like the [BARN Challenge](../authors-projects/barn-challenge.md) are a good sandbox for feeling the search-vs-sampling trade: grid search is reliable in tight 2D gaps where sampling planners waste samples, and the inflation/heuristic tuning matters more than the algorithm choice.

***

## State machines, boolean logic, and behavior trees

Every robot has a discrete control layer above the continuous one: idle → navigating → docking → charging → fault. Three formalisms compete for that job.

**Finite state machines (FSMs).** States, transitions, guards. Simple, analyzable, and fine up to ~10 states. Past that, the transition table grows roughly quadratically and every new feature means auditing every existing transition. SMACH-era ROS code is a museum of FSMs that grew until nobody dared touch them.

**Boolean logic** underpins the guards and the safety layer. Interlock conditions ("motion allowed = e-stop clear ∧ localization valid ∧ battery > threshold") are combinational logic, and writing them as explicit truth tables - or at least as a single pure predicate function - beats scattering `if` statements across five nodes. The discrete-math habit that pays off here is *minimization*: fewer, orthogonal conditions are auditable; twelve overlapping flags are not.

**Behavior trees (BTs)** won the modern argument, and Nav2 is the proof. A BT is a tree whose internal nodes are control flow (sequence, fallback/selector, parallel, decorators) and whose leaves are conditions and actions. The tree is *ticked* at a fixed rate; each node returns SUCCESS, FAILURE, or RUNNING. The killer features over FSMs:

* **Modularity** - subtrees compose; transitions are implicit in the structure, so adding a recovery behavior doesn't touch existing logic.
* **Reactivity** - a higher-priority condition node can preempt a running branch on any tick.
* **Data, not code** - Nav2's `bt_navigator` loads the tree from XML at runtime; the default `navigate_to_pose_w_replanning_and_recovery` tree wires planning, control, and recoveries without recompiling anything.

If you work with Nav2 at all, read the BT section of [nav2-deep-dive.md](../ros-2/nav2-deep-dive.md) - customizing that XML is the single highest-leverage Nav2 skill, and it's pure discrete math: you are editing a tree whose tick semantics you need to predict.

> **Field notes:** the most common BT bug I see is misunderstanding RUNNING propagation - someone puts a long-running action under a sequence and is surprised the earlier condition nodes get re-ticked (or don't, depending on reactive vs. non-reactive sequence). Trace the tick path by hand on paper once. It's a five-minute exercise that saves hours.

***

## Combinatorics and why planning blows up

The reason planning is hard is countable. Discretize each dimension of your configuration space into $$r$$ cells. The number of states is

$$
|S| = r^d
$$

exponential in dimension $$d$$. A 2D grid at $$r = 100$$ is $$10^4$$ cells - trivial. A 6-DOF arm at the same resolution is $$10^{12}$$. A 7-DOF arm plus a mobile base plus a gripper is beyond enumeration. This is the curse of dimensionality, and it's why:

* **Grid search owns low dimensions.** 2D/3D mobile-base planning: A\* and friends, done.
* **Sampling owns high dimensions.** RRT/PRM never enumerate the space; they're only *probabilistically complete* (probability of finding a path → 1 as samples → ∞), which is the price of escaping $$r^d$$.
* **Exact motion planning is provably hard** - the generalized piano mover's problem is PSPACE-hard. Nobody is going to fix this with a clever algorithm; you change the problem instead.

Two more combinatorial walls worth recognizing on sight:

* **Task sequencing is TSP-shaped.** Multi-goal inspection, drilling holes in a panel, multi-pick ordering - visiting $$n$$ goals optimally is the traveling salesman problem, NP-hard, with $$(n-1)!/2$$ tours. For $$n \lesssim 15$$ you can afford exact solvers (Held-Karp, or just OR-Tools); beyond that, take the 2-opt heuristic and move on.
* **Multi-robot anything multiplies state spaces.** Two robots with $$|S|$$ states each give a joint space of $$|S|^2$$. Coupled multi-agent path finding is NP-hard; practical fleets use decoupled planning (prioritized, or conflict-based search) precisely to dodge the product space.

The engineering takeaway: when a planning problem feels intractable, don't reach for more compute first. Reach for a *smaller graph* - coarser discretization, a topological layer over the metric map, motion primitives instead of raw cells, hierarchy instead of one flat search. Every successful planner in production is a combinatorics dodge.

***

## Where to go next

* [graph-slam.md](../slam-and-state-estimation/graph-slam.md) - pose graphs and factor graphs as nonlinear least squares; where the graph structure becomes the sparsity of your solver.
* [nav2-deep-dive.md](../ros-2/nav2-deep-dive.md) - graph search and behavior trees as deployed software: planners, costmaps, and the `bt_navigator` XML.
* [advanced-algorithms.md](advanced-algorithms.md) - the algorithmic toolbox beyond search: complexity, dynamic programming, and the data structures behind real-time robotics code.
* [widgets.md](../widgets/widgets.md) - run A\* vs Dijkstra and RRT\* interactively; ten minutes there beats re-reading this page.
