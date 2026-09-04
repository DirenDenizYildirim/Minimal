//! The pursuer — Idea B (build doc section 3).
//!
//! The v1 pursuer — nearest target, perfect perception, unbounded range — made a
//! tight cluster the *cheapest* thing to hunt, so aggregation scored as the
//! worst possible strategy and the metric never saw the dilution effect. The
//! corrected family adds three perception dials, under which aggregation has two
//! mechanisms by which it *can* protect the swarm:
//!
//!   * **search cost** — with finite range `r_p`, a pursuer that sees nothing
//!     must search, and time spent searching is time not capturing. Fewer,
//!     tighter clusters are harder to find.
//!   * **confusion** — `p_lock = 1/(1 + kappa * n_local)`, after Olson et al.
//!     (2013). Confusion is a property of the *predator's* perception, not of
//!     the prey's behaviour, so it is modelled here and not in the controller.
//!
//! Whether aggregation actually protects, and at what capability `c`, is the
//! experiment. `r_p = inf, kappa = 0` recovers the v1 pursuer exactly and is
//! kept as one adversarial corner of the sweep.
//!
//! The pursuer's own sensing is **omnidirectional within `r_p`** — it is not a
//! line-of-sight ray. That asymmetry is deliberate: the robots are the minimal
//! agents under study, the pursuer is part of the environment.

use crate::geom::{angle_diff, Vec2};
use crate::rng::Rng;
use crate::robot::{integrate, Pose};
use crate::sensor::Target;
use rand::Rng as _;
use rand_distr::{Distribution, Normal};
use serde::{Deserialize, Serialize};

/// What the pursuer does when nothing is in range. Time spent here is time not
/// capturing, which is the first of aggregation's two protective mechanisms.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SearchStrategy {
    /// Correlated random walk: heading perturbed by a Gaussian each step.
    RandomWalk,
    /// Archimedean spiral outward from where the search began, which is the
    /// standard systematic-search baseline in the pursuit-evasion literature.
    Spiral,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum TargetingRule {
    /// Closest visible robot.
    Nearest,
    /// Visible robot with the fewest neighbours: the edge-picker.
    FewestNeighbours,
    /// Uniform among visible robots.
    RandomVisible,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct PursuerConfig {
    /// `rho`: pursuer speed / robot speed. `rho > 1` means a locked target cannot escape.
    pub speed_ratio: f64,
    /// `r_p`: sensing range in metres. `None` = unbounded (the v1 corner).
    /// Finite range forces a search phase, and time searching is time not capturing.
    pub range: Option<f64>,
    /// `kappa`: confusion. `p_lock = 1 / (1 + kappa * n_local)`, after Olson et al. (2013).
    /// Confusion is a property of the *predator's* perception, not the prey's behaviour.
    pub confusion: f64,
    pub targeting: TargetingRule,
    /// Radius counted as "local" when evaluating confusion.
    pub confusion_radius: f64,
    /// Centre-to-centre distance at which a locked target is captured.
    pub capture_distance: f64,
    /// Seconds the pursuer is out of action after a capture — Holling's
    /// handling time.
    ///
    /// **This is what makes dilution exist.** With zero handling time, capture
    /// is instantaneous on contact, so a packed cluster is a buffet: the
    /// pursuer takes one robot per control step and a swarm of twenty is gone in
    /// two seconds. Aggregation is then maximally *bad* under any metric, which
    /// is the v1 failure mode reappearing in a new place — the build doc fixed
    /// the pursuer's perception but capture remained free.
    ///
    /// With a handling time, being one of many means the predator is busy with
    /// somebody else, which is the dilution effect Idea B is about. Standard
    /// since Holling's disc equation; the same quantity appears in the Olson et
    /// al. predator-confusion models.
    pub handling_time: f64,
    pub search: SearchStrategy,
    /// Heading diffusion of the random-walk search, radians per second (std dev).
    pub search_turn_noise: f64,
    /// How fast the search spiral opens out, metres per radian.
    pub spiral_pitch: f64,
    /// Number of pursuers.
    pub count: usize,
}

impl Default for PursuerConfig {
    fn default() -> Self {
        Self {
            speed_ratio: 1.5,
            range: Some(1.0),
            confusion: 0.0,
            targeting: TargetingRule::Nearest,
            confusion_radius: 0.5,
            capture_distance: 0.08,
            handling_time: 5.0,
            search: SearchStrategy::RandomWalk,
            search_turn_noise: 1.0,
            spiral_pitch: 0.05,
            count: 1,
        }
    }
}

impl PursuerConfig {
    /// `p_lock` given the number of robots inside the pursuer's confusion radius.
    pub fn lock_probability(&self, n_local: usize) -> f64 {
        1.0 / (1.0 + self.confusion * n_local as f64)
    }
}

/// A pursuer in play.
///
/// State is deliberately thin: a pose, the target it is currently locked onto,
/// and where its current search began. Everything else is in the config, because
/// the config is what the sweep varies.
#[derive(Clone, Debug)]
pub struct Pursuer {
    pub pose: Pose,
    pub radius: f64,
    /// Index of the locked robot, if any.
    pub locked: Option<usize>,
    cfg: PursuerConfig,
    /// Seconds of handling time still owed after the last capture.
    handling: f64,
    /// Where the current search phase started, and how far into it we are.
    search_origin: Vec2,
    search_angle: f64,
}

impl Pursuer {
    pub fn new(pose: Pose, radius: f64, cfg: PursuerConfig) -> Self {
        Self {
            pose,
            radius,
            locked: None,
            cfg,
            handling: 0.0,
            search_origin: pose.p,
            search_angle: 0.0,
        }
    }

    pub fn config(&self) -> &PursuerConfig {
        &self.cfg
    }

    pub fn as_target(&self) -> Target {
        Target::pursuer(self.pose, self.radius)
    }

    fn in_range(&self, p: Vec2) -> bool {
        match self.cfg.range {
            None => true,
            Some(r) => (p - self.pose.p).norm() <= r,
        }
    }

    /// Robots inside the confusion radius. This is the `n_local` of
    /// `p_lock = 1/(1 + kappa * n_local)`.
    /// True while the pursuer is occupied with its last catch.
    pub fn is_handling(&self) -> bool {
        self.handling > 0.0
    }

    pub fn local_count(&self, robots: &[Target]) -> usize {
        robots
            .iter()
            .filter(|r| r.alive && (r.pose.p - self.pose.p).norm() <= self.cfg.confusion_radius)
            .count()
    }

    /// Pick a target among those in range, by the configured rule.
    fn choose(&self, robots: &[Target], rng: &mut Rng) -> Option<usize> {
        let visible: Vec<usize> = robots
            .iter()
            .enumerate()
            .filter(|(_, r)| r.alive && self.in_range(r.pose.p))
            .map(|(i, _)| i)
            .collect();
        if visible.is_empty() {
            return None;
        }
        match self.cfg.targeting {
            TargetingRule::Nearest => visible.into_iter().min_by(|&a, &b| {
                let da = (robots[a].pose.p - self.pose.p).norm_sq();
                let db = (robots[b].pose.p - self.pose.p).norm_sq();
                da.partial_cmp(&db).unwrap_or(std::cmp::Ordering::Equal)
            }),
            // The edge-picker: whichever visible robot has the fewest neighbours,
            // which is the selfish-herd prediction for who gets taken.
            TargetingRule::FewestNeighbours => {
                let neighbours = |i: usize| {
                    robots
                        .iter()
                        .enumerate()
                        .filter(|(j, r)| {
                            *j != i
                                && r.alive
                                && (r.pose.p - robots[i].pose.p).norm() <= self.cfg.confusion_radius
                        })
                        .count()
                };
                visible.into_iter().min_by_key(|&i| neighbours(i))
            }
            TargetingRule::RandomVisible => Some(visible[rng.gen_range(0..visible.len())]),
        }
    }

    /// Advance one control step. Returns the index of a robot captured this step.
    ///
    /// Order: drop a lock that has gone out of range or died, try to acquire one
    /// if unlocked, then either pursue or search.
    pub fn step(
        &mut self,
        robots: &[Target],
        dt: f64,
        axle: f64,
        robot_max_wheel_speed: f64,
        rng: &mut Rng,
    ) -> Option<usize> {
        let speed = self.cfg.speed_ratio * robot_max_wheel_speed;

        // Handling: out of action, and not moving, until the debt is paid.
        if self.handling > 0.0 {
            self.handling -= dt;
            return None;
        }

        if let Some(i) = self.locked {
            if !robots[i].alive || !self.in_range(robots[i].pose.p) {
                self.locked = None;
            }
        }

        if self.locked.is_none() {
            if let Some(candidate) = self.choose(robots, rng) {
                // Confusion is re-rolled on every acquisition attempt, so a dense
                // neighbourhood costs the pursuer time rather than accuracy.
                let p_lock = self.cfg.lock_probability(self.local_count(robots));
                if rng.gen::<f64>() < p_lock {
                    self.locked = Some(candidate);
                }
            }
        }

        match self.locked {
            Some(i) => {
                let delta = robots[i].pose.p - self.pose.p;
                if delta.norm() <= self.cfg.capture_distance {
                    self.locked = None;
                    self.handling = self.cfg.handling_time;
                    self.begin_search();
                    return Some(i);
                }
                self.drive_towards(delta.angle(), speed, dt, axle);
                None
            }
            None => {
                self.search(speed, dt, axle, rng);
                None
            }
        }
    }

    fn begin_search(&mut self) {
        self.search_origin = self.pose.p;
        self.search_angle = 0.0;
    }

    /// Proportional heading control, then drive. Forward speed is scaled by
    /// `cos(bearing)` so the pursuer turns before it commits, rather than
    /// orbiting its target.
    fn drive_towards(&mut self, target_heading: f64, speed: f64, dt: f64, axle: f64) {
        let bearing = angle_diff(target_heading, self.pose.theta);
        let max_omega = 2.0 * speed / axle;
        let omega = (bearing / dt).clamp(-max_omega, max_omega);
        let v = speed * bearing.cos().max(0.0);
        let (vl, vr) = (v - 0.5 * omega * axle, v + 0.5 * omega * axle);
        self.pose = integrate(self.pose, vl, vr, axle, dt);
    }

    fn search(&mut self, speed: f64, dt: f64, axle: f64, rng: &mut Rng) {
        match self.cfg.search {
            SearchStrategy::RandomWalk => {
                let sigma = self.cfg.search_turn_noise * dt.sqrt();
                let turn = if sigma > 0.0 {
                    Normal::new(0.0, sigma)
                        .expect("sigma is finite and positive")
                        .sample(rng)
                } else {
                    0.0
                };
                self.drive_towards(self.pose.theta + turn, speed, dt, axle);
            }
            SearchStrategy::Spiral => {
                // Archimedean spiral about where the search began: r = pitch * angle.
                self.search_angle +=
                    speed * dt / (self.cfg.spiral_pitch * (1.0 + self.search_angle)).max(1e-6);
                let r = self.cfg.spiral_pitch * self.search_angle;
                let goal = self.search_origin + Vec2::from_angle(self.search_angle) * r;
                let delta = goal - self.pose.p;
                if delta.norm() > 1e-9 {
                    self.drive_towards(delta.angle(), speed, dt, axle);
                }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::rng::rng_from;

    #[test]
    fn zero_confusion_always_locks() {
        let p = PursuerConfig {
            confusion: 0.0,
            ..Default::default()
        };
        assert_eq!(p.lock_probability(0), 1.0);
        assert_eq!(p.lock_probability(50), 1.0);
    }

    fn robots_at(xs: &[(f64, f64)]) -> Vec<Target> {
        xs.iter()
            .map(|&(x, y)| Target::robot(Pose::new(x, y, 0.0), 0.037))
            .collect()
    }

    fn pursuer_at(x: f64, y: f64, cfg: PursuerConfig) -> Pursuer {
        Pursuer::new(Pose::new(x, y, 0.0), 0.037, cfg)
    }

    #[test]
    fn an_unlimited_pursuer_runs_a_target_down() {
        // The v1 corner: infinite range, no confusion, faster than the prey.
        // A stationary robot must be caught.
        let cfg = PursuerConfig {
            range: None,
            confusion: 0.0,
            speed_ratio: 1.5,
            ..Default::default()
        };
        let mut p = pursuer_at(-1.0, 0.0, cfg);
        let robots = robots_at(&[(0.0, 0.0)]);
        let mut rng = rng_from(1);
        let mut captured = None;
        for step in 0..400 {
            if let Some(i) = p.step(&robots, 0.1, 0.051, 0.128, &mut rng) {
                captured = Some((i, step));
                break;
            }
        }
        let (i, step) = captured.expect("an unlimited faster pursuer must capture");
        assert_eq!(i, 0);
        // 1 m at 1.5 * 0.128 m/s is ~5.2 s, i.e. ~52 steps, plus turning.
        assert!((40..120).contains(&step), "took {step} steps");
    }

    #[test]
    fn a_pursuer_cannot_lock_beyond_its_range() {
        let cfg = PursuerConfig {
            range: Some(0.5),
            ..Default::default()
        };
        let mut p = pursuer_at(-5.0, 0.0, cfg);
        let robots = robots_at(&[(0.0, 0.0)]);
        let mut rng = rng_from(2);
        for _ in 0..50 {
            assert!(p.step(&robots, 0.1, 0.051, 0.128, &mut rng).is_none());
            assert!(p.locked.is_none(), "locked onto a robot outside r_p");
        }
    }

    #[test]
    fn finite_range_forces_a_search_that_costs_time() {
        // The first of aggregation's two protective mechanisms. A pursuer that
        // cannot see the swarm has to move, and moving is not capturing.
        let cfg = PursuerConfig {
            range: Some(0.3),
            search: SearchStrategy::RandomWalk,
            ..Default::default()
        };
        let mut p = pursuer_at(0.0, 0.0, cfg);
        let robots = robots_at(&[(50.0, 50.0)]);
        let mut rng = rng_from(3);
        let start = p.pose.p;
        for _ in 0..200 {
            p.step(&robots, 0.1, 0.051, 0.128, &mut rng);
        }
        assert!(p.locked.is_none());
        assert!((p.pose.p - start).norm() > 0.1, "the searcher did not move");
    }

    #[test]
    fn the_spiral_search_expands() {
        let cfg = PursuerConfig {
            range: Some(0.3),
            search: SearchStrategy::Spiral,
            spiral_pitch: 0.05,
            ..Default::default()
        };
        let mut p = pursuer_at(0.0, 0.0, cfg);
        let robots = robots_at(&[(50.0, 50.0)]);
        let mut rng = rng_from(4);
        let mut radii = vec![];
        for step in 0..600 {
            p.step(&robots, 0.1, 0.051, 0.128, &mut rng);
            if step % 200 == 199 {
                radii.push(p.pose.p.norm());
            }
        }
        assert!(
            radii[0] < radii[1] && radii[1] < radii[2],
            "spiral radii {radii:?}"
        );
    }

    #[test]
    fn confusion_delays_lock_on_in_a_crowd() {
        // The second protective mechanism, and the one that makes aggregation
        // potentially worth doing: a dense neighbourhood costs the pursuer
        // acquisition attempts, not accuracy.
        let crowd: Vec<(f64, f64)> = (0..12).map(|i| (0.1 + 0.02 * i as f64, 0.0)).collect();
        let attempts_until_lock = |kappa: f64, seed: u64| {
            let cfg = PursuerConfig {
                confusion: kappa,
                confusion_radius: 1.0,
                range: Some(2.0),
                speed_ratio: 0.0001, // effectively stationary, so we time lock-on alone
                ..Default::default()
            };
            let mut p = pursuer_at(0.0, 0.0, cfg);
            let robots = robots_at(&crowd);
            let mut rng = rng_from(seed);
            for step in 0..10_000 {
                p.step(&robots, 0.1, 0.051, 0.128, &mut rng);
                if p.locked.is_some() {
                    return step;
                }
            }
            10_000
        };
        let clear: f64 = (0..20)
            .map(|s| attempts_until_lock(0.0, s) as f64)
            .sum::<f64>()
            / 20.0;
        let confused: f64 = (0..20)
            .map(|s| attempts_until_lock(1.0, s) as f64)
            .sum::<f64>()
            / 20.0;
        assert_eq!(clear, 0.0, "with kappa = 0 the first attempt must succeed");
        assert!(
            confused > 2.0,
            "confusion did not delay lock-on: {confused}"
        );
    }

    #[test]
    fn the_edge_picker_takes_the_loneliest_robot() {
        // Robot 0 is off on its own; 1..4 are a tight group.
        let robots = robots_at(&[
            (1.0, 1.0),
            (0.2, 0.0),
            (0.24, 0.0),
            (0.28, 0.0),
            (0.32, 0.0),
        ]);
        let cfg = PursuerConfig {
            targeting: TargetingRule::FewestNeighbours,
            confusion_radius: 0.3,
            range: Some(5.0),
            confusion: 0.0,
            ..Default::default()
        };
        let mut p = pursuer_at(0.0, 0.0, cfg);
        let mut rng = rng_from(5);
        p.step(&robots, 0.1, 0.051, 0.128, &mut rng);
        assert_eq!(p.locked, Some(0), "should have picked the isolated robot");

        // Nearest picks differently on the same scene, which is the whole point
        // of having the rule be a dial.
        let cfg = PursuerConfig {
            targeting: TargetingRule::Nearest,
            ..cfg
        };
        let mut p = pursuer_at(0.0, 0.0, cfg);
        p.step(&robots, 0.1, 0.051, 0.128, &mut rng);
        assert_ne!(p.locked, Some(0));
    }

    #[test]
    fn a_dead_robot_is_dropped_and_never_retargeted() {
        let mut robots = robots_at(&[(0.3, 0.0)]);
        let cfg = PursuerConfig {
            range: Some(2.0),
            confusion: 0.0,
            ..Default::default()
        };
        let mut p = pursuer_at(0.0, 0.0, cfg);
        let mut rng = rng_from(6);
        p.step(&robots, 0.1, 0.051, 0.128, &mut rng);
        assert_eq!(p.locked, Some(0));
        robots[0].alive = false;
        for _ in 0..20 {
            assert!(p.step(&robots, 0.1, 0.051, 0.128, &mut rng).is_none());
        }
        assert!(p.locked.is_none(), "kept chasing a captured robot");
    }

    #[test]
    fn local_count_respects_the_confusion_radius() {
        let robots = robots_at(&[(0.1, 0.0), (0.2, 0.0), (0.9, 0.0)]);
        let cfg = PursuerConfig {
            confusion_radius: 0.5,
            ..Default::default()
        };
        let p = pursuer_at(0.0, 0.0, cfg);
        assert_eq!(p.local_count(&robots), 2);
        let cfg = PursuerConfig {
            confusion_radius: 1.0,
            ..Default::default()
        };
        assert_eq!(pursuer_at(0.0, 0.0, cfg).local_count(&robots), 3);
    }

    #[test]
    fn handling_time_takes_the_pursuer_out_of_action() {
        // Without this, a packed cluster is taken one robot per control step.
        let cfg = PursuerConfig {
            range: None,
            confusion: 0.0,
            speed_ratio: 1.5,
            capture_distance: 0.5,
            handling_time: 3.0,
            ..Default::default()
        };
        let mut p = pursuer_at(0.0, 0.0, cfg);
        // Two robots both already inside the capture distance.
        let mut robots = robots_at(&[(0.2, 0.0), (0.25, 0.0)]);
        let mut rng = rng_from(9);

        let first = p
            .step(&robots, 0.1, 0.051, 0.128, &mut rng)
            .expect("immediate capture");
        robots[first].alive = false;
        assert!(p.is_handling());

        // The second robot is in reach the whole time, and must survive the
        // handling period: 3 s at dt = 0.1 is 30 steps.
        for step in 0..29 {
            assert!(
                p.step(&robots, 0.1, 0.051, 0.128, &mut rng).is_none(),
                "captured during handling at step {step}"
            );
        }
        let mut caught = None;
        for _ in 0..20 {
            if let Some(i) = p.step(&robots, 0.1, 0.051, 0.128, &mut rng) {
                caught = Some(i);
                break;
            }
        }
        assert!(caught.is_some(), "never resumed hunting after handling");
        // ...and it is immediately handling again, having just caught one.
        assert!(p.is_handling());
    }

    #[test]
    fn zero_handling_time_makes_a_cluster_a_buffet() {
        // Documents why the default is non-zero: with no handling time the
        // pursuer clears a packed group at one robot per step.
        let cfg = PursuerConfig {
            range: None,
            confusion: 0.0,
            capture_distance: 0.5,
            handling_time: 0.0,
            ..Default::default()
        };
        let mut p = pursuer_at(0.0, 0.0, cfg);
        let mut robots = robots_at(&[(0.2, 0.0), (0.22, 0.0), (0.24, 0.0), (0.26, 0.0)]);
        let mut rng = rng_from(10);
        let mut taken = 0;
        for _ in 0..4 {
            let i = p
                .step(&robots, 0.1, 0.051, 0.128, &mut rng)
                .expect("capture every step");
            robots[i].alive = false;
            taken += 1;
        }
        assert_eq!(taken, 4, "four robots in four control steps");
    }

    #[test]
    fn confusion_falls_with_the_number_of_local_robots() {
        let p = PursuerConfig {
            confusion: 0.5,
            ..Default::default()
        };
        assert_eq!(p.lock_probability(0), 1.0);
        assert!((p.lock_probability(2) - 0.5).abs() < 1e-12);
        assert!(p.lock_probability(10) < p.lock_probability(2));
    }
}
