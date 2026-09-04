//! Run configuration. Every field is `serde(default)` so a config file states
//! only what it changes from the clean-arena baseline — which keeps the diff
//! between a baseline cell and a hostile cell readable.

use crate::controller::ControllerConfig;
use crate::occlusion::OcclusionConfig;
use crate::pursuer::PursuerConfig;
use crate::sensor::SensorConfig;
use crate::terrain::TerrainConfig;
use serde::{Deserialize, Serialize};

/// e-puck body and drivetrain constants.
///
/// **These are the numbers the week-1 gate must confirm against Gauci et al.
/// (2014) IJRR before any absolute figure is quoted.** See `docs/validation.md`.
#[derive(Clone, Copy, Debug, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct RobotConfig {
    /// Body radius in metres.
    pub radius: f64,
    /// Wheel separation in metres.
    pub axle_length: f64,
    /// Maximum wheel speed in m/s; table constants are normalised to this.
    pub max_wheel_speed: f64,
}

impl Default for RobotConfig {
    fn default() -> Self {
        Self {
            radius: 0.037,
            axle_length: 0.053,
            max_wheel_speed: 0.128,
        }
    }
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize)]
#[serde(tag = "shape", rename_all = "snake_case", deny_unknown_fields)]
pub enum InitConfig {
    /// Uniform, non-overlapping placement in a disk.
    Disk {
        /// Explicit start radius in metres. When absent it is derived from
        /// `coverage` so that initial density is constant across swarm sizes —
        /// which is what makes the scaling curve in `n` interpretable.
        #[serde(default)]
        radius: Option<f64>,
        /// Fraction of the start disk covered by robot bodies.
        #[serde(default = "default_coverage")]
        coverage: f64,
    },
}

fn default_coverage() -> f64 {
    0.05
}

impl Default for InitConfig {
    fn default() -> Self {
        InitConfig::Disk {
            radius: None,
            coverage: default_coverage(),
        }
    }
}

impl InitConfig {
    pub fn start_radius(&self, n: usize, robot_radius: f64) -> f64 {
        match self {
            InitConfig::Disk {
                radius: Some(r), ..
            } => *r,
            InitConfig::Disk {
                radius: None,
                coverage,
            } => {
                let coverage = coverage.clamp(1e-4, 0.9);
                robot_radius * (n as f64 / coverage).sqrt()
            }
        }
    }
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct SwarmConfig {
    pub n: usize,
    pub init: InitConfig,
}

impl Default for SwarmConfig {
    fn default() -> Self {
        Self {
            n: 20,
            init: InitConfig::default(),
        }
    }
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct SimParams {
    /// Control period in seconds.
    pub dt: f64,
    /// Trial length `tau` in seconds; metrics are reported at `tau`.
    pub duration: f64,
    pub seed: u64,
    /// Resolve body overlaps after each step. Daymude et al. (2021) report that
    /// collisions and slipping are what break deterministic deadlock in
    /// practice, so this is on by default and is a documented model choice.
    pub collisions: bool,
    /// Maximum relaxation passes per step. The loop exits early once the worst
    /// residual overlap is under `contact_tolerance`, so a sparse swarm pays for
    /// one pass and only a packed cluster pays for the rest.
    pub collision_iterations: usize,
    /// Residual overlap in metres that counts as resolved.
    pub contact_tolerance: f64,
    /// The arena is unbounded, as in Gauci's simulation. A bounded arena would
    /// let a downhill wall do the aggregating for us (build doc, Idea A).
    pub unbounded: bool,
}

impl Default for SimParams {
    fn default() -> Self {
        Self {
            dt: 0.1,
            duration: 600.0,
            seed: 0,
            collisions: true,
            collision_iterations: 32,
            contact_tolerance: 1e-5,
            unbounded: true,
        }
    }
}

/// Actuation noise present on a flat, clean board.
///
/// Not a hostility dial — a property of the robot. Without it the state-0 wheel
/// constants trace an *exactly closed* circle: the robot returns to where it
/// started and never explores, so a sparse swarm can never find itself. Real
/// e-pucks slip, and Daymude et al. (2021) report that collisions and slipping
/// are what break deterministic deadlock in practice; the build doc's H1 leans
/// on the same observation ("small alpha and theta_m help, as motion noise did
/// in Daymude et al."). A noise-free simulator is the anomaly, not the baseline.
///
/// See `docs/decisions/0004-baseline-actuation-noise.md`.
#[derive(Clone, Copy, Debug, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct NoiseConfig {
    /// Per-wheel Gaussian noise added to the realised wheel speed each control
    /// step, as a fraction of `max_wheel_speed`. 0 reproduces the noise-free
    /// idealisation, which is useful as a control and useless as a baseline.
    pub wheel_noise: f64,
}

impl Default for NoiseConfig {
    fn default() -> Self {
        // Off by default: the reference baseline is the noise-free idealisation
        // Gauci's simulation uses, and adding noise silently would change every
        // number measured against it. Measured effect at n = 20 is mildly
        // negative (see docs/decisions/0004-baseline-actuation-noise.md), so
        // this is a dial to sweep, not a correction to apply.
        Self { wheel_noise: 0.0 }
    }
}

#[derive(Clone, Copy, Debug, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct MetricsConfig {
    /// Two bodies are linked when their centres are within this many body radii.
    ///
    /// The cluster count is sensitive to this: an aggregated swarm keeps one
    /// robot hovering near the threshold, so "is it exactly one cluster?"
    /// flickers between 1 and 2 from sample to sample. Report the value used,
    /// and prefer dispersion or the largest-cluster fraction over the boolean.
    pub cluster_link_radii: f64,
    /// Seconds between samples. 0 disables sampling (and with it the
    /// time-resolved metrics). Sampling is cheap relative to the sensor loop.
    pub sample_interval: f64,
    /// Keep the per-sample series on the run record. Off for sweeps, where the
    /// series would dominate the output size — the aggregate time-resolved
    /// metrics are computed either way.
    pub store_series: bool,
}

impl Default for MetricsConfig {
    fn default() -> Self {
        Self {
            cluster_link_radii: 3.0,
            sample_interval: 10.0,
            store_series: true,
        }
    }
}

#[derive(Clone, Debug, Default, Serialize, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub struct SimConfig {
    pub robot: RobotConfig,
    pub swarm: SwarmConfig,
    pub sim: SimParams,
    pub sensor: SensorConfig,
    pub controller: ControllerConfig,
    pub noise: NoiseConfig,
    pub occlusion: OcclusionConfig,
    pub terrain: TerrainConfig,
    /// Idea B. Not implemented yet; rejected by `validate` so a config cannot
    /// quietly produce pursuer-free results under a pursuer filename.
    pub pursuer: Option<PursuerConfig>,
    pub metrics: MetricsConfig,
}

#[derive(Debug)]
pub struct ConfigError(pub String);

impl std::fmt::Display for ConfigError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl std::error::Error for ConfigError {}

impl SimConfig {
    pub fn validate(&self) -> Result<(), ConfigError> {
        let err = |m: String| Err(ConfigError(m));
        if self.swarm.n == 0 {
            return err("swarm.n must be at least 1".into());
        }
        if self.sim.dt <= 0.0 || !self.sim.dt.is_finite() {
            return err(format!(
                "sim.dt must be positive and finite, got {}",
                self.sim.dt
            ));
        }
        if self.sim.duration <= 0.0 {
            return err(format!(
                "sim.duration must be positive, got {}",
                self.sim.duration
            ));
        }
        if self.robot.radius <= 0.0 || self.robot.axle_length <= 0.0 {
            return err("robot.radius and robot.axle_length must be positive".into());
        }
        if self.robot.max_wheel_speed <= 0.0 {
            return err("robot.max_wheel_speed must be positive".into());
        }
        if self.noise.wheel_noise < 0.0 || !self.noise.wheel_noise.is_finite() {
            return err(format!(
                "noise.wheel_noise must be non-negative and finite, got {}",
                self.noise.wheel_noise
            ));
        }
        if !(0.0..=1.0).contains(&self.occlusion.fn_rate)
            || !(0.0..=1.0).contains(&self.occlusion.fp_rate)
        {
            return err("occlusion rates must lie in [0, 1]".into());
        }
        if !self.sim.unbounded {
            return err(
                "bounded arenas are not implemented: a wall would aggregate the swarm for us \
                 (build doc, Idea A)"
                    .into(),
            );
        }
        if self.pursuer.is_some() {
            return err(
                "pursuer is configured but Idea B is not implemented yet (weeks 7-11); \
                 refusing to run so results cannot be mislabelled"
                    .into(),
            );
        }
        let encoding = self.sensor.encoding;
        self.controller
            .build(encoding)
            .map_err(|e| ConfigError(format!("controller: {e}")))?;
        if let ControllerConfig::Gauci { .. } = self.controller {
            if encoding.states() != 2 {
                return err(format!(
                    "controller kind 'gauci' has 2 sensor states but sensor.encoding has {}",
                    encoding.states()
                ));
            }
        }
        Ok(())
    }

    /// Parse from JSON. The CLI reads TOML and converts; keeping `swarm-core`
    /// free of a TOML dependency means the same config structs can be driven
    /// from Python, from a sweep file, or from a test literal without change.
    pub fn from_json(s: &str) -> Result<Self, ConfigError> {
        let cfg: SimConfig =
            serde_json::from_str(s).map_err(|e| ConfigError(format!("parsing config: {e}")))?;
        cfg.validate()?;
        Ok(cfg)
    }

    pub fn from_json_value(v: serde_json::Value) -> Result<Self, ConfigError> {
        let cfg: SimConfig =
            serde_json::from_value(v).map_err(|e| ConfigError(format!("parsing config: {e}")))?;
        cfg.validate()?;
        Ok(cfg)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn defaults_are_a_valid_clean_arena() {
        let cfg = SimConfig::default();
        cfg.validate().unwrap();
        assert!(cfg.terrain.is_flat());
        assert!(cfg.occlusion.is_clean());
        assert!(cfg.pursuer.is_none());
    }

    #[test]
    fn start_radius_holds_density_constant_across_n() {
        let init = InitConfig::default();
        let r = 0.037;
        let coverage = |n: usize| {
            let rad = init.start_radius(n, r);
            n as f64 * r * r / (rad * rad)
        };
        assert!((coverage(10) - coverage(1000)).abs() < 1e-12);
        assert!((coverage(10) - 0.05).abs() < 1e-12);
    }

    #[test]
    fn explicit_start_radius_wins() {
        let init = InitConfig::Disk {
            radius: Some(1.5),
            coverage: 0.05,
        };
        assert_eq!(init.start_radius(10, 0.037), 1.5);
        assert_eq!(init.start_radius(1000, 0.037), 1.5);
    }

    #[test]
    fn a_configured_pursuer_is_refused_rather_than_ignored() {
        let cfg = SimConfig {
            pursuer: Some(PursuerConfig::default()),
            ..Default::default()
        };
        let e = cfg.validate().unwrap_err().to_string();
        assert!(e.contains("Idea B is not implemented"), "{e}");
    }

    #[test]
    fn mismatched_sensor_encoding_and_controller_is_refused() {
        let cfg = SimConfig {
            sensor: SensorConfig {
                encoding: crate::sensor::SensorEncoding::Ternary,
                ..Default::default()
            },
            ..Default::default()
        };
        assert!(cfg.validate().is_err());
    }

    #[test]
    fn bad_numbers_are_refused() {
        let bad = |f: fn(&mut SimConfig)| {
            let mut c = SimConfig::default();
            f(&mut c);
            assert!(c.validate().is_err());
        };
        bad(|c| c.swarm.n = 0);
        bad(|c| c.sim.dt = 0.0);
        bad(|c| c.sim.duration = -1.0);
        bad(|c| c.robot.radius = 0.0);
        bad(|c| c.occlusion.fn_rate = 1.5);
        bad(|c| c.sim.unbounded = false);
    }
}
