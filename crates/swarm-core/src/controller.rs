//! Lookup-table controllers, indexed by the full capability vector.
//!
//! Build doc section 2.1: `c = (S, M, A, K)` where
//!   * `S` — sensor **states** per timestep (not bits),
//!   * `M` — persistent memory bits carried across timesteps,
//!   * `A` — arithmetic flag; 0 means a pure lookup table,
//!   * `K` — communication bits broadcast per timestep.
//!
//! Everything in Ideas A and B is `A = 0`, so a table indexed by
//! `(sensor_state, memory, received_bits)` covers every row. Table size is
//! `S * 2^M * 2^K_rx`, and the number of free wheel constants is twice that —
//! which is exactly the quantity that decides whether a row is *enumerable* at
//! Gauci's grid resolution or only reachable by an optimiser (section 2.2).

use crate::sensor::SensorEncoding;
use serde::{Deserialize, Serialize};

/// `c = (S, M, A, K)`.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Capability {
    pub sensor_states: usize,
    pub memory_bits: u32,
    pub arithmetic: bool,
    pub comm_bits: u32,
}

impl Capability {
    /// Number of free wheel constants in the table: two per row.
    pub fn free_constants(&self) -> usize {
        2 * self.sensor_states * (1usize << self.memory_bits) * (1usize << self.comm_bits)
    }

    /// Grid points an exhaustive search would visit at `resolution` values per
    /// constant. Gauci's exhaustive search was 4 constants at his resolution;
    /// anything larger is optimiser territory, and therefore an upper bound.
    pub fn exhaustive_grid_size(&self, resolution: u64) -> f64 {
        (resolution as f64).powi(self.free_constants() as i32)
    }

    /// Secondary summary only — the build doc asks for states, with log2 as a
    /// footnote, because bits hide the difference between 3 and 4 states.
    pub fn sensor_bits(&self) -> f64 {
        (self.sensor_states as f64).log2()
    }
}

/// One table row: wheel speeds plus the memory and broadcast updates.
#[derive(Clone, Copy, Debug, PartialEq, Serialize, Deserialize)]
pub struct Entry {
    /// Left/right wheel speeds, normalised to [-1, 1] and scaled by `max_wheel_speed`.
    pub wheels: [f64; 2],
    /// Memory contents for the next timestep. Ignored when `M = 0`.
    #[serde(default)]
    pub next_memory: u32,
    /// Bits broadcast this timestep. Ignored when `K = 0`.
    #[serde(default)]
    pub tx: u32,
}

impl Entry {
    pub fn wheels(left: f64, right: f64) -> Self {
        Self {
            wheels: [left, right],
            next_memory: 0,
            tx: 0,
        }
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct TableController {
    capability: Capability,
    entries: Vec<Entry>,
}

#[derive(Debug)]
pub enum ControllerError {
    WrongLength { expected: usize, got: usize },
    MemoryOutOfRange { row: usize, value: u32, bits: u32 },
    TxOutOfRange { row: usize, value: u32, bits: u32 },
    WheelOutOfRange { row: usize, value: f64 },
}

impl std::fmt::Display for ControllerError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::WrongLength { expected, got } => {
                write!(
                    f,
                    "controller needs {expected} entries for its capability vector, got {got}"
                )
            }
            Self::MemoryOutOfRange { row, value, bits } => {
                write!(
                    f,
                    "row {row}: next_memory {value} does not fit in {bits} bit(s)"
                )
            }
            Self::TxOutOfRange { row, value, bits } => {
                write!(f, "row {row}: tx {value} does not fit in {bits} bit(s)")
            }
            Self::WheelOutOfRange { row, value } => {
                write!(f, "row {row}: wheel constant {value} is outside [-1, 1]")
            }
        }
    }
}

impl std::error::Error for ControllerError {}

impl TableController {
    pub fn new(capability: Capability, entries: Vec<Entry>) -> Result<Self, ControllerError> {
        let expected = capability.sensor_states
            * (1usize << capability.memory_bits)
            * (1usize << capability.comm_bits);
        if entries.len() != expected {
            return Err(ControllerError::WrongLength {
                expected,
                got: entries.len(),
            });
        }
        for (row, e) in entries.iter().enumerate() {
            if capability.memory_bits < 32 && e.next_memory >> capability.memory_bits != 0 {
                return Err(ControllerError::MemoryOutOfRange {
                    row,
                    value: e.next_memory,
                    bits: capability.memory_bits,
                });
            }
            if capability.comm_bits < 32 && e.tx >> capability.comm_bits != 0 {
                return Err(ControllerError::TxOutOfRange {
                    row,
                    value: e.tx,
                    bits: capability.comm_bits,
                });
            }
            for w in e.wheels {
                if !(-1.0..=1.0).contains(&w) {
                    return Err(ControllerError::WheelOutOfRange { row, value: w });
                }
            }
        }
        Ok(Self {
            capability,
            entries,
        })
    }

    /// The Gauci (2014) IJRR controller: one binary sensor, no memory, no
    /// arithmetic, four wheel constants `(vl0, vr0, vl1, vr1)`.
    pub fn gauci(constants: [f64; 4]) -> Result<Self, ControllerError> {
        let capability = Capability {
            sensor_states: 2,
            memory_bits: 0,
            arithmetic: false,
            comm_bits: 0,
        };
        let entries = vec![
            Entry::wheels(constants[0], constants[1]),
            Entry::wheels(constants[2], constants[3]),
        ];
        Self::new(capability, entries)
    }

    pub fn capability(&self) -> Capability {
        self.capability
    }

    pub fn entries(&self) -> &[Entry] {
        &self.entries
    }

    /// Row index for `(sensor_state, memory, rx)`. Memory is the fastest-varying
    /// axis after rx so that a fixed sensor state keeps its rows adjacent.
    pub fn index(&self, sensor_state: usize, memory: u32, rx: u32) -> usize {
        let m = 1usize << self.capability.memory_bits;
        let k = 1usize << self.capability.comm_bits;
        let memory = (memory as usize) % m;
        let rx = (rx as usize) % k;
        (sensor_state.min(self.capability.sensor_states - 1) * m + memory) * k + rx
    }

    pub fn act(&self, sensor_state: usize, memory: u32, rx: u32) -> Entry {
        self.entries[self.index(sensor_state, memory, rx)]
    }
}

/// How a controller's parameters were obtained. Section 2.2 of the build doc:
/// only enumerated rows are tight; everything else is an **upper bound** on
/// `c*(theta)` and every figure and abstract has to say so.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Provenance {
    /// Exhaustive grid search at a stated resolution — ours, or a paper's.
    /// Gauci's four-constant grid qualifies. The minimum is **tight**.
    Enumerated,
    /// Reproduced from a paper whose search was not exhaustive. Trustworthy as
    /// a controller, but not evidence that nothing smaller works.
    Published,
    /// Found by CMA-ES / annealing / AutoMoDe: "not found" != "not possible".
    OptimiserFound,
    /// Hand-written, e.g. for a smoke test.
    HandDesigned,
}

impl Provenance {
    /// True when a reported minimum from this row may be called tight.
    pub fn is_tight(&self) -> bool {
        matches!(self, Provenance::Enumerated)
    }
}

/// Config-file form of a controller.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum ControllerConfig {
    /// Four constants against a binary sensor.
    Gauci {
        constants: [f64; 4],
        #[serde(default = "default_optimiser")]
        provenance: Provenance,
    },
    /// A general table. `sensor_states` must match the sensor encoding.
    Table {
        memory_bits: u32,
        #[serde(default)]
        comm_bits: u32,
        entries: Vec<Entry>,
        #[serde(default = "default_optimiser")]
        provenance: Provenance,
    },
}

/// A row that does not state its provenance is assumed optimiser-found. Four
/// constants happen to be enumerable, but the config cannot know whether *this*
/// set came out of a grid search or an optimiser, and the pessimistic default is
/// the one that keeps a claim honest.
fn default_optimiser() -> Provenance {
    Provenance::OptimiserFound
}

impl ControllerConfig {
    pub fn provenance(&self) -> Provenance {
        match self {
            ControllerConfig::Gauci { provenance, .. } => *provenance,
            ControllerConfig::Table { provenance, .. } => *provenance,
        }
    }

    pub fn build(&self, encoding: SensorEncoding) -> Result<TableController, ControllerError> {
        match self {
            ControllerConfig::Gauci { constants, .. } => TableController::gauci(*constants),
            ControllerConfig::Table {
                memory_bits,
                comm_bits,
                entries,
                ..
            } => {
                let capability = Capability {
                    sensor_states: encoding.states(),
                    memory_bits: *memory_bits,
                    arithmetic: false,
                    comm_bits: *comm_bits,
                };
                TableController::new(capability, entries.clone())
            }
        }
    }
}

impl Default for ControllerConfig {
    fn default() -> Self {
        ControllerConfig::Gauci {
            constants: crate::GAUCI_CONSTANTS,
            // These constants *are* the output of Gauci's exhaustive grid.
            provenance: Provenance::Enumerated,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn gauci_row_is_two_entries_and_four_constants() {
        let c = TableController::gauci(crate::GAUCI_CONSTANTS).unwrap();
        assert_eq!(c.entries().len(), 2);
        assert_eq!(c.capability().free_constants(), 4);
        assert_eq!(c.capability().sensor_states, 2);
        assert_eq!(c.capability().memory_bits, 0);
        assert!(!c.capability().arithmetic);
        assert_eq!(c.capability().comm_bits, 0);
    }

    #[test]
    fn one_memory_bit_doubles_the_table_and_leaves_enumeration_behind() {
        // The week-3 shakedown's hysteresis row: 8 constants, not 4.
        let cap = Capability {
            sensor_states: 2,
            memory_bits: 1,
            arithmetic: false,
            comm_bits: 0,
        };
        assert_eq!(cap.free_constants(), 8);
        // At Gauci's resolution the grid grows from r^4 to r^8.
        let gauci = Capability {
            memory_bits: 0,
            ..cap
        };
        assert_eq!(
            cap.exhaustive_grid_size(20) / gauci.exhaustive_grid_size(20),
            20f64.powi(4)
        );
    }

    #[test]
    fn index_is_a_bijection_over_the_table() {
        let cap = Capability {
            sensor_states: 3,
            memory_bits: 1,
            arithmetic: false,
            comm_bits: 1,
        };
        let entries = vec![Entry::wheels(0.0, 0.0); 3 * 2 * 2];
        let c = TableController::new(cap, entries).unwrap();
        let mut seen = vec![false; 12];
        for s in 0..3 {
            for m in 0..2 {
                for k in 0..2 {
                    let i = c.index(s, m, k);
                    assert!(!seen[i], "index collision at ({s},{m},{k})");
                    seen[i] = true;
                }
            }
        }
        assert!(seen.into_iter().all(|x| x));
    }

    #[test]
    fn wrong_table_length_is_rejected() {
        let cap = Capability {
            sensor_states: 3,
            memory_bits: 0,
            arithmetic: false,
            comm_bits: 0,
        };
        let err = TableController::new(cap, vec![Entry::wheels(0.0, 0.0); 2]).unwrap_err();
        assert!(matches!(
            err,
            ControllerError::WrongLength {
                expected: 3,
                got: 2
            }
        ));
    }

    #[test]
    fn out_of_range_memory_and_wheels_are_rejected() {
        let cap = Capability {
            sensor_states: 2,
            memory_bits: 1,
            arithmetic: false,
            comm_bits: 0,
        };
        let mut entries = vec![Entry::wheels(0.0, 0.0); 4];
        entries[2].next_memory = 3;
        assert!(TableController::new(cap, entries).is_err());

        let cap0 = Capability {
            memory_bits: 0,
            ..cap
        };
        let entries = vec![Entry::wheels(0.0, 0.0), Entry::wheels(1.5, 0.0)];
        assert!(TableController::new(cap0, entries).is_err());
    }

    #[test]
    fn only_enumerated_rows_are_tight() {
        assert!(Provenance::Enumerated.is_tight());
        assert!(!Provenance::OptimiserFound.is_tight());
        assert!(!Provenance::Published.is_tight());
        // An unlabelled Gauci-shaped row is four constants, but the config
        // cannot know they came from a grid search, so it must not claim tight.
        let cfg: ControllerConfig =
            serde_json::from_str(r#"{"kind":"gauci","constants":[0,0,0,0]}"#).unwrap();
        assert_eq!(cfg.provenance(), Provenance::OptimiserFound);
        // An unlabelled table row defaults to the honest assumption.
        let cfg: ControllerConfig = serde_json::from_str(
            r#"{"kind":"table","memory_bits":0,"entries":[{"wheels":[0,0]},{"wheels":[0,0]}]}"#,
        )
        .unwrap();
        assert_eq!(cfg.provenance(), Provenance::OptimiserFound);
    }
}
