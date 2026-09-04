//! Occlusion: the week-3 shakedown dial.
//!
//! Build doc, "Week-3 shakedown": at what false-negative rate does the
//! zero-memory Gauci controller fall below the threshold `T`, and does one bit
//! of hysteresis restore it?
//!
//! The dial is a pair of rates applied to the line-of-sight reading:
//!   * `fn_rate` — probability a genuine detection is dropped;
//!   * `fp_rate` — probability an empty reading reports a robot.
//!
//! Both are **spatially correlated** rather than i.i.d.: `correlation_amplitude`
//! modulates the local rate by a smoothed random field of correlation length
//! `correlation_length`, so the arena has patches where the sensor is
//! systematically worse — the regime a real occluder produces. Setting
//! `correlation_amplitude = 0` recovers i.i.d. dropout, which is the cheap
//! control condition to run alongside it.
//!
//! Note the modulation is multiplicative and clamped, so the *mean* realised
//! rate is close to `fn_rate` but not exactly equal to it; `realised_fn_rate`
//! on the run record reports what actually happened.

use crate::field::ScalarField;
use crate::geom::Vec2;
use crate::rng::Rng;
use crate::sensor::{AgentKind, Hit};
use rand::Rng as _;
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct OcclusionConfig {
    pub fn_rate: f64,
    pub fp_rate: f64,
    /// 0 = i.i.d. dropout; >0 makes the rate vary smoothly across the arena.
    pub correlation_amplitude: f64,
    pub correlation_length: f64,
    /// Distance reported for a fabricated (false-positive) hit, in metres.
    pub false_positive_distance: f64,
}

impl Default for OcclusionConfig {
    fn default() -> Self {
        Self {
            fn_rate: 0.0,
            fp_rate: 0.0,
            correlation_amplitude: 0.0,
            correlation_length: 0.5,
            false_positive_distance: 0.5,
        }
    }
}

impl OcclusionConfig {
    pub fn is_clean(&self) -> bool {
        self.fn_rate == 0.0 && self.fp_rate == 0.0
    }
}

#[derive(Clone, Copy, Debug)]
pub struct Occlusion {
    cfg: OcclusionConfig,
    field: ScalarField,
}

/// Tally of how many readings were actually corrupted, so a run can report the
/// realised rate rather than only the nominal dial setting.
#[derive(Clone, Copy, Debug, Default, Serialize, Deserialize)]
pub struct OcclusionTally {
    pub true_positives: u64,
    pub dropped: u64,
    pub true_negatives: u64,
    pub fabricated: u64,
}

impl OcclusionTally {
    pub fn realised_fn_rate(&self) -> f64 {
        let d = self.true_positives + self.dropped;
        if d == 0 {
            0.0
        } else {
            self.dropped as f64 / d as f64
        }
    }

    pub fn realised_fp_rate(&self) -> f64 {
        let d = self.true_negatives + self.fabricated;
        if d == 0 {
            0.0
        } else {
            self.fabricated as f64 / d as f64
        }
    }
}

impl Occlusion {
    pub fn new(cfg: OcclusionConfig, seed: u64) -> Self {
        let field = ScalarField::new(seed, cfg.correlation_length);
        Self { cfg, field }
    }

    pub fn config(&self) -> &OcclusionConfig {
        &self.cfg
    }

    /// Local rate at `p`, modulated by the correlated field and clamped to [0, 1].
    pub fn local_rate(&self, base: f64, p: Vec2) -> f64 {
        if base == 0.0 || self.cfg.correlation_amplitude == 0.0 {
            return base.clamp(0.0, 1.0);
        }
        (base * (1.0 + self.cfg.correlation_amplitude * self.field.sample(p))).clamp(0.0, 1.0)
    }

    /// Corrupt one reading taken at `p`.
    pub fn corrupt(
        &self,
        hit: Option<Hit>,
        p: Vec2,
        rng: &mut Rng,
        tally: &mut OcclusionTally,
    ) -> Option<Hit> {
        if self.cfg.is_clean() {
            return hit;
        }
        match hit {
            Some(h) => {
                if rng.gen::<f64>() < self.local_rate(self.cfg.fn_rate, p) {
                    tally.dropped += 1;
                    None
                } else {
                    tally.true_positives += 1;
                    Some(h)
                }
            }
            None => {
                if rng.gen::<f64>() < self.local_rate(self.cfg.fp_rate, p) {
                    tally.fabricated += 1;
                    Some(Hit {
                        kind: AgentKind::Robot,
                        distance: self.cfg.false_positive_distance,
                        bearing: 0.0,
                    })
                } else {
                    tally.true_negatives += 1;
                    None
                }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::rng::rng_from;

    fn a_hit() -> Option<Hit> {
        Some(Hit {
            kind: AgentKind::Robot,
            distance: 0.4,
            bearing: 0.0,
        })
    }

    #[test]
    fn clean_config_passes_readings_through() {
        let o = Occlusion::new(OcclusionConfig::default(), 1);
        let mut rng = rng_from(0);
        let mut tally = OcclusionTally::default();
        assert!(o
            .corrupt(a_hit(), Vec2::ZERO, &mut rng, &mut tally)
            .is_some());
        assert!(o.corrupt(None, Vec2::ZERO, &mut rng, &mut tally).is_none());
    }

    #[test]
    fn iid_false_negative_rate_matches_the_dial() {
        let cfg = OcclusionConfig {
            fn_rate: 0.3,
            ..Default::default()
        };
        let o = Occlusion::new(cfg, 5);
        let mut rng = rng_from(7);
        let mut tally = OcclusionTally::default();
        for _ in 0..20_000 {
            o.corrupt(a_hit(), Vec2::new(1.0, 1.0), &mut rng, &mut tally);
        }
        assert!(
            (tally.realised_fn_rate() - 0.3).abs() < 0.02,
            "realised {}",
            tally.realised_fn_rate()
        );
    }

    #[test]
    fn correlated_rates_vary_across_the_arena_but_average_near_the_dial() {
        let cfg = OcclusionConfig {
            fn_rate: 0.3,
            correlation_amplitude: 0.9,
            correlation_length: 0.5,
            ..Default::default()
        };
        let o = Occlusion::new(cfg, 5);
        let rates: Vec<f64> = (0..400)
            .map(|i| o.local_rate(0.3, Vec2::new(i as f64 * 0.37, i as f64 * 0.21)))
            .collect();
        let mean = rates.iter().sum::<f64>() / rates.len() as f64;
        let spread = rates.iter().cloned().fold(f64::MIN, f64::max)
            - rates.iter().cloned().fold(f64::MAX, f64::min);
        assert!(
            spread > 0.1,
            "correlated rates should vary, spread {spread}"
        );
        assert!((mean - 0.3).abs() < 0.05, "mean rate drifted to {mean}");
    }

    #[test]
    fn false_positives_fabricate_a_robot_not_a_pursuer() {
        let cfg = OcclusionConfig {
            fp_rate: 1.0,
            ..Default::default()
        };
        let o = Occlusion::new(cfg, 1);
        let mut rng = rng_from(0);
        let mut tally = OcclusionTally::default();
        let h = o.corrupt(None, Vec2::ZERO, &mut rng, &mut tally).unwrap();
        assert_eq!(h.kind, AgentKind::Robot);
        assert_eq!(tally.fabricated, 1);
    }
}
