//! Controller search: separable CMA-ES over a lookup table's wheel constants.
//!
//! # Which variant, and why it matters
//!
//! This is **sep-CMA-ES** (Ros & Hansen, 2008): the covariance matrix is
//! restricted to its diagonal. Saying "CMA-ES" without qualification would be
//! imprecise — the separable variant cannot exploit correlations between
//! constants, so it is a *weaker* searcher than full CMA-ES, and a row it fails
//! to improve is correspondingly weaker evidence.
//!
//! That direction is the safe one for this project. Every searched row is an
//! **upper bound** on what its capability can do (build doc §2.2), and a weaker
//! searcher only makes the bound looser, never falsely tight. The budget is
//! fixed and logged with the result so the bound is quotable.
//!
//! # Honest accounting
//!
//! * The search runs on **training seeds**; the row is then evaluated on a
//!   disjoint seed range. Reporting the training objective as the result would
//!   be reporting the maximum of a noisy sample.
//! * Constants are box-constrained to [-1, 1]. Candidates outside are repaired
//!   to the box and charged a quadratic penalty for the repair distance, so the
//!   optimiser is not rewarded for drifting out.
//! * The objective is the **median** over `runs_per_eval` trials, matching how
//!   results are reported elsewhere; a mean would sit between the two modes of a
//!   bimodal cell.

use anyhow::{Context, Result};
use rand::SeedableRng;
use rand_distr::{Distribution, StandardNormal};
use rayon::prelude::*;
use serde::Serialize;
use serde_json::Value;
use swarm_core::{SimConfig, World};

type Rng = rand_pcg::Pcg64;

/// Separable CMA-ES state.
pub struct SepCmaEs {
    n: usize,
    lambda: usize,
    weights: Vec<f64>,
    mueff: f64,
    cc: f64,
    cs: f64,
    c1: f64,
    cmu: f64,
    damps: f64,
    chi_n: f64,
    mean: Vec<f64>,
    sigma: f64,
    /// Square roots of the diagonal of C.
    d: Vec<f64>,
    pc: Vec<f64>,
    ps: Vec<f64>,
    gen: usize,
    rng: Rng,
}

impl SepCmaEs {
    pub fn new(mean: Vec<f64>, sigma: f64, seed: u64) -> Self {
        let n = mean.len();
        let lambda = 4 + (3.0 * (n as f64).ln()).floor() as usize;
        let mu = lambda / 2;
        let raw: Vec<f64> = (0..mu)
            .map(|i| (mu as f64 + 0.5).ln() - ((i + 1) as f64).ln())
            .collect();
        let sum: f64 = raw.iter().sum();
        let weights: Vec<f64> = raw.iter().map(|w| w / sum).collect();
        let mueff = 1.0 / weights.iter().map(|w| w * w).sum::<f64>();

        let nf = n as f64;
        let cs = (mueff + 2.0) / (nf + mueff + 3.0);
        let cc = 4.0 / (nf + 4.0);
        // The separable variant scales the learning rates up by (n+2)/3, which
        // is what buys it faster progress with a diagonal-only model.
        let sep = (nf + 2.0) / 3.0;
        let c1 = (2.0 / ((nf + 1.3) * (nf + 1.3) + mueff)) * sep;
        let cmu = ((2.0 * (mueff - 2.0 + 1.0 / mueff) / ((nf + 2.0) * (nf + 2.0) + mueff)) * sep)
            .min(1.0 - c1);
        let damps = 1.0 + 2.0 * (0.0f64).max(((mueff - 1.0) / (nf + 1.0)).sqrt() - 1.0) + cs;
        let chi_n = nf.sqrt() * (1.0 - 1.0 / (4.0 * nf) + 1.0 / (21.0 * nf * nf));

        Self {
            n,
            lambda,
            weights,
            mueff,
            cc,
            cs,
            c1,
            cmu,
            damps,
            chi_n,
            mean,
            sigma,
            d: vec![1.0; n],
            pc: vec![0.0; n],
            ps: vec![0.0; n],
            gen: 0,
            rng: Rng::seed_from_u64(seed),
        }
    }

    pub fn population_size(&self) -> usize {
        self.lambda
    }

    /// Draw a generation of candidates, as `(repaired_point, penalty)`.
    pub fn ask(&mut self) -> Vec<(Vec<f64>, f64)> {
        (0..self.lambda)
            .map(|_| {
                let raw: Vec<f64> = (0..self.n)
                    .map(|i| {
                        let z: f64 = StandardNormal.sample(&mut self.rng);
                        self.mean[i] + self.sigma * self.d[i] * z
                    })
                    .collect();
                let repaired: Vec<f64> = raw.iter().map(|x| x.clamp(-1.0, 1.0)).collect();
                let penalty: f64 = raw
                    .iter()
                    .zip(&repaired)
                    .map(|(a, b)| (a - b) * (a - b))
                    .sum();
                (repaired, penalty)
            })
            .collect()
    }

    /// Update from a generation's fitnesses (lower is better).
    pub fn tell(&mut self, candidates: &[(Vec<f64>, f64)], fitness: &[f64]) {
        let mut order: Vec<usize> = (0..candidates.len()).collect();
        order.sort_by(|&a, &b| {
            fitness[a]
                .partial_cmp(&fitness[b])
                .unwrap_or(std::cmp::Ordering::Equal)
        });

        let old_mean = self.mean.clone();
        let mut new_mean = vec![0.0; self.n];
        for (rank, w) in self.weights.iter().enumerate() {
            let x = &candidates[order[rank]].0;
            for i in 0..self.n {
                new_mean[i] += w * x[i];
            }
        }

        let step: Vec<f64> = (0..self.n)
            .map(|i| (new_mean[i] - old_mean[i]) / self.sigma)
            .collect();

        let ps_gain = (self.cs * (2.0 - self.cs) * self.mueff).sqrt();
        for ((ps, d), st) in self.ps.iter_mut().zip(&self.d).zip(&step) {
            *ps = (1.0 - self.cs) * *ps + ps_gain * st / d;
        }
        let ps_norm = self.ps.iter().map(|v| v * v).sum::<f64>().sqrt();
        let denom = (1.0 - (1.0 - self.cs).powi(2 * (self.gen as i32 + 1))).sqrt();
        let hsig = ps_norm / denom < (1.4 + 2.0 / (self.n as f64 + 1.0)) * self.chi_n;

        let pc_gain = if hsig {
            (self.cc * (2.0 - self.cc) * self.mueff).sqrt()
        } else {
            0.0
        };
        for (pc, st) in self.pc.iter_mut().zip(&step) {
            *pc = (1.0 - self.cc) * *pc + pc_gain * st;
        }

        let sigma = self.sigma;
        let (c1, cmu, cc) = (self.c1, self.cmu, self.cc);
        for (i, (d, pc)) in self.d.iter_mut().zip(&self.pc).enumerate() {
            let mut c = *d * *d;
            let rank_mu: f64 = self
                .weights
                .iter()
                .enumerate()
                .map(|(rank, w)| {
                    let y = (candidates[order[rank]].0[i] - old_mean[i]) / sigma;
                    w * y * y
                })
                .sum();
            let correction = if hsig { 0.0 } else { cc * (2.0 - cc) * c };
            c = (1.0 - c1 - cmu) * c + c1 * (pc * pc + correction) + cmu * rank_mu;
            *d = c.max(1e-12).sqrt();
        }

        self.sigma *= ((self.cs / self.damps) * (ps_norm / self.chi_n - 1.0)).exp();
        self.sigma = self.sigma.clamp(1e-6, 10.0);
        self.mean = new_mean;
        self.gen += 1;
    }
}

/// What a search run produces, written next to the results so a row's upper
/// What the search optimises.
///
/// `Dispersion` is the objective sections 9, 13 and 19-21 were searched against
/// and is the **default**, so every recorded search reproduces unchanged. The two
/// survival objectives were added for freeze lift 1 experiment 1, whose
/// pre-registration (`docs/preregistration/searched-s3-pursuer.md`) fixes their
/// definitions, their zero guard and the sign convention below before they
/// existed.
///
/// # Sign
///
/// sep-CMA-ES minimises. A survival objective is better when larger, so the
/// optimiser is handed `-score` and every number that leaves this module — the
/// reported best, the per-generation history, the progress line — is converted
/// back to its natural orientation. `SearchResult::objective` says which way is
/// better, in words, so a reader of the JSON never has to infer it.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Objective {
    /// Median `final_dispersion` over the trials of a condition. Lower is better.
    Dispersion,
    /// Mean per-robot survival at tau, captured robots counting as 0. Higher is
    /// better.
    Survival,
    /// Geometric mean of survival and `1 / dispersion_among_survivors`, so
    /// survival cannot be bought by abandoning the task. Higher is better.
    SurvivalTask,
}

impl Objective {
    pub fn parse(name: &str) -> Result<Self> {
        Ok(match name {
            "dispersion" => Objective::Dispersion,
            "survival" => Objective::Survival,
            "survival_task" => Objective::SurvivalTask,
            other => anyhow::bail!(
                "unknown --objective {other:?}; expected dispersion, survival or survival_task"
            ),
        })
    }

    pub fn higher_is_better(self) -> bool {
        !matches!(self, Objective::Dispersion)
    }

    /// The value sep-CMA-ES compares. Negated for a maximising objective, so the
    /// box-repair penalty always makes a candidate worse whichever way is better.
    fn to_minimise(self, score: f64) -> f64 {
        if self.higher_is_better() {
            -score
        } else {
            score
        }
    }

    /// Back to the natural orientation, for everything a human or a figure reads.
    fn to_report(self, minimised: f64) -> f64 {
        if self.higher_is_better() {
            -minimised
        } else {
            minimised
        }
    }
}

/// FNV-1a over the resolved base config, so a later edit to the config cannot
/// silently invalidate a recorded row.
///
/// Written out rather than pulled in: a cryptographic hash would be a new
/// dependency for a job that only has to answer "is this the same config", and
/// `DefaultHasher` is explicitly not stable across Rust releases, which is the
/// one property a provenance field needs.
fn config_hash(base: &Value) -> String {
    let text = serde_json::to_string(base).unwrap_or_default();
    let mut h: u64 = 0xcbf2_9ce4_8422_2325;
    for b in text.as_bytes() {
        h ^= *b as u64;
        h = h.wrapping_mul(0x0000_0100_0000_01b3);
    }
    format!("fnv1a64:{h:016x}")
}

/// The commit the working tree was at, with `-dirty` when it was not clean.
///
/// Best effort: `None` if git is not available or this is not a repository. A
/// missing hash is recorded as missing rather than as something else, because
/// finding F3 was exactly a row whose provenance looked complete and was not.
fn git_hash() -> Option<String> {
    let rev = std::process::Command::new("git")
        .args(["rev-parse", "HEAD"])
        .output()
        .ok()?;
    if !rev.status.success() {
        return None;
    }
    let hash = String::from_utf8(rev.stdout).ok()?.trim().to_string();
    let dirty = std::process::Command::new("git")
        .args(["status", "--porcelain"])
        .output()
        .ok()
        .map(|o| !o.stdout.is_empty())
        .unwrap_or(false);
    Some(if dirty { format!("{hash}-dirty") } else { hash })
}

/// bound can be quoted with the budget that produced it.
#[derive(Debug, Serialize)]
pub struct SearchResult {
    pub encoding: String,
    pub dimensions: usize,
    /// Candidate evaluations actually spent.
    pub budget_evaluations: usize,
    pub population_size: usize,
    pub generations: usize,
    pub runs_per_evaluation: usize,
    pub simulation_runs: usize,
    pub seed: u64,
    pub training_seed_base: u64,
    /// Where the search started. A warm start changes what a null result means:
    /// from "the optimiser did not find anything good" to "the optimiser could
    /// not improve on this specific known-good point".
    pub initial_mean: Vec<f64>,
    pub warm_started: bool,
    pub best_constants: Vec<f64>,
    pub best_training_objective: f64,
    /// Objective of the incumbent after each generation, for a convergence plot.
    pub history: Vec<f64>,
    /// The environment class the objective was averaged over, as crossed axes.
    /// Empty for a single-condition search, and also empty when the class was
    /// given as explicit points; `training_condition_points` is always filled.
    pub training_class: Vec<(String, Vec<Value>)>,
    /// Every training condition, resolved. A class whose conditions differ in
    /// more than one dial cannot be recovered from crossed axes — a τ that is
    /// 3600 s at one start radius and 600 s at another is not a product — so the
    /// file records the conditions themselves and not only how they were spelt.
    pub training_condition_points: Vec<Condition>,
    pub training_conditions: usize,
    pub objective: String,
    pub optimiser: String,
    /// Provenance, required since freeze lift 1 finding F3: four searches in the
    /// record cannot be regenerated because no document states the optimiser
    /// seed they ran at. `seed`, `training_seed_base` and `budget_evaluations`
    /// above are the rest of it.
    pub git_hash: Option<String>,
    pub config_hash: String,
}

/// One training condition: config-path overrides applied on top of the base.
///
/// An empty condition is the ordinary single-condition search; a list of them is
/// a **mission class**, and the objective below is then a statement about the
/// class rather than about one arena.
pub type Condition = Vec<(String, Value)>;

/// Cartesian product of named axes, in the order given.
///
/// `[("swarm.init.radius", [0.74, 1.5, 3.0]), ("swarm.n", [20, 50])]` becomes
/// the six conditions of the mission class, each carrying both overrides.
pub fn class_conditions(axes: &[(String, Vec<Value>)]) -> Vec<Condition> {
    let mut out: Vec<Condition> = vec![Vec::new()];
    for (path, values) in axes {
        let mut next = Vec::with_capacity(out.len() * values.len());
        for base in &out {
            for v in values {
                let mut c = base.clone();
                c.push((path.clone(), v.clone()));
                next.push(c);
            }
        }
        out = next;
    }
    out
}

fn median(mut xs: Vec<f64>) -> f64 {
    xs.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    xs[xs.len() / 2]
}

/// Below this many survivors, "the dispersion of the survivors" is degenerate:
/// one or zero robots score 0, which is a perfect aggregation score for a swarm
/// that has been wiped out.
const MIN_SURVIVORS_FOR_TASK: usize = 3;

/// What one trial contributes. Kept as a struct rather than three parallel
/// vectors so a condition cannot be scored on survivors from one run and
/// dispersion from another.
#[derive(Clone, Copy)]
struct Trial {
    final_dispersion: f64,
    survivors: usize,
    n: usize,
}

/// Score one training condition, in its natural orientation.
///
/// Survival is **pooled per robot** — total survivors over total robots — not a
/// mean of per-run fractions. They agree when `n` is constant across a
/// condition, which it is here, and the pooled form is the one
/// `scripts/recompute_paired_and_survival.py` and §12.1 D0 put the record on.
fn score_condition(objective: Objective, trials: &[Trial]) -> f64 {
    match objective {
        Objective::Dispersion => median(trials.iter().map(|t| t.final_dispersion).collect()),
        Objective::Survival => pooled_survival(trials),
        Objective::SurvivalTask => {
            let survival = pooled_survival(trials);
            // The guard is per trial: a run that ends with fewer than three
            // robots has no meaningful "dispersion among survivors", so it
            // contributes survival and nothing else. A condition in which NO run
            // clears the bar has no task term at all and scores 0 -- which is
            // the honest score for a candidate that wipes out there, and is why
            // this is not written as a floor.
            let usable: Vec<f64> = trials
                .iter()
                .filter(|t| t.survivors >= MIN_SURVIVORS_FOR_TASK)
                .map(|t| t.final_dispersion)
                .collect();
            if usable.is_empty() || survival <= 0.0 {
                return 0.0;
            }
            let dispersion = median(usable);
            if dispersion <= 0.0 {
                return 0.0;
            }
            (survival * (1.0 / dispersion)).sqrt()
        }
    }
}

fn pooled_survival(trials: &[Trial]) -> f64 {
    let robots: usize = trials.iter().map(|t| t.n).sum();
    if robots == 0 {
        return 0.0;
    }
    trials.iter().map(|t| t.survivors).sum::<usize>() as f64 / robots as f64
}

/// Combine per-condition scores into the class objective: the geometric mean.
///
/// The dispersion path keeps its exact original arithmetic, `1e-6` floor
/// included, so every search in the record reproduces bit-for-bit. The survival
/// path deliberately does **not** floor: a proportion of 0 is a real value, a
/// candidate that wipes out in any one condition should score 0 for the class,
/// and a floor would quietly turn that into "very slightly better than wiped
/// out" and let the optimiser trade one dead condition for five good ones.
fn combine_conditions(objective: Objective, per_condition: &[f64]) -> f64 {
    match objective {
        Objective::Dispersion => {
            let logs: Vec<f64> = per_condition.iter().map(|v| v.max(1e-6).ln()).collect();
            (logs.iter().sum::<f64>() / logs.len() as f64).exp()
        }
        _ => {
            if per_condition.iter().any(|v| *v <= 0.0) {
                return 0.0;
            }
            let logs: Vec<f64> = per_condition.iter().map(|v| v.ln()).collect();
            (logs.iter().sum::<f64>() / logs.len() as f64).exp()
        }
    }
}

/// The training objective.
///
/// With a single condition this is the median final dispersion over `runs`
/// trials — exactly the objective sections 9 and 13 searched against, unchanged.
///
/// With several, it is the **geometric mean of the per-condition medians**. Two
/// reasons, both of which bite here:
///
/// * The conditions are not on a common scale. Median dispersion runs from about
///   1.2 at a 0.74 m start radius to tens at 3.0 m under terrain, so a plain mean
///   — or a median over the pooled runs — is the hardest condition wearing a
///   disguise, and the optimiser would be free to abandon the rest of the class.
///   Averaging logs weights a 10% improvement the same everywhere.
/// * It reduces to the single-condition objective exactly when the class has one
///   member, so a class search and a fixed-condition search are one procedure at
///   two class sizes rather than two protocols that cannot be compared.
///
/// Runs are split evenly across conditions, each condition drawing its own
/// disjoint block of run indices, so every candidate in the search is scored on
/// the same (condition, seed) pairs and candidates are compared on identical
/// work. `runs` must divide by the class size.
fn evaluate(
    base: &Value,
    constants: &[f64],
    runs: usize,
    seed_base: u64,
    class: &[Condition],
    objective: Objective,
) -> Result<f64> {
    let entries: Vec<Value> = constants
        .chunks(2)
        .map(|c| serde_json::json!({ "wheels": [c[0], c[1]] }))
        .collect();
    let per_condition = runs / class.len();
    let mut configs = Vec::with_capacity(class.len());
    for condition in class {
        let mut value = base.clone();
        crate::sweep::set_path(
            &mut value,
            "controller",
            serde_json::json!({
                "kind": "table",
                "memory_bits": 0,
                "provenance": "optimiser_found",
                "entries": entries,
            }),
        )?;
        for (path, v) in condition {
            crate::sweep::set_path(&mut value, path, v.clone())?;
        }
        crate::sweep::set_path(&mut value, "sim.seed", Value::from(seed_base))?;
        crate::sweep::set_path(&mut value, "metrics.store_series", Value::from(false))?;
        configs.push(SimConfig::from_json_value(value).map_err(|e| anyhow::anyhow!("{e}"))?);
    }

    // Parallelise over every (condition, run) pair rather than over the runs of
    // one condition at a time: with six conditions and two runs each, a loop of
    // parallel pairs leaves all but two cores idle.
    let jobs: Vec<(usize, u64)> = (0..class.len())
        .flat_map(|k| (0..per_condition as u64).map(move |i| (k, i)))
        .collect();
    let scores: Vec<(usize, Trial)> = jobs
        .par_iter()
        .map(|&(k, i)| -> Result<(usize, Trial)> {
            let offset = (k * per_condition) as u64;
            let record = World::new(configs[k].clone(), offset + i)
                .map_err(|e| anyhow::anyhow!("{e}"))?
                .run();
            Ok((
                k,
                Trial {
                    final_dispersion: record.final_dispersion,
                    survivors: record.survivors,
                    n: configs[k].swarm.n,
                },
            ))
        })
        .collect::<Result<Vec<_>>>()?;

    let mut by_condition = vec![Vec::with_capacity(per_condition); class.len()];
    for (k, v) in scores {
        by_condition[k].push(v);
    }
    let per_condition_scores: Vec<f64> = by_condition
        .iter()
        .map(|trials| score_condition(objective, trials))
        .collect();
    Ok(combine_conditions(objective, &per_condition_scores))
}

#[allow(clippy::too_many_arguments)]
pub fn run_search(
    base: &Value,
    encoding: &str,
    states: usize,
    budget: usize,
    runs_per_eval: usize,
    seed: u64,
    training_seed_base: u64,
    init: Option<Vec<f64>>,
    class_axes: &[(String, Vec<Value>)],
    class_points: &[Condition],
    objective: Objective,
) -> Result<SearchResult> {
    let dims = 2 * states;
    if !class_axes.is_empty() && !class_points.is_empty() {
        anyhow::bail!(
            "give the class as crossed axes OR as explicit points, not both — \
             which conditions were trained on would otherwise depend on how the \
             two were meant to combine"
        );
    }
    let class = if class_points.is_empty() {
        class_conditions(class_axes)
    } else {
        class_points.to_vec()
    };
    if runs_per_eval % class.len() != 0 {
        anyhow::bail!(
            "runs_per_eval ({runs_per_eval}) must divide by the class size ({}), \
             or the conditions are unequally weighted",
            class.len()
        );
    }
    // Default: Gauci's constants tiled across the extra states, so the search
    // begins at a known-good four-constant controller rather than at random.
    //
    // With `init`, the caller supplies the start instead, tiled the same way if
    // it is shorter than the space. Tiling a four-constant controller into an
    // eight-constant table gives a table whose two halves are equal — an S = 4
    // row that starts out *ignoring* its extra bit and behaving exactly like the
    // S = 2 controller it came from. The search can then only be asked one
    // question: does using the bit improve on not using it?
    let warm_started = init.is_some();
    let source = init.unwrap_or_else(|| swarm_core::GAUCI_CONSTANTS.to_vec());
    if source.is_empty() {
        anyhow::bail!("initial constants must not be empty");
    }
    let seed_point: Vec<f64> = (0..dims).map(|i| source[i % source.len()]).collect();

    let mut es = SepCmaEs::new(seed_point.clone(), 0.3, seed);
    let lambda = es.population_size();
    let generations = budget / lambda;
    let mut best = (f64::INFINITY, vec![0.0; dims]);
    let mut history = Vec::with_capacity(generations);

    for g in 0..generations {
        let candidates = es.ask();
        let mut fitness = Vec::with_capacity(candidates.len());
        for (x, penalty) in &candidates {
            let score = evaluate(
                base,
                x,
                runs_per_eval,
                training_seed_base,
                &class,
                objective,
            )?;
            // The penalty is added AFTER the sign flip, so leaving the box costs
            // a candidate the same whichever direction is better.
            let f = objective.to_minimise(score) + 10.0 * penalty;
            if f < best.0 {
                best = (f, x.clone());
            }
            fitness.push(f);
        }
        es.tell(&candidates, &fitness);
        history.push(objective.to_report(best.0));
        eprint!(
            "\r  generation {}/{generations}  best {:.4}",
            g + 1,
            objective.to_report(best.0)
        );
    }
    eprintln!();

    Ok(SearchResult {
        encoding: encoding.to_string(),
        dimensions: dims,
        budget_evaluations: generations * lambda,
        population_size: lambda,
        generations,
        runs_per_evaluation: runs_per_eval,
        simulation_runs: generations * lambda * runs_per_eval,
        seed,
        training_seed_base,
        initial_mean: seed_point,
        warm_started,
        best_constants: best.1,
        best_training_objective: objective.to_report(best.0),
        history,
        training_class: class_axes
            .iter()
            .map(|(p, v)| (p.clone(), v.clone()))
            .collect(),
        training_condition_points: class.clone(),
        training_conditions: class.len(),
        objective: describe_objective(objective, class.len(), runs_per_eval),
        optimiser: "sep-CMA-ES (Ros & Hansen 2008), diagonal covariance".into(),
        git_hash: git_hash(),
        config_hash: config_hash(base),
    })
}

/// The `objective` string in the output JSON: the definition in words, so the
/// file is readable without this source.
///
/// The dispersion wording is unchanged from before freeze lift 1, because the
/// recorded searches' JSON carries it and a re-run must reproduce the file.
fn describe_objective(objective: Objective, conditions: usize, runs_per_eval: usize) -> String {
    let per = runs_per_eval / conditions.max(1);
    match objective {
        Objective::Dispersion if conditions == 1 => "median final_dispersion over \
             runs_per_evaluation trials, lower is better; +10x squared box-repair penalty"
            .into(),
        Objective::Dispersion => format!(
            "geometric mean over {conditions} training conditions of the median \
             final_dispersion in each ({per} trials per condition), lower is \
             better; +10x squared box-repair penalty"
        ),
        Objective::Survival => format!(
            "geometric mean over {conditions} training conditions of the mean \
             per-robot survival at tau in each ({per} trials per condition, \
             pooled over robots, captured robots counting as 0), HIGHER is \
             better; a condition scoring 0 makes the class objective 0; \
             +10x squared box-repair penalty"
        ),
        Objective::SurvivalTask => format!(
            "geometric mean over {conditions} training conditions of the \
             geometric mean of (mean per-robot survival at tau) and \
             (1 / median dispersion among survivors) in each ({per} trials per \
             condition); trials with fewer than {MIN_SURVIVORS_FOR_TASK} \
             survivors contribute no task term and a condition with no such \
             trial scores 0, as does the class objective then; HIGHER is \
             better; +10x squared box-repair penalty"
        ),
    }
}

pub fn write_result(path: &std::path::Path, result: &SearchResult) -> Result<()> {
    if let Some(dir) = path.parent() {
        if !dir.as_os_str().is_empty() {
            std::fs::create_dir_all(dir)?;
        }
    }
    std::fs::write(path, serde_json::to_string_pretty(result)?)
        .with_context(|| format!("writing {}", path.display()))?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn trial(dispersion: f64, survivors: usize) -> Trial {
        Trial {
            final_dispersion: dispersion,
            survivors,
            n: 20,
        }
    }

    #[test]
    fn the_default_objective_is_the_one_the_record_was_searched_against() {
        // Bit-neutrality, as a test rather than as a promise: the dispersion
        // path must still be the median, and `--objective` must default to it.
        assert_eq!(
            Objective::parse("dispersion").unwrap(),
            Objective::Dispersion
        );
        let trials = [trial(1.0, 20), trial(3.0, 20), trial(2.0, 20)];
        assert_eq!(score_condition(Objective::Dispersion, &trials), 2.0);
        assert!(!Objective::Dispersion.higher_is_better());
    }

    #[test]
    fn an_unknown_objective_is_refused_rather_than_defaulted() {
        // Silently falling back to dispersion would search the wrong thing and
        // record a JSON that says so only in a field nobody reads.
        let err = Objective::parse("survivial").unwrap_err().to_string();
        assert!(err.contains("survivial"), "{err}");
        assert!(err.contains("survival_task"), "{err}");
    }

    #[test]
    fn survival_is_pooled_over_robots_not_averaged_over_runs() {
        // 15 + 5 survivors out of 40 robots is 0.5. It agrees with the mean of
        // the per-run fractions only because n is constant, which is the case
        // this search creates and the reason the pooled form is safe here.
        let trials = [trial(1.4, 15), trial(1.4, 5)];
        assert!((score_condition(Objective::Survival, &trials) - 0.5).abs() < 1e-12);
        assert!(Objective::Survival.higher_is_better());
    }

    #[test]
    fn a_wiped_out_condition_scores_zero_and_takes_the_class_with_it() {
        // The point of the guard. A candidate that survives beautifully in five
        // conditions and dies in the sixth must not be able to average its way
        // to a good class score.
        let dead = [trial(0.0, 0), trial(0.0, 0)];
        assert_eq!(score_condition(Objective::Survival, &dead), 0.0);
        assert_eq!(
            combine_conditions(Objective::Survival, &[0.9, 0.9, 0.9, 0.9, 0.9, 0.0]),
            0.0
        );
        // and the same for the two-axis objective
        assert_eq!(score_condition(Objective::SurvivalTask, &dead), 0.0);
        assert_eq!(
            combine_conditions(Objective::SurvivalTask, &[0.5, 0.0]),
            0.0
        );
    }

    #[test]
    fn a_run_with_too_few_survivors_contributes_no_task_term() {
        // Two survivors sitting on top of each other score a dispersion near 0,
        // which is a PERFECT aggregation score for a swarm that has been all but
        // wiped out. Such a run must not set the task term.
        let mixed = [trial(0.01, 2), trial(4.0, 18)];
        let s = score_condition(Objective::SurvivalTask, &mixed);
        // survival = 20/40 = 0.5; the only usable run has dispersion 4.0
        assert!((s - (0.5f64 * 0.25).sqrt()).abs() < 1e-12, "{s}");
        // With no usable run at all the condition scores 0 rather than taking
        // the degenerate dispersion.
        let all_tiny = [trial(0.01, 2), trial(0.02, 1)];
        assert_eq!(score_condition(Objective::SurvivalTask, &all_tiny), 0.0);
    }

    #[test]
    fn survival_task_refuses_to_buy_survival_by_abandoning_the_task() {
        // The whole reason the second objective exists. A dispersive row that
        // keeps everyone alive at dispersion 400 must score BELOW an aggregating
        // row that loses a third of the swarm and holds a cluster at 1.5.
        let dispersive = [trial(400.0, 20), trial(400.0, 20)];
        let aggregating = [trial(1.5, 13), trial(1.5, 14)];
        assert!(
            score_condition(Objective::Survival, &dispersive)
                > score_condition(Objective::Survival, &aggregating)
        );
        assert!(
            score_condition(Objective::SurvivalTask, &dispersive)
                < score_condition(Objective::SurvivalTask, &aggregating)
        );
    }

    #[test]
    fn the_class_objective_reduces_to_one_condition() {
        // A class search and a fixed-condition search must be one procedure at
        // two class sizes, for every objective.
        for o in [
            Objective::Dispersion,
            Objective::Survival,
            Objective::SurvivalTask,
        ] {
            let v = combine_conditions(o, &[0.42]);
            assert!((v - 0.42).abs() < 1e-12, "{o:?} gave {v}");
        }
    }

    #[test]
    fn the_sign_flip_round_trips_and_the_penalty_always_hurts() {
        for o in [
            Objective::Dispersion,
            Objective::Survival,
            Objective::SurvivalTask,
        ] {
            assert!(
                (o.to_report(o.to_minimise(0.73)) - 0.73).abs() < 1e-12,
                "{o:?}"
            );
            // A repaired candidate must compare worse than the same score unrepaired,
            // whichever direction is better.
            assert!(
                o.to_minimise(0.73) + 10.0 * 0.5 > o.to_minimise(0.73),
                "{o:?}"
            );
        }
    }

    #[test]
    fn the_config_hash_is_stable_and_notices_an_edit() {
        let a = serde_json::json!({"sim": {"duration": 600.0}, "swarm": {"n": 20}});
        let b = serde_json::json!({"sim": {"duration": 600.0}, "swarm": {"n": 50}});
        assert_eq!(config_hash(&a), config_hash(&a));
        assert_ne!(config_hash(&a), config_hash(&b));
        assert!(config_hash(&a).starts_with("fnv1a64:"));
    }

    #[test]
    fn a_class_is_the_cartesian_product_of_its_axes() {
        let axes = vec![
            (
                "swarm.init.radius".to_string(),
                vec![Value::from(0.74), Value::from(1.5), Value::from(3.0)],
            ),
            (
                "swarm.n".to_string(),
                vec![Value::from(20), Value::from(50)],
            ),
        ];
        let conditions = class_conditions(&axes);
        assert_eq!(conditions.len(), 6);
        // Every condition carries every axis, or a condition would silently
        // inherit the base config's value for the axis it is meant to vary.
        for c in &conditions {
            assert_eq!(c.len(), 2);
            assert_eq!(c[0].0, "swarm.init.radius");
            assert_eq!(c[1].0, "swarm.n");
        }
        let radii: Vec<f64> = conditions
            .iter()
            .map(|c| c[0].1.as_f64().unwrap())
            .collect();
        assert_eq!(radii, vec![0.74, 0.74, 1.5, 1.5, 3.0, 3.0]);
    }

    #[test]
    fn explicit_points_are_taken_as_given() {
        // The case the axis form cannot express: tau differs BETWEEN conditions
        // rather than across a dial of its own, so the class is not a product.
        let points: Vec<Condition> = vec![
            vec![
                ("swarm.init.radius".into(), Value::from(0.74)),
                ("sim.duration".into(), Value::from(600.0)),
            ],
            vec![
                ("swarm.init.radius".into(), Value::from(3.0)),
                ("sim.duration".into(), Value::from(3600.0)),
            ],
        ];
        // Crossing the same dials would give four conditions, two of which
        // (0.74 m at 3600 s, 3.0 m at 600 s) are not wanted.
        let crossed = class_conditions(&[
            (
                "swarm.init.radius".into(),
                vec![Value::from(0.74), Value::from(3.0)],
            ),
            (
                "sim.duration".into(),
                vec![Value::from(600.0), Value::from(3600.0)],
            ),
        ]);
        assert_eq!(crossed.len(), 4);
        assert_eq!(points.len(), 2);
    }

    #[test]
    fn no_axes_is_a_single_empty_condition() {
        // The single-condition search must stay exactly what it was: one
        // condition applying no overrides, so `evaluate` reduces to the median.
        let conditions = class_conditions(&[]);
        assert_eq!(conditions.len(), 1);
        assert!(conditions[0].is_empty());
    }

    #[test]
    fn the_class_objective_is_the_geometric_mean_of_condition_medians() {
        // Stated as arithmetic rather than as a simulation: the property that
        // matters is that a condition scoring 100 cannot be averaged away by
        // one scoring 1, which is what an arithmetic mean would allow.
        let medians = [1.0_f64, 100.0];
        let geometric = (medians.iter().map(|m| m.ln()).sum::<f64>() / medians.len() as f64).exp();
        assert!((geometric - 10.0).abs() < 1e-9);
        let arithmetic = medians.iter().sum::<f64>() / medians.len() as f64;
        assert!(arithmetic > 5.0 * geometric);
    }

    /// A convex quadratic with a known optimum, offset so the answer is not the
    /// starting point and not zero.
    fn sphere(x: &[f64]) -> f64 {
        x.iter()
            .enumerate()
            .map(|(i, v)| {
                let target = 0.3 - 0.1 * i as f64;
                (v - target) * (v - target)
            })
            .sum()
    }

    #[test]
    fn sep_cmaes_minimises_a_quadratic() {
        let mut es = SepCmaEs::new(vec![0.0; 8], 0.3, 42);
        let mut best = f64::INFINITY;
        for _ in 0..80 {
            let candidates = es.ask();
            let fitness: Vec<f64> = candidates
                .iter()
                .map(|(x, p)| sphere(x) + 10.0 * p)
                .collect();
            best = fitness.iter().cloned().fold(best, f64::min);
            es.tell(&candidates, &fitness);
        }
        assert!(best < 1e-6, "did not converge on a sphere: {best}");
    }

    #[test]
    fn candidates_stay_inside_the_box_and_pay_for_leaving() {
        let mut es = SepCmaEs::new(vec![0.9; 4], 2.0, 7);
        let candidates = es.ask();
        assert!(candidates
            .iter()
            .all(|(x, _)| x.iter().all(|v| (-1.0..=1.0).contains(v))));
        assert!(
            candidates.iter().any(|(_, p)| *p > 0.0),
            "a sigma of 2 from 0.9 should have produced repairs"
        );
    }

    #[test]
    fn a_short_warm_start_tiles_across_the_space() {
        // Tiling a 4-constant controller into an 8-constant table gives a table
        // whose halves are equal: an S = 4 row that starts out ignoring its
        // extra bit. That is the whole point of the warm start.
        let source = [-0.7, -1.0, 1.0, -1.0];
        let tiled: Vec<f64> = (0..8).map(|i| source[i % source.len()]).collect();
        assert_eq!(tiled, vec![-0.7, -1.0, 1.0, -1.0, -0.7, -1.0, 1.0, -1.0]);
        assert_eq!(tiled[..4], tiled[4..]);
    }

    #[test]
    fn population_size_follows_the_standard_formula() {
        // 4 + floor(3 ln n): 8 for n = 4, 10 for n = 8.
        assert_eq!(SepCmaEs::new(vec![0.0; 4], 0.3, 1).population_size(), 8);
        assert_eq!(SepCmaEs::new(vec![0.0; 8], 0.3, 1).population_size(), 10);
    }

    #[test]
    fn the_search_is_reproducible_from_its_seed() {
        let run = || {
            let mut es = SepCmaEs::new(vec![0.0; 6], 0.3, 99);
            let mut trace = vec![];
            for _ in 0..5 {
                let c = es.ask();
                let f: Vec<f64> = c.iter().map(|(x, p)| sphere(x) + 10.0 * p).collect();
                trace.push(f.clone());
                es.tell(&c, &f);
            }
            trace
        };
        assert_eq!(run(), run());
    }
}
