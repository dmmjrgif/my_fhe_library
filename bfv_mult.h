/*
 * BFV Multiplication with proper scaling
 * Implements the exact algorithm from the research paper
 */

#ifndef FHE_BFV_MULT_H
#define FHE_BFV_MULT_H

#include "ntt.h"
#include <vector>

namespace fhe_cpp {

class BFVMultiplier {
private:
    NTT ntt;
    ModInt q;
    ModInt t;
    int N;
    ModInt delta;  // floor(q/t)
    
    // Gadget matrix operations
    std::vector<ModInt> gadget_decompose(const std::vector<ModInt>& vec);
    std::vector<ModInt> gadget_compose(const std::vector<ModInt>& vec);
    
public:
    BFVMultiplier(int N, ModInt q, ModInt t);
    ~BFVMultiplier() = default;
    
    // Multiply two ciphertexts (c0, c1) format
    // Returns (d0, d1, d2) which needs relinearization
    std::vector<std::vector<ModInt>> multiply_ciphertexts(
        const std::vector<ModInt>& c1_0,
        const std::vector<ModInt>& c1_1,
        const std::vector<ModInt>& c2_0,
        const std::vector<ModInt>& c2_1
    );
    
    // Relinearize (d0, d1, d2) back to (c0, c1)
    std::vector<std::vector<ModInt>> relinearize(
        const std::vector<ModInt>& d0,
        const std::vector<ModInt>& d1,
        const std::vector<ModInt>& d2,
        const std::vector<std::vector<ModInt>>& relin_key
    );
    
    // Scale multiplication result properly (BFV specific)
    std::vector<ModInt> scale_down(const std::vector<ModInt>& poly);
    
    ModInt get_delta() const { return delta; }
};

} // namespace fhe_cpp

#endif // FHE_BFV_MULT_H
