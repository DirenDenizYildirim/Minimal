//! Smoothed random scalar field with a tunable correlation length.
//!
//! Used for two hostility dials that both need *spatially correlated* structure
//! rather than per-step i.i.d. noise:
//!   * `terrain` — the per-wheel traction multiplier `m_w(x, y)` (Idea A);
//!   * `occlusion` — spatially correlated false-negative/false-positive rates.
//!
//! Implementation is lattice value noise with quintic interpolation: cheap,
//! stateless (no grid to allocate or bound), and exactly reproducible from a
//! seed. Output is in `[-1, 1]` but is *not* uniformly distributed — it is
//! bell-shaped, concentrated near 0. Anything that needs a calibrated rate
//! must say so explicitly (see `occlusion.rs`).

use crate::geom::Vec2;

#[derive(Clone, Copy, Debug)]
pub struct ScalarField {
    seed: u64,
    /// Lattice spacing in metres; features are roughly this size.
    correlation_length: f64,
}

impl ScalarField {
    pub fn new(seed: u64, correlation_length: f64) -> Self {
        Self {
            seed,
            correlation_length: correlation_length.max(1e-6),
        }
    }

    /// Sample the field at `p`. Range `[-1, 1]`.
    pub fn sample(&self, p: Vec2) -> f64 {
        let u = p.x / self.correlation_length;
        let v = p.y / self.correlation_length;
        let (i0, j0) = (u.floor(), v.floor());
        let (fu, fv) = (u - i0, v - j0);
        let (i0, j0) = (i0 as i64, j0 as i64);

        let su = quintic(fu);
        let sv = quintic(fv);

        let c00 = lattice(self.seed, i0, j0);
        let c10 = lattice(self.seed, i0 + 1, j0);
        let c01 = lattice(self.seed, i0, j0 + 1);
        let c11 = lattice(self.seed, i0 + 1, j0 + 1);

        let a = c00 + su * (c10 - c00);
        let b = c01 + su * (c11 - c01);
        a + sv * (b - a)
    }
}

/// Quintic smoothstep: C2-continuous, so the field has no visible lattice creases.
fn quintic(t: f64) -> f64 {
    t * t * t * (t * (t * 6.0 - 15.0) + 10.0)
}

/// Hash a lattice point to a value in [-1, 1].
fn lattice(seed: u64, i: i64, j: i64) -> f64 {
    let mut z = seed
        ^ (i as u64).wrapping_mul(0x9E37_79B9_7F4A_7C15)
        ^ (j as u64).wrapping_mul(0xC2B2_AE3D_27D4_EB4F);
    z = (z ^ (z >> 33)).wrapping_mul(0xFF51_AFD7_ED55_8CCD);
    z = (z ^ (z >> 33)).wrapping_mul(0xC4CE_B9FE_1A85_EC53);
    z ^= z >> 33;
    // Map to [-1, 1].
    (z as f64 / u64::MAX as f64) * 2.0 - 1.0
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn output_is_bounded() {
        let f = ScalarField::new(42, 0.25);
        for i in 0..2000 {
            let p = Vec2::new(i as f64 * 0.013 - 13.0, i as f64 * -0.021 + 5.0);
            let s = f.sample(p);
            assert!((-1.0..=1.0).contains(&s), "sample out of range: {s}");
        }
    }

    #[test]
    fn field_is_smooth_at_correlation_scale() {
        // Two points a hundredth of a correlation length apart must be close.
        let f = ScalarField::new(7, 0.5);
        for i in 0..500 {
            let p = Vec2::new(i as f64 * 0.037, i as f64 * 0.011);
            let q = p + Vec2::new(0.005, 0.0);
            assert!((f.sample(p) - f.sample(q)).abs() < 0.1);
        }
    }

    #[test]
    fn field_decorrelates_beyond_correlation_length() {
        let f = ScalarField::new(11, 0.2);
        let mut far_diff = 0.0;
        for i in 0..200 {
            let p = Vec2::new(i as f64 * 0.9, 0.3);
            far_diff += (f.sample(p) - f.sample(p + Vec2::new(0.6, 0.6))).abs();
        }
        assert!(
            far_diff / 200.0 > 0.1,
            "field looks constant across lattice cells"
        );
    }

    #[test]
    fn same_seed_same_field() {
        let a = ScalarField::new(3, 0.4);
        let b = ScalarField::new(3, 0.4);
        let p = Vec2::new(1.7, -0.4);
        assert_eq!(a.sample(p), b.sample(p));
        assert_ne!(ScalarField::new(4, 0.4).sample(p), a.sample(p));
    }
}
