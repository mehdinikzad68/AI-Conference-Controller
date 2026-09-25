# 🔧 راهنمای نصب dlib - مشکل مسیر طولانی

## ⚠️ مشکل

نصب dlib با `pip install dlib` به دلیل **مسیر طولانی در Temp** با خطا مواجه می‌شود.

این یک مشکل شناخته شده در Windows است که MSBuild نمی‌تواند با مسیرهای طولانی کار کند.

---

## ✅ راه حل 1: استفاده از Pre-built Wheel (توصیه می‌شود)

### مرحله 1: دانلود Wheel File

1. به این آدرس بروید:
   ```
   https://github.com/sachadee/Dlib/releases
   ```

2. فایل مناسب را دانلود کنید:
   - برای Python 3.11 Windows x64: `dlib-19.24.0-cp311-cp311-win_amd64.whl`

### مرحله 2: نصب

```bash
# Navigate to download folder
cd Downloads

# Install wheel file
py -3.11 -m pip install dlib-19.24.0-cp311-cp311-win_amd64.whl
```

---

## ✅ راه حل 2: استفاده از Visual Studio Developer Command Prompt

### مرحله 1: باز کردن Developer Command Prompt

1. در Start Menu جستجو کنید: **"Developer Command Prompt for VS 2022"**
2. یا از این مسیر:
   ```
   C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat
   ```

### مرحله 2: نصب dlib

```bash
# In Developer Command Prompt
py -3.11 -m pip install dlib
```

---

## ✅ راه حل 3: استفاده از Conda (اگر Conda نصب است)

```bash
conda install -c conda-forge dlib
```

---

## ✅ راه حل 4: تغییر مسیر Temp (موقت)

```powershell
# Set shorter temp path
$env:TEMP = "C:\Temp"
$env:TMP = "C:\Temp"

# Create directory
New-Item -ItemType Directory -Force -Path "C:\Temp"

# Install dlib
py -3.11 -m pip install dlib
```

---

## 📝 خلاصه

**بهترین روش:** استفاده از pre-built wheel file از GitHub

**لینک دانلود:**
- https://github.com/sachadee/Dlib/releases
- یا: https://github.com/z-mahmoud22/Dlib/releases

---

## ⚠️ نکته مهم

**dlib اختیاری است!**

اگر نصب dlib مشکل دارد:
- Face AI می‌تواند از **DeepFace** استفاده کند
- برنامه بدون dlib نیز کار می‌کند ✅

---

**تاریخ:** 2025-11-05

