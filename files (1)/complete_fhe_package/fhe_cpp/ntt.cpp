/*
 * NTT Implementation - Fast Polynomial Multiplication
 * O(N log N) complexity using Number Theoretic Transform
 */

#include "ntt.h"
#include <algorithm>
#include <cmath>
#include <iostream>

namespace fhe_cpp {

// Helper: Extended Euclidean Algorithm for modular inverse
ModInt extended_gcd(ModInt a, ModInt b, ModInt& x, ModInt& y) {
    if (b == 0) {
        x = 1;
        y = 0;
        return a;
    }
    ModInt x1, y1;
    ModInt gcd = extended_gcd(b, a % b, x1, y1);
    x = y1;
    y = x1 - (a / b) * y1;
    return gcd;
}

NTT::NTT(int N, ModInt q) : N(N), q(q) {
    // Verify N is a power of 2
    if ((N & (N - 1)) != 0) {
        throw std::invalid_argument("N must be a power of 2");
    }
    
    // Find 2N-th primitive root of unity
    // For NTT to work: q = 1 (mod 2N)
    if ((q - 1) % (2 * N) != 0) {
        throw std::invalid_argument("q must be 1 (mod 2N) for NTT to work");
    }
    
    // Find primitive root (simplified approach)
    // In practice, this should be precomputed or use known values
    psi = find_primitive_root();
    
    if (psi == 0) {
        throw std::runtime_error("Could not find primitive root of unity");
    }
    
    psi_inv = mod_inv(psi);
    N_inv = mod_inv(N);
    
    // Precompute powers of psi and psi_inv
    psi_powers.resize(N);
    psi_inv_powers.resize(N);
    
    psi_powers[0] = 1;
    psi_inv_powers[0] = 1;
    
    for (int i = 1; i < N; i++) {
        psi_powers[i] = mod_mul(psi_powers[i-1], psi);
        psi_inv_powers[i] = mod_mul(psi_inv_powers[i-1], psi_inv);
    }
}

ModInt NTT::mod_add(ModInt a, ModInt b) const {
    ModInt result = (a + b) % q;
    if (result < 0) result += q;
    return result;
}

ModInt NTT::mod_sub(ModInt a, ModInt b) const {
    ModInt result = (a - b) % q;
    if (result < 0) result += q;
    return result;
}

ModInt NTT::mod_mul(ModInt a, ModInt b) const {
    // Use 128-bit intermediate to prevent overflow
    __int128 result = ((__int128)a * (__int128)b) % q;
    if (result < 0) result += q;
    return (ModInt)result;
}

ModInt NTT::mod_exp(ModInt base, ModInt exp) const {
    ModInt result = 1;
    base = base % q;
    
    while (exp > 0) {
        if (exp & 1) {
            result = mod_mul(result, base);
        }
        base = mod_mul(base, base);
        exp >>= 1;
    }
    
    return result;
}

ModInt NTT::mod_inv(ModInt a) const {
    ModInt x, y;
    ModInt gcd = extended_gcd(a, q, x, y);
    
    if (gcd != 1) {
        throw std::runtime_error("Modular inverse does not exist");
    }
    
    ModInt result = (x % q + q) % q;
    return result;
}

ModInt NTT::find_primitive_root() {
    // Try to find 2N-th primitive root of unity
    // This is a simplified version - in production, use precomputed values
    
    ModInt phi = q - 1;
    ModInt target_order = 2 * N;
    
    // Generator must have order 2N
    // g^(2N) = 1 (mod q) but g^N != 1 (mod q)
    
    for (ModInt g = 2; g < q; g++) {
        ModInt val = mod_exp(g, phi / target_order);
        
        // Check if this is a 2N-th root
        ModInt check_2n = mod_exp(val, target_order);
        ModInt check_n = mod_exp(val, N);
        
        if (check_2n == 1 && check_n != 1) {
            return val;
        }
    }
    
    return 0; // Failed to find
}

int NTT::bit_reverse(int x, int log_n) const {
    int result = 0;
    for (int i = 0; i < log_n; i++) {
        result <<= 1;
        result |= (x & 1);
        x >>= 1;
    }
    return result;
}

void NTT::bit_reverse_copy(std::vector<ModInt>& a) const {
    int log_n = 0;
    int temp_n = N;
    while (temp_n > 1) {
        log_n++;
        temp_n >>= 1;
    }
    
    for (int i = 0; i < N; i++) {
        int rev = bit_reverse(i, log_n);
        if (i < rev) {
            std::swap(a[i], a[rev]);
        }
    }
}

void NTT::forward(std::vector<ModInt>& a) const {
    if (a.size() != N) {
        throw std::invalid_argument("Input size must equal N");
    }
    
    // Cooley-Tukey NTT algorithm
    bit_reverse_copy(a);
    
    for (int s = 1; s <= std::log2(N); s++) {
        int m = 1 << s;
        int m2 = m >> 1;
        
        // Root of unity for this stage
        ModInt omega = psi_powers[N / m];
        
        for (int k = 0; k < N; k += m) {
            ModInt omega_power = 1;
            
            for (int j = 0; j < m2; j++) {
                ModInt t = mod_mul(omega_power, a[k + j + m2]);
                ModInt u = a[k + j];
                
                a[k + j] = mod_add(u, t);
                a[k + j + m2] = mod_sub(u, t);
                
                omega_power = mod_mul(omega_power, omega);
            }
        }
    }
}

void NTT::inverse(std::vector<ModInt>& a) const {
    if (a.size() != N) {
        throw std::invalid_argument("Input size must equal N");
    }
    
    // Similar to forward, but with inverse roots
    bit_reverse_copy(a);
    
    for (int s = 1; s <= std::log2(N); s++) {
        int m = 1 << s;
        int m2 = m >> 1;
        
        ModInt omega = psi_inv_powers[N / m];
        
        for (int k = 0; k < N; k += m) {
            ModInt omega_power = 1;
            
            for (int j = 0; j < m2; j++) {
                ModInt t = mod_mul(omega_power, a[k + j + m2]);
                ModInt u = a[k + j];
                
                a[k + j] = mod_add(u, t);
                a[k + j + m2] = mod_sub(u, t);
                
                omega_power = mod_mul(omega_power, omega);
            }
        }
    }
    
    // Scale by 1/N
    for (int i = 0; i < N; i++) {
        a[i] = mod_mul(a[i], N_inv);
    }
}

std::vector<ModInt> NTT::multiply(const std::vector<ModInt>& a,
                                   const std::vector<ModInt>& b) const {
    if (a.size() != N || b.size() != N) {
        throw std::invalid_argument("Input sizes must equal N");
    }
    
    // Copy inputs
    std::vector<ModInt> a_ntt = a;
    std::vector<ModInt> b_ntt = b;
    
    // Transform to NTT domain
    forward(a_ntt);
    forward(b_ntt);
    
    // Pointwise multiplication in NTT domain
    std::vector<ModInt> c_ntt(N);
    for (int i = 0; i < N; i++) {
        c_ntt[i] = mod_mul(a_ntt[i], b_ntt[i]);
    }
    
    // Transform back
    inverse(c_ntt);
    
    return c_ntt;
}

std::vector<ModInt> NTT::add(const std::vector<ModInt>& a,
                              const std::vector<ModInt>& b) const {
    if (a.size() != b.size()) {
        throw std::invalid_argument("Input sizes must match");
    }
    
    std::vector<ModInt> result(a.size());
    for (size_t i = 0; i < a.size(); i++) {
        result[i] = mod_add(a[i], b[i]);
    }
    return result;
}

std::vector<ModInt> NTT::subtract(const std::vector<ModInt>& a,
                                   const std::vector<ModInt>& b) const {
    if (a.size() != b.size()) {
        throw std::invalid_argument("Input sizes must match");
    }
    
    std::vector<ModInt> result(a.size());
    for (size_t i = 0; i < a.size(); i++) {
        result[i] = mod_sub(a[i], b[i]);
    }
    return result;
}

std::vector<ModInt> NTT::scalar_mul(const std::vector<ModInt>& a,
                                     ModInt scalar) const {
    std::vector<ModInt> result(a.size());
    for (size_t i = 0; i < a.size(); i++) {
        result[i] = mod_mul(a[i], scalar);
    }
    return result;
}

bool NTT::is_valid() const {
    return psi != 0 && psi_inv != 0 && N_inv != 0;
}

} // namespace fhe_cpp
