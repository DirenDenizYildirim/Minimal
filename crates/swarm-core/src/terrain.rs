//! Terrain: the Idea A hostility dial.
//!
//! Build doc section 3, Idea A. The v1 model (a scalar speed field scaling both
//! wheels equally, plus a constant drift) could not deform one robot's path
//! relative to another's: equal scaling keeps the instantaneous centre of
//! rotation fixed, so each robot still traces the *same* circle at a
//! position-dependent rate, and a constant drift is a Galilean shift that leaves
//! every line-of-sight reading unchanged. The corrected model, per wheel `w`:
//!
//! ```text
//! v_w = v_cmd,w * m_w(x, y) - g_eff * sin(alpha) * (h_hat . s_hat)
//! ```
//!
//! Two mechanisms, both of which a real e-puck on a tilted board exhibits:
//!
//! 1. `m_w(x, y)` — a per-wheel traction multiplier drawn from one smoothed
//!    random field (correlation length `lambda`, amplitude `theta_m`). The two
//!    wheels sample that field **at their own contact points**, so they
//!    generally differ, the curvature changes, and the state-0 circle becomes a
//!    distorted loop.
//! 2. The gravity term depends on the robot's heading, so the circle is
//!    stretched downhill and compressed uphill (trochoid-like).
//!
//! ## Sign convention
//!
//! The build doc writes the gravity term as `- g_eff sin(alpha) (h_hat . s_hat)`
//! with `s_hat` described as the downhill direction, which would make a robot
//! *slow down* when pointed downhill. We keep the doc's minus sign and define
//! `slope_dir` as the **uphill** direction, so heading uphill costs speed and
//! heading downhill gains it. Same equation, physical sign. See
//! `docs/decisions/0002-terrain-sign-convention.md`.

use crate::field::ScalarField;
use crate::geom::Vec2;
use crate::rng::Rng;
use crate::robot::Pose;
use rand::Rng as _;
use rand_distr::{Distribution, Normal};
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct TerrainConfig {
    /// Slope angle `alpha` in radians. 0 = flat board.
    pub slope_angle: f64,
    /// Uphill direction in radians (see the sign-convention note above).
    pub slope_dir: f64,
    /// `g_eff` in m/s: the speed a robot gains rolling straight down a 90-degree
    /// slope. Phenomenological, calibrated against the tiltable board.
    pub slope_gain: f64,
    /// `theta_m`: amplitude of the per-wheel traction multiplier, `m_w in [1-a, 1+a]`.
    pub friction_amplitude: f64,
    /// `lambda`: correlation length of the traction field, in metres.
    /// Report it alongside every terrain result; it sets the ratio to `R0`.
    pub correlation_length: f64,
    /// Std. dev. of per-wheel slip noise (m/s), scaled by `|sin alpha|`.
    pub slip_noise: f64,
    /// Lower bound on the traction multiplier.
    ///
    /// A safety net, not a modelling choice. The field reaches `|f| = 1`, so at
    /// `theta_m = 1` the multiplier `1 + theta_m*f` can reach zero and a wheel
    /// stalls outright — a different dynamical regime (the robot pivots), not
    /// terrain deformation. Sweeps are cut at `theta_m = 0.9`, below the
    /// `1/max|f| = 1.0` at which that becomes possible, so this floor should
    /// never bind inside the swept range;
    /// `tests::the_traction_floor_does_not_bind_in_the_swept_range` holds that.
    pub traction_floor: f64,
    /// Whether the wheels sample the field at their own contact points, or both
    /// take one value sampled at the robot's centre.
    ///
    /// `ScalarCentre` is the *control condition* for the mechanism test: it is
    /// the v1 model the build doc rejected, in which one multiplier scales both
    /// wheels, the instantaneous centre of rotation is unmoved, and no
    /// trajectory is deformed relative to any other.
    pub traction_mode: TractionMode,
}

/// How the traction field is sampled. See `TerrainConfig::traction_mode`.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum TractionMode {
    /// Each wheel samples at its own contact point: the corrected model.
    PerWheel,
    /// Both wheels take one multiplier sampled at the robot centre: a pure
    /// scalar speed field, which cannot change the turn radius.
    ScalarCentre,
}

impl Default for TerrainConfig {
    fn default() -> Self {
        Self {
            slope_angle: 0.0,
            slope_dir: 0.0,
            slope_gain: 0.0,
            friction_amplitude: 0.0,
            correlation_length: 0.25,
            slip_noise: 0.0,
            traction_floor: 0.05,
            traction_mode: TractionMode::PerWheel,
        }
    }
}

impl TerrainConfig {
    /// True when the terrain is exactly the flat, uniform board Gauci assumed.
    pub fn is_flat(&self) -> bool {
        self.friction_amplitude == 0.0
            && (self.slope_angle == 0.0 || self.slope_gain == 0.0)
            && self.slip_noise == 0.0
    }
}

#[derive(Clone, Copy, Debug)]
pub struct Terrain {
    cfg: TerrainConfig,
    field: ScalarField,
}

impl Terrain {
    pub fn new(cfg: TerrainConfig, seed: u64) -> Self {
        let field = ScalarField::new(seed, cfg.correlation_length);
        Self { cfg, field }
    }

    pub fn config(&self) -> &TerrainConfig {
        &self.cfg
    }

    /// Traction multiplier `m_w` at a wheel contact point. Clamped at 0 so a
    /// large amplitude cannot flip a wheel into reverse.
    pub fn traction(&self, contact: Vec2) -> f64 {
        if self.cfg.friction_amplitude == 0.0 {
            return 1.0;
        }
        (1.0 + self.cfg.friction_amplitude * self.field.sample(contact))
            .max(self.cfg.traction_floor)
    }

    /// The heading-dependent gravity term, in m/s. Positive means "subtract
    /// this much speed", i.e. the robot is pointed uphill.
    pub fn gravity_term(&self, heading: Vec2) -> f64 {
        if self.cfg.slope_angle == 0.0 || self.cfg.slope_gain == 0.0 {
            return 0.0;
        }
        let uphill = Vec2::from_angle(self.cfg.slope_dir);
        self.cfg.slope_gain * self.cfg.slope_angle.sin() * heading.dot(uphill)
    }

    /// Map commanded wheel speeds (m/s) to realised wheel speeds.
    pub fn apply(&self, pose: &Pose, axle: f64, cmd: [f64; 2], rng: &mut Rng) -> [f64; 2] {
        if self.cfg.is_flat() {
            return cmd;
        }
        let (m_left, m_right) = match self.cfg.traction_mode {
            TractionMode::PerWheel => {
                let (l, r) = pose.wheel_contacts(axle);
                (self.traction(l), self.traction(r))
            }
            TractionMode::ScalarCentre => {
                let m = self.traction(pose.p);
                (m, m)
            }
        };
        let g = self.gravity_term(pose.heading());
        let mut out = [cmd[0] * m_left - g, cmd[1] * m_right - g];
        let sigma = self.cfg.slip_noise * self.cfg.slope_angle.sin().abs();
        if sigma > 0.0 {
            let n = Normal::new(0.0, sigma).expect("slip sigma is finite and positive");
            out[0] += n.sample(rng);
            out[1] += n.sample(rng);
        } else {
            // Keep the RNG stream aligned whether or not slip is on.
            let _: f64 = rng.gen();
        }
        out
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::rng::rng_from;
    use std::f64::consts::PI;

    fn flat() -> Terrain {
        Terrain::new(TerrainConfig::default(), 1)
    }

    #[test]
    fn flat_terrain_is_a_no_op() {
        let t = flat();
        assert!(t.config().is_flat());
        let mut rng = rng_from(0);
        let cmd = [0.1, -0.05];
        assert_eq!(
            t.apply(&Pose::new(3.0, -2.0, 0.9), 0.051, cmd, &mut rng),
            cmd
        );
    }

    #[test]
    fn the_traction_floor_does_not_bind_in_the_swept_range() {
        // Sweeps are cut at theta_m = 0.9 precisely so the floor is inert. If
        // this fails, a figure is showing wheel stall rather than terrain.
        let cfg = TerrainConfig {
            friction_amplitude: 0.9,
            correlation_length: 0.1,
            ..Default::default()
        };
        let t = Terrain::new(cfg, 17);
        let mut at_floor = 0;
        for i in 0..20_000 {
            let p = Vec2::new(i as f64 * 0.0073 - 70.0, i as f64 * 0.0041 - 40.0);
            if t.traction(p) <= cfg.traction_floor + 1e-12 {
                at_floor += 1;
            }
        }
        assert_eq!(
            at_floor, 0,
            "the floor bound {at_floor} times at theta_m = 0.9"
        );
    }

    #[test]
    fn a_scalar_centre_field_cannot_change_the_turn_radius() {
        // The v1 model, and the reason it could not break symmetry: one
        // multiplier scales both wheels, so the instantaneous centre of rotation
        // is unmoved and the loop keeps its shape.
        let cfg = TerrainConfig {
            friction_amplitude: 0.9,
            correlation_length: 0.05,
            traction_mode: TractionMode::ScalarCentre,
            ..Default::default()
        };
        let t = Terrain::new(cfg, 3);
        let mut rng = rng_from(0);
        let (axle, vmax): (f64, f64) = (0.051, 0.128);
        let cmd = [-0.7 * vmax, -vmax];
        let nominal = crate::robot::turn_radius(cmd[0], cmd[1], axle).unwrap();
        for i in 0..500 {
            let pose = Pose::new(i as f64 * 0.031, i as f64 * -0.017, i as f64 * 0.1);
            let r = t.apply(&pose, axle, cmd, &mut rng);
            if let Some(radius) = crate::robot::turn_radius(r[0], r[1], axle) {
                assert!(
                    (radius - nominal).abs() < 1e-9,
                    "scalar field changed the turn radius: {radius} vs {nominal}"
                );
            }
        }
        // Stronger: the traced path is the *same circle*, only traversed at a
        // position-dependent rate. Scaling both wheels by m gives v' = m*v and
        // omega' = m*omega, so dp/dtheta = v/omega is independent of m — a time
        // reparameterisation, which is exactly the build doc's diagnosis of the
        // v1 model. (It is also why a fixed step count no longer covers one
        // period, so a bounding box would be the wrong check here.)
        let start = Pose::new(0.0, 0.0, 0.0);
        let signed_r = 0.5 * (cmd[0] + cmd[1]) * axle / (cmd[1] - cmd[0]);
        let centre = start.p + start.heading().perp() * signed_r;
        let mut pose = start;
        for _ in 0..5000 {
            let r = t.apply(&pose, axle, cmd, &mut rng);
            pose = crate::robot::integrate(pose, r[0], r[1], axle, 0.01);
            let d = (pose.p - centre).norm();
            assert!(
                (d - nominal).abs() < 1e-9,
                "left the circle: {d} vs R0 {nominal}"
            );
        }
    }

    #[test]
    fn wheels_sample_the_field_at_their_own_contact_points() {
        // This is the property the v1 model lacked: the two wheels must be able
        // to differ, or the curvature never changes and no symmetry breaks.
        let cfg = TerrainConfig {
            friction_amplitude: 0.5,
            correlation_length: 0.05, // small relative to the axle
            ..Default::default()
        };
        let t = Terrain::new(cfg, 99);
        let mut differed = 0;
        for i in 0..200 {
            let pose = Pose::new(i as f64 * 0.031, i as f64 * -0.017, i as f64 * 0.1);
            let (l, r) = pose.wheel_contacts(0.051);
            if (t.traction(l) - t.traction(r)).abs() > 1e-3 {
                differed += 1;
            }
        }
        assert!(
            differed > 150,
            "wheels differed in only {differed}/200 poses"
        );
    }

    #[test]
    fn equal_wheel_scaling_would_not_change_curvature() {
        // Documents *why* the v1 model failed: scaling both wheels by the same
        // factor leaves the turn radius invariant, so the circle is unchanged.
        let (vl, vr, axle) = (-0.7 * 0.128, -0.128, 0.051);
        let r_nominal = crate::robot::turn_radius(vl, vr, axle).unwrap();
        let r_scaled = crate::robot::turn_radius(0.4 * vl, 0.4 * vr, axle).unwrap();
        assert!((r_nominal - r_scaled).abs() < 1e-12);
    }

    #[test]
    fn per_wheel_traction_does_change_curvature() {
        let (vl, vr, axle) = (-0.7 * 0.128, -0.128, 0.051);
        let r_nominal = crate::robot::turn_radius(vl, vr, axle).unwrap();
        let r_skewed = crate::robot::turn_radius(0.8 * vl, 1.1 * vr, axle).unwrap();
        assert!(
            (r_nominal - r_skewed).abs() > 1e-3,
            "R0 {r_nominal} vs skewed {r_skewed}"
        );
    }

    #[test]
    fn gravity_term_is_heading_dependent_and_signed_downhill_positive() {
        let cfg = TerrainConfig {
            slope_angle: 10f64.to_radians(),
            slope_dir: 0.0, // uphill is +x
            slope_gain: 0.05,
            ..Default::default()
        };
        let t = Terrain::new(cfg, 1);
        let uphill = t.gravity_term(Vec2::from_angle(0.0));
        let downhill = t.gravity_term(Vec2::from_angle(PI));
        let across = t.gravity_term(Vec2::from_angle(PI / 2.0));
        assert!(uphill > 0.0, "pointing uphill must cost speed");
        assert!(downhill < 0.0, "pointing downhill must gain speed");
        assert!(across.abs() < 1e-12, "across-slope is unaffected");
        assert!((uphill + downhill).abs() < 1e-12);
    }

    /// Integrate the state-0 circle for exactly one period and return the
    /// extent of the traced loop along and across the fall line, **after
    /// removing the linear drift**.
    ///
    /// Removing the drift is the whole point. A constant drift vector is a
    /// Galilean shift: it moves the loop but cannot change its shape, and every
    /// line-of-sight reading between two robots evolves exactly as it would
    /// without it. So a bounding box that still contains the drift measures the
    /// wrong thing. What has to change for terrain to break symmetry is the
    /// shape that remains once the drift is taken out.
    fn drift_removed_extent(t: &Terrain) -> (f64, f64) {
        let (axle, vmax): (f64, f64) = (0.051, 0.128);
        let cmd: [f64; 2] = [-0.7 * vmax, -vmax];
        let omega: f64 = (cmd[1] - cmd[0]) / axle;
        let steps = 4000usize;
        let dt = (std::f64::consts::TAU / omega.abs()) / steps as f64;

        let mut rng = rng_from(0);
        let mut pose = Pose::new(0.0, 0.0, 0.0);
        let mut path = Vec::with_capacity(steps + 1);
        path.push(pose.p);
        for _ in 0..steps {
            let realised = t.apply(&pose, axle, cmd, &mut rng);
            pose = crate::robot::integrate(pose, realised[0], realised[1], axle, dt);
            path.push(pose.p);
        }
        let total = steps as f64 * dt;
        let drift = (path[steps] - path[0]) / total;
        let (mut xmin, mut xmax, mut ymin, mut ymax) = (f64::MAX, f64::MIN, f64::MAX, f64::MIN);
        for (i, p) in path.iter().enumerate() {
            let q = *p - drift * (i as f64 * dt);
            xmin = xmin.min(q.x);
            xmax = xmax.max(q.x);
            ymin = ymin.min(q.y);
            ymax = ymax.max(q.y);
        }
        (xmax - xmin, ymax - ymin)
    }

    #[test]
    fn flat_terrain_traces_a_circle() {
        // Control condition: with no terrain the drift-removed loop is a circle,
        // so its extent along and across any axis is the same.
        let (along, across) = drift_removed_extent(&flat());
        assert!(
            (along - across).abs() < 1e-6,
            "along {along} vs across {across}"
        );
    }

    #[test]
    fn a_slope_deforms_the_loop_once_the_drift_is_removed() {
        // The corrected model's first mechanism: speed depends on heading, so
        // the loop is stretched along the fall line even with the drift gone.
        // This is exactly what v1's scalar speed field and constant drift could
        // not do.
        let cfg = TerrainConfig {
            slope_angle: 10f64.to_radians(),
            slope_dir: 0.0, // uphill is +x, so the fall line is the x axis
            slope_gain: 0.4,
            ..Default::default()
        };
        let (along, across) = drift_removed_extent(&Terrain::new(cfg, 1));
        let (flat_along, flat_across) = drift_removed_extent(&flat());
        assert!(
            (flat_along / flat_across - 1.0).abs() < 1e-6,
            "flat control is not circular: {flat_along} vs {flat_across}"
        );
        assert!(along / across > 1.03, "along {along} vs across {across}");
    }

    #[test]
    fn deformation_grows_with_slope_angle() {
        let extent_at = |deg: f64| {
            let cfg = TerrainConfig {
                slope_angle: deg.to_radians(),
                slope_dir: 0.0,
                slope_gain: 0.4,
                ..Default::default()
            };
            let (along, across) = drift_removed_extent(&Terrain::new(cfg, 1));
            along / across
        };
        let (flat, gentle, steep) = (extent_at(0.0), extent_at(5.0), extent_at(15.0));
        assert!((flat - 1.0).abs() < 1e-6, "flat ratio {flat}");
        assert!(gentle > flat, "{gentle} vs {flat}");
        assert!(steep > gentle, "{steep} vs {gentle}");
    }

    #[test]
    fn friction_heterogeneity_alone_deforms_the_loop() {
        // The second mechanism, independent of any slope: the two wheels sample
        // the traction field at different contact points, so curvature varies
        // along the path and the loop stops being a circle.
        let cfg = TerrainConfig {
            friction_amplitude: 0.3,
            correlation_length: 0.15,
            ..Default::default()
        };
        let (along, across) = drift_removed_extent(&Terrain::new(cfg, 3));
        let (flat_along, flat_across) = drift_removed_extent(&flat());
        let deformed = (along - across).abs() / across;
        let baseline = (flat_along - flat_across).abs() / flat_across;
        assert!(baseline < 1e-6);
        assert!(
            deformed > 0.01,
            "friction field left the loop circular: {deformed}"
        );
    }
}
