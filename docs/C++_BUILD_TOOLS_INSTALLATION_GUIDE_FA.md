# 🔧 راهنمای نصب C++ Build Tools

## 📋 خلاصه

برای نصب `dlib` و `pyaudio` در Python 3.11.9، نیاز به **C++ Build Tools** دارید.

---

## ✅ روش 1: استفاده از Visual Studio Build Tools (توصیه می‌شود)

### مرحله 1: دانلود Visual Studio Installer

1. به این آدرس بروید:
   ```
   https://visualstudio.microsoft.com/downloads/
   ```

2. **"Build Tools for Visual Studio 2022"** را دانلود کنید
   - یا مستقیم: https://aka.ms/vs/17/release/vs_buildtools.exe

### مرحله 2: نصب

1. فایل دانلود شده را اجرا کنید (نیاز به Administrator دارد)
2. در صفحه **"Workloads"**:
   - ✅ **"C++ build tools"** را انتخاب کنید
   - ✅ **"Desktop development with C++"** را انتخاب کنید
3. در بخش **"Individual components"** (اختیاری):
   - ✅ **Windows 10 SDK** (آخرین نسخه)
   - ✅ **CMake tools for Windows**
4. روی **"Install"** کلیک کنید
5. منتظر بمانید تا نصب کامل شود (حدود 3-6 GB)

### مرحله 3: راه‌اندازی مجدد

1. کامپیوتر را **Restart** کنید
2. یا **Visual Studio Developer Command Prompt** را باز کنید

---

## ✅ روش 2: استفاده از Visual Studio Community (اگر Visual Studio را می‌خواهید)

1. دانلود Visual Studio Community 2022:
   ```
   https://visualstudio.microsoft.com/vs/community/
   ```

2. در نصب:
   - ✅ **"Desktop development with C++"** را انتخاب کنید
   - ✅ **"Python development"** (اختیاری)

---

## ✅ روش 3: استفاده از Chocolatey (اگر نصب است)

```powershell
# اجرا به عنوان Administrator
choco install visualstudio2022buildtools --package-parameters "--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
```

---

## ✅ روش 4: استفاده از winget (Windows Package Manager)

```powershell
# اجرا به عنوان Administrator
winget install Microsoft.VisualStudio.2022.BuildTools --override "--quiet --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
```

---

## 🔍 بررسی نصب

بعد از نصب، بررسی کنید:

```powershell
# بررسی وجود cl.exe (C++ compiler)
where cl

# بررسی وجود cmake
where cmake

# بررسی نسخه Visual Studio
dir "C:\Program Files (x86)\Microsoft Visual Studio\2022\"
```

---

## 🚀 نصب dlib بعد از نصب Build Tools

بعد از نصب C++ Build Tools:

```bash
# باز کردن Visual Studio Developer Command Prompt
# یا استفاده از:
py -3.11 -m pip install dlib
```

---

## 🚀 نصب pyaudio بعد از نصب Build Tools

```bash
# روش 1: استفاده از wheel file (توصیه می‌شود)
# دانلود از: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
# برای Python 3.11: PyAudio-0.2.14-cp311-cp311-win_amd64.whl
py -3.11 -m pip install PyAudio-0.2.14-cp311-cp311-win_amd64.whl

# روش 2: نصب مستقیم (بعد از نصب Build Tools)
py -3.11 -m pip install pyaudio
```

---

## ⚠️ مشکلات رایج

### مشکل 1: "cl.exe not found"

**راه‌حل:**
1. Visual Studio Developer Command Prompt را باز کنید
2. یا مسیر را به PATH اضافه کنید:
   ```
   C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\<version>\bin\Hostx64\x64
   ```

### مشکل 2: "CMake not found"

**راه‌حل:**
1. CMake را نصب کنید:
   ```
   https://cmake.org/download/
   ```
2. یا از Visual Studio Installer → Individual components → CMake tools

### مشکل 3: "Windows SDK not found"

**راه‌حل:**
1. Visual Studio Installer را باز کنید
2. Modify → Individual components
3. Windows 10 SDK را انتخاب کنید

---

## 📝 نکات مهم

1. **نیاز به Administrator:** نصب Build Tools نیاز به دسترسی Administrator دارد
2. **فضای دیسک:** حداقل 3-6 GB فضا نیاز است
3. **زمان نصب:** حدود 15-30 دقیقه
4. **Restart:** بعد از نصب، بهتر است کامپیوتر را restart کنید

---

## ✅ بعد از نصب

1. **Restart کامپیوتر**
2. **Visual Studio Developer Command Prompt** را باز کنید
3. یا از **PowerShell/CMD** عادی:
   ```bash
   py -3.11 -m pip install dlib pyaudio
   ```

---

## 🔗 لینک‌های مفید

- Visual Studio Build Tools: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
- CMake: https://cmake.org/download/
- Python Windows Build Tools: https://wiki.python.org/moin/WindowsCompilers

---

## 📞 پشتیبانی

اگر مشکل داشتید:
1. بررسی کنید که Build Tools درست نصب شده
2. Visual Studio Developer Command Prompt را امتحان کنید
3. کامپیوتر را restart کنید

---

**آماده نصب! 🚀**

