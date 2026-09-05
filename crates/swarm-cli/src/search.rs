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
    pub best_constants: Vec<f64>,
    pub best_training_objective: f64,
    /// Objective of the incumbent after each generation, for a convergence plot.
    pub history: Vec<f64>,
    pub objective: String,
    pub optimiser: String,
}

/// Median final dispersion over `runs` trials of `base` with these constants.
fn evaluate(base: &Value, constants: &[f64], runs: usize, seed_base: u64) -> Result<f64> {
    let entries: Vec<Value> = constants
        .chunks(2)
        .map(|c| serde_json::json!({ "wheels": [c[0], c[1]] }))
        .collect();
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
    crate::sweep::set_path(&mut value, "sim.seed", Value::from(seed_base))?;
    crate::sweep::set_path(&mut value, "metrics.store_series", Value::from(false))?;
    let cfg = SimConfig::from_json_value(value).map_err(|e| anyhow::anyhow!("{e}"))?;

    let mut scores: Vec<f64> = (0..runs as u64)
        .into_par_iter()
        .map(|i| -> Result<f64> {
            Ok(World::new(cfg.clone(), i)
                .map_err(|e| anyhow::anyhow!("{e}"))?
                .run()
                .final_dispersion)
        })
        .collect::<Result<Vec<_>>>()?;
    scores.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    Ok(scores[scores.len() / 2])
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
) -> Result<SearchResult> {
    let dims = 2 * states;
    // Start from Gauci's constants tiled across the extra states: the search
    // begins at the known-good four-constant controller rather than at random,
    // so a failure to improve is a statement about the search, not the start.
    let seed_point: Vec<f64> = (0..dims)
        .map(|i| swarm_core::GAUCI_CONSTANTS[i % 4])
        .collect();

    let mut es = SepCmaEs::new(seed_point, 0.3, seed);
    let lambda = es.population_size();
    let generations = budget / lambda;
    let mut best = (f64::INFINITY, vec![0.0; dims]);
    let mut history = Vec::with_capacity(generations);

    for g in 0..generations {
        let candidates = es.ask();
        let mut fitness = Vec::with_capacity(candidates.len());
        for (x, penalty) in &candidates {
            let f = evaluate(base, x, runs_per_eval, training_seed_base)? + 10.0 * penalty;
            if f < best.0 {
                best = (f, x.clone());
            }
            fitness.push(f);
        }
        es.tell(&candidates, &fitness);
        history.push(best.0);
        eprint!("\r  generation {}/{generations}  best {:.4}", g + 1, best.0);
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
        best_constants: best.1,
        best_training_objective: best.0,
        history,
        objective: "median final_dispersion over runs_per_evaluation trials, \
                    lower is better; +10x squared box-repair penalty"
            .into(),
        optimiser: "sep-CMA-ES (Ros & Hansen 2008), diagonal covariance".into(),
    })
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
