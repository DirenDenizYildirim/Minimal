//! The simulation loop.
//!
//! One step, in order:
//!   1. every robot reads its line-of-sight sensor (synchronous update — all
//!      readings are taken before anything moves);
//!   2. occlusion corrupts the readings;
//!   3. the lookup table maps `(sensor_state, memory, rx)` to wheel commands;
//!   4. terrain maps commanded wheel speeds to realised ones;
//!   5. exact-arc integration;
//!   6. contact resolution.
//!
//! Cost is O(n^2) per step, dominated by step 1 — the build doc's stated Tier-1
//! budget.

use crate::config::SimConfig;
use crate::controller::{Capability, Provenance, TableController};
use crate::geom::Vec2;
use crate::metrics;
use crate::occlusion::{Occlusion, OcclusionTally};
use crate::pursuer::Pursuer;
use crate::rng::{rng_from, split_seed, Rng};
use crate::robot::{integrate, turn_radius, Pose};
use crate::sensor::{cast, Target};
use crate::terrain::Terrain;
use rand::Rng as _;
use rand_distr::{Distribution, Normal};
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, Serialize, Deserialize)]
pub struct Sample {
    pub t: f64,
    pub dispersion: f64,
    pub clusters: usize,
    pub largest_cluster_fraction: f64,
}

/// One trial's outcome. This is the row the sweep harness aggregates.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RunRecord {
    pub run_index: u64,
    pub seed: u64,
    pub n: usize,
    pub duration: f64,
    pub capability: Capability,
    pub provenance: Provenance,
    /// False for every optimiser-found row: the reported minimum is an **upper
    /// bound** on `c*(theta)`, not a minimum (build doc section 2.2).
    pub minimum_is_tight: bool,
    /// Radius of the state-0 circle in metres — the controller's only intrinsic
    /// length scale, and the quantity hypothesis H2 says the terrain transition
    /// should scale with.
    pub state0_turn_radius: Option<f64>,
    pub initial_dispersion: f64,
    pub final_dispersion: f64,
    /// `final / initial`. Below 1 means the swarm contracted.
    pub dispersion_ratio: f64,
    pub final_clusters: usize,
    pub final_largest_cluster_fraction: f64,
    /// Whether the swarm was exactly one cluster **at tau**. This is a
    /// knife-edge: an aggregated swarm typically keeps one robot near the link
    /// threshold, so the boolean flips between samples. Kept for comparability,
    /// but `final_largest_cluster_fraction` and `fraction_time_single_cluster`
    /// are the stable readouts.
    pub single_cluster: bool,
    /// First sample time at which the swarm was a single cluster, if ever.
    pub time_to_first_single_cluster: Option<f64>,
    /// Whether the swarm was *ever* a single cluster during the trial.
    ///
    /// This — not `single_cluster` at tau — is the criterion the aggregation
    /// literature actually uses. Steinberg and Solovey (2024) define aggregation
    /// as the union of discs around the robots becoming **connected**; the
    /// definition does not require them to stay connected. For a small swarm the
    /// two differ enormously: a pair reaches contact in ~90% of runs and is
    /// touching at tau in ~10%. See `docs/decisions/0005-aggregation-criterion.md`.
    pub ever_single_cluster: bool,
    /// Share of samples at which the swarm was a single cluster. Robust to the
    /// flicker above, and the metric to use for time-resolved comparisons.
    pub fraction_time_single_cluster: f64,
    pub realised_fn_rate: f64,
    pub realised_fp_rate: f64,
    pub pursuers: usize,
    pub captures: u64,
    pub survivors: usize,
    /// Share of the swarm still alive at tau.
    pub survival_fraction: f64,
    /// **Idea B's primary metric**: captures per unit time, normalised by swarm
    /// size.
    ///
    /// Not survival at tau. For rho > 1 a locked robot cannot escape, so
    /// survival at tau collapses into a travel-time quantity and stops measuring
    /// anything about the swarm's behaviour. Capture rate keeps measuring how
    /// hard the swarm is to hunt.
    ///
    /// **It saturates.** Once the swarm is wiped out the rate is pinned at
    /// `1/tau` regardless of how much harder the swarm made the hunt, and every
    /// configuration scores the same. Any Idea B sweep must pick tau short
    /// enough that the most dangerous cell in the grid still leaves survivors —
    /// check `survivors > 0` across the grid before reading the surface — or use
    /// `time_to_wipeout` instead, which does not saturate.
    ///
    /// This is not hypothetical: at rho = 1.5 with unlimited range the pursuer
    /// takes a swarm of 20 in under 20 s, while the base task needs ~600 s to
    /// aggregate at all. The two timescales do not overlap, so an Idea B design
    /// has to lower rho, shrink the capture distance, or score the hunt by its
    /// timing rather than its total.
    pub capture_rate: f64,
    /// When the first robot was taken.
    pub time_to_first_capture: Option<f64>,
    /// When the last robot was taken, if the swarm was wiped out.
    ///
    /// The non-saturating counterpart to `capture_rate`: in the lethal regime
    /// where every configuration loses every robot, how *long* it took is still
    /// a measure of how hard the swarm was to hunt.
    pub time_to_wipeout: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub series: Option<Vec<Sample>>,
    /// Sweep-cell coordinates, attached by the CLI.
    #[serde(default, skip_serializing_if = "serde_json::Map::is_empty")]
    pub cell: serde_json::Map<String, serde_json::Value>,
}

/// Sub-stream identifiers, so that changing the swarm size does not reshuffle
/// the terrain and changing the terrain does not reshuffle the sensor dropouts.
const TERRAIN_SEED_STREAM: u64 = 0xE1;
const OCCLUSION_SEED_STREAM: u64 = 0xE2;
const PURSUER_SEED_STREAM: u64 = 0xE3;

pub struct World {
    cfg: SimConfig,
    controller: TableController,
    targets: Vec<Target>,
    memory: Vec<u32>,
    rx: Vec<u32>,
    tx: Vec<u32>,
    terrain: Terrain,
    occlusion: Occlusion,
    tally: OcclusionTally,
    pursuers: Vec<Pursuer>,
    /// Scratch buffer for what the robots' sensors can see: the robots
    /// themselves (indices aligned with `targets`) followed by the pursuers.
    /// Reused each step so the sensor loop allocates nothing.
    scene: Vec<Target>,
    captures: u64,
    first_capture: Option<f64>,
    last_capture: Option<f64>,
    rng: Rng,
    seed: u64,
    run_index: u64,
    t: f64,
}

impl World {
    pub fn new(cfg: SimConfig, run_index: u64) -> Result<Self, crate::config::ConfigError> {
        cfg.validate()?;
        let controller = cfg
            .controller
            .build(cfg.sensor.encoding)
            .map_err(|e| crate::config::ConfigError(format!("controller: {e}")))?;

        let seed = split_seed(cfg.sim.seed, run_index);
        let mut rng = rng_from(seed);

        // The environment fields get their own seed streams so that changing the
        // number of robots does not reshuffle the terrain, and vice versa.
        let terrain = Terrain::new(cfg.terrain, split_seed(seed, TERRAIN_SEED_STREAM));
        let occlusion = Occlusion::new(cfg.occlusion, split_seed(seed, OCCLUSION_SEED_STREAM));

        let n = cfg.swarm.n;
        let targets = place_robots(&cfg, n, &mut rng);
        let pursuers = place_pursuers(&cfg, &targets, split_seed(seed, PURSUER_SEED_STREAM));

        Ok(Self {
            controller,
            targets,
            memory: vec![0; n],
            rx: vec![0; n],
            tx: vec![0; n],
            terrain,
            occlusion,
            tally: OcclusionTally::default(),
            scene: Vec::with_capacity(n + pursuers.len()),
            captures: 0,
            first_capture: None,
            last_capture: None,
            pursuers,
            rng,
            seed,
            run_index,
            t: 0.0,
            cfg,
        })
    }

    pub fn time(&self) -> f64 {
        self.t
    }

    /// All robot positions, captured ones included. Use `alive_positions` for
    /// anything that scores the swarm.
    pub fn positions(&self) -> Vec<Vec2> {
        self.targets.iter().map(|t| t.pose.p).collect()
    }

    pub fn poses(&self) -> Vec<Pose> {
        self.targets.iter().map(|t| t.pose).collect()
    }

    fn link_distance(&self) -> f64 {
        self.cfg.metrics.cluster_link_radii * self.cfg.robot.radius
    }

    pub fn sample(&self) -> Sample {
        let p = self.alive_positions();
        let link = self.link_distance();
        Sample {
            t: self.t,
            dispersion: metrics::dispersion(&p, self.cfg.robot.radius),
            clusters: metrics::cluster_count(&p, link),
            largest_cluster_fraction: metrics::largest_cluster_fraction(&p, link),
        }
    }

    pub fn step(&mut self) {
        let n = self.targets.len();
        let vmax = self.robot_vmax();
        let axle = self.cfg.robot.axle_length;
        let dt = self.cfg.sim.dt;

        // Scene the robots' sensors read: the robots themselves, index-aligned,
        // followed by the pursuers. Built before anything moves, so all readings
        // are taken from the same instant.
        self.scene.clear();
        self.scene.extend_from_slice(&self.targets);
        self.scene
            .extend(self.pursuers.iter().map(|p| p.as_target()));

        // 1-3: read, corrupt, look up.
        let mut commands = vec![[0.0f64; 2]; n];
        let mut next_memory = vec![0u32; n];
        for i in 0..n {
            let observer = self.targets[i];
            if !observer.alive {
                continue;
            }
            let hit = cast(&observer, i, &self.scene, &self.cfg.sensor);
            let hit = self
                .occlusion
                .corrupt(hit, observer.pose.p, &mut self.rng, &mut self.tally);
            let state = self.cfg.sensor.encoding.encode(hit);
            let entry = self.controller.act(state, self.memory[i], self.rx[i]);
            commands[i] = [entry.wheels[0] * vmax, entry.wheels[1] * vmax];
            next_memory[i] = entry.next_memory;
            self.tx[i] = entry.tx;
        }

        // 4-5: terrain, actuation noise, then motion.
        let wheel_noise = self.cfg.noise.wheel_noise * vmax;
        let slip = (wheel_noise > 0.0)
            .then(|| Normal::new(0.0, wheel_noise).expect("sigma is finite and positive"));
        for i in 0..n {
            if !self.targets[i].alive {
                continue;
            }
            let pose = self.targets[i].pose;
            let mut realised = self.terrain.apply(&pose, axle, commands[i], &mut self.rng);
            if let Some(slip) = slip {
                realised[0] += slip.sample(&mut self.rng);
                realised[1] += slip.sample(&mut self.rng);
            }
            self.targets[i].pose = integrate(pose, realised[0], realised[1], axle, dt);
            self.memory[i] = next_memory[i];
        }

        // Broadcast is wired but inert until row B4: with K = 0 every table has
        // a single rx column, so rx stays 0 and the index is unaffected.
        self.rx.fill(0);

        // 6: contacts.
        if self.cfg.sim.collisions {
            self.resolve_contacts();
        }

        // 7: the pursuers move last, against the robots' updated positions.
        for k in 0..self.pursuers.len() {
            let mut p = std::mem::replace(
                &mut self.pursuers[k],
                Pursuer::new(
                    Pose::default(),
                    0.0,
                    crate::pursuer::PursuerConfig::default(),
                ),
            );
            if let Some(victim) = p.step(&self.targets, dt, axle, vmax, &mut self.rng) {
                self.targets[victim].alive = false;
                self.captures += 1;
                self.first_capture.get_or_insert(self.t);
                self.last_capture = Some(self.t);
            }
            self.pursuers[k] = p;
        }
        self.t += dt;
    }

    /// Positions of the robots still in play. Every metric uses this: a captured
    /// robot is out of the swarm, not a member sitting at its last position.
    fn alive_positions(&self) -> Vec<Vec2> {
        self.targets
            .iter()
            .filter(|t| t.alive)
            .map(|t| t.pose.p)
            .collect()
    }

    pub fn survivors(&self) -> usize {
        self.targets.iter().filter(|t| t.alive).count()
    }

    pub fn captures(&self) -> u64 {
        self.captures
    }

    fn robot_vmax(&self) -> f64 {
        self.cfg.robot.max_wheel_speed
    }

    /// Positional relaxation: push overlapping bodies apart. An approximation of
    /// contact physics, adequate for Tier 1; Tier 2 (ARGoS) is where real
    /// contact dynamics get checked.
    fn resolve_contacts(&mut self) {
        let n = self.targets.len();
        let min_d = 2.0 * self.cfg.robot.radius;
        let tol = self.cfg.sim.contact_tolerance;
        for _ in 0..self.cfg.sim.collision_iterations {
            let mut worst = 0.0f64;
            for i in 0..n {
                for j in (i + 1)..n {
                    let delta = self.targets[j].pose.p - self.targets[i].pose.p;
                    let d = delta.norm();
                    if d >= min_d {
                        continue;
                    }
                    worst = worst.max(min_d - d);
                    let dir = if d < 1e-9 {
                        // Exactly coincident: pick a direction rather than divide by zero.
                        Vec2::from_angle(self.rng.gen::<f64>() * std::f64::consts::TAU)
                    } else {
                        delta / d
                    };
                    let push = dir * (0.5 * (min_d - d));
                    self.targets[i].pose.p = self.targets[i].pose.p - push;
                    self.targets[j].pose.p += push;
                }
            }
            if worst <= tol {
                break;
            }
        }
    }

    pub fn run(mut self) -> RunRecord {
        let initial = self.sample();
        let interval = self.cfg.metrics.sample_interval;
        let store = self.cfg.metrics.store_series && interval > 0.0;
        let mut series = if store { Some(vec![initial]) } else { None };
        let mut time_to_single = if initial.clusters == 1 {
            Some(0.0)
        } else {
            None
        };
        let mut samples_taken = 1u64;
        let mut samples_single = u64::from(initial.clusters == 1);

        let steps = (self.cfg.sim.duration / self.cfg.sim.dt).round() as u64;
        let every = if interval > 0.0 {
            ((interval / self.cfg.sim.dt).round() as u64).max(1)
        } else {
            u64::MAX
        };

        for s in 1..=steps {
            self.step();
            if s % every == 0 {
                let sample = self.sample();
                samples_taken += 1;
                if sample.clusters == 1 {
                    samples_single += 1;
                    if time_to_single.is_none() {
                        time_to_single = Some(sample.t);
                    }
                }
                if let Some(v) = series.as_mut() {
                    v.push(sample);
                }
            }
        }

        let final_sample = self.sample();
        if time_to_single.is_none() && final_sample.clusters == 1 {
            time_to_single = Some(final_sample.t);
        }
        if let Some(v) = series.as_mut() {
            if v.last().map_or(true, |l| l.t < final_sample.t) {
                v.push(final_sample);
            }
        }

        let vmax = self.cfg.robot.max_wheel_speed;
        let state0 = self.controller.act(0, 0, 0);
        let r0 = turn_radius(
            state0.wheels[0] * vmax,
            state0.wheels[1] * vmax,
            self.cfg.robot.axle_length,
        );

        RunRecord {
            run_index: self.run_index,
            seed: self.seed,
            n: self.cfg.swarm.n,
            duration: self.cfg.sim.duration,
            capability: self.controller.capability(),
            provenance: self.cfg.controller.provenance(),
            minimum_is_tight: self.cfg.controller.provenance().is_tight(),
            state0_turn_radius: r0,
            initial_dispersion: initial.dispersion,
            final_dispersion: final_sample.dispersion,
            dispersion_ratio: if initial.dispersion > 0.0 {
                final_sample.dispersion / initial.dispersion
            } else {
                f64::NAN
            },
            final_clusters: final_sample.clusters,
            final_largest_cluster_fraction: final_sample.largest_cluster_fraction,
            single_cluster: final_sample.clusters == 1,
            time_to_first_single_cluster: time_to_single,
            ever_single_cluster: time_to_single.is_some(),
            fraction_time_single_cluster: samples_single as f64 / samples_taken as f64,
            realised_fn_rate: self.tally.realised_fn_rate(),
            realised_fp_rate: self.tally.realised_fp_rate(),
            pursuers: self.pursuers.len(),
            captures: self.captures,
            survivors: self.survivors(),
            survival_fraction: self.survivors() as f64 / self.cfg.swarm.n as f64,
            capture_rate: self.captures as f64 / (self.cfg.sim.duration * self.cfg.swarm.n as f64),
            time_to_first_capture: self.first_capture,
            time_to_wipeout: (self.survivors() == 0).then_some(()).and(self.last_capture),
            series,
            cell: serde_json::Map::new(),
        }
    }
}

/// Uniform non-overlapping placement in a disk, with random headings.
fn place_robots(cfg: &SimConfig, n: usize, rng: &mut Rng) -> Vec<Target> {
    let r = cfg.robot.radius;
    let mut radius = cfg.swarm.init.start_radius(n, r);
    let mut out: Vec<Target> = Vec::with_capacity(n);
    let mut attempts = 0usize;

    while out.len() < n {
        let a = rng.gen::<f64>() * std::f64::consts::TAU;
        let d = radius * rng.gen::<f64>().sqrt(); // uniform over the disk
        let p = Vec2::new(d * a.cos(), d * a.sin());
        attempts += 1;
        if out.iter().all(|t| (t.pose.p - p).norm() >= 2.0 * r) {
            out.push(Target::robot(
                Pose {
                    p,
                    theta: rng.gen::<f64>() * std::f64::consts::TAU,
                },
                r,
            ));
            attempts = 0;
        } else if attempts > 2000 {
            // Too dense to place by rejection: grow the disk rather than
            // silently overlapping bodies or looping forever.
            radius *= 1.1;
            attempts = 0;
        }
    }
    out
}

/// Pursuers start on the far edge of the swarm's start disk, facing inward.
///
/// Not at the centre: a pursuer that begins inside the swarm has already solved
/// the search problem, which is one of the two mechanisms the experiment is
/// about. Starting outside means finite `r_p` costs it something from the first
/// step.
fn place_pursuers(cfg: &SimConfig, robots: &[Target], seed: u64) -> Vec<Pursuer> {
    let Some(pcfg) = cfg.pursuer else {
        return Vec::new();
    };
    let mut rng = rng_from(seed);
    let start_radius = cfg.swarm.init.start_radius(cfg.swarm.n, cfg.robot.radius);
    let centre = crate::metrics::centroid(&robots.iter().map(|t| t.pose.p).collect::<Vec<_>>());
    (0..pcfg.count)
        .map(|_| {
            let a = rng.gen::<f64>() * std::f64::consts::TAU;
            let p = centre + Vec2::from_angle(a) * start_radius;
            // Facing the swarm centre.
            let pose = Pose {
                p,
                theta: (centre - p).angle(),
            };
            Pursuer::new(pose, cfg.robot.radius, pcfg)
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::{MetricsConfig, SimParams, SwarmConfig};
    use crate::controller::ControllerConfig;

    fn short(n: usize, duration: f64) -> SimConfig {
        SimConfig {
            swarm: SwarmConfig {
                n,
                ..Default::default()
            },
            sim: SimParams {
                duration,
                seed: 12345,
                ..Default::default()
            },
            metrics: MetricsConfig {
                sample_interval: 0.0,
                ..Default::default()
            },
            ..Default::default()
        }
    }

    #[test]
    fn robots_are_placed_without_overlap() {
        let cfg = short(50, 1.0);
        let w = World::new(cfg.clone(), 0).unwrap();
        let p = w.positions();
        assert_eq!(p.len(), 50);
        for i in 0..p.len() {
            for j in (i + 1)..p.len() {
                assert!(
                    (p[i] - p[j]).norm() >= 2.0 * cfg.robot.radius - 1e-9,
                    "bodies {i} and {j} overlap at start"
                );
            }
        }
    }

    #[test]
    fn runs_are_bit_for_bit_reproducible() {
        let cfg = short(15, 30.0);
        let a = World::new(cfg.clone(), 3).unwrap().run();
        let b = World::new(cfg, 3).unwrap().run();
        assert_eq!(a.final_dispersion, b.final_dispersion);
        assert_eq!(a.final_clusters, b.final_clusters);
        assert_eq!(a.seed, b.seed);
    }

    #[test]
    fn different_run_indices_give_different_trials() {
        let cfg = short(15, 30.0);
        let a = World::new(cfg.clone(), 0).unwrap().run();
        let b = World::new(cfg, 1).unwrap().run();
        assert_ne!(a.seed, b.seed);
        assert_ne!(a.initial_dispersion, b.initial_dispersion);
    }

    #[test]
    fn contact_resolution_keeps_residual_overlap_negligible() {
        // Positional relaxation is iterative and pairwise, so a dense cluster
        // keeps a small residual overlap rather than reaching an exact
        // non-overlapping configuration. That is an accepted Tier-1
        // approximation — real contact dynamics are Tier 2 (ARGoS) — but the
        // residual has to stay far below the body scale or the effective robot
        // radius, and hence the dispersion metric, would be biased.
        let cfg = short(25, 60.0);
        let mut w = World::new(cfg.clone(), 1).unwrap();
        for _ in 0..600 {
            w.step();
        }
        let p = w.positions();
        let min_d = 2.0 * cfg.robot.radius;
        let mut worst: f64 = 0.0;
        for i in 0..p.len() {
            for j in (i + 1)..p.len() {
                worst = worst.max(min_d - (p[i] - p[j]).norm());
            }
        }
        assert!(
            worst < 0.001 * min_d,
            "residual overlap {worst} m is more than 0.1% of the body diameter {min_d} m"
        );
    }

    #[test]
    fn a_lone_robot_traces_the_state0_circle() {
        // n = 1 never sees anything, so it must stay on the circle of radius R0
        // for the whole trial. This is the sanity check that the controller,
        // the scaling by max_wheel_speed and the integrator agree.
        let mut cfg = short(1, 120.0);
        cfg.sim.dt = 0.01;
        let rec = World::new(cfg.clone(), 0).unwrap().run();
        let r0 = rec.state0_turn_radius.unwrap();

        let mut w = World::new(cfg.clone(), 0).unwrap();
        let start = w.poses()[0];
        // The instantaneous centre of rotation sits at R0, ninety degrees
        // counter-clockwise of the heading -- which is how the paper describes
        // it. Derived from the config, not hardcoded, so a parameter change
        // cannot silently make this test vacuous.
        let (vl, vr) = {
            let c = crate::GAUCI_CONSTANTS;
            (
                c[0] * cfg.robot.max_wheel_speed,
                c[1] * cfg.robot.max_wheel_speed,
            )
        };
        let signed_r = 0.5 * (vl + vr) * cfg.robot.axle_length / (vr - vl);
        assert!(
            signed_r > 0.0,
            "ICR must be counter-clockwise of the heading"
        );
        let centre = start.p + start.heading().perp() * signed_r;
        for _ in 0..12_000 {
            w.step();
            let d = (w.positions()[0] - centre).norm();
            assert!(
                (d - r0).abs() < 1e-6,
                "drifted off the circle: {d} vs R0 {r0}"
            );
        }
    }

    #[test]
    fn gauci_controller_contracts_a_swarm_in_a_clean_arena() {
        // The behavioural gate in miniature: the published constants must
        // aggregate, not disperse. Absolute values are checked in
        // tests/gauci_baseline.rs; here we only assert the sign of the effect.
        let mut cfg = short(20, 600.0);
        cfg.sim.seed = 2024;
        let contracted = (0..5)
            .filter(|i| World::new(cfg.clone(), *i).unwrap().run().dispersion_ratio < 1.0)
            .count();
        assert_eq!(contracted, 5, "aggregation failed in a clean arena");
    }

    #[test]
    fn a_stationary_controller_does_not_aggregate() {
        // Negative control: if this passed, the metric would be measuring the
        // initial placement rather than the behaviour.
        let mut cfg = short(20, 300.0);
        cfg.controller = ControllerConfig::Gauci {
            constants: [0.0, 0.0, 0.0, 0.0],
            provenance: crate::controller::Provenance::HandDesigned,
        };
        let rec = World::new(cfg, 0).unwrap().run();
        assert!((rec.dispersion_ratio - 1.0).abs() < 1e-9);
        assert!(!rec.single_cluster);
    }

    #[test]
    fn heavy_false_negatives_hurt_aggregation() {
        // The week-3 shakedown's expected direction of effect.
        let mut cfg = short(20, 600.0);
        cfg.sim.seed = 99;
        let clean: f64 = (0..5)
            .map(|i| World::new(cfg.clone(), i).unwrap().run().dispersion_ratio)
            .sum::<f64>()
            / 5.0;
        cfg.occlusion.fn_rate = 0.9;
        let blinded: f64 = (0..5)
            .map(|i| World::new(cfg.clone(), i).unwrap().run().dispersion_ratio)
            .sum::<f64>()
            / 5.0;
        assert!(blinded > clean, "clean {clean} vs 90% dropout {blinded}");
    }

    #[test]
    fn reaching_a_cluster_and_being_one_at_tau_are_different_measurements() {
        // The distinction the small-n gate turned on. A pair reaches contact in
        // most runs and is almost never still touching at tau, because nothing
        // in the controller holds two robots together once they arrive.
        let mut cfg = short(2, 600.0);
        cfg.metrics.sample_interval = 1.0;
        cfg.sim.seed = 20260904;
        let recs: Vec<_> = (0..40)
            .map(|i| World::new(cfg.clone(), i).unwrap().run())
            .collect();
        let ever = recs.iter().filter(|r| r.ever_single_cluster).count();
        let at_tau = recs.iter().filter(|r| r.single_cluster).count();
        assert!(ever > 3 * at_tau, "ever {ever} vs at tau {at_tau}");
        assert!(
            ever * 4 > recs.len() * 3,
            "pairs should reach contact in most runs: {ever}/40"
        );
        for r in &recs {
            assert_eq!(
                r.ever_single_cluster,
                r.time_to_first_single_cluster.is_some()
            );
        }
    }

    #[test]
    fn time_resolved_aggregates_survive_dropping_the_series() {
        // A sweep drops the per-sample rows for file size, so the aggregate
        // metrics must not be computed from the stored series.
        let mut cfg = short(20, 300.0);
        cfg.metrics.sample_interval = 10.0;
        cfg.sim.seed = 4242;
        let with = World::new(cfg.clone(), 0).unwrap().run();
        cfg.metrics.store_series = false;
        let without = World::new(cfg, 0).unwrap().run();
        assert!(with.series.is_some());
        assert!(without.series.is_none());
        assert_eq!(
            with.fraction_time_single_cluster,
            without.fraction_time_single_cluster
        );
        assert_eq!(
            with.time_to_first_single_cluster,
            without.time_to_first_single_cluster
        );
    }

    #[test]
    fn dispersion_ignores_the_link_distance_but_cluster_counts_do_not() {
        // Measured on the baseline (configs/sweeps/link_distance_sensitivity.toml,
        // 30 runs/cell): final dispersion is 1.401 at every link distance from
        // 2.2R to 6R, while the share of time the swarm reads as a single
        // cluster climbs from 0.43 to 0.98. So dispersion is the metric that can
        // carry a threshold `T`, and any cluster-count number must be quoted
        // with the link distance it used. See docs/validation.md.
        let mut cfg = short(20, 300.0);
        cfg.metrics.sample_interval = 10.0;
        cfg.sim.seed = 20260904;

        let at = |radii: f64, cfg: &SimConfig| {
            let mut c = cfg.clone();
            c.metrics.cluster_link_radii = radii;
            let recs: Vec<_> = (0..4)
                .map(|i| World::new(c.clone(), i).unwrap().run())
                .collect();
            let disp = recs.iter().map(|r| r.final_dispersion).sum::<f64>() / 4.0;
            let frac = recs
                .iter()
                .map(|r| r.fraction_time_single_cluster)
                .sum::<f64>()
                / 4.0;
            (disp, frac)
        };
        let (tight_disp, tight_frac) = at(2.2, &cfg);
        let (loose_disp, loose_frac) = at(6.0, &cfg);
        assert!(
            (tight_disp - loose_disp).abs() < 1e-12,
            "dispersion moved with the link distance: {tight_disp} vs {loose_disp}"
        );
        assert!(
            loose_frac > tight_frac + 0.15,
            "cluster fraction barely moved: {tight_frac} vs {loose_frac}"
        );
    }

    fn with_pursuer(n: usize, duration: f64, p: crate::pursuer::PursuerConfig) -> SimConfig {
        SimConfig {
            pursuer: Some(p),
            ..short(n, duration)
        }
    }

    #[test]
    fn wipeout_timing_is_recorded_and_does_not_saturate() {
        use crate::pursuer::PursuerConfig;
        let v1 = PursuerConfig {
            range: None,
            confusion: 0.0,
            speed_ratio: 1.5,
            ..Default::default()
        };
        let wipeout = |p: PursuerConfig| {
            let cfg = with_pursuer(20, 300.0, p);
            let recs: Vec<_> = (0..6)
                .map(|i| World::new(cfg.clone(), i).unwrap().run())
                .collect();
            // Both configurations wipe the swarm out, so capture_rate is pinned...
            assert!(recs.iter().all(|r| r.survivors == 0));
            let rates: Vec<f64> = recs.iter().map(|r| r.capture_rate).collect();
            assert!(
                rates.windows(2).all(|w| w[0] == w[1]),
                "capture_rate should be saturated"
            );
            // ...but the timing still separates them.
            recs.iter().map(|r| r.time_to_wipeout.unwrap()).sum::<f64>() / 6.0
        };
        let fast = wipeout(v1);
        let slow = wipeout(PursuerConfig {
            confusion: 3.0,
            confusion_radius: 0.5,
            ..v1
        });
        assert!(
            slow > fast * 1.5,
            "confusion did not slow the hunt: {slow} vs {fast}"
        );
    }

    #[test]
    fn a_pursuer_captures_and_the_swarm_shrinks() {
        use crate::pursuer::PursuerConfig;
        let cfg = with_pursuer(
            20,
            600.0,
            PursuerConfig {
                range: None,
                confusion: 0.0,
                speed_ratio: 1.5,
                ..Default::default()
            },
        );
        let rec = World::new(cfg.clone(), 0).unwrap().run();
        assert_eq!(rec.pursuers, 1);
        assert!(
            rec.captures > 0,
            "an unlimited faster pursuer caught nobody"
        );
        assert_eq!(rec.survivors, cfg.swarm.n - rec.captures as usize);
        assert!((rec.survival_fraction - rec.survivors as f64 / 20.0).abs() < 1e-12);
        assert!((rec.capture_rate - rec.captures as f64 / (600.0 * 20.0)).abs() < 1e-12);
    }

    #[test]
    fn no_pursuer_means_no_captures() {
        let rec = World::new(short(20, 300.0), 0).unwrap().run();
        assert_eq!(rec.pursuers, 0);
        assert_eq!(rec.captures, 0);
        assert_eq!(rec.survivors, 20);
        assert_eq!(rec.capture_rate, 0.0);
    }

    #[test]
    #[ignore = "calibration probe, run explicitly"]
    fn probe_pursuer_lethality() {
        use crate::pursuer::PursuerConfig;
        for tau in [10.0f64, 20.0, 30.0, 60.0, 120.0] {
            for (label, p) in [
                (
                    "v1 (inf range, k=0)",
                    PursuerConfig {
                        range: None,
                        confusion: 0.0,
                        speed_ratio: 1.5,
                        ..Default::default()
                    },
                ),
                (
                    "r_p=0.3",
                    PursuerConfig {
                        range: Some(0.3),
                        confusion: 0.0,
                        speed_ratio: 1.5,
                        ..Default::default()
                    },
                ),
                (
                    "kappa=5",
                    PursuerConfig {
                        range: None,
                        confusion: 5.0,
                        confusion_radius: 0.5,
                        speed_ratio: 1.5,
                        ..Default::default()
                    },
                ),
            ] {
                let cfg = with_pursuer(20, tau, p);
                let recs: Vec<_> = (0..8)
                    .map(|i| World::new(cfg.clone(), i).unwrap().run())
                    .collect();
                let cap: f64 = recs.iter().map(|r| r.captures as f64).sum::<f64>() / 8.0;
                let minsurv = recs.iter().map(|r| r.survivors).min().unwrap();
                println!(
                    "tau={tau:5.0} {label:22} mean captures {cap:5.2}  min survivors {minsurv:3}"
                );
            }
        }
    }

    #[test]
    fn confusion_reduces_the_capture_rate() {
        // tau = 60 s: long enough for the counts to separate, short enough that
        // even the v1 corner leaves survivors. capture_rate saturates once the
        // swarm is wiped out — see the note on `RunRecord::capture_rate`.
        use crate::pursuer::PursuerConfig;
        let runs = |p: PursuerConfig| {
            let cfg = with_pursuer(20, 60.0, p);
            let recs: Vec<_> = (0..12)
                .map(|i| World::new(cfg.clone(), i).unwrap().run())
                .collect();
            assert!(
                recs.iter().all(|r| r.survivors > 0),
                "swarm wiped out; shorten tau or this comparison is vacuous"
            );
            recs
        };
        let v1 = PursuerConfig {
            range: None,
            confusion: 0.0,
            speed_ratio: 1.5,
            ..Default::default()
        };
        let mean =
            |rs: &[RunRecord]| rs.iter().map(|r| r.capture_rate).sum::<f64>() / rs.len() as f64;
        let worst = mean(&runs(v1));
        let confused = mean(&runs(PursuerConfig {
            confusion: 5.0,
            confusion_radius: 0.5,
            ..v1
        }));
        assert!(worst > 0.0);
        assert!(
            confused < worst * 0.8,
            "confusion did not cost the pursuer: {confused} vs {worst}"
        );
    }

    #[test]
    fn finite_range_costs_the_pursuer_a_search_after_every_capture() {
        // Search cost is **recurring**, which was not obvious in advance.
        //
        // The expected story was that finite range costs the pursuer one search
        // at the start and nothing afterwards, since inside a packed cluster the
        // neighbours are closer than any plausible r_p. Measured, that is wrong:
        // the post-discovery rate is still halved. The reason is handling time —
        // every capture drops the lock and puts the pursuer back into search for
        // the handling period, and with a short range it has to re-find a target
        // each time rather than simply turning to the next one.
        //
        // So the two protective mechanisms are not as separable as the build doc
        // implies: handling time converts a one-off search cost into a per-capture
        // one, and the pursuer's range interacts with its handling time. An Idea B
        // sweep must vary them together rather than treating r_p as a pure
        // find-the-swarm dial.
        use crate::pursuer::PursuerConfig;
        let v1 = PursuerConfig {
            range: None,
            confusion: 0.0,
            speed_ratio: 1.5,
            ..Default::default()
        };
        let tau = 60.0;
        let stats = |p: PursuerConfig| {
            let cfg = with_pursuer(20, tau, p);
            let recs: Vec<_> = (0..12)
                .map(|i| World::new(cfg.clone(), i).unwrap().run())
                .collect();
            let first: Vec<f64> = recs
                .iter()
                .filter_map(|r| r.time_to_first_capture)
                .collect();
            let mean_first = first.iter().sum::<f64>() / first.len() as f64;
            let overall = recs.iter().map(|r| r.capture_rate).sum::<f64>() / recs.len() as f64;
            // Rate measured from the opening capture, which removes the search.
            let after: f64 = recs
                .iter()
                .filter_map(|r| {
                    r.time_to_first_capture
                        .map(|t| r.captures as f64 / ((tau - t).max(1e-9) * r.n as f64))
                })
                .sum::<f64>()
                / first.len() as f64;
            (mean_first, overall, after)
        };
        let (t_inf, overall_inf, after_inf) = stats(v1);
        let (t_short, overall_short, after_short) = stats(PursuerConfig {
            range: Some(0.1),
            ..v1
        });

        assert!(
            t_short > t_inf * 1.5,
            "a short range did not delay the first capture: {t_short} vs {t_inf}"
        );
        assert!(
            overall_short < overall_inf * 0.8,
            "the delay should show up in the whole-trial rate: {overall_short} vs {overall_inf}"
        );
        assert!(
            after_short < after_inf * 0.8,
            "the range cost should persist after discovery, via handling: \
             {after_short} vs {after_inf}"
        );
    }

    #[test]
    fn captured_robots_leave_the_swarm_entirely() {
        // A captured robot must stop sensing, stop moving, stop occluding and
        // stop counting towards the metrics. If it kept its last position it
        // would sit inside the cluster inflating the aggregation score forever.
        use crate::pursuer::PursuerConfig;
        let cfg = with_pursuer(
            10,
            300.0,
            PursuerConfig {
                range: None,
                confusion: 0.0,
                speed_ratio: 2.0,
                ..Default::default()
            },
        );
        let mut w = World::new(cfg, 0).unwrap();
        for _ in 0..3000 {
            w.step();
        }
        assert!(w.captures() > 0);
        assert_eq!(w.survivors(), 10 - w.captures() as usize);
        assert_eq!(w.alive_positions().len(), w.survivors());
        assert_eq!(
            w.positions().len(),
            10,
            "dead bodies stay in the array, out of the metrics"
        );
        // Frozen: a captured robot's pose must not change again.
        let dead: Vec<Vec2> = w
            .targets
            .iter()
            .filter(|t| !t.alive)
            .map(|t| t.pose.p)
            .collect();
        for _ in 0..200 {
            w.step();
        }
        let dead_after: Vec<Vec2> = w
            .targets
            .iter()
            .filter(|t| !t.alive)
            .map(|t| t.pose.p)
            .collect();
        for (a, b) in dead.iter().zip(&dead_after) {
            assert!((*a - *b).norm() < 1e-12, "a captured robot moved");
        }
    }

    #[test]
    fn robots_can_see_the_pursuer_when_the_sensor_can_tell_it_apart() {
        // Row B1 needs the ternary sensor to distinguish robot from pursuer.
        // Here we only check the plumbing: the pursuer is in the scene the
        // robots' rays are cast against.
        use crate::pursuer::PursuerConfig;
        use crate::sensor::{cast, AgentKind};
        let cfg = with_pursuer(4, 10.0, PursuerConfig::default());
        let w = World::new(cfg, 0).unwrap();
        let mut scene: Vec<Target> = w.targets.clone();
        scene.extend(w.pursuers.iter().map(|p| p.as_target()));
        assert_eq!(scene.len(), 5);
        // Point robot 0 straight at the pursuer and it must see a Pursuer.
        let mut scene2 = scene.clone();
        let to_pursuer = (scene[4].pose.p - scene[0].pose.p).angle();
        scene2[0].pose.theta = to_pursuer;
        let hit = cast(&scene2[0], 0, &scene2, &w.cfg.sensor);
        assert_eq!(hit.map(|h| h.kind), Some(AgentKind::Pursuer));
    }

    #[test]
    fn time_series_is_recorded_at_the_requested_interval() {
        let mut cfg = short(10, 100.0);
        cfg.metrics.sample_interval = 10.0;
        let rec = World::new(cfg, 0).unwrap().run();
        let series = rec.series.expect("series requested");
        assert_eq!(series.len(), 11, "t = 0, 10, ..., 100");
        assert!((series[0].t - 0.0).abs() < 1e-9);
        assert!((series.last().unwrap().t - 100.0).abs() < 1e-6);
    }
}
