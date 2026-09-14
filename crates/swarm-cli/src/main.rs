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

mod search;
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
    /// Search a lookup table's wheel constants with sep-CMA-ES.
    ///
    /// Produces an UPPER BOUND on what the capability can do, and writes the
    /// budget that produced it alongside the constants so the bound is quotable.
    Search {
        /// Base config giving the training condition (terrain dials, n, tau).
        #[arg(short, long)]
        config: PathBuf,
        /// Candidate evaluations. Rounded down to a whole number of generations.
        #[arg(long, default_value_t = 600)]
        budget: usize,
        /// Trials per candidate; the objective is their median final dispersion.
        #[arg(long, default_value_t = 12)]
        runs_per_eval: usize,
        /// What to optimise: `dispersion` (the default, and the objective every
        /// row in the record was searched against), `survival`, or
        /// `survival_task`.
        ///
        /// The two survival objectives are for a pursuer class and need a
        /// `[pursuer]` block in the base config; both are HIGHER-is-better and
        /// the output JSON says so. `survival` alone can be maximised by
        /// abandoning aggregation entirely — that is a real strategy, not a bug,
        /// and `survival_task` is the version that cannot.
        #[arg(long, default_value = "dispersion")]
        objective: String,
        /// Seed for the optimiser itself.
        #[arg(long, default_value_t = 1)]
        seed: u64,
        /// Seed base for the TRAINING trials. Keep this disjoint from the seeds
        /// the row is later evaluated on, or the result is the maximum of a
        /// noisy sample rather than a controller.
        #[arg(long, default_value_t = 900_000)]
        training_seed: u64,
        /// Warm start: JSON array of constants for the initial mean, tiled if
        /// shorter than the search space. Passing an S = 2 controller to an
        /// S = 4 search starts it at a table that ignores its extra bit, so the
        /// only question left is whether using the bit improves on not using it.
        #[arg(long)]
        init: Option<String>,
        /// Train against an environment CLASS rather than one arena. Repeatable,
        /// `--class path=v1,v2,...`; the axes are crossed, and the objective
        /// becomes the geometric mean of the per-condition medians. Use it when
        /// the claim is "this controller works across these conditions" rather
        /// than "this controller is best here" — §14 shows the two differ.
        /// `runs_per_eval` must divide by the number of conditions.
        #[arg(long = "class", value_name = "PATH=V1,V2,...")]
        class: Vec<String>,
        /// Give the class as explicit CONDITIONS instead of crossed axes.
        /// Repeatable, `--class-point path=v,path=v,...`; each flag is one
        /// training condition. Use it when the conditions are not a product —
        /// a τ of 3600 s at the largest start radius and 600 s at the others is
        /// not expressible as crossed axes. Mutually exclusive with `--class`.
        #[arg(long = "class-point", value_name = "PATH=V,PATH=V,...")]
        class_point: Vec<String>,
        #[arg(short, long)]
        out: PathBuf,
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
        Command::Search {
            config,
            budget,
            runs_per_eval,
            objective,
            seed,
            training_seed,
            init,
            class,
            class_point,
            out,
            threads,
        } => {
            set_threads(threads)?;
            search_cmd(
                &config,
                budget,
                runs_per_eval,
                &objective,
                seed,
                training_seed,
                init,
                &class,
                &class_point,
                &out,
            )
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

#[allow(clippy::too_many_arguments)]
/// Parse repeated `--class path=v1,v2,...` into crossed axes.
///
/// Values are parsed as JSON so a config path taking an integer (`swarm.n`) gets
/// an integer and one taking a float (`swarm.init.radius`) gets a float —
/// passing 20 as 20.0 would fail the config's own typing.
/// Parse repeated `--class-point path=v,path=v,...` into explicit conditions.
fn parse_class_points(specs: &[String]) -> Result<Vec<search::Condition>> {
    specs
        .iter()
        .map(|spec| {
            let condition: Result<search::Condition> = spec
                .split(',')
                .map(|pair| {
                    let (path, raw) = pair.split_once('=').with_context(|| {
                        format!("--class-point expects PATH=V,PATH=V,...; got {pair:?}")
                    })?;
                    let value: Value = serde_json::from_str(raw.trim())
                        .with_context(|| format!("parsing {raw:?} in --class-point {path}"))?;
                    Ok((path.trim().to_string(), value))
                })
                .collect();
            let condition = condition?;
            if condition.is_empty() {
                anyhow::bail!("--class-point {spec:?} sets nothing");
            }
            Ok(condition)
        })
        .collect()
}

fn parse_class(specs: &[String]) -> Result<Vec<(String, Vec<Value>)>> {
    specs
        .iter()
        .map(|spec| {
            let (path, list) = spec
                .split_once('=')
                .with_context(|| format!("--class expects PATH=V1,V2,...; got {spec:?}"))?;
            let values: Result<Vec<Value>> = list
                .split(',')
                .map(|t| {
                    serde_json::from_str(t.trim())
                        .with_context(|| format!("parsing {t:?} in --class {path}"))
                })
                .collect();
            let values = values?;
            if values.is_empty() {
                anyhow::bail!("--class {path} lists no values");
            }
            Ok((path.to_string(), values))
        })
        .collect()
}

#[allow(clippy::too_many_arguments)]
fn search_cmd(
    path: &Path,
    budget: usize,
    runs_per_eval: usize,
    objective: &str,
    seed: u64,
    training_seed: u64,
    init: Option<String>,
    class: &[String],
    class_point: &[String],
    out: &Path,
) -> Result<()> {
    let value = read_config_value(path)?;
    // Validate the base before spending the budget, and read the encoding from
    // it: the table's row count must match the sensor's state count.
    let cfg = build_config(value.clone())?;
    let states = cfg.sensor.encoding.states();
    let encoding = format!("{:?}", cfg.sensor.encoding);

    eprintln!(
        "searching {} constants for encoding {encoding} (S = {states})",
        2 * states
    );
    let objective = search::Objective::parse(objective)?;
    eprintln!(
        "budget {budget} evaluations x {runs_per_eval} runs; training seed base {training_seed}"
    );
    eprintln!(
        "objective {objective:?} ({} is better)",
        if objective.higher_is_better() {
            "higher"
        } else {
            "lower"
        }
    );
    let init: Option<Vec<f64>> = match init {
        Some(text) => {
            let v: Vec<f64> = serde_json::from_str(&text)
                .with_context(|| format!("parsing --init as a JSON array: {text}"))?;
            eprintln!("warm start from {v:?} (tiled to {} constants)", 2 * states);
            Some(v)
        }
        None => None,
    };
    let class_axes = parse_class(class)?;
    let class_points = parse_class_points(class_point)?;
    if !class_axes.is_empty() {
        let n = search::class_conditions(&class_axes).len();
        eprintln!(
            "training class: {n} conditions from {}",
            class_axes
                .iter()
                .map(|(p, v)| format!("{p}={v:?}"))
                .collect::<Vec<_>>()
                .join(", ")
        );
    }
    for (i, c) in class_points.iter().enumerate() {
        eprintln!(
            "training condition {}/{}: {}",
            i + 1,
            class_points.len(),
            c.iter()
                .map(|(p, v)| format!("{p}={v}"))
                .collect::<Vec<_>>()
                .join(" ")
        );
    }
    let result = search::run_search(
        &value,
        &encoding,
        states,
        budget,
        runs_per_eval,
        seed,
        training_seed,
        init,
        &class_axes,
        &class_points,
        objective,
    )?;
    search::write_result(out, &result)?;
    eprintln!(
        "best training objective {:.4} after {} evaluations ({} simulation runs)",
        result.best_training_objective, result.budget_evaluations, result.simulation_runs
    );
    eprintln!("constants: {:?}", result.best_constants);
    eprintln!(
        "note: this row is an UPPER BOUND — sep-CMA-ES is not exhaustive, and a \
         weaker searcher only loosens the bound"
    );
    println!("{}", serde_json::to_string(&result.best_constants)?);
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
