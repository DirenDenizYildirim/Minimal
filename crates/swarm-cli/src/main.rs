//! `swarm` — runner for the Tier-1 simulator.
//!
//! Three subcommands:
//!   * `describe` — capability accounting for a config: `c = (S, M, A, K)`,
//!     the state-0 circle radius `R0`, table size, and whether the row could be
//!     enumerated at Gauci's resolution or is only an upper bound.
//!   * `run` — repeated trials of one config to JSONL.
//!   * `sweep` — a grid of environment dials crossed with capability rows.
//!
//! Output is JSON Lines, one `RunRecord` per trial, consumed by `harness/`.

mod sweep;

use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use rayon::prelude::*;
use serde_json::Value;
use std::io::Write;
use std::path::{Path, PathBuf};
use swarm_core::{SimConfig, World};

#[derive(Parser)]
#[command(
    name = "swarm",
    version,
    about = "Minimal swarms in hostile environments — Tier-1 sim"
)]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    /// Print the capability accounting for a config without running anything.
    Describe {
        #[arg(short, long)]
        config: PathBuf,
    },
    /// Run repeated trials of a single config.
    Run {
        #[arg(short, long)]
        config: PathBuf,
        #[arg(short, long, default_value_t = 30)]
        runs: u64,
        /// Output JSONL path. Omit to write to stdout.
        #[arg(short, long)]
        out: Option<PathBuf>,
        /// Override `sim.seed`.
        #[arg(long)]
        seed: Option<u64>,
        /// Drop the per-run time series. Time-resolved *aggregates* are still
        /// computed; only the per-sample rows are omitted.
        #[arg(long)]
        no_series: bool,
        #[arg(short, long)]
        threads: Option<usize>,
    },
    /// Run a sweep file: capability rows crossed with a grid of hostility dials.
    Sweep {
        #[arg(short, long)]
        config: PathBuf,
        #[arg(short, long)]
        out: PathBuf,
        #[arg(short, long)]
        threads: Option<usize>,
        /// Validate every cell and report the workload without simulating.
        #[arg(long)]
        dry_run: bool,
        /// Keep the per-run time series. Off by default: a sweep is usually
        /// tens of thousands of runs and the series dominates the file size.
        #[arg(long)]
        series: bool,
    },
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.command {
        Command::Describe { config } => describe(&config),
        Command::Run {
            config,
            runs,
            out,
            seed,
            no_series,
            threads,
        } => {
            set_threads(threads)?;
            run_cmd(&config, runs, out.as_deref(), seed, no_series)
        }
        Command::Sweep {
            config,
            out,
            threads,
            dry_run,
            series,
        } => {
            set_threads(threads)?;
            sweep_cmd(&config, &out, dry_run, series)
        }
    }
}

fn set_threads(threads: Option<usize>) -> Result<()> {
    if let Some(t) = threads {
        rayon::ThreadPoolBuilder::new()
            .num_threads(t)
            .build_global()
            .context("configuring the thread pool")?;
    }
    Ok(())
}

/// Read a TOML config into a JSON tree. `swarm-core` speaks JSON so that the
/// same structs can be driven from a file, a sweep override, or Python.
fn read_config_value(path: &Path) -> Result<Value> {
    let text = std::fs::read_to_string(path)
        .with_context(|| format!("reading config {}", path.display()))?;
    let value: Value =
        toml::from_str(&text).with_context(|| format!("parsing config {}", path.display()))?;
    Ok(value)
}

fn build_config(value: Value) -> Result<SimConfig> {
    SimConfig::from_json_value(value).map_err(|e| anyhow::anyhow!("{e}"))
}

fn describe(path: &Path) -> Result<()> {
    let cfg = build_config(read_config_value(path)?)?;
    let controller = cfg
        .controller
        .build(cfg.sensor.encoding)
        .map_err(|e| anyhow::anyhow!("{e}"))?;
    let cap = controller.capability();
    let provenance = cfg.controller.provenance();
    let state0 = controller.act(0, 0, 0);
    let r0 = swarm_core::robot::turn_radius(
        state0.wheels[0] * cfg.robot.max_wheel_speed,
        state0.wheels[1] * cfg.robot.max_wheel_speed,
        cfg.robot.axle_length,
    );

    println!("config                {}", path.display());
    println!(
        "capability c=(S,M,A,K) ({}, {}, {}, {})",
        cap.sensor_states,
        cap.memory_bits,
        u8::from(cap.arithmetic),
        cap.comm_bits
    );
    println!(
        "  sensor states       {} ({:.2} bits)",
        cap.sensor_states,
        cap.sensor_bits()
    );
    println!("  table rows          {}", controller.entries().len());
    println!("  free constants      {}", cap.free_constants());
    println!("provenance            {:?}", provenance);
    println!(
        "minimum is            {}",
        if provenance.is_tight() {
            "TIGHT (enumerated)"
        } else {
            "AN UPPER BOUND — 'not found' is not 'not possible'"
        }
    );
    println!(
        "exhaustive grid @20   {:.3e} points (Gauci's 4-constant row: {:.3e})",
        cap.exhaustive_grid_size(20),
        20f64.powi(4)
    );
    match r0 {
        Some(r) => println!(
            "state-0 circle R0     {r:.4} m ({:.1} body radii)",
            r / cfg.robot.radius
        ),
        None => println!("state-0 circle R0     straight-line motion"),
    }
    println!("swarm n               {}", cfg.swarm.n);
    println!(
        "start radius          {:.3} m",
        cfg.swarm.init.start_radius(cfg.swarm.n, cfg.robot.radius)
    );
    println!(
        "trial length tau      {} s at dt = {} s",
        cfg.sim.duration, cfg.sim.dt
    );
    println!(
        "terrain               {}",
        if cfg.terrain.is_flat() {
            "flat (clean arena)"
        } else {
            "ACTIVE"
        }
    );
    if !cfg.terrain.is_flat() {
        println!(
            "  alpha={:.3} rad, g_eff={}, theta_m={}, lambda={} m",
            cfg.terrain.slope_angle,
            cfg.terrain.slope_gain,
            cfg.terrain.friction_amplitude,
            cfg.terrain.correlation_length
        );
        if let Some(r) = r0 {
            println!(
                "  lambda / R0         {:.2}",
                cfg.terrain.correlation_length / r
            );
        }
    }
    println!(
        "occlusion             {}",
        if cfg.occlusion.is_clean() {
            "clean"
        } else {
            "ACTIVE"
        }
    );
    if !cfg.occlusion.is_clean() {
        println!(
            "  fn={}, fp={}, corr_amp={}, lambda={} m",
            cfg.occlusion.fn_rate,
            cfg.occlusion.fp_rate,
            cfg.occlusion.correlation_amplitude,
            cfg.occlusion.correlation_length
        );
    }
    Ok(())
}

fn open_out(out: Option<&Path>) -> Result<Box<dyn Write + Send>> {
    match out {
        Some(p) => {
            if let Some(dir) = p.parent() {
                if !dir.as_os_str().is_empty() {
                    std::fs::create_dir_all(dir)
                        .with_context(|| format!("creating {}", dir.display()))?;
                }
            }
            let f =
                std::fs::File::create(p).with_context(|| format!("creating {}", p.display()))?;
            Ok(Box::new(std::io::BufWriter::new(f)))
        }
        None => Ok(Box::new(std::io::stdout())),
    }
}

fn run_cmd(
    path: &Path,
    runs: u64,
    out: Option<&Path>,
    seed: Option<u64>,
    no_series: bool,
) -> Result<()> {
    let mut value = read_config_value(path)?;
    if let Some(s) = seed {
        sweep::set_path(&mut value, "sim.seed", Value::from(s))?;
    }
    if no_series {
        sweep::set_path(&mut value, "metrics.store_series", Value::from(false))?;
    }
    let cfg = build_config(value)?;

    let records: Vec<swarm_core::RunRecord> = (0..runs)
        .into_par_iter()
        .map(|i| -> Result<swarm_core::RunRecord> {
            Ok(World::new(cfg.clone(), i)
                .map_err(|e| anyhow::anyhow!("{e}"))?
                .run())
        })
        .collect::<Result<Vec<_>>>()?;

    let mut w = open_out(out)?;
    for r in &records {
        writeln!(w, "{}", serde_json::to_string(r)?)?;
    }
    w.flush()?;

    let single = records.iter().filter(|r| r.single_cluster).count();
    eprintln!(
        "{} runs | single cluster {}/{} ({:.0}%) | median dispersion ratio {:.3}",
        records.len(),
        single,
        records.len(),
        100.0 * single as f64 / records.len() as f64,
        median(records.iter().map(|r| r.dispersion_ratio).collect())
    );
    if !records.is_empty() && !records[0].minimum_is_tight {
        eprintln!("note: this row is not enumerated — any minimum read off it is an UPPER BOUND");
    }
    Ok(())
}

fn sweep_cmd(path: &Path, out: &Path, dry_run: bool, series: bool) -> Result<()> {
    let spec = sweep::SweepFile::load(path)?;
    let base_path = path
        .parent()
        .map(|d| d.join(&spec.base))
        .unwrap_or_else(|| spec.base.clone());
    let base = read_config_value(&base_path)?;
    let cells = spec.cells(&base)?;

    // Validate every cell before simulating anything: a sweep that dies on cell
    // 900 of 1000 has wasted an afternoon.
    let mut configs = Vec::with_capacity(cells.len());
    for (i, cell) in cells.iter().enumerate() {
        let mut value = cell.config.clone();
        if !series {
            sweep::set_path(&mut value, "metrics.store_series", Value::from(false))?;
        }
        let cfg = build_config(value)
            .with_context(|| format!("cell {i} ({})", format_coords(&cell.coords)))?;
        configs.push(cfg);
    }

    let total = configs.len() as u64 * spec.runs_per_cell;
    eprintln!(
        "sweep '{}': {} cells x {} runs = {} trials",
        spec.name,
        configs.len(),
        spec.runs_per_cell,
        total
    );
    let untight = configs
        .iter()
        .filter(|c| !c.controller.provenance().is_tight())
        .count();
    if untight > 0 {
        eprintln!(
            "note: {untight}/{} cells use a non-enumerated controller; their minima are UPPER BOUNDS",
            configs.len()
        );
    }
    if dry_run {
        for (cfg, cell) in configs.iter().zip(&cells) {
            println!(
                "{}  n={}  tau={}",
                format_coords(&cell.coords),
                cfg.swarm.n,
                cfg.sim.duration
            );
        }
        return Ok(());
    }

    let jobs: Vec<(usize, u64)> = (0..configs.len())
        .flat_map(|c| (0..spec.runs_per_cell).map(move |r| (c, r)))
        .collect();

    let records: Vec<String> = jobs
        .par_iter()
        .map(|&(c, r)| -> Result<String> {
            let mut rec = World::new(configs[c].clone(), r)
                .map_err(|e| anyhow::anyhow!("{e}"))?
                .run();
            rec.cell = cells[c].coords.clone();
            Ok(serde_json::to_string(&rec)?)
        })
        .collect::<Result<Vec<_>>>()?;

    let mut w = open_out(Some(out))?;
    for line in &records {
        writeln!(w, "{line}")?;
    }
    w.flush()?;
    eprintln!("wrote {} records to {}", records.len(), out.display());
    Ok(())
}

fn format_coords(coords: &serde_json::Map<String, Value>) -> String {
    coords
        .iter()
        .filter(|(k, _)| k.as_str() != "sweep")
        .map(|(k, v)| format!("{k}={v}"))
        .collect::<Vec<_>>()
        .join(" ")
}

fn median(mut v: Vec<f64>) -> f64 {
    if v.is_empty() {
        return f64::NAN;
    }
    v.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    let m = v.len() / 2;
    if v.len() % 2 == 0 {
        0.5 * (v[m - 1] + v[m])
    } else {
        v[m]
    }
}
