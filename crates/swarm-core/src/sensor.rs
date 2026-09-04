//! Line-of-sight sensor.
//!
//! The Gauci family of controllers reads one forward-facing line-of-sight
//! sensor. We model it as a cone of half-angle `fov_half_angle` (0 = a bare
//! ray, which is the Gauci limit) fired from the front of the body along the
//! heading. Bodies are disks, so "agent j is in the cone" is exact:
//! j subtends a half-width of `asin(R / d)` about its bearing.
//!
//! The nearest agent in the cone wins, which is what gives occlusion for free:
//! a robot standing between the observer and a further agent hides it.
//!
//! Returning the nearest *hit with its kind and bearing* — rather than a bare
//! boolean — is what lets one sensor implementation serve every capability row
//! in the build doc: binary (S=2), ternary (S=3, Idea B rows B1/B3/B4) and
//! ternary-with-side (S=5, row B2).

use crate::geom::angle_diff;
use crate::robot::Pose;
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AgentKind {
    Robot,
    Pursuer,
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Hit {
    pub kind: AgentKind,
    /// Centre-to-centre distance to the detected body.
    pub distance: f64,
    /// Bearing relative to the observer's heading, in (-pi, pi].
    pub bearing: f64,
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct SensorConfig {
    /// Maximum detection range in metres. `None` = unlimited, as in Gauci's sim.
    pub range: Option<f64>,
    /// Half-angle of the sensor cone in radians. 0 = a single ray.
    ///
    /// **VERIFY against Gauci et al. before quoting any small-swarm result.**
    /// This is a physical parameter of their setup that we have guessed, and the
    /// guess decides whether n = 2 aggregates at all: with a bare ray it does
    /// not, and it recovers completely by a half-FOV of 90 degrees. Results at
    /// n >= 10 are qualitatively insensitive to it. See `docs/validation.md` §2.
    pub fov_half_angle: f64,
    /// How raw hits map onto discrete sensor states.
    pub encoding: SensorEncoding,
}

impl Default for SensorConfig {
    fn default() -> Self {
        Self {
            range: None,
            fov_half_angle: 0.0,
            encoding: SensorEncoding::Binary,
        }
    }
}

/// Mapping from a raw hit to the discrete state index the lookup table is indexed by.
///
/// `states()` is the `S` component of the capability vector `c = (S, M, A, K)`
/// — sensor *states*, not bits (build doc, section 2.1).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SensorEncoding {
    /// Gauci (2014) IJRR: nothing / something. S = 2.
    Binary,
    /// Gauci et al. (2014) AAMAS: nothing / robot / other. S = 3.
    Ternary,
    /// Ternary plus which side of the sensor axis the body sits on: nothing,
    /// robot-left, robot-right, pursuer-left, pursuer-right. S = 5.
    ///
    /// This is row B2 ("ternary + pursuer left/right half"). Resolving the side
    /// for both kinds is what makes it five states rather than four, and it is
    /// the reading consistent with the S column of the build doc's table. Side
    /// is meaningful even for a zero-width ray: the bearing to a visible body's
    /// centre is bounded by its angular half-width, not zero, so it still says
    /// which way to turn to face it.
    TernaryWithSide,
}

impl SensorEncoding {
    pub fn states(&self) -> usize {
        match self {
            SensorEncoding::Binary => 2,
            SensorEncoding::Ternary => 3,
            SensorEncoding::TernaryWithSide => 5,
        }
    }

    pub fn encode(&self, hit: Option<Hit>) -> usize {
        match (self, hit) {
            (_, None) => 0,
            (SensorEncoding::Binary, Some(_)) => 1,
            (SensorEncoding::Ternary, Some(h)) => match h.kind {
                AgentKind::Robot => 1,
                AgentKind::Pursuer => 2,
            },
            (SensorEncoding::TernaryWithSide, Some(h)) => {
                // A bearing of exactly zero is measure-zero; break the tie
                // deterministically towards "left" so the mapping is total.
                let right = usize::from(h.bearing < 0.0);
                match h.kind {
                    AgentKind::Robot => 1 + right,
                    AgentKind::Pursuer => 3 + right,
                }
            }
        }
    }
}

/// A body the sensor can return.
#[derive(Clone, Copy, Debug)]
pub struct Target {
    pub pose: Pose,
    pub radius: f64,
    pub kind: AgentKind,
}

/// Cast the observer's sensor against `targets`, returning the nearest hit.
///
/// `observer_index` indexes into `targets` and is skipped. Cost is O(n) per
/// observer, hence O(n^2) per step for the swarm — the build doc's stated
/// budget for Tier 1.
pub fn cast(
    observer: &Target,
    observer_index: usize,
    targets: &[Target],
    cfg: &SensorConfig,
) -> Option<Hit> {
    let origin = observer.pose.p + observer.pose.heading() * observer.radius;
    let mut best: Option<Hit> = None;

    for (j, t) in targets.iter().enumerate() {
        if j == observer_index {
            continue;
        }
        let delta = t.pose.p - origin;
        let d = delta.norm();
        if let Some(r) = cfg.range {
            if d - t.radius > r {
                continue;
            }
        }
        // Body already overlaps the sensor origin: unambiguously in view.
        let bearing = angle_diff(delta.angle(), observer.pose.theta);
        if d <= t.radius {
            let hit = Hit {
                kind: t.kind,
                distance: d,
                bearing,
            };
            if best.map_or(true, |b| d < b.distance) {
                best = Some(hit);
            }
            continue;
        }
        let half_width = (t.radius / d).clamp(-1.0, 1.0).asin();
        if bearing.abs() - half_width > cfg.fov_half_angle {
            continue;
        }
        if best.map_or(true, |b| d < b.distance) {
            best = Some(Hit {
                kind: t.kind,
                distance: d,
                bearing,
            });
        }
    }
    best
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::f64::consts::PI;

    fn robot(x: f64, y: f64, theta: f64) -> Target {
        Target {
            pose: Pose::new(x, y, theta),
            radius: 0.037,
            kind: AgentKind::Robot,
        }
    }

    #[test]
    fn sees_a_robot_dead_ahead() {
        let ts = vec![robot(0.0, 0.0, 0.0), robot(1.0, 0.0, PI)];
        let hit = cast(&ts[0], 0, &ts, &SensorConfig::default()).expect("should see");
        assert_eq!(hit.kind, AgentKind::Robot);
        assert!(hit.bearing.abs() < 1e-9);
    }

    #[test]
    fn does_not_see_a_robot_behind() {
        let ts = vec![robot(0.0, 0.0, 0.0), robot(-1.0, 0.0, 0.0)];
        assert!(cast(&ts[0], 0, &ts, &SensorConfig::default()).is_none());
    }

    #[test]
    fn does_not_see_a_robot_the_ray_misses() {
        // 1 m away, 0.5 m off-axis: far outside the body's angular half-width.
        let ts = vec![robot(0.0, 0.0, 0.0), robot(1.0, 0.5, 0.0)];
        assert!(cast(&ts[0], 0, &ts, &SensorConfig::default()).is_none());
    }

    #[test]
    fn grazing_body_edge_is_still_seen() {
        // Offset just under one body radius at 1 m: the disk still covers the ray.
        let ts = vec![robot(0.0, 0.0, 0.0), robot(1.0, 0.036, 0.0)];
        assert!(cast(&ts[0], 0, &ts, &SensorConfig::default()).is_some());
        let ts = vec![robot(0.0, 0.0, 0.0), robot(1.0, 0.038, 0.0)];
        assert!(cast(&ts[0], 0, &ts, &SensorConfig::default()).is_none());
    }

    #[test]
    fn nearer_body_occludes_the_further_one() {
        let mut ts = vec![robot(0.0, 0.0, 0.0), robot(1.0, 0.0, 0.0)];
        ts.push(Target {
            pose: Pose::new(0.5, 0.0, 0.0),
            radius: 0.037,
            kind: AgentKind::Pursuer,
        });
        let hit = cast(&ts[0], 0, &ts, &SensorConfig::default()).unwrap();
        assert_eq!(hit.kind, AgentKind::Pursuer, "nearest body must win");
        assert!((hit.distance - (0.5 - 0.037)).abs() < 0.05);
    }

    #[test]
    fn range_limit_is_respected() {
        let ts = vec![robot(0.0, 0.0, 0.0), robot(1.0, 0.0, 0.0)];
        let cfg = SensorConfig {
            range: Some(0.5),
            ..Default::default()
        };
        assert!(cast(&ts[0], 0, &ts, &cfg).is_none());
        let cfg = SensorConfig {
            range: Some(1.5),
            ..Default::default()
        };
        assert!(cast(&ts[0], 0, &ts, &cfg).is_some());
    }

    #[test]
    fn wide_cone_sees_off_axis_bodies() {
        let ts = vec![robot(0.0, 0.0, 0.0), robot(1.0, 0.5, 0.0)];
        let cfg = SensorConfig {
            fov_half_angle: 0.6,
            ..Default::default()
        };
        assert!(cast(&ts[0], 0, &ts, &cfg).is_some());
    }

    #[test]
    fn encodings_report_the_capability_vectors_s_component() {
        assert_eq!(SensorEncoding::Binary.states(), 2);
        assert_eq!(SensorEncoding::Ternary.states(), 3);
        assert_eq!(SensorEncoding::TernaryWithSide.states(), 5);

        let hit = |kind, bearing| {
            Some(Hit {
                kind,
                distance: 1.0,
                bearing,
            })
        };
        let pursuer_left = hit(AgentKind::Pursuer, 0.2);
        let pursuer_right = hit(AgentKind::Pursuer, -0.2);
        let robot_left = hit(AgentKind::Robot, 0.2);
        let robot_right = hit(AgentKind::Robot, -0.2);

        // A coarser encoding must not be able to tell finer cases apart.
        assert_eq!(SensorEncoding::Binary.encode(pursuer_left), 1);
        assert_eq!(SensorEncoding::Binary.encode(robot_right), 1);
        assert_eq!(SensorEncoding::Ternary.encode(pursuer_left), 2);
        assert_eq!(SensorEncoding::Ternary.encode(pursuer_right), 2);
        assert_eq!(SensorEncoding::Ternary.encode(robot_left), 1);

        // S = 5: nothing, robot L/R, pursuer L/R -- every state reachable and
        // distinct, which is what makes the row worth five states.
        let five: Vec<usize> = [None, robot_left, robot_right, pursuer_left, pursuer_right]
            .into_iter()
            .map(|h| SensorEncoding::TernaryWithSide.encode(h))
            .collect();
        assert_eq!(five, vec![0, 1, 2, 3, 4]);
        assert!(five
            .iter()
            .all(|&i| i < SensorEncoding::TernaryWithSide.states()));

        assert_eq!(SensorEncoding::Ternary.encode(None), 0);
    }
}
