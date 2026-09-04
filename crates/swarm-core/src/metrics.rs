//! Aggregation metrics, all computed in the swarm-centroid frame.
//!
//! Working in the centroid frame is not cosmetic: on a slope the whole swarm
//! translates downhill, and a lab-frame metric would score that translation as
//! a loss of aggregation (build doc, Idea A: "metrics relative to swarm
//! centroid so downhill translation is factored out").

use crate::geom::Vec2;

pub fn centroid(points: &[Vec2]) -> Vec2 {
    if points.is_empty() {
        return Vec2::ZERO;
    }
    let sum = points.iter().fold(Vec2::ZERO, |a, &p| a + p);
    sum / points.len() as f64
}

/// Second moment about the centroid, `sum |p_i - pbar|^2`.
pub fn second_moment(points: &[Vec2]) -> f64 {
    let c = centroid(points);
    points.iter().map(|&p| (p - c).norm_sq()).sum()
}

/// Dispersion: the second moment normalised so that a perfectly packed cluster
/// of `n` bodies of radius `R` scores ~1 and larger means more spread out.
///
/// Derivation of the normaliser: `n` disks of radius `R` packed into one disk
/// occupy area `n*pi*R^2`, hence outer radius `R*sqrt(n)`; a uniform disk of
/// radius `rho` has second moment `n*rho^2/2` for `n` unit masses, giving
/// `n^2 R^2 / 2`. So `u = 2 * sum|p_i - pbar|^2 / (n^2 R^2)`.
///
/// This is the Graham & Sloane normalised-second-moment convention that Gauci
/// et al. report. **Verify the exact constant against the paper before quoting
/// absolute numbers** — see `docs/validation.md`; the scaling in `n` and the
/// ordering between runs are unaffected by the constant.
pub fn dispersion(points: &[Vec2], robot_radius: f64) -> f64 {
    let n = points.len();
    if n == 0 || robot_radius <= 0.0 {
        return 0.0;
    }
    2.0 * second_moment(points) / ((n * n) as f64 * robot_radius * robot_radius)
}

/// Connected components of the graph linking bodies closer than `link_distance`
/// (centre to centre). Returns one label per point.
pub fn cluster_labels(points: &[Vec2], link_distance: f64) -> Vec<usize> {
    let n = points.len();
    let mut parent: Vec<usize> = (0..n).collect();

    fn find(parent: &mut [usize], mut x: usize) -> usize {
        while parent[x] != x {
            parent[x] = parent[parent[x]];
            x = parent[x];
        }
        x
    }

    let d2 = link_distance * link_distance;
    for i in 0..n {
        for j in (i + 1)..n {
            if (points[i] - points[j]).norm_sq() <= d2 {
                let (a, b) = (find(&mut parent, i), find(&mut parent, j));
                if a != b {
                    parent[a] = b;
                }
            }
        }
    }
    (0..n).map(|i| find(&mut parent, i)).collect()
}

pub fn cluster_count(points: &[Vec2], link_distance: f64) -> usize {
    let labels = cluster_labels(points, link_distance);
    let mut seen = labels.clone();
    seen.sort_unstable();
    seen.dedup();
    seen.len()
}

/// Fraction of the swarm in the single largest cluster. 1.0 = fully aggregated.
pub fn largest_cluster_fraction(points: &[Vec2], link_distance: f64) -> f64 {
    if points.is_empty() {
        return 0.0;
    }
    let labels = cluster_labels(points, link_distance);
    let mut counts = std::collections::HashMap::new();
    for l in labels {
        *counts.entry(l).or_insert(0usize) += 1;
    }
    counts.values().copied().max().unwrap_or(0) as f64 / points.len() as f64
}

#[cfg(test)]
mod tests {
    use super::*;

    fn hex_packing(rings: i32, r: f64) -> Vec<Vec2> {
        // Triangular lattice with spacing 2R: touching disks.
        let mut pts = vec![];
        let s = 2.0 * r;
        for q in -rings..=rings {
            for w in -rings..=rings {
                let x = s * (q as f64 + 0.5 * w as f64);
                let y = s * (3f64.sqrt() / 2.0) * w as f64;
                let p = Vec2::new(x, y);
                if p.norm() <= s * rings as f64 + 1e-9 {
                    pts.push(p);
                }
            }
        }
        pts
    }

    #[test]
    fn dispersion_of_a_packed_cluster_is_order_one() {
        let r = 0.037;
        let pts = hex_packing(6, r);
        let u = dispersion(&pts, r);
        assert!((0.5..2.0).contains(&u), "packed dispersion {u} is not O(1)");
    }

    #[test]
    fn dispersion_is_translation_and_rotation_invariant() {
        let r = 0.037;
        let pts = hex_packing(4, r);
        let base = dispersion(&pts, r);
        let shifted: Vec<Vec2> = pts.iter().map(|&p| p + Vec2::new(17.0, -4.0)).collect();
        assert!((dispersion(&shifted, r) - base).abs() < 1e-9);
        let (c, s) = (0.7f64.cos(), 0.7f64.sin());
        let rotated: Vec<Vec2> = pts
            .iter()
            .map(|&p| Vec2::new(c * p.x - s * p.y, s * p.x + c * p.y))
            .collect();
        assert!((dispersion(&rotated, r) - base).abs() < 1e-9);
    }

    #[test]
    fn dispersion_grows_when_the_swarm_spreads() {
        let r = 0.037;
        let pts = hex_packing(4, r);
        let spread: Vec<Vec2> = pts.iter().map(|&p| p * 3.0).collect();
        assert!(dispersion(&spread, r) > dispersion(&pts, r) * 8.0);
    }

    #[test]
    fn clusters_are_found_and_counted() {
        let a = [
            Vec2::new(0.0, 0.0),
            Vec2::new(0.05, 0.0),
            Vec2::new(0.1, 0.0),
        ];
        let b = [Vec2::new(5.0, 0.0), Vec2::new(5.05, 0.0)];
        let all: Vec<Vec2> = a.iter().chain(b.iter()).copied().collect();
        assert_eq!(cluster_count(&all, 0.11), 2);
        assert!((largest_cluster_fraction(&all, 0.11) - 3.0 / 5.0).abs() < 1e-12);
        assert_eq!(cluster_count(&all, 10.0), 1);
        assert_eq!(largest_cluster_fraction(&all, 10.0), 1.0);
        assert_eq!(cluster_count(&all, 0.01), 5);
    }

    #[test]
    fn chained_bodies_form_one_cluster() {
        // Transitivity: a chain of links is a single component even though the
        // endpoints are far apart.
        let pts: Vec<Vec2> = (0..10).map(|i| Vec2::new(i as f64 * 0.05, 0.0)).collect();
        assert_eq!(cluster_count(&pts, 0.06), 1);
    }

    #[test]
    fn empty_and_degenerate_inputs_do_not_panic() {
        assert_eq!(dispersion(&[], 0.037), 0.0);
        assert_eq!(largest_cluster_fraction(&[], 0.1), 0.0);
        assert_eq!(centroid(&[]), Vec2::ZERO);
        assert_eq!(dispersion(&[Vec2::ZERO], 0.037), 0.0);
    }
}
