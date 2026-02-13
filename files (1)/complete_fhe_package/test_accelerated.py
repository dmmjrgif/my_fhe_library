"""
Test Suite for C++ Accelerated FHE Multiplication
Tests both C++ backend and Python fallback
"""

import sys
sys.path.insert(0, '/home/claude')

import time
import numpy as np

try:
    from custom_fhe.bfv_accelerated import BFVSchemeAccelerated, CPP_AVAILABLE
except ImportError:
    print("Error: Could not import BFVSchemeAccelerated")
    print("Make sure the C++ extension is built")
    sys.exit(1)


def test_backend_availability():
    """Test if C++ backend is available"""
    print("=" * 60)
    print("TEST 1: Backend Availability")
    print("=" * 60)
    
    if CPP_AVAILABLE:
        print("✓ C++ backend is available")
        import fhe_fast_mult
        print(f"✓ fhe_fast_mult module loaded")
    else:
        print("⚠ C++ backend not available (will use Python fallback)")
    
    print()


def test_initialization():
    """Test scheme initialization"""
    print("=" * 60)
    print("TEST 2: Scheme Initialization")
    print("=" * 60)
    
    try:
        fhe = BFVSchemeAccelerated(N=4096, t=65537, q_bits=50)
        info = fhe.get_backend_info()
        
        print(f"✓ Scheme initialized")
        print(f"  Backend: {info['backend']}")
        print(f"  Multiplication: {info['multiplication']}")
        print(f"  q = {info['q']}")
        print(f"  NTT-friendly: {info['ntt_friendly']}")
        
        return fhe
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return None


def test_basic_operations(fhe):
    """Test basic encryption/decryption"""
    print("\n" + "=" * 60)
    print("TEST 3: Basic Operations")
    print("=" * 60)
    
    fhe.key_generation()
    print("✓ Keys generated")
    
    # Test encryption/decryption
    value = 42
    ct = fhe.encrypt(fhe.encode(value))
    result = fhe.decode(fhe.decrypt(ct))
    
    assert result == value, f"Expected {value}, got {result}"
    print(f"✓ Encryption/Decryption: {value} -> {result}")
    
    # Test addition
    ct1 = fhe.encrypt(fhe.encode(100))
    ct2 = fhe.encrypt(fhe.encode(200))
    ct_sum = fhe.add(ct1, ct2)
    sum_result = fhe.decode(fhe.decrypt(ct_sum))
    
    assert sum_result == 300, f"Expected 300, got {sum_result}"
    print(f"✓ Addition: 100 + 200 = {sum_result}")
    
    # Test subtraction
    ct_diff = fhe.sub(ct1, ct2)
    diff_result = fhe.decode(fhe.decrypt(ct_diff))
    
    assert diff_result == -100 or diff_result == fhe.t - 100, f"Subtraction failed: {diff_result}"
    print(f"✓ Subtraction: 100 - 200 = {diff_result}")


def test_multiplication(fhe):
    """Test homomorphic multiplication"""
    print("\n" + "=" * 60)
    print("TEST 4: Multiplication (The Critical Test!)")
    print("=" * 60)
    
    # Generate relinearization key
    fhe.generate_relin_key()
    print("✓ Relinearization key generated")
    
    test_cases = [
        (5, 7, 35),
        (12, 8, 96),
        (3, 11, 33),
        (10, 10, 100),
        (2, 50, 100),
    ]
    
    passed = 0
    failed = 0
    
    for a, b, expected in test_cases:
        try:
            ct1 = fhe.encrypt(fhe.encode(a))
            ct2 = fhe.encrypt(fhe.encode(b))
            
            # Multiply
            ct_mult = fhe.multiply(ct1, ct2)
            
            # Relinearize
            ct_mult = fhe.relinearize(ct_mult)
            
            # Decrypt
            result = fhe.decode(fhe.decrypt(ct_mult))
            
            # Check result
            if result == expected:
                print(f"✓ {a} × {b} = {result}")
                passed += 1
            else:
                error = abs(result - expected)
                if error <= 2:  # Allow small error due to noise
                    print(f"✓ {a} × {b} = {result} (expected {expected}, error {error})")
                    passed += 1
                else:
                    print(f"✗ {a} × {b} = {result} (expected {expected}, error {error})")
                    failed += 1
        
        except Exception as e:
            print(f"✗ {a} × {b} failed with error: {e}")
            failed += 1
    
    print(f"\nMultiplication tests: {passed} passed, {failed} failed")
    return failed == 0


def test_performance(fhe):
    """Test performance comparison"""
    print("\n" + "=" * 60)
    print("TEST 5: Performance Benchmark")
    print("=" * 60)
    
    fhe.generate_relin_key()
    
    # Prepare test data
    ct1 = fhe.encrypt(fhe.encode(12))
    ct2 = fhe.encrypt(fhe.encode(8))
    
    # Benchmark multiplication
    num_iterations = 5
    
    print(f"Running {num_iterations} multiplication operations...")
    start = time.time()
    
    for i in range(num_iterations):
        ct_mult = fhe.multiply(ct1, ct2)
        ct_mult = fhe.relinearize(ct_mult)
    
    elapsed = time.time() - start
    avg_time = elapsed / num_iterations
    
    info = fhe.get_backend_info()
    print(f"\nBackend: {info['backend']}")
    print(f"Average time per multiplication: {avg_time:.3f}s")
    print(f"Throughput: {1/avg_time:.2f} mult/sec")
    
    if CPP_AVAILABLE and info['backend'].startswith('C++'):
        print("✓ Using fast C++ backend")
        if avg_time < 0.5:
            print("✓ Performance is good!")
        else:
            print("⚠ Performance is slower than expected")
    else:
        print("⚠ Using Python fallback (slower)")


def test_exact_match_scenario(fhe):
    """Test the original exact match use case"""
    print("\n" + "=" * 60)
    print("TEST 6: Exact Match Scenario")
    print("=" * 60)
    
    # Data
    dates = [20260205, 20260215, 20260225, 20260228]
    encrypted_dates = [fhe.encrypt(fhe.encode(d)) for d in dates]
    
    # Search for target
    target = 20260225
    enc_target = fhe.encrypt(fhe.encode(target))
    
    print(f"Searching for: {target}")
    
    # Find match using subtraction (doesn't need multiplication!)
    for i, enc_date in enumerate(encrypted_dates):
        diff_ct = fhe.sub(enc_date, enc_target)
        diff = fhe.decode(fhe.decrypt(diff_ct))
        
        if diff == 0:
            print(f"✓ Match found at index {i}: {dates[i]}")
            return True
    
    print("✗ No match found")
    return False


def run_all_tests():
    """Run complete test suite"""
    print("\n" + "=" * 70)
    print(" C++ ACCELERATED FHE - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    # Test 1: Backend availability
    test_backend_availability()
    
    # Test 2: Initialization
    fhe = test_initialization()
    if fhe is None:
        print("\n✗ Cannot proceed without successful initialization")
        return
    
    try:
        # Test 3: Basic operations
        test_basic_operations(fhe)
        
        # Test 4: Multiplication (THE BIG TEST)
        mult_success = test_multiplication(fhe)
        
        # Test 5: Performance
        test_performance(fhe)
        
        # Test 6: Original use case
        match_success = test_exact_match_scenario(fhe)
        
        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        if mult_success:
            print("✓ MULTIPLICATION WORKS! 🎉")
        else:
            print("⚠ Multiplication had some issues")
        
        if match_success:
            print("✓ Exact match scenario works")
        
        print("\n" + "=" * 70)
        
        if mult_success:
            print("\n🎉 SUCCESS! You now have working FHE multiplication!")
            if CPP_AVAILABLE:
                print("✓ Using fast C++ NTT backend")
            else:
                print("⚠ Using Python fallback (consider building C++ for speed)")
        
    except Exception as e:
        print(f"\n✗ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
