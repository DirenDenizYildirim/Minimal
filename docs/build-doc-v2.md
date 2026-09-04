# Minimal Swarms in Hostile Environments — Build Doc v2

**Changes from v1.** Idea A's terrain model replaced (v1's was a time-reparameterisation plus a Galilean shift; it could not deform one robot's path relative to another's). Idea B's pursuer given perception dials (v1's perfect-perception pursuer made aggregation the *worst* strategy). Capability accounting fixed (sensor states not bits, communication counted, ladder is a vector not a chain, optimiser-found minima are upper bounds). Occlusion dial promoted to the week-3 shakedown. Frontier figure replaced by a performance surface with threshold contours. Citations corrected. Venues updated for the ANTS calendar shift.

**Working thesis (unchanged).** Minimalist swarm robotics asks "what is the least sensing/compute/memory that produces behaviour X?" but answers it in flat, uniform, unthreatened arenas. We measure how that minimum *moves* under environmental hostility. Capability is the dependent variable; the environment is the independent one.

---

## 1. Literature — corrected and extended

### 1.1 Baselines (clean arenas, known minima)

| Work | Budget | Behaviour | Role here |
|---|---|---|---|
| Gauci, Chen, Li, Dodd, Groß (2014), IJRR — *Self-organized aggregation without computation* | 1 binary LOS sensor, no memory, no arithmetic; 4 wheel-speed constants | Aggregation | The anchor. Exhaustive grid search at 4 constants; proof for n=2; empirical to 1000. State-0 motion is a circle whose radius is the controller's only intrinsic length scale. |
| Gauci et al. (2014), AAMAS — *Clustering objects with robots that do not compute* | **Ternary** LOS sensor (nothing / robot / object) | Object clustering | Same hardware, three sensor states. This is exactly the sensor Idea B's "distinguish robot from pursuer" rung needs, so it is precedent, not a new capability. |
| Özdemir, Gauci, Groß (2017), **ECAL** — *Shepherding with robots that do not compute* | Ternary sensor, no memory | Shepherding | Only minimal result with a non-cooperating agent in the arena. Sheep are passive; ours pursue. |
| Özdemir, Gauci, Bonnet, Groß (2018), RA-L — *Finding consensus without computation* | Binary sensor | Collective decision | Program generalises beyond aggregation. |
| Daymude, Harasha, Richa, Yiu (2021), SSS — *Deadlock and noise in self-organized aggregation without computation* | Gauci's | Aggregation | Deadlock exists for n > 3 under deterministic uniform motion (**verify exact n before quoting**); collisions and slipping help avoid it in practice; tolerant of small sensor and motion noise. Built a discrete noisy variant amenable to analysis. Their argument leans on isotropy of the step distribution — that is what terrain breaks (§3, Idea A). |
| Johnson & Brown (2015), **EAI BICT** — perimeter, rendezvous, foraging in a computation-free swarm | Gauci family | Multiple | More behaviours, same budget. |
| Brown, Turgut, Goodrich — *Discovery and exploration of novel swarm behaviors given limited robot capabilities*, **DARS 2016 (Springer volume 2018)** | Constrained capability model | Exploratory | Capability-vector framing precedent. |
| Hamann (2018), *Swarm Robotics: A Formal Approach* | — | — | Mean-field models; assume homogeneous space. |

### 1.2 Prior art a reviewer will name

- **BEECLUST** (Schmickl, Kernbach, and colleagues, 2008–2009). Minimal robots aggregating in an explicitly non-uniform environment (light/temperature gradient). Must be cited and distinguished: in BEECLUST the heterogeneity is the *target* the swarm is meant to find; in ours it is a *perturbation* the swarm is meant to survive. Same mechanism class, opposite role.
- **Pursuit–evasion.** Chung, Hollinger & Isler (2011), *Search and pursuit-evasion in mobile robotics: a survey*, Autonomous Robots. Idea B sits at the minimal-sensing corner of this literature and should say so.
- **Predator confusion / selfish herd.** Olson, Hintze, Dyer, Knoester, Adami (2013), J. R. Soc. Interface — confusion is a property of the *predator's* perception: attack success falls with the number of prey in the predator's sensing field. Olson, Knoester, Adami (2016), Artificial Life. Wood & Ackland (2007), Proc. R. Soc. B.
- **Temporal vs spatial sensing.** Berg & Purcell (1977), *Physics of chemoreception*, Biophys. J. — at small scales, temporal comparison beats spatial comparison. This converts Idea D from speculation to a known principle being tested in robots.
- **Hunt (2020), Frontiers Robotics & AI** — phenotypic-plasticity position paper for minimal field swarms; argues early local sensory experience gives useful diversity "for free" including resistance to adversarial agents. Motivation citation; no experiments.
- **Automatic design (Birattari lab).** AutoMoDe injects design bias by restricting control software to combinations of predefined parametric modules, reducing variance and improving reality-gap transfer. Their protocol (ARGoS, ≥30 runs, Friedman + post-hoc, sim-vs-real) is the ANTS standard. Ligot & Birattari (ANTS 2018) on mimicking the reality gap with simulation-only perturbations.
- **Insider adversaries** (Byzantine robots in collective decision-making; FL poisoning in ROS2 swarms, 2026). Different problem — corrupting information rather than removing robots. Cite to distinguish.

### 1.3 The gap

No paper fixes a performance threshold, parameterises the environment along hostility axes, and reports how the capability minimum moves. Everything nearby either fixes capability and measures robustness, or fixes hostility at zero and measures minimality.

---

## 2. Framing

### 2.1 Capability vector

`c = (S, M, A, K)`:
- `S` — **sensor states per timestep**, not bits. Gauci = 2 states. AAMAS/ECAL ternary = 3. A tilt bit alongside a binary LOS = 2×2 = 4 states. Report states; report log₂ only as a secondary summary.
- `M` — persistent memory bits across timesteps.
- `A` — arithmetic flag (0 = pure lookup table).
- `K` — **communication bits broadcast per timestep**. Any "I can tell a neighbour is fleeing" cue is `K ≥ 1` on the sender and an extra sensor state on the receiver. It is not free and it is not sensing.

The capability ladder is a **set of vectors**, not a chain of supersets. Some rows are incomparable (2 extra sensor states vs 1 memory bit). That is fine; the surface handles it (§2.3).

### 2.2 Minima are upper bounds unless the search is exhaustive

Gauci's 4-constant grid is exhaustive at its resolution. At 8 constants the grid grows as resolution⁴; at PFSM budgets it is not enumerable at all. Wherever CMA-ES, simulated annealing, or AutoMoDe is used, "no controller found meeting T" means **not found**, not **not possible**. Consequences, stated in every paper up front:
- Every 2-bit row in Ideas A and B, and every frontier from Idea C, is an **upper bound** on `c*(θ)`.
- Only the Gauci row and any row we can enumerate at Gauci's resolution are tight.
- Report search budget per cell and, where feasible, run two independent optimisers and report agreement.

### 2.3 The figure

Not a one-step frontier. For each capability row, plot the **performance surface** over the hostility dial(s), then draw the threshold contour(s) `P = T` on it. Several contours (T = 0.7, 0.8, 0.9) on one panel show how the "minimum" depends on where you set the bar — which is the visual answer to "minimality is ill-defined." The frontier `c*(θ)` is then read off as the lowest row whose contour still encloses θ.

### 2.4 Environment dials

- `θ_occ` — occlusion: false-negative and false-positive rates on the LOS sensor, spatially correlated.
- `θ_terr` — terrain: heading-dependent speed on a slope + per-wheel friction field (§3A).
- `θ_pred` — pursuer: speed ratio ρ **and** perception (range, confusion, search) (§3B).

Task threshold `T` and metric are fixed per paper and pre-registered.

---

## 3. Project ideas

### Week-3 shakedown — occlusion (not a paper, a harness test)

Run before terrain. Question: at what false-negative rate does the zero-memory Gauci controller fall below T, and does one bit of hysteresis (`M = 1`: "saw a robot last step") restore it? Cheap, one dial, exercises the sweep harness, the surface plot, and the enumerable-vs-optimised distinction (the hysteresis row has 8 constants and is *not* exhaustively searchable at Gauci's resolution — good place to learn what "upper bound" costs in practice). If the result is clean it becomes one figure in Paper 1; if not, it was still the right test.

### Idea A — aggregation under terrain: what actually deforms the trajectory

**What was wrong in v1.** A scalar speed field `v(x,y)` scaling both wheels equally keeps the ICR fixed, so each robot still traces the same circle at a position-dependent rate — desynchronisation, not symmetry breaking. A constant drift vector is a Galilean shift: relative positions, headings, and every LOS reading evolve exactly as without it. Unbounded arena → no effect. Bounded arena → robots pile against the downhill wall and the wall aggregates them. H2 was false or an artefact, and "does the cluster slide downhill" was trivially yes.

**Corrected terrain model.** Per wheel `w ∈ {L, R}`:

```
v_w = v_cmd,w · m_w(x, y)  −  g_eff · sin(α) · (ĥ · ŝ)
```

- `m_w(x,y)` — per-wheel friction/traction multiplier from a smoothed random field (correlation length λ, amplitude θ_m); the two wheels sample the field at their own contact points so they generally differ → curvature changes → the state-0 circle becomes a distorted loop.
- `g_eff · sin(α) · (ĥ·ŝ)` — gravity component along the robot's heading `ĥ` on a slope of angle α with downhill direction `ŝ`. Speed depends on heading, so the circle is stretched downhill and compressed uphill (trochoid-like). This is what an e-puck on a tilted board physically does, so the hardware track tests the same model.
- Optional: per-wheel slip noise scaled by `|sin α|`.

Two dials: α (slope) and θ_m (friction heterogeneity), with λ reported. Arena unbounded (as Gauci's sim), metrics relative to swarm centroid so downhill translation is factored out.

**Hypotheses (revised).**
- H1: small α and θ_m help, as motion noise did in Daymude et al.
- H2: aggregation fails when the trajectory deformation over one state-0 circle exceeds a fraction of the **circle radius R₀** — i.e. the transition should scale with R₀, not with swarm scale. Test by sweeping the four constants (which change R₀) and checking the transition tracks R₀.
- H3: past the transition, a fifth sensor state (binary "on slope / not") with a second lookup row recovers T, whereas re-tuning the original 4 constants does not. The 8-constant row is an upper bound (§2.2).

**Analytic hook (revised).** Extend Daymude et al.'s discrete model with an **anisotropic step distribution** (heading-dependent step length), not a constant drift. Their proof leans on isotropy; the question is how much anisotropy the n=2 argument tolerates. A bound of the form "aggregation holds if the anisotropy ratio is below f(R₀, sensor range)" would be the theorem. A constant-drift model gives a trivial result and should not be attempted.

**Metrics.** Dispersion at τ (Gauci's), single-cluster fraction, time to single cluster — all in the centroid frame.

### Idea B — the pursuer with imperfect perception

**What was wrong in v1.** Nearest-target pursuit with perfect perception and unbounded range: a tight cluster minimises the pursuer's travel time between victims, so the blind aggregating baseline is the *worst* controller, not the protected one. Dilution protects individuals; the swarm-level survival metric doesn't see it. The time-to-capture hook had the same sign problem — smaller clusters die faster under that pursuer.

**Corrected pursuer family.** Three perception dials plus speed:
- `ρ` — speed ratio (pursuer / robot).
- `r_p` — pursuer sensing range. Finite range forces a **search phase** (random walk or spiral) when no robot is visible; time spent searching is time not capturing.
- `κ` — confusion: probability of a successful lock-on decays with the number of robots in the pursuer's sensing radius, e.g. `p_lock = 1 / (1 + κ·n_local)`, following the Olson et al. mechanism.
- Targeting rule as a categorical: nearest, fewest-neighbours (edge-picker), random-visible.

With `r_p` finite and `κ > 0`, aggregation has two mechanisms by which it *can* protect the swarm: fewer, harder-to-find targets (search cost) and lower lock-on probability. Whether it does, and at what `c`, is the experiment. With `r_p = ∞, κ = 0` we recover the v1 pursuer as the adversarial extreme — keep it as one corner of the sweep.

**Primary metric.** **Capture rate** (captures per unit time, normalised by swarm size) rather than survival at τ, because for ρ > 1 a targeted robot cannot escape and survival at τ collapses to a travel-time quantity. Secondary: base-task performance among survivors; Pareto front of capture rate vs task.

**Capability rows (a set, not a chain).**
| Row | S (states) | M | K | Meaning |
|---|---|---|---|---|
| B0 | 2 | 0 | 0 | Gauci, blind |
| B1 | 3 | 0 | 0 | Ternary LOS: nothing / robot / pursuer (AAMAS sensor) |
| B2 | 5 | 0 | 0 | Ternary + pursuer left/right half |
| B3 | 3 | 1 | 0 | Ternary + 1 bit "saw pursuer within last k steps" |
| B4 | 3 (recv) | 0 | 1 (send) | Binary LOS on robots + received alarm bit; sender broadcasts 1 bit when it is in state "pursuer seen" |

B3 and B4 are incomparable with B2. Report all rows on the surface; do not pretend a ladder.

**Analytic hook (revised).** Under finite `r_p` and a searching pursuer, expected time-to-first-detection for a cluster of radius R is a search-theory quantity (area coverage rate vs target footprint); combined with `p_lock(n_local)` this gives an expected capture rate as a function of R and n that has a minimum at intermediate compactness. That predicted optimum is the thing to compare against what the minimal controllers actually achieve.

### Idea C — measuring the frontier automatically

Unchanged in intent; two corrections.
- Every frontier from C is an upper bound (§2.2). Say so in the abstract.
- Run C's design with Ligot & Birattari's reality-gap-mimicking perturbations on, so the optimiser cannot exploit sim artefacts (wedging on slopes, exact-range sensing).

Architecture: PFSMs with capped states and a capped module set; each cap is a capability budget. Environment instances sampled from the A/B generators per mission-class. Fixed design budget per cell; evaluate on held-out instances.

### Idea D — transient sensor plus a latch

**Accounting fix.** The startup bit is set from k steps of per-step sensing, so the honest comparison is **"transient sensor + 1-bit latch"** versus **"permanent sensor, no memory."** Count it as `S_transient` for k steps, `M = 1` thereafter, `S = 2` (Gauci) for the rest of the run. The claim being tested is Berg & Purcell's: at small scale, *when* you sample can beat *how much* you sample. That is the framing, not "plasticity."

Runs as an ablation row in Paper 2. Graduates to its own figure only if it beats the permanent-sensor row on the surface.

---

## 4. Infrastructure

**Tier 1 sim — decide the language now.** Pairwise LOS with ray checks is O(n²) per step; NumPy will not reach 10⁵–10⁶ runs at n = 50. Options: Rust (rayon over runs, simple to validate against Gauci) or a vectorised GPU sim (JAX / Warp / Taichi, batch runs as an extra axis). Rust if one person; GPU if someone already knows the stack. Either way, reproduce Gauci's published constants and scaling curve before adding a single dial.

**Tier 2 — ARGoS** with e-puck plugin, for the cells defended against Birattari-lab reviewers and for anything needing contact physics.

**Environment generator.** Occlusion (correlated FN/FP), terrain (per-wheel friction field, slope), pursuer (ρ, r_p, κ, targeting rule, search behaviour). Seeded, logged.

**Controllers.** `act(sensor_state, memory_bits, rx_bits) → (v_L, v_R, memory_bits', tx_bits)`. Lookup tables indexed by full capability vector; PFSM family for C.

**Sweep harness.** For each (row, θ) cell: run, record performance distribution, emit surface + contours. Flag every cell where the row was optimiser-found rather than enumerated.

**Statistics.** ≥100 runs/cell Tier 1, ≥30 Tier 2; medians with bootstrap CIs; Friedman + post-hoc across rows. Pre-register T.

**Hardware track (minimum viable).** e-pucks or Pi-pucks on a 2×2 m tiltable board (0°, 5°, 10°) with rubber friction patches — this realises the corrected terrain model directly. One e-puck as pursuer with an overhead-tracker feed, its perception artificially limited to (r_p, κ) in software. 3 cells from A, 3 from B, 10 runs each.

---

## 5. Papers and venues

**ANTS calendar.** ANTS 2026 has already run (Darmstadt, 8–10 June 2026; paper deadline was 10 November 2025; a *Swarm Intelligence* special issue takes extended versions). The series is now summer-conference / autumn-deadline. Next paper cycle: **ANTS 2028**, deadline probably autumn 2027. Near-term targets are therefore the **Swarm Intelligence** journal and **ALIFE 2027**.

**Paper 1 — the map.** Framework (§2), aggregation only, Gauci lookup tables, two dials (terrain, pursuer), one surface-with-contours figure per dial with the same rows, the anisotropy lemma as a short theorem, occlusion shakedown as a supporting figure. The finding is the *contrast*: the minimum moves differently for passive vs active hostility. Target: *Swarm Intelligence* (journal-length) now, or ANTS 2028 if you'd rather wait for the conference and take the special-issue extension.

**Paper 2 — the instrument.** Idea C + hardware + Idea D as an ablation row. Extended-paper relationship to Paper 1 is legitimate and expected at *Swarm Intelligence*. Alternative: *Frontiers in Robotics and AI* (where Hunt's paper sits).

**Paper 3 (optional) — the analysis.** Anisotropy bound (A) and search-theory capture-rate optimum (B). **SSS**, where Daymude et al. published. Not DISC.

**Idea B alone, if the Olson connection dominates:** ALIFE 2027 or *Artificial Life*.

**Title discipline.** Lead with minimality: "How much must a robot sense to aggregate on a slope?" Never "robust."

**Do not** publish A then B as "A with a predator."

---

## 6. Timeline

This is a **team-of-three** schedule. Solo, multiply by ~2.5 and drop the hardware track until Paper 1 is submitted.

1. Weeks 1–3: Tier-1 sim in Rust/GPU; reproduce Gauci constants and scaling. Gate.
2. Week 3: occlusion shakedown.
3. Weeks 4–7: corrected terrain generator; Idea A sweep; H2 test against R₀; anisotropy lemma draft.
4. Weeks 7–11: pursuer family with perception dials; Idea B rows; capture-rate surfaces.
5. Weeks 11–15: ARGoS cells; hardware if available.
6. Week 15+: write Paper 1. Decide C vs D emphasis for Paper 2 from the surfaces.

---

## 7. Objections and answers (updated)

- **"Just robustness testing."** Capability is the dependent variable; performance is held at T.
- **"Your terrain model can't break symmetry."** It now can: per-wheel friction changes curvature; heading-dependent gravity stretches the state-0 circle. Both are what a tilted board does physically.
- **"Aggregation can't help against a pursuer."** Against a perfect-perception, infinite-range pursuer it can't, and we show that corner. Against finite range and confusion it can via search cost and lock-on failure; those are dials, and the frontier over them is the result.
- **"Your minima aren't minima."** Correct for every optimiser-found row; they are upper bounds and labelled as such. Only enumerated rows are tight.
- **"BEECLUST did non-uniform environments."** As a target, not a perturbation. Cited and distinguished.
- **"Rung 3 is communication."** It is, and it's counted in K.
- **"Minimality is ill-defined."** Multiple threshold contours on one surface show exactly how the answer depends on T.
- **"Sim only."** Two tiers plus a hardware track that realises the terrain model directly.

---

## 8. Reading list

Core: Gauci et al. 2014 (IJRR; AAMAS); Özdemir et al. 2017 (ECAL), 2018 (RA-L); Daymude et al. 2021 (SSS); Johnson & Brown 2015 (BICT); Brown, Turgut & Goodrich DARS 2016/2018; Hamann 2018.
Non-uniform environments: Schmickl et al. BEECLUST papers (2008–2009); Hunt 2020.
Pursuit/predation: Chung, Hollinger & Isler 2011; Olson et al. 2013, 2016; Wood & Ackland 2007.
Temporal sensing: Berg & Purcell 1977.
Methodology: Francesca et al. 2014; Birattari et al. 2019 manifesto; Ligot & Birattari ANTS 2018; Jakobi, Husbands & Harvey 1995.
