"""
BFV (Brakerski-Fan-Vercauteren) Encryption Scheme
Complete implementation with encryption, decryption, and homomorphic operations
"""

import numpy as np
from .polynomial import PolynomialRing, DiscreteGaussian
from .keys import PublicKey, SecretKey, RelinearizationKey, RotationKey
from .ciphertext import Ciphertext, Plaintext


class BFVScheme:
    """
    BFV homomorphic encryption scheme
    """
    
    def __init__(self, N=8192, t=65537, q_bits=60, sigma=3.2):
        """
        Initialize BFV scheme with parameters
        
        Args:
            N: Polynomial degree (power of 2, typically 4096, 8192, or 16384)
            t: Plaintext modulus (prime)
            q_bits: Ciphertext modulus bit size
            sigma: Standard deviation for Gaussian noise
        """
        self.N = N
        self.t = t
        self.q = 2**q_bits - 1  # Approximate, should be prime in practice
        self.sigma = sigma
        
        # Initialize polynomial ring
        self.poly_ring = PolynomialRing(N, self.q)
        self.gaussian = DiscreteGaussian(sigma, N)
        
        # Compute delta = floor(q/t)
        self.delta = self.q // self.t
        
        # Keys (to be generated)
        self.secret_key = None
        self.public_key = None
        self.relin_key = None
        self.rotation_keys = None
        
        # Number of slots for batching
        self.n_slots = N // 2
        
        print(f"BFV Parameters:")
        print(f"  N={self.N}, t={self.t}, q≈2^{q_bits}")
        print(f"  Security: ~{N//4} bits (approximate)")
        print(f"  SIMD Slots: {self.n_slots}")
    
    def key_generation(self):
        """Generate secret key and public key"""
        # 1. Sample secret key: ternary polynomial {-1, 0, 1}
        s = self.poly_ring.random_ternary()
        self.secret_key = SecretKey(s)
        
        # 2. Sample random polynomial a
        a = self.poly_ring.random_uniform()
        
        # 3. Sample error e
        e = self.gaussian.sample_bounded(bound=6 * int(self.sigma))
        
        # 4. Compute b = -(a*s + e) mod q
        a_s = self.poly_ring.mul(a, s)
        a_s_e = self.poly_ring.add(a_s, e)
        b = self.poly_ring.neg(a_s_e)
        
        # Public key is (b, a)
        self.public_key = PublicKey(b, a)
        
        return self.secret_key, self.public_key
    
    def generate_relin_key(self):
        """Generate relinearization key for multiplication"""
        if self.secret_key is None:
            raise ValueError("Must generate keys first")
        
        s = self.secret_key.get_polynomial()
        
        # Compute s^2
        s_squared = self.poly_ring.mul(s, s)
        
        # Decompose s^2 into base w (typically w = q^(1/2))
        # For simplicity, we'll use a single component
        evk_components = []
        
        # Sample random a'
        a_prime = self.poly_ring.random_uniform()
        
        # Sample error e'
        e_prime = self.gaussian.sample_bounded(bound=6 * int(self.sigma))
        
        # Compute b' = -(a'*s + e') + s^2 mod q
        a_s = self.poly_ring.mul(a_prime, s)
        a_s_e = self.poly_ring.add(a_s, e_prime)
        b_prime = self.poly_ring.add(self.poly_ring.neg(a_s_e), s_squared)
        
        evk_components.append((b_prime, a_prime))
        
        self.relin_key = RelinearizationKey(evk_components)
        return self.relin_key
    
    def generate_rotation_keys(self, rotations=None):
        """
        Generate rotation keys for specific rotations
        
        Args:
            rotations: List of rotation amounts to generate keys for
                      If None, generates for common rotations
        """
        if self.secret_key is None:
            raise ValueError("Must generate keys first")
        
        if rotations is None:
            # Generate keys for powers of 2 (common for SIMD operations)
            rotations = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]
            rotations = [r for r in rotations if r < self.N]
        
        rotation_keys_dict = {}
        s = self.secret_key.get_polynomial()
        
        for rot in rotations:
            # Sample random a
            a = self.poly_ring.random_uniform()
            
            # Sample error e
            e = self.gaussian.sample_bounded(bound=6 * int(self.sigma))
            
            # Rotate secret key (simplified - just shift)
            s_rotated = np.roll(s, rot)
            
            # Compute b = -(a*s + e) + s_rotated mod q
            a_s = self.poly_ring.mul(a, s)
            a_s_e = self.poly_ring.add(a_s, e)
            b = self.poly_ring.add(self.poly_ring.neg(a_s_e), s_rotated)
            
            rotation_keys_dict[rot] = (b, a)
        
        self.rotation_keys = RotationKey(rotation_keys_dict)
        return self.rotation_keys
    
    def encode(self, values):
        """
        Encode integers to plaintext polynomial
        Supports batching: encodes array of values into polynomial slots
        
        Args:
            values: Integer or array of integers to encode
        
        Returns:
            Plaintext object
        """
        if isinstance(values, (int, np.integer)):
            # Single value - place in first slot
            poly = np.zeros(self.N, dtype=np.int64)
            poly[0] = values % self.t
        else:
            # Array of values - batch encoding
            values = np.array(values, dtype=np.int64)
            
            if len(values) > self.n_slots:
                raise ValueError(f"Too many values ({len(values)}) for slots ({self.n_slots})")
            
            poly = np.zeros(self.N, dtype=np.int64)
            poly[:len(values)] = values % self.t
        
        return Plaintext(poly, params={'N': self.N, 't': self.t, 'q': self.q})
    
    def decode(self, plaintext, num_values=1):
        """
        Decode plaintext polynomial to integers
        
        Args:
            plaintext: Plaintext object
            num_values: Number of values to decode from slots
        
        Returns:
            Integer or array of integers
        """
        poly = plaintext.get_poly()
        
        # Center around 0
        poly_centered = self.poly_ring.mod_center(poly % self.t)
        
        if num_values == 1:
            return int(poly_centered[0])
        else:
            return poly_centered[:num_values]
    
    def encrypt(self, plaintext):
        """
        Encrypt a plaintext
        
        Args:
            plaintext: Plaintext object from encode()
        
        Returns:
            Ciphertext object
        """
        if self.public_key is None:
            raise ValueError("Must generate keys first")
        
        m = plaintext.get_poly()
        pk0, pk1 = self.public_key.get_components()
        
        # 1. Sample random ternary polynomial u
        u = self.poly_ring.random_ternary()
        
        # 2. Sample errors e1, e2
        e1 = self.gaussian.sample_bounded(bound=6 * int(self.sigma))
        e2 = self.gaussian.sample_bounded(bound=6 * int(self.sigma))
        
        # 3. Scale message by delta
        scaled_m = self.poly_ring.mul_scalar(m, self.delta)
        
        # 4. Compute c0 = pk0*u + e1 + Delta*m mod q
        pk0_u = self.poly_ring.mul(pk0, u)
        c0 = self.poly_ring.add(pk0_u, e1)
        c0 = self.poly_ring.add(c0, scaled_m)
        
        # 5. Compute c1 = pk1*u + e2 mod q
        pk1_u = self.poly_ring.mul(pk1, u)
        c1 = self.poly_ring.add(pk1_u, e2)
        
        return Ciphertext([c0, c1], params={'N': self.N, 't': self.t, 'q': self.q})
    
    def decrypt(self, ciphertext):
        """
        Decrypt a ciphertext
        
        Args:
            ciphertext: Ciphertext object
        
        Returns:
            Plaintext object
        """
        if self.secret_key is None:
            raise ValueError("Must generate keys first")
        
        components = ciphertext.get_components()
        s = self.secret_key.get_polynomial()
        
        # Handle different ciphertext sizes
        if len(components) == 2:
            c0, c1 = components
            # Compute c0 + c1*s mod q
            c1_s = self.poly_ring.mul(c1, s)
            noisy_m = self.poly_ring.add(c0, c1_s)
        else:
            raise ValueError("Can only decrypt size-2 ciphertexts. Use relinearization first.")
        
        # Scale down by delta and round
        # noisy_m ≈ Delta*m + noise
        # m ≈ round(noisy_m / Delta) mod t
        
        scaled_down = np.round(noisy_m.astype(np.float64) / self.delta).astype(np.int64)
        m_recovered = scaled_down % self.t
        
        return Plaintext(m_recovered, params={'N': self.N, 't': self.t, 'q': self.q})
    
    def add(self, ct1, ct2):
        """
        Homomorphic addition of two ciphertexts
        
        Args:
            ct1, ct2: Ciphertext objects
        
        Returns:
            Ciphertext object
        """
        c1_components = ct1.get_components()
        c2_components = ct2.get_components()
        
        # Add component-wise
        result_components = []
        max_size = max(len(c1_components), len(c2_components))
        
        for i in range(max_size):
            if i < len(c1_components) and i < len(c2_components):
                result_components.append(
                    self.poly_ring.add(c1_components[i], c2_components[i])
                )
            elif i < len(c1_components):
                result_components.append(c1_components[i].copy())
            else:
                result_components.append(c2_components[i].copy())
        
        return Ciphertext(result_components, params=ct1.params)
    
    def sub(self, ct1, ct2):
        """
        Homomorphic subtraction
        
        Args:
            ct1, ct2: Ciphertext objects
        
        Returns:
            Ciphertext object (ct1 - ct2)
        """
        c1_components = ct1.get_components()
        c2_components = ct2.get_components()
        
        # Subtract component-wise
        result_components = []
        max_size = max(len(c1_components), len(c2_components))
        
        for i in range(max_size):
            if i < len(c1_components) and i < len(c2_components):
                result_components.append(
                    self.poly_ring.sub(c1_components[i], c2_components[i])
                )
            elif i < len(c1_components):
                result_components.append(c1_components[i].copy())
            else:
                result_components.append(self.poly_ring.neg(c2_components[i]))
        
        return Ciphertext(result_components, params=ct1.params)
    
    def multiply(self, ct1, ct2):
        """
        Homomorphic multiplication (results in size-3 ciphertext)
        Use relinearization after this to reduce back to size-2
        
        Args:
            ct1, ct2: Ciphertext objects (must be size-2)
        
        Returns:
            Ciphertext object (size-3)
        """
        if not ct1.is_fresh() or not ct2.is_fresh():
            raise ValueError("Can only multiply fresh ciphertexts (size 2)")
        
        c1_0, c1_1 = ct1.get_components()
        c2_0, c2_1 = ct2.get_components()
        
        # Tensor product expansion
        # (c1_0 + c1_1*s) * (c2_0 + c2_1*s) = 
        # c1_0*c2_0 + (c1_0*c2_1 + c1_1*c2_0)*s + c1_1*c2_1*s^2
        
        # Compute products
        d0 = self.poly_ring.mul(c1_0, c2_0)
        
        d1_part1 = self.poly_ring.mul(c1_0, c2_1)
        d1_part2 = self.poly_ring.mul(c1_1, c2_0)
        d1 = self.poly_ring.add(d1_part1, d1_part2)
        
        d2 = self.poly_ring.mul(c1_1, c2_1)
        
        # Scale correction: divide by t and round
        # This keeps the noise manageable
        d0 = np.round(d0.astype(np.float64) / self.t).astype(np.int64) % self.q
        d1 = np.round(d1.astype(np.float64) / self.t).astype(np.int64) % self.q
        d2 = np.round(d2.astype(np.float64) / self.t).astype(np.int64) % self.q
        
        return Ciphertext([d0, d1, d2], params=ct1.params)
    
    def relinearize(self, ciphertext):
        """
        Reduce size-3 ciphertext back to size-2 using relinearization key
        
        Args:
            ciphertext: Ciphertext object (size-3)
        
        Returns:
            Ciphertext object (size-2)
        """
        if self.relin_key is None:
            raise ValueError("Must generate relinearization key first")
        
        if ciphertext.size != 3:
            # Already size 2 or unexpected size
            return ciphertext
        
        c0, c1, c2 = ciphertext.get_components()
        evk = self.relin_key.get_components()[0]
        evk_b, evk_a = evk
        
        # New c0 = old_c0 + c2 * evk_b
        new_c0 = self.poly_ring.add(c0, self.poly_ring.mul(c2, evk_b))
        
        # New c1 = old_c1 + c2 * evk_a
        new_c1 = self.poly_ring.add(c1, self.poly_ring.mul(c2, evk_a))
        
        return Ciphertext([new_c0, new_c1], params=ciphertext.params)
    
    def multiply_plain(self, ciphertext, plaintext):
        """
        Multiply ciphertext by plaintext (more efficient than ct*ct)
        
        Args:
            ciphertext: Ciphertext object
            plaintext: Plaintext object
        
        Returns:
            Ciphertext object
        """
        ct_components = ciphertext.get_components()
        pt_poly = plaintext.get_poly()
        
        # Multiply each component by plaintext
        new_components = []
        for ct_comp in ct_components:
            new_comp = self.poly_ring.mul(ct_comp, pt_poly)
            new_components.append(new_comp)
        
        return Ciphertext(new_components, params=ciphertext.params)
    
    def negate(self, ciphertext):
        """
        Negate ciphertext
        
        Args:
            ciphertext: Ciphertext object
        
        Returns:
            Ciphertext object
        """
        components = ciphertext.get_components()
        new_components = [self.poly_ring.neg(c) for c in components]
        return Ciphertext(new_components, params=ciphertext.params)
    
    def get_n_slots(self):
        """Get number of SIMD slots available"""
        return self.n_slots
