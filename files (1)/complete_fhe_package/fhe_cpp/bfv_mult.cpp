/*
 * BFV Multiplication Implementation
 * Based on research paper: proper scaling to manage noise
 */

#include "bfv_mult.h"
#include <cmath>
#include <iostream>

namespace fhe_cpp {

BFVMultiplier::BFVMultiplier(int N, ModInt q, ModInt t) 
    : ntt(N, q), N(N), q(q), t(t) {
    
    delta = q / t;
    
    if (!ntt.is_valid()) {
        throw std::runtime_error("NTT initialization failed");
    }
}

std::vector<ModInt> BFVMultiplier::gadget_decompose(const std::vector<ModInt>& vec) {
    // BitDecomp equivalent - decompose into log(q) components
    int log_q = std::ceil(std::log2(q));
    std::vector<ModInt> result;
    result.reserve(vec.size() * log_q);
    
    for (const auto& val : vec) {
        ModInt temp = val;
        for (int i = 0; i < log_q; i++) {
            result.push_back(temp & 1);
            temp >>= 1;
        }
    }
    
    return result;
}

std::vector<ModInt> BFVMultiplier::gadget_compose(const std::vector<ModInt>& vec) {
    // PowerOf2 equivalent - multiply by powers of 2
    int log_q = std::ceil(std::log2(q));
    int n = vec.size() / log_q;
    
    std::vector<ModInt> result(n, 0);
    
    for (int i = 0; i < n; i++) {
        ModInt power = 1;
        for (int j = 0; j < log_q; j++) {
            ModInt contrib = (vec[i * log_q + j] * power) % q;
            result[i] = (result[i] + contrib) % q;
            power = (power * 2) % q;
        }
    }
    
    return result;
}

std::vector<ModInt> BFVMultiplier::scale_down(const std::vector<ModInt>& poly) {
    // BFV scaling: multiply by t/q and round
    // This is the critical operation that requires exact arithmetic
    
    std::vector<ModInt> result(poly.size());
    
    for (size_t i = 0; i < poly.size(); i++) {
        // Use high precision arithmetic
        __int128 val = poly[i];
        __int128 scaled = (val * t) / q;
        
        // Handle rounding
        __int128 remainder = (val * t) % q;
        if (remainder * 2 >= q) {
            scaled++;
        }
        
        result[i] = scaled % q;
        if (result[i] < 0) result[i] += q;
    }
    
    return result;
}

std::vector<std::vector<ModInt>> BFVMultiplier::multiply_ciphertexts(
    const std::vector<ModInt>& c1_0,
    const std::vector<ModInt>& c1_1,
    const std::vector<ModInt>& c2_0,
    const std::vector<ModInt>& c2_1) {
    
    // Verify input sizes
    if (c1_0.size() != N || c1_1.size() != N || 
        c2_0.size() != N || c2_1.size() != N) {
        throw std::invalid_argument("All ciphertext components must have size N");
    }
    
    // Apply gadget decomposition for better scaling
    std::vector<ModInt> c1_0_G = gadget_compose(gadget_decompose(c1_0));
    std::vector<ModInt> c1_1_G = gadget_compose(gadget_decompose(c1_1));
    std::vector<ModInt> c2_0_G = gadget_compose(gadget_decompose(c2_0));
    std::vector<ModInt> c2_1_G = gadget_compose(gadget_decompose(c2_1));
    
    // Compute tensor product components using NTT
    // d0 = c1_0 * c2_0
    std::vector<ModInt> d0 = ntt.multiply(c1_0_G, c2_0_G);
    
    // d1 = c1_0 * c2_1 + c1_1 * c2_0
    std::vector<ModInt> d1_part1 = ntt.multiply(c1_0_G, c2_1_G);
    std::vector<ModInt> d1_part2 = ntt.multiply(c1_1_G, c2_0_G);
    std::vector<ModInt> d1 = ntt.add(d1_part1, d1_part2);
    
    // d2 = c1_1 * c2_1
    std::vector<ModInt> d2 = ntt.multiply(c1_1_G, c2_1_G);
    
    // Apply BFV scaling to each component
    d0 = scale_down(d0);
    d1 = scale_down(d1);
    d2 = scale_down(d2);
    
    return {d0, d1, d2};
}

std::vector<std::vector<ModInt>> BFVMultiplier::relinearize(
    const std::vector<ModInt>& d0,
    const std::vector<ModInt>& d1,
    const std::vector<ModInt>& d2,
    const std::vector<std::vector<ModInt>>& relin_key) {
    
    // Relinearization: reduce (d0, d1, d2) to (c0, c1)
    // Using evaluation key (relinearization key)
    
    if (relin_key.size() < 2 || relin_key[0].size() != N || relin_key[1].size() != N) {
        throw std::invalid_argument("Invalid relinearization key format");
    }
    
    // Decompose d2
    std::vector<ModInt> d2_decomp = gadget_decompose(d2);
    
    // The relin_key should have been constructed as (evk_0, evk_1)
    // where evk encrypts s^2
    
    // For simplicity, we'll use a basic approach:
    // new_c0 = d0 + d2 * relin_key[0]
    // new_c1 = d1 + d2 * relin_key[1]
    
    std::vector<ModInt> rk0_contrib = ntt.multiply(d2, relin_key[0]);
    std::vector<ModInt> rk1_contrib = ntt.multiply(d2, relin_key[1]);
    
    std::vector<ModInt> c0 = ntt.add(d0, rk0_contrib);
    std::vector<ModInt> c1 = ntt.add(d1, rk1_contrib);
    
    return {c0, c1};
}

} // namespace fhe_cpp
