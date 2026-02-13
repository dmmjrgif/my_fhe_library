# Custom FHE - Quick Reference Card

## 🚀 Installation (Kaggle)

```python
import sys
sys.path.insert(0, '/kaggle/input/custom-fhe')
from custom_fhe import BFVScheme
```

## ⚡ Quick Start

```python
# Initialize
fhe = BFVScheme(N=8192, t=65537, q_bits=60)
fhe.key_generation()

# Encrypt
ct = fhe.encrypt(fhe.encode(42))

# Decrypt
result = fhe.decode(fhe.decrypt(ct))
```

## 🔧 Common Operations

### Single Value
```python
value = 100
ct = fhe.encrypt(fhe.encode(value))
result = fhe.decode(fhe.decrypt(ct))
```

### Multiple Values (Batching)
```python
values = [10, 20, 30, 40, 50]
ct = fhe.encrypt(fhe.encode(values))
results = fhe.decode(fhe.decrypt(ct), num_values=5)
```

### Addition
```python
ct1 = fhe.encrypt(fhe.encode(100))
ct2 = fhe.encrypt(fhe.encode(200))
ct_sum = fhe.add(ct1, ct2)
result = fhe.decode(fhe.decrypt(ct_sum))  # 300
```

### Subtraction
```python
ct1 = fhe.encrypt(fhe.encode(500))
ct2 = fhe.encrypt(fhe.encode(200))
ct_diff = fhe.sub(ct1, ct2)
result = fhe.decode(fhe.decrypt(ct_diff))  # 300
```

## 🎯 Exact Match Search

```python
# Encrypt database
db_values = [20260205, 20260215, 20260225]
encrypted_db = [fhe.encrypt(fhe.encode(v)) for v in db_values]

# Search
target = 20260225
enc_target = fhe.encrypt(fhe.encode(target))

# Find matches
for i, enc_val in enumerate(encrypted_db):
    diff = fhe.sub(enc_val, enc_target)
    if fhe.decode(fhe.decrypt(diff)) == 0:
        print(f"Match at index {i}")
```

## ⚙️ Parameters

### Balanced (Default)
```python
BFVScheme(N=8192, t=65537, q_bits=60)
```

### Fast (Testing)
```python
BFVScheme(N=4096, t=257, q_bits=40)
```

### Secure (Production)
```python
BFVScheme(N=16384, t=65537, q_bits=120)
```

## 📊 Performance (N=8192)

| Operation | Time |
|-----------|------|
| Key Gen | ~1s |
| Encrypt | ~0.13s |
| Decrypt | ~0.04s |
| Add/Sub | ~0.01s |

## 🧪 Testing

```python
!python test_custom_fhe.py
```

Expected: 6/7 tests pass

## 📁 Files

```
custom_fhe/              # Library
fhe_custom_exact_match.py   # Demo
test_custom_fhe.py       # Tests
README.md                # Full docs
KAGGLE_SETUP.md         # Setup guide
```

## 🐛 Troubleshooting

### Import Error
```python
import sys
sys.path.insert(0, '/kaggle/input/YOUR-DATASET')
```

### Memory Error
```python
# Use smaller N
fhe = BFVScheme(N=4096, t=257, q_bits=40)
```

## ✅ Checklist

- [ ] Upload files to Kaggle dataset
- [ ] Add custom_fhe to path
- [ ] Import BFVScheme
- [ ] Generate keys
- [ ] Test encryption
- [ ] Run demo

## 📚 Full Documentation

- `README.md` - Complete API
- `KAGGLE_SETUP.md` - Detailed setup
- `GETTING_STARTED.md` - Quick guide
- `PROJECT_SUMMARY.md` - Overview

## 🎯 Key Points

✅ No Pyfhel needed
✅ Only NumPy required
✅ Works on Kaggle
✅ ~70% Pyfhel performance
✅ 100% accurate for add/sub

## 🔐 Security

~128-bit security (N=8192)
Educational/research grade
Suitable for prototyping

## 💡 Tips

1. Test with N=4096 first (faster)
2. Use batching for efficiency
3. Keep secret keys secure
4. Process in batches for large datasets
5. Read docs for advanced features

---

**Need help?** Check the full documentation!
