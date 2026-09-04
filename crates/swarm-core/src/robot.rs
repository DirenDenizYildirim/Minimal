//! Differential-drive kinematics.
//!
//! Integration is *exact arc* rather than Euler. This matters more here than in
//! a typical sim: the Gauci controller's state-0 motion is a circle, and that
//! circle's radius `R0` is the controller's only intrinsic length scale
//! (build doc, section 1.1). Euler integration inflates `R0` with the timestep,
//! which would corrupt the H2 test that the terrain transition scales with `R0`.

use crate::geom::{wrap_angle, Vec2};
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, Default, PartialEq, Serialize, Deserialize)]
pub struct Pose {
    pub p: Vec2,
    /// Heading in radians, counter-clockwise from +x.
    pub theta: f64,
}

impl Pose {
    pub fn new(x: f64, y: f64, theta: f64) -> Self {
        Self {
            p: Vec2::new(x, y),
            theta,
        }
    }

    pub fn heading(&self) -> Vec2 {
        Vec2::from_angle(self.theta)
    }

    /// Contact points of the two wheels, `axle` apart, centred on the body.
    /// Left wheel is on the +90-degree side of the heading.
    pub fn wheel_contacts(&self, axle: f64) -> (Vec2, Vec2) {
        let n = self.heading().perp() * (axle * 0.5);
        (self.p + n, self.p - n)
    }
}

/// Integrate a differential drive over `dt` at constant wheel speeds (m/s).
///
/// Straight-line motion is handled separately because the arc form divides by
/// the angular rate.
pub fn integrate(pose: Pose, v_left: f64, v_right: f64, axle: f64, dt: f64) -> Pose {
    let v = 0.5 * (v_left + v_right);
    let omega = (v_right - v_left) / axle;

    if omega.abs() < 1e-12 {
        return Pose {
            p: pose.p + pose.heading() * (v * dt),
            theta: pose.theta,
        };
    }

    let r = v / omega; // signed radius of the instantaneous centre of rotation
    let theta1 = pose.theta + omega * dt;
    let dp = Vec2::new(
        r * (theta1.sin() - pose.theta.sin()),
        -r * (theta1.cos() - pose.theta.cos()),
    );
    Pose {
        p: pose.p + dp,
        theta: wrap_angle(theta1),
    }
}

/// Radius of the circle traced by constant wheel speeds. `None` for straight motion.
///
/// This is `R0` when evaluated on the state-0 wheel constants.
pub fn turn_radius(v_left: f64, v_right: f64, axle: f64) -> Option<f64> {
    let diff = v_right - v_left;
    if diff.abs() < 1e-12 {
        return None;
    }
    Some((0.5 * (v_left + v_right) * axle / diff).abs())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::f64::consts::TAU;

    #[test]
    fn straight_motion_is_straight() {
        let p = integrate(Pose::new(0.0, 0.0, 0.0), 0.1, 0.1, 0.053, 1.0);
        assert!((p.p.x - 0.1).abs() < 1e-12);
        assert!(p.p.y.abs() < 1e-12);
        assert!(p.theta.abs() < 1e-12);
    }

    #[test]
    fn spin_in_place_does_not_translate() {
        let p = integrate(Pose::new(1.0, 2.0, 0.4), -0.1, 0.1, 0.053, 0.7);
        assert!((p.p - Vec2::new(1.0, 2.0)).norm() < 1e-12);
    }

    #[test]
    fn circle_closes_and_radius_matches_analytic_r0() {
        // Gauci's published state-0 constants, scaled by e-puck max wheel speed.
        let (axle, vmax) = (0.053, 0.128);
        let (vl, vr) = (-0.7 * vmax, -vmax);
        let r0 = turn_radius(vl, vr, axle).unwrap();

        let omega = (vr - vl) / axle;
        let period = TAU / omega.abs();
        // Choose dt so that an integer number of steps is *exactly* one period,
        // otherwise the closure check below measures the leftover arc.
        let steps = 1000usize;
        let dt = period / steps as f64;

        let start = Pose::new(0.0, 0.0, 0.0);
        let mut pose = start;
        let mut max_r: f64 = 0.0;
        let mut min_r = f64::INFINITY;
        // Centre of the traced circle is at distance r0 on the +/- normal side.
        let centre = start.p + start.heading().perp() * (0.5 * (vl + vr) * axle / (vr - vl));
        for _ in 0..steps {
            pose = integrate(pose, vl, vr, axle, dt);
            let r = (pose.p - centre).norm();
            max_r = max_r.max(r);
            min_r = min_r.min(r);
        }
        assert!((max_r - r0).abs() < 1e-9, "max radius {max_r} vs R0 {r0}");
        assert!((min_r - r0).abs() < 1e-9, "min radius {min_r} vs R0 {r0}");
        // One full period returns to the start.
        assert!(
            (pose.p - start.p).norm() < 1e-9,
            "circle did not close: {:?}",
            pose.p
        );
    }

    #[test]
    fn integration_is_timestep_independent() {
        let (axle, vl, vr) = (0.053, -0.09, -0.128);
        let coarse = integrate(Pose::default(), vl, vr, axle, 0.1);
        let mut fine = Pose::default();
        for _ in 0..100 {
            fine = integrate(fine, vl, vr, axle, 0.001);
        }
        assert!((coarse.p - fine.p).norm() < 1e-9);
    }
}
