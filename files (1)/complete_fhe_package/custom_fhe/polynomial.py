"""
Polynomial Ring Operations
Implements efficient polynomial arithmetic in R_q = Z_q[X]/(X^N + 1)
"""

import numpy as np
from numpy.polynomial import polynomial as P


class PolynomialRing:
    """
    Polynomial operations in the ring Z_q[X]/(X^N + 1)
    where N is a power of 2 (for NTT optimization)
    """
    
    def __init__(self, N, q):
        """
        Args:
            N: Polynomial degree (must be power of 2)
            q: Coefficient modulus
        """
        self.N = N
        self.q = q
        
        # Verify N is power of 2
        if N & (N - 1) != 0:
            raise ValueError("N must be a power of 2")
    
    def add(self, a, b):
        """Add two polynomials (mod q)"""
        result = (a + b) % self.q
        return result
    
    def sub(self, a, b):
        """Subtract two polynomials (mod q)"""
        result = (a - b) % self.q
        return result
    
    def mul_scalar(self, a, scalar):
        """Multiply polynomial by scalar (mod q)"""
        result = (a * scalar) % self.q
        return result
    
    def mul(self, a, b):
        """
        Multiply two polynomials in R_q
        Uses convolution followed by modular reduction by (X^N + 1)
        """
        # Use int64 to prevent overflow during intermediate calculations
        a_big = a.astype(np.int64)
        b_big = b.astype(np.int64)
        
        # Standard polynomial multiplication
        conv = np.convolve(a_big, b_big)
        
        # Reduce modulo (X^N + 1)
        # For (X^N + 1), X^N = -1, so X^(N+k) = -X^k
        result = np.zeros(self.N, dtype=np.int64)
        
        for i in range(len(conv)):
            if i < self.N:
                result[i] += conv[i]
            else:
                # X^N = -1, so X^i = -X^(i-N) for i >= N
                result[i - self.N] -= conv[i]
        
        # Apply modular reduction
        result = result % self.q
        
        return result
    
    def neg(self, a):
        """Negate polynomial (mod q)"""
        return (-a) % self.q
    
    def mod_center(self, a):
        """
        Center coefficients around 0 instead of [0, q)
        Maps [0, q) to [-(q-1)/2, (q-1)/2]
        """
        result = a.copy()
        half_q = self.q // 2
        mask = result > half_q
        result[mask] -= self.q
        return result
    
    def random_uniform(self, size=None):
        """Generate random polynomial with uniform coefficients in [0, q)"""
        if size is None:
            size = self.N
        return np.random.randint(0, self.q, size=size, dtype=np.int64)
    
    def random_ternary(self):
        """Generate random ternary polynomial {-1, 0, 1}"""
        return np.random.choice([-1, 0, 1], size=self.N)
    
    def random_bounded(self, bound):
        """Generate random polynomial with coefficients in [-bound, bound]"""
        return np.random.randint(-bound, bound + 1, size=self.N, dtype=np.int64)


class DiscreteGaussian:
    """
    Discrete Gaussian sampler for generating noise polynomials
    Uses Box-Muller transform approximation
    """
    
    def __init__(self, sigma, N):
        """
        Args:
            sigma: Standard deviation
            N: Polynomial degree
        """
        self.sigma = sigma
        self.N = N
    
    def sample(self):
        """Sample a polynomial with discrete Gaussian noise"""
        # Use normal distribution and round
        samples = np.random.normal(0, self.sigma, self.N)
        return np.round(samples).astype(np.int64)
    
    def sample_bounded(self, bound):
        """Sample and clip to [-bound, bound]"""
        samples = self.sample()
        return np.clip(samples, -bound, bound)
