//! Pursuer parameters — Idea B (build doc section 3, weeks 7-11).
//!
//! **Status: parameters only.** The pursuer is not stepped yet; a config that
//! sets one is rejected by `SimConfig::validate` rather than silently ignored.
//! The types live here now because they pin down the design the rest of the
//! simulator already accommodates: `AgentKind::Pursuer` exists in the sensor,
//! and the ternary and ternary-with-side encodings (rows B1-B4) are implemented
//! and tested against it.
//!
//! The v1 pursuer — nearest target, perfect perception, unbounded range — made
//! a tight cluster the *cheapest* thing to hunt, so aggregation scored as the
//! worst strategy and the metric never saw the dilution effect. The corrected
//! family adds three perception dials, under which aggregation has two possible
//! protective mechanisms: search cost (fewer, harder-to-find targets) and
//! lock-on failure (confusion). `r_p = inf, kappa = 0` recovers the v1 pursuer
//! and is kept as one adversarial corner of the sweep.

use serde::{Deserialize, Serialize};

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
        }
    }
}

impl PursuerConfig {
    /// `p_lock` given the number of robots inside the pursuer's confusion radius.
    pub fn lock_probability(&self, n_local: usize) -> f64 {
        1.0 / (1.0 + self.confusion * n_local as f64)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zero_confusion_always_locks() {
        let p = PursuerConfig {
            confusion: 0.0,
            ..Default::default()
        };
        assert_eq!(p.lock_probability(0), 1.0);
        assert_eq!(p.lock_probability(50), 1.0);
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
