# 🚀 راه حل فوری برای TensorFlow DLL Error

## ⚡ Quick Fix (5 دقیقه)

### گام 1: نصب Visual C++ Redistributable (2 دقیقه)

1. **دانلود:**
   - لینک مستقیم: https://aka.ms/vs/17/release/vc_redist.x64.exe
   - یا جستجو: "Visual C++ Redistributable 2015-2022 x64"

2. **نصب:**
   - فایل را اجرا کنید
   - Next > Install > Finish
   - **Restart کامپیوتر** (مهم!)

### گام 2: Reinstall TensorFlow (2 دقیقه)

```powershell
# Uninstall
pip uninstall tensorflow tensorflow-cpu tf-keras -y

# Install compatible version
pip install tensorflow==2.16.1
pip install tf-keras
```

### گام 3: تست (1 دقیقه)

```powershell
# تست TensorFlow
python -c "import tensorflow as tf; print('TensorFlow:', tf.__version__)"

# تست DeepFace
python -c "from deepface import DeepFace; print('DeepFace OK')"

# تست FER
python -c "from fer.fer import FER; print('FER OK')"
```

### گام 4: Restart برنامه

```powershell
python main.py
```

---

## ✅ اگر کار نکرد

### Alternative 1: استفاده از TensorFlow CPU-Only

```powershell
pip uninstall tensorflow -y
pip install tensorflow-cpu==2.16.1
```

### Alternative 2: استفاده از Conda

```bash
conda install tensorflow -c conda-forge
```

### Alternative 3: Downgrade Python به 3.11

```bash
# اگر راه حل‌های بالا کار نکرد
# استفاده از Python 3.11 یا 3.12
```

---

## 📋 Checklist

- [ ] Visual C++ Redistributable نصب شد
- [ ] کامپیوتر restart شد
- [ ] TensorFlow uninstall شد
- [ ] TensorFlow 2.16.1 نصب شد
- [ ] tf-keras نصب شد
- [ ] تست TensorFlow موفق بود
- [ ] برنامه restart شد

---

**Estimated Time:** 5-10 minutes  
**Difficulty:** Easy  
**Success Rate:** 90%

