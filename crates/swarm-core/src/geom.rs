//! Minimal 2-D vector algebra and angle helpers.

use serde::{Deserialize, Serialize};
use std::ops::{Add, AddAssign, Div, Mul, Neg, Sub};

#[derive(Clone, Copy, Debug, Default, PartialEq, Serialize, Deserialize)]
pub struct Vec2 {
    pub x: f64,
    pub y: f64,
}

impl Vec2 {
    pub const ZERO: Vec2 = Vec2 { x: 0.0, y: 0.0 };

    pub fn new(x: f64, y: f64) -> Self {
        Self { x, y }
    }

    /// Unit vector at `theta` radians measured counter-clockwise from +x.
    pub fn from_angle(theta: f64) -> Self {
        Self {
            x: theta.cos(),
            y: theta.sin(),
        }
    }

    pub fn dot(self, o: Vec2) -> f64 {
        self.x * o.x + self.y * o.y
    }

    pub fn norm_sq(self) -> f64 {
        self.dot(self)
    }

    pub fn norm(self) -> f64 {
        self.norm_sq().sqrt()
    }

    pub fn angle(self) -> f64 {
        self.y.atan2(self.x)
    }

    /// Left-hand normal (90 degrees counter-clockwise).
    pub fn perp(self) -> Self {
        Self {
            x: -self.y,
            y: self.x,
        }
    }

    pub fn normalized(self) -> Self {
        let n = self.norm();
        if n <= f64::EPSILON {
            Vec2::ZERO
        } else {
            self / n
        }
    }
}

impl Add for Vec2 {
    type Output = Vec2;
    fn add(self, o: Vec2) -> Vec2 {
        Vec2::new(self.x + o.x, self.y + o.y)
    }
}

impl AddAssign for Vec2 {
    fn add_assign(&mut self, o: Vec2) {
        self.x += o.x;
        self.y += o.y;
    }
}

impl Sub for Vec2 {
    type Output = Vec2;
    fn sub(self, o: Vec2) -> Vec2 {
        Vec2::new(self.x - o.x, self.y - o.y)
    }
}

impl Mul<f64> for Vec2 {
    type Output = Vec2;
    fn mul(self, s: f64) -> Vec2 {
        Vec2::new(self.x * s, self.y * s)
    }
}

impl Div<f64> for Vec2 {
    type Output = Vec2;
    fn div(self, s: f64) -> Vec2 {
        Vec2::new(self.x / s, self.y / s)
    }
}

impl Neg for Vec2 {
    type Output = Vec2;
    fn neg(self) -> Vec2 {
        Vec2::new(-self.x, -self.y)
    }
}

/// Wrap an angle to (-pi, pi].
pub fn wrap_angle(a: f64) -> f64 {
    let tau = std::f64::consts::TAU;
    let mut a = a % tau;
    if a > std::f64::consts::PI {
        a -= tau;
    } else if a <= -std::f64::consts::PI {
        a += tau;
    }
    a
}

/// Signed smallest rotation taking `from` to `to`.
pub fn angle_diff(to: f64, from: f64) -> f64 {
    wrap_angle(to - from)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn wrap_is_in_range() {
        for k in -10..10 {
            let a = wrap_angle(0.3 + k as f64 * std::f64::consts::TAU);
            assert!((a - 0.3).abs() < 1e-9, "got {a}");
        }
    }

    #[test]
    fn perp_is_orthogonal() {
        let v = Vec2::new(0.3, -1.2);
        assert!(v.dot(v.perp()).abs() < 1e-12);
    }
}
