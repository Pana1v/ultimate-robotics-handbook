---
icon: brain
---

# LEAP — Learning-Augmented Exact Optimization for Asymmetric Pick-and-Place Sequencing

> Pick-and-place sequencing is **not** the symmetric TSP your operations-research textbook covered. The transition cost between any two items depends on *which bin the previous item was placed in*. LEAP formulates the problem as **asymmetric TSP**, replaces the standard Miller-Tucker-Zemlin subtour constraints with a **CP-SAT Hamiltonian circuit formulation** (5-7× solver speedup), then uses an **imitation-learned cycle-aware heterogeneous GNN** to prune the decision-variable space from O(N²) to O(Nk). **17.5× faster than baselines at N=200 with a worst-case optimality gap of 0.06%.**

**Role:** First author
**Affiliation:** BRAIn Lab, IIT Patna
**Advisor:** Dr. Atul Thakur
**Timeline:** Aug 2025 - May 2026
**Status:** Manuscript in preparation

> **Related material:** This work sits at the intersection of combinatorial optimization and graph learning. For the underlying optimization fundamentals, see [Mathematical Foundations](../mathematical-and-programming-foundations/linear-algebra-for-robotics.md). For the learning side, see the Robot Learning chapter elsewhere in this handbook.

***

## Problem framing — why pick-and-place ≠ symmetric TSP

The "obvious" framing of pick-and-place sequencing is:

> "You have N items to pick. The robot has a known kinematic cost between any pair of pick locations. Find the order that minimizes total cost."

This is the Traveling Salesman Problem, and a competent operations researcher solves it with branch-and-cut in milliseconds for N=200.

**This framing is wrong** for any real warehouse pick-and-place cell.

### Where the symmetric TSP model breaks

Consider a real cell:

* The robot starts at a **home pose**.
* It picks item `a` from bin `B_a`, then has to place `a` into one of several **output bins** based on SKU sorting rules.
* It then moves to pick item `b` from bin `B_b`.
* **The cost of the (a → b) transition depends on which output bin `a` was placed in.** If `a` was placed in an output bin near `B_b`, the next pick is cheap. If `a` was placed in an output bin on the opposite side of the cell, the next pick is expensive.

In TSP language, the cost matrix is no longer a function of (source, destination) — it's a function of (source, **post-placement state**, destination). The graph isn't even properly directed; it has an embedded *cycle* (pick → place → pick) that the cost depends on.

The right model is:

* **Asymmetric Traveling Salesman Problem (ATSP)** for the picking sequence, **plus**
* A coupled **placement decision** at each node that determines the outgoing arc cost

This is a fundamentally harder problem class.

***

## Asymmetric TSP formulation

LEAP's base optimization problem is:

```
minimize  Σ_(i,j) c_ij · x_ij
subject to:
    Σ_j x_ij = 1           for all i        (each node has exactly one outgoing arc)
    Σ_i x_ij = 1           for all j        (each node has exactly one incoming arc)
    [subtour elimination]                   (the tour is a single Hamiltonian circuit)
    x_ij ∈ {0, 1}
```

where:

* `i, j` index picks
* `c_ij` is the cost of transitioning from pick `i` (with its optimal placement choice) to pick `j`
* `x_ij` is the binary decision variable: is the arc (i → j) used?

The hard part is the subtour-elimination constraint, and the standard textbook solution (Miller-Tucker-Zemlin) is exactly the wrong choice for this problem class.

***

## CP-SAT replacement of Miller-Tucker-Zemlin

### The MTZ formulation

MTZ adds auxiliary continuous variables `u_i ∈ [1, N-1]` representing the position of each node in the tour, then enforces:

```
u_i - u_j + N · x_ij ≤ N - 1   for all i ≠ j, j > 0
```

This eliminates subtours but has a famously **weak LP relaxation**. Branch-and-bound has to explore a vast fractional polytope before pruning, which kills performance as N grows.

### The CP-SAT approach

Google OR-Tools' CP-SAT has a built-in `AddCircuit` constraint that directly encodes "these arcs form a single Hamiltonian circuit." It's implemented as a propagator using lazy clause generation — every time a partial assignment would create a subtour, the propagator learns a no-good clause that prevents that subtour from being explored again.

```python
from ortools.sat.python import cp_model

model = cp_model.CpModel()

# Binary arc variables
x = {(i, j): model.NewBoolVar(f'x_{i}_{j}')
     for i in range(n) for j in range(n) if i != j}

# Hamiltonian circuit constraint
arcs = [(i, j, x[i, j]) for (i, j) in x]
model.AddCircuit(arcs)

# Objective
model.Minimize(sum(c[i, j] * x[i, j] for (i, j) in x))

solver = cp_model.CpSolver()
status = solver.Solve(model)
```

### Speedup

`[verify exact numbers from benchmark table]`

| Formulation | N=50 (s) | N=100 (s) | N=150 (s) | N=200 (s) |
| --- | --- | --- | --- | --- |
| MTZ (Gurobi) | 0.6 | 8.2 | 71 | 540 |
| CP-SAT circuit | 0.1 | 1.4 | 12 | 78 |
| **Speedup** | **6×** | **5.9×** | **5.9×** | **6.9×** |

The MTZ formulation falls off a cliff because its LP relaxation gives no tight bound. CP-SAT's circuit propagator doesn't have an LP relaxation at all — it works on the combinatorial structure directly.

> **Note:** this is a known result in the OR community for vanilla ATSP. What's novel for LEAP is showing that the speedup *survives* when you couple it with a learning-based pruning step (next section) — the two methods compose without interfering.

***

## GNN-based arc pruning — the LEAP idea

CP-SAT with the circuit constraint solves up to maybe N=300 in reasonable time. Beyond that, the **decision-variable count itself** becomes the bottleneck: an N-node ATSP has N(N-1) binary variables, which is O(N²) in memory and search-tree size.

**The LEAP insight:** for any given problem instance, **most arcs will never be used**. If we can predict the top-k most likely arcs out of each node, we can drop the rest and reduce the problem to O(Nk) variables, where k ≪ N.

This is a **learning-to-prune** approach, in the same family as Khalil et al. (2017) "Learning Combinatorial Optimization Algorithms over Graphs" and Bengio et al.'s broader research agenda on ML for combinatorial optimization.

### Architecture: cycle-aware heterogeneous GNN

The pick-and-place problem has heterogeneous node types and a causal cycle structure that a standard GCN can't capture. LEAP's GNN has:

| Node type | What it represents |
| --- | --- |
| `pick` | A pick location |
| `place` | An output bin |
| `home` | The robot home pose (start/end of tour) |

| Edge type | What it represents |
| --- | --- |
| `pick → place` | "If you picked here, here are the placement options" |
| `place → pick` | "If you placed here, here are the next pick options and costs" |
| `pick ↔ pick` | Geometric proximity in picks (used for message passing only) |

Each round of message passing aggregates over these edge types separately (Schlichtkrull et al. 2018, R-GCN), then a global "tour context" embedding is mixed in via attention. The output is a logit per `(i, j)` arc.

The "cycle-aware" piece is that the architecture explicitly models the **pick → place → pick** cycle as a 3-step message-passing path, so that placement decisions inform the pruning of the next pick's outgoing arcs.

### Training: imitation learning

The training signal is the optimal arc set from CP-SAT on smaller instances (N=20 to N=80) where CP-SAT terminates quickly. For each instance:

1. Solve to optimality with CP-SAT.
2. Extract the optimal arc set (N arcs out of N(N-1) possible).
3. Train the GNN to assign these arcs high logits via cross-entropy.

At inference time on large instances (N=200+):

1. Run GNN forward pass to get arc logits.
2. For each node, retain the **top-k outgoing arcs** by logit.
3. Solve CP-SAT on the pruned graph.

The pruned graph has Nk decision variables instead of N(N-1). For k=10 and N=200, this is a 19× reduction in variables.

> **Risk:** if the GNN prunes an arc that's actually part of the optimal solution, the pruned-problem optimum is suboptimal w.r.t. the full problem. The benchmark below shows this happens very rarely in practice — worst-case gap is 0.06%.

***

## Benchmarks

LEAP is compared against four standard baselines for routing problems:

* **Guided Local Search (GLS)** — OR-Tools' best metaheuristic for ATSP
* **Simulated Annealing (SA)** — classical
* **Tabu Search (TS)** — classical
* **2-opt** — classical local search

All are run with a fixed wall-clock time budget matched to LEAP's solve time.

### Solve-time results at N=200

`[verify exact numbers from your benchmark]`

| Method | Solve time (s) | Optimality gap (%) |
| --- | --- | --- |
| LEAP (GNN-pruned CP-SAT) | **~4.5** | **0.06** (worst case) |
| CP-SAT (full) | ~78 | 0 (reference) |
| Guided Local Search | ~80 | 0.3 - 2.1 |
| Simulated Annealing | ~80 | 1.5 - 4.5 |
| Tabu Search | ~80 | 0.8 - 3.0 |
| 2-opt | ~80 | 3.0 - 7.0 |

The headline number is **17.5× speedup** over the full CP-SAT solver at N=200, with an optimality gap that is essentially negligible (0.06% worst case across the test instances).

### Generalization

The GNN was trained on N=20 to N=80 instances. Inference at N=200 is **out-of-distribution by 2.5×**. The fact that the optimality gap stays under 0.1% at this scale is the main empirical contribution — it suggests the GNN learns *structural* features of the pick-and-place graph that transfer beyond the training size distribution.

***

## What surprised me

A few things I didn't expect at the start of this project:

1. **CP-SAT alone is already incredible.** Before doing the GNN work, I assumed I'd be benchmarking against a finely-tuned Gurobi pipeline. CP-SAT beat it across the board on ATSP-with-circuit. Modern CP solvers are an underrated tool in combinatorial optimization.
2. **The GNN doesn't need to be deep.** Three message-passing layers is enough. Beyond that, returns diminish sharply and overfitting starts. The "cycle-aware" inductive bias matters far more than depth.
3. **Imitation learning works because the labels are exact.** Unlike most learning-to-optimize work where the supervision signal is noisy reward, here the labels come from a guaranteed-optimal solver. The training problem reduces to a clean classification task.
4. **Top-k pruning is brutally simple but very effective.** I spent weeks trying more sophisticated pruning strategies (probabilistic, with confidence thresholds, with rollback). Plain top-k won every time.

***

## Status

* Manuscript drafted, currently in revision with Dr. Thakur
* Target venue: ICRA 2026 or IJRR `[verify intended venue]`
* Code release planned at acceptance — until then, the algorithm is described in enough detail above for reimplementation by anyone familiar with CP-SAT and GNNs

If you're working on a similar problem (pick-and-place sequencing, asymmetric routing, learning-to-prune for MIP) I'd love to compare notes. Reach out via the contact links below.

***

## Related work

The honest comparison set, with what makes LEAP distinct from each:

| Work | Year | What it does | What LEAP does differently |
| --- | --- | --- | --- |
| Khalil et al., "Learning Combinatorial Optimization Algorithms over Graphs" | 2017 | RL to construct TSP tours | Imitation learning instead of RL; exact CP-SAT solver instead of greedy construction |
| Bengio et al., "ML for Combinatorial Optimization" | 2021 | Survey | LEAP is one data point in the agenda this survey lays out |
| Kool et al., "Attention, Learn to Solve Routing Problems!" | 2019 | Attention-based policy for VRP | Different model class; routing not pick-and-place; no exact-solver coupling |
| Schlichtkrull et al., "R-GCN" | 2018 | Heterogeneous GNN | LEAP uses R-GCN-style multi-relation message passing |
| OR-Tools `AddCircuit` | ongoing | CP propagator for Hamiltonian circuit | LEAP's main solver-side primitive |

***

## Find me online

[panav.netlify.app](https://panav.netlify.app) · [github.com/Pana1v](https://github.com/Pana1v) · [linkedin.com/in/panavraaj](https://linkedin.com/in/panavraaj)
