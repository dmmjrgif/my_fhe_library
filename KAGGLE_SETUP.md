# Custom FHE on Kaggle - Setup Guide

## 🚀 Quick Setup for Kaggle

### Option 1: Direct Upload (Recommended for Kaggle)

1. **Upload the `custom_fhe` folder** to your Kaggle notebook as a dataset or directly to the working directory

2. **In your Kaggle notebook:**

```python
# Add custom_fhe to Python path
import sys
sys.path.insert(0, '/kaggle/input/custom-fhe')  # Adjust path if needed

# Import and use
from custom_fhe import BFVScheme

# Initialize
fhe = BFVScheme(N=8192, t=65537, q_bits=60)
fhe.key_generation()

# Now use it!
ct = fhe.encrypt(fhe.encode(42))
result = fhe.decode(fhe.decrypt(ct))
print(result)  # 42
```

### Option 2: Copy Files to Working Directory

In your Kaggle notebook:

```python
# Copy the custom_fhe folder to working directory
import shutil
import os

# If uploaded as dataset
source = '/kaggle/input/custom-fhe/custom_fhe'
dest = '/kaggle/working/custom_fhe'

if os.path.exists(source):
    shutil.copytree(source, dest)
    print("✓ Custom FHE copied to working directory")

# Now import normally
from custom_fhe import BFVScheme
```

### Option 3: Install as Package

```python
# In Kaggle cell
!pip install -q /kaggle/input/custom-fhe

# Then use normally
from custom_fhe import BFVScheme
```

## 📁 Required Files for Kaggle

Upload these files as a Kaggle dataset:

```
custom_fhe/
├── __init__.py
├── bfv_scheme.py
├── polynomial.py
├── keys.py
└── ciphertext.py
```

## 🎯 Complete Kaggle Example

```python
# Cell 1: Setup
import sys
sys.path.insert(0, '/kaggle/input/custom-fhe')

import numpy as np
from custom_fhe import BFVScheme

print("✓ Custom FHE imported successfully")

# Cell 2: Initialize
fhe = BFVScheme(
    N=8192,      # Good balance of security and speed
    t=65537,     # Prime number for plaintext modulus
    q_bits=60,   # Ciphertext modulus
    sigma=3.2    # Noise parameter
)

print("Generating keys...")
fhe.key_generation()
fhe.generate_relin_key()
print("✓ Keys generated")

# Cell 3: Basic Operations
# Encryption
value = 12345
ct = fhe.encrypt(fhe.encode(value))
print(f"Encrypted {value}")

# Decryption
result = fhe.decode(fhe.decrypt(ct))
print(f"Decrypted: {result}")

# Cell 4: Homomorphic Operations
a, b = 100, 200
ct_a = fhe.encrypt(fhe.encode(a))
ct_b = fhe.encrypt(fhe.encode(b))

# Addition
ct_sum = fhe.add(ct_a, ct_b)
sum_result = fhe.decode(fhe.decrypt(ct_sum))
print(f"{a} + {b} = {sum_result}")

# Subtraction
ct_diff = fhe.sub(ct_a, ct_b)
diff_result = fhe.decode(fhe.decrypt(ct_diff))
print(f"{a} - {b} = {diff_result}")

# Cell 5: Batch Processing (SIMD)
values = [10, 20, 30, 40, 50]
pt = fhe.encode(values)
ct = fhe.encrypt(pt)

decrypted = fhe.decrypt(ct)
results = fhe.decode(decrypted, num_values=len(values))
print(f"Batch encrypted and decrypted: {list(results)}")
```

## 🏃 Running Your Exact Match Example

```python
# Copy the fhe_custom_exact_match.py to Kaggle
# Then run:

import sys
sys.path.insert(0, '/kaggle/input/custom-fhe')

# Run the exact match example
exec(open('/kaggle/input/custom-fhe/fhe_custom_exact_match.py').read())
```

## ⚡ Performance Tips for Kaggle

### 1. Use Smaller Parameters for Testing

```python
# Fast testing (less secure)
fhe = BFVScheme(N=4096, t=257, q_bits=40)
```

### 2. Enable NumPy Optimizations

```python
import numpy as np
# Kaggle usually has optimized NumPy by default
print(np.__config__.show())
```

### 3. GPU Usage

Note: This FHE implementation is CPU-based. GPUs won't help much for polynomial operations.

### 4. Memory Management

```python
# For large datasets, process in batches
batch_size = 100
for i in range(0, len(data), batch_size):
    batch = data[i:i+batch_size]
    # Process batch
```

## 🐛 Troubleshooting

### Import Error

```python
# If you get: ModuleNotFoundError: No module named 'custom_fhe'
# Check your path:
import sys
print(sys.path)

# Add correct path:
sys.path.insert(0, '/kaggle/input/YOUR_DATASET_NAME')
```

### NumPy Version

```python
# Check NumPy version
import numpy as np
print(f"NumPy version: {np.__version__}")

# Upgrade if needed (shouldn't be necessary on Kaggle)
!pip install --upgrade numpy
```

### Memory Issues

```python
# Use smaller parameters
fhe = BFVScheme(N=4096, t=257, q_bits=40)

# Or process data in smaller batches
```

## 📊 Expected Performance on Kaggle

With default settings (N=8192):
- **Key Generation**: 1-2 seconds
- **Encryption**: ~0.3 seconds per value
- **Homomorphic Op**: ~0.1 seconds per operation
- **Decryption**: ~0.1 seconds per value

## 🎓 Learning Resources

1. **Try the tests**:
```python
exec(open('/kaggle/input/custom-fhe/test_custom_fhe.py').read())
```

2. **Read the README**:
```python
with open('/kaggle/input/custom-fhe/README.md') as f:
    print(f.read())
```

3. **Explore the code**:
```python
# View the BFV implementation
!cat /kaggle/input/custom-fhe/custom_fhe/bfv_scheme.py
```

## 🎯 Your Exact Match Use Case

```python
import sys
sys.path.insert(0, '/kaggle/input/custom-fhe')

from custom_fhe import BFVScheme

# Initialize
fhe = BFVScheme(N=8192, t=65537, q_bits=60)
fhe.key_generation()

# Your data
data = [
    {"date": 20260205, "email": "spam@x.com"},
    {"date": 20260225, "email": "me@home.net"},
    # ... more data
]

# Encrypt dates
encrypted_dates = []
for row in data:
    pt = fhe.encode(row['date'])
    ct = fhe.encrypt(pt)
    encrypted_dates.append(ct)

# Search for target
target = 20260225
ct_target = fhe.encrypt(fhe.encode(target))

# Find matches (homomorphic subtraction)
for i, ct_date in enumerate(encrypted_dates):
    ct_diff = fhe.sub(ct_date, ct_target)
    diff = fhe.decode(fhe.decrypt(ct_diff))
    
    if diff == 0:
        print(f"Match found at index {i}: {data[i]}")
```

## ✅ Verification

Run this to verify everything works:

```python
# Quick verification
import sys
sys.path.insert(0, '/kaggle/input/custom-fhe')

from custom_fhe import BFVScheme

fhe = BFVScheme(N=4096, t=65537, q_bits=50)
fhe.key_generation()

# Test
ct1 = fhe.encrypt(fhe.encode(10))
ct2 = fhe.encrypt(fhe.encode(20))
ct_sum = fhe.add(ct1, ct2)
result = fhe.decode(fhe.decrypt(ct_sum))

assert result == 30, "Something went wrong!"
print("✓ Custom FHE is working perfectly on Kaggle!")
```

---

**Ready to encrypt on Kaggle! 🔐**
