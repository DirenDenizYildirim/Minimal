//! Sweep files: a base config, a grid of environment dials, and a set of
//! capability rows evaluated on that same grid.
//!
//! The build doc's figure is a **performance surface** per capability row with
//! threshold contours drawn on it, so the natural unit of work is
//! `(row, theta-cell, run)`. Rows are a *set* of capability vectors, not a
//! chain of supersets — B3 and B4 are incomparable with B2 — so nothing here
//! assumes an ordering between them.

use anyhow::{bail, Context, Result};
use serde::Deserialize;
use serde_json::Value;
use std::path::{Path, PathBuf};

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SweepFile {
    pub name: String,
    /// Path to the base config, relative to the sweep file.
    pub base: PathBuf,
    #[serde(default = "default_runs")]
    pub runs_per_cell: u64,
    /// Axes of the environment grid. An empty list means a single cell.
    #[serde(default)]
    pub axis: Vec<Axis>,
    /// Capability rows compared on the grid. Empty means the base config alone.
    #[serde(default)]
    pub rows: Vec<Row>,
}

fn default_runs() -> u64 {
    100
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Axis {
    /// Dotted path into the config, e.g. `occlusion.fn_rate`.
    pub path: String,
    pub values: Vec<Value>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Row {
    pub label: String,
    /// Dotted path -> value. Setting a parent path replaces the whole subtree,
    /// which is how a row swaps in a different controller table.
    #[serde(default)]
    pub overrides: std::collections::BTreeMap<String, Value>,
}

/// One point of the (row x theta) product: a fully-resolved config plus the
/// coordinates that identify it in the output.
pub struct Cell {
    pub config: Value,
    pub coords: serde_json::Map<String, Value>,
}

impl SweepFile {
    pub fn load(path: &Path) -> Result<Self> {
        let text = std::fs::read_to_string(path)
            .with_context(|| format!("reading sweep file {}", path.display()))?;
        let sweep: SweepFile = toml::from_str(&text)
            .with_context(|| format!("parsing sweep file {}", path.display()))?;
        if sweep.runs_per_cell == 0 {
            bail!("runs_per_cell must be at least 1");
        }
        for a in &sweep.axis {
            if a.values.is_empty() {
                bail!("axis '{}' has no values", a.path);
            }
        }
        Ok(sweep)
    }

    /// Expand into every `(row, theta-cell)` combination.
    pub fn cells(&self, base: &Value) -> Result<Vec<Cell>> {
        let rows: Vec<&Row> = if self.rows.is_empty() {
            vec![]
        } else {
            self.rows.iter().collect()
        };
        let grid = self.grid();

        let mut out = Vec::new();
        if rows.is_empty() {
            for point in &grid {
                out.push(self.make_cell(base, None, point)?);
            }
        } else {
            for row in rows {
                for point in &grid {
                    out.push(self.make_cell(base, Some(row), point)?);
                }
            }
        }
        Ok(out)
    }

    /// Cartesian product of the axes, as `(path, value)` lists.
    fn grid(&self) -> Vec<Vec<(String, Value)>> {
        let mut grid: Vec<Vec<(String, Value)>> = vec![vec![]];
        for axis in &self.axis {
            let mut next = Vec::with_capacity(grid.len() * axis.values.len());
            for prefix in &grid {
                for v in &axis.values {
                    let mut p = prefix.clone();
                    p.push((axis.path.clone(), v.clone()));
                    next.push(p);
                }
            }
            grid = next;
        }
        grid
    }

    fn make_cell(
        &self,
        base: &Value,
        row: Option<&Row>,
        point: &[(String, Value)],
    ) -> Result<Cell> {
        let mut config = base.clone();
        let mut coords = serde_json::Map::new();
        coords.insert("sweep".into(), Value::String(self.name.clone()));

        if let Some(row) = row {
            coords.insert("row".into(), Value::String(row.label.clone()));
            for (path, value) in &row.overrides {
                set_path(&mut config, path, value.clone())
                    .with_context(|| format!("row '{}': setting {path}", row.label))?;
            }
        }
        for (path, value) in point {
            set_path(&mut config, path, value.clone())
                .with_context(|| format!("setting axis {path}"))?;
        }
        for (path, value) in point {
            coords.insert(path.clone(), value.clone());
        }
        Ok(Cell { config, coords })
    }
}

/// Set a dotted path in a JSON tree, creating intermediate objects as needed.
pub fn set_path(root: &mut Value, path: &str, value: Value) -> Result<()> {
    if path.is_empty() {
        bail!("empty override path");
    }
    let parts: Vec<&str> = path.split('.').collect();
    let mut node = root;
    for part in &parts[..parts.len() - 1] {
        if !node.is_object() {
            *node = Value::Object(serde_json::Map::new());
        }
        node = node
            .as_object_mut()
            .expect("just ensured object")
            .entry((*part).to_string())
            .or_insert_with(|| Value::Object(serde_json::Map::new()));
    }
    if !node.is_object() {
        *node = Value::Object(serde_json::Map::new());
    }
    node.as_object_mut()
        .expect("just ensured object")
        .insert(parts[parts.len() - 1].to_string(), value);
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn set_path_creates_and_overwrites() {
        let mut v = json!({"a": {"b": 1}});
        set_path(&mut v, "a.b", json!(2)).unwrap();
        set_path(&mut v, "a.c", json!("x")).unwrap();
        set_path(&mut v, "d.e.f", json!(true)).unwrap();
        assert_eq!(v, json!({"a": {"b": 2, "c": "x"}, "d": {"e": {"f": true}}}));
    }

    #[test]
    fn setting_a_parent_replaces_the_whole_subtree() {
        // This is how a capability row swaps a 4-constant Gauci table for an
        // 8-constant hysteresis table without leaving stale keys behind.
        let mut v = json!({"controller": {"kind": "gauci", "constants": [1, 2, 3, 4]}});
        set_path(
            &mut v,
            "controller",
            json!({"kind": "table", "memory_bits": 1}),
        )
        .unwrap();
        assert_eq!(v["controller"], json!({"kind": "table", "memory_bits": 1}));
        assert!(v["controller"].get("constants").is_none());
    }

    #[test]
    fn grid_is_the_cartesian_product_of_the_axes() {
        let sweep = SweepFile {
            name: "t".into(),
            base: "b.toml".into(),
            runs_per_cell: 1,
            axis: vec![
                Axis {
                    path: "a".into(),
                    values: vec![json!(1), json!(2)],
                },
                Axis {
                    path: "b".into(),
                    values: vec![json!(10), json!(20), json!(30)],
                },
            ],
            rows: vec![],
        };
        assert_eq!(sweep.grid().len(), 6);
        let cells = sweep.cells(&json!({})).unwrap();
        assert_eq!(cells.len(), 6);
        assert_eq!(cells[0].config, json!({"a": 1, "b": 10}));
        assert_eq!(cells[0].coords["a"], json!(1));
    }

    #[test]
    fn rows_multiply_the_grid_and_are_labelled() {
        let sweep = SweepFile {
            name: "t".into(),
            base: "b.toml".into(),
            runs_per_cell: 1,
            axis: vec![Axis {
                path: "a".into(),
                values: vec![json!(1), json!(2)],
            }],
            rows: vec![
                Row {
                    label: "r1".into(),
                    overrides: Default::default(),
                },
                Row {
                    label: "r2".into(),
                    overrides: Default::default(),
                },
            ],
        };
        let cells = sweep.cells(&json!({})).unwrap();
        assert_eq!(cells.len(), 4);
        assert_eq!(cells[0].coords["row"], json!("r1"));
        assert_eq!(cells[3].coords["row"], json!("r2"));
    }

    #[test]
    fn an_axis_overrides_a_row_setting_the_same_path() {
        let mut overrides = std::collections::BTreeMap::new();
        overrides.insert("a".to_string(), json!(99));
        let sweep = SweepFile {
            name: "t".into(),
            base: "b.toml".into(),
            runs_per_cell: 1,
            axis: vec![Axis {
                path: "a".into(),
                values: vec![json!(1)],
            }],
            rows: vec![Row {
                label: "r".into(),
                overrides,
            }],
        };
        let cells = sweep.cells(&json!({})).unwrap();
        assert_eq!(cells[0].config["a"], json!(1), "the swept dial must win");
    }
}
