//! Deterministic, reproducible seeding.
//!
//! Every run derives its stream from `(base_seed, run_index)` through SplitMix64,
//! so a cell of a sweep can be re-run in isolation and reproduce bit-for-bit.

use rand::SeedableRng;

pub type Rng = rand_pcg::Pcg64;

/// SplitMix64: mixes a counter into a well-distributed 64-bit seed.
pub fn split_seed(base: u64, index: u64) -> u64 {
    let mut z = base.wrapping_add(index.wrapping_mul(0x9E37_79B9_7F4A_7C15));
    z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    z ^ (z >> 31)
}

pub fn rng_from(seed: u64) -> Rng {
    Rng::seed_from_u64(seed)
}

#[cfg(test)]
mod tests {
    use super::*;
    use rand::Rng as _;

    #[test]
    fn same_seed_same_stream() {
        let a: Vec<f64> = (0..8).map(|_| rng_from(7).gen()).collect();
        let b: Vec<f64> = (0..8).map(|_| rng_from(7).gen()).collect();
        assert_eq!(a, b);
    }

    #[test]
    fn distinct_indices_diverge() {
        assert_ne!(split_seed(1, 0), split_seed(1, 1));
        assert_ne!(split_seed(1, 0), split_seed(2, 0));
    }
}
