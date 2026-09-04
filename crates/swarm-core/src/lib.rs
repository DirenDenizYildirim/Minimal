//! # swarm-core — Tier-1 simulator for *Minimal Swarms in Hostile Environments*
//!
//! Minimalist swarm robotics asks "what is the least sensing, compute and memory
//! that produces behaviour X?" and answers it in flat, uniform, unthreatened
//! arenas. This project measures how that minimum **moves** under environmental
//! hostility: capability is the dependent variable, the environment is the
//! independent one.
//!
//! ## What this crate provides
//!
//! * [`controller`] — lookup-table controllers indexed by the capability vector
//!   `c = (S, M, A, K)`, plus the [`controller::Provenance`] tag that keeps
//!   optimiser-found rows labelled as upper bounds.
//! * [`sensor`] — the line-of-sight sensor, with binary / ternary /
//!   ternary-with-side encodings covering the build doc's capability rows.
//! * [`robot`], [`world`] — exact-arc differential-drive kinematics and the loop.
//! * [`terrain`], [`occlusion`] — the implemented hostility dials.
//! * [`pursuer`] — parameters for Idea B; **not stepped yet**, and a config that
//!   asks for one is refused rather than silently ignored.
//! * [`metrics`] — dispersion and clustering, in the swarm-centroid frame.
//!
//! ## Reading order
//!
//! `world::World::step` is the whole model in forty lines; everything else is a
//! detail it calls into.

pub mod config;
pub mod controller;
pub mod field;
pub mod geom;
pub mod metrics;
pub mod occlusion;
pub mod pursuer;
pub mod rng;
pub mod robot;
pub mod sensor;
pub mod terrain;
pub mod world;

pub use config::SimConfig;
pub use controller::{Capability, Provenance, TableController};
pub use world::{RunRecord, World};

/// The controller reported by Gauci, Chen, Li, Dodd and Gross (2014), IJRR,
/// *Self-organized aggregation without computation*, as
/// `(v_l0, v_r0, v_l1, v_r1)` normalised to the maximum wheel speed.
///
/// State 0 (nothing in view) is a circular arc; state 1 (something in view) is a
/// rotation on the spot. Found by exhaustive grid search over four constants,
/// which is why this row — alone among the rows in the build doc — is a *tight*
/// minimum rather than an upper bound.
///
/// Reproducing the aggregation curve these constants produce is the week-1 gate
/// (`docs/validation.md`); until that gate passes, treat every absolute number
/// out of this crate as provisional.
pub const GAUCI_CONSTANTS: [f64; 4] = [-0.7, -1.0, 1.0, -1.0];
