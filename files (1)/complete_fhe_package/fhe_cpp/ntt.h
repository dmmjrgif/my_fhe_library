/*
 * NTT (Number Theoretic Transform) Implementation
 * Fast polynomial multiplication in Z_q[X]/(X^N + 1)
 * Based on academic paper recommendations
 */

#ifndef FHE_NTT_H
#define FHE_NTT_H

#include <vector>
#include <cstdint>
#include <stdexcept>

namespace fhe_cpp {

// Use 64-bit integers for intermediate calculations
typedef int64_t ModInt;
typedef uint64_t UModInt;

class NTT {
private:
    int N;                          // Polynomial degree (must be power of 2)
    ModInt q;                       // Modulus
    ModInt psi;                     // 2N-th primitive root of unity mod q
    ModInt psi_inv;                 // Inverse of psi
    std::vector<ModInt> psi_powers; // Precomputed powers of psi
    std::vector<ModInt> psi_inv_powers; // Precomputed powers of psi_inv
    ModInt N_inv;                   // Inverse of N mod q
    
    // Modular arithmetic helpers
    ModInt mod_add(ModInt a, ModInt b) const;
    ModInt mod_sub(ModInt a, ModInt b) const;
    ModInt mod_mul(ModInt a, ModInt b) const;
    ModInt mod_exp(ModInt base, ModInt exp) const;
    ModInt mod_inv(ModInt a) const;
    
    // Bit reversal for NTT
    int bit_reverse(int x, int log_n) const;
    void bit_reverse_copy(std::vector<ModInt>& a) const;

public:
    NTT(int N, ModInt q);
    ~NTT() = default;
    
    // Forward NTT transform
    void forward(std::vector<ModInt>& a) const;
    
    // Inverse NTT transform
    void inverse(std::vector<ModInt>& a) const;
    
    // Multiply two polynomials using NTT (result in standard form)
    std::vector<ModInt> multiply(const std::vector<ModInt>& a, 
                                  const std::vector<ModInt>& b) const;
    
    // Add two polynomials
    std::vector<ModInt> add(const std::vector<ModInt>& a,
                            const std::vector<ModInt>& b) const;
    
    // Subtract two polynomials  
    std::vector<ModInt> subtract(const std::vector<ModInt>& a,
                                  const std::vector<ModInt>& b) const;
    
    // Scalar multiplication
    std::vector<ModInt> scalar_mul(const std::vector<ModInt>& a,
                                    ModInt scalar) const;
    
    // Check if NTT is properly initialized
    bool is_valid() const;
    
    // Getters
    int get_N() const { return N; }
    ModInt get_q() const { return q; }
};

} // namespace fhe_cpp

#endif // FHE_NTT_H
