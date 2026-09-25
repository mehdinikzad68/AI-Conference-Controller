# 🎤 راهنمای اتصال میکروفون لپ‌تاپ به AI Timer

## 📋 فهرست مطالب

1. [مراحل سریع](#1-مراحل-سریع)
2. [نصب کتابخانه‌ها](#2-نصب-کتابخانه‌ها)
3. [تشخیص میکروفون لپ‌تاپ](#3-تشخیص-میکروفون-لپ‌تاپ)
4. [اتصال به AI Timer](#4-اتصال-به-ai-timer)
5. [استفاده از طریق UI](#5-استفاده-از-طریق-ui)
6. [استفاده با کد](#6-استفاده-با-کد)
7. [مشکلات رایج](#7-مشکلات-رایج)

---

## 1. مراحل سریع

### ✅ چک‌لیست سریع:

1. ✅ نصب کتابخانه‌ها: `pip install SpeechRecognition pyaudio`
2. ✅ تست میکروفون: `python test_devices.py`
3. ✅ پیدا کردن Index میکروفون لپ‌تاپ
4. ✅ فعال‌سازی Voice Detection در AI Timer
5. ✅ انتخاب میکروفون صحیح

---

## 2. نصب کتابخانه‌ها

### Windows:

```bash
pip install SpeechRecognition pyaudio
```

### اگر pyaudio نصب نشد:

```bash
# Windows - استفاده از wheel file
pip install pipwin
pipwin install pyaudio

# یا دانلود مستقیم:
# https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
# دانلود PyAudio wheel برای Python شما
pip install PyAudio-0.2.11-cp313-cp313-win_amd64.whl
```

---

## 3. تشخیص میکروفون لپ‌تاپ

### روش 1: استفاده از Device Manager

```bash
python test_devices.py
```

خروجی را بررسی کنید و Index میکروفون لپ‌تاپ را پیدا کنید:

```
[MICROPHONES] Checking Microphones...
----------------------------------------------------------------------
[OK] Microphone 0: Microsoft Sound Mapper - Input
[OK] Microphone 1: Microphone Array (AMD Audio Device)  ← این میکروفون لپ‌تاپ است
[OK] Microphone 2: ...
```

### روش 2: استفاده از کد Python

```python
import speech_recognition as sr

# لیست همه میکروفون‌ها
mic_list = sr.Microphone.list_microphone_names()
for i, name in enumerate(mic_list):
    print(f"Microphone {i}: {name}")
    
    # معمولاً میکروفون لپ‌تاپ شامل این کلمات است:
    # "Microphone", "Array", "Built-in", "Internal"
    if any(word in name.lower() for word in ['microphone', 'array', 'built-in', 'internal']):
        print(f"  ← احتمالاً میکروفون لپ‌تاپ است!")
```

### روش 3: تست میکروفون

```python
import speech_recognition as sr

# تست میکروفون
r = sr.Recognizer()
mic = sr.Microphone(device_index=1)  # Index میکروفون لپ‌تاپ

print("در حال تست...")
with mic as source:
    r.adjust_for_ambient_noise(source, duration=1)
    print("✅ میکروفون کار می‌کند!")
    print("صحبت کنید...")
    audio = r.listen(source, timeout=5)
    print("✅ صدا دریافت شد!")
```

---

## 4. اتصال به AI Timer

### از طریق UI (راهنمای کامل):

1. **برنامه را اجرا کنید**: `python main.py`

2. **باز کردن Timer Module**:
   - از صفحه اصلی: کلیک روی `Timer Module`

3. **فعال‌سازی AI Timer**:
   - در Timer Module، گزینه‌های AI را پیدا کنید
   - یا از `Tools → AI Timing` استفاده کنید

4. **تنظیم میکروفون**:
   - در Settings، گزینه `Enable Voice Detection` را فعال کنید
   - `Microphone Index` را انتخاب کنید (مثلاً 1 برای میکروفون لپ‌تاپ)

### از طریق کد (برای توسعه‌دهندگان):

```python
from modules.ai_timing import AIIntegrationController

# ایجاد AI Timer Controller
ai_timer = AIIntegrationController()

# شروع AI Timer با میکروفون لپ‌تاپ
# microphone_index=1 → Index میکروفون لپ‌تاپ شما
success = ai_timer.start_ai_timing(
    presenter_camera=0,      # دوربین سخنران
    audience_camera=1,      # دوربین حضار
    enable_voice=True       # فعال‌سازی Voice Detection
)

if success:
    print("✅ AI Timer با Voice Detection شروع شد!")
else:
    print("❌ خطا در شروع AI Timer")
```

---

## 5. استفاده از طریق UI

### گام به گام:

#### مرحله 1: پیدا کردن Index میکروفون

```bash
python test_devices.py
```

**خروجی مثال:**
```
[OK] Microphone 1: Microphone Array (AMD Audio Device)
   Status: [OK] Working
```

➡️ **Index میکروفون لپ‌تاپ: 1**

#### مرحله 2: باز کردن Timer Module

1. برنامه را اجرا کنید
2. از صفحه اصلی: `Timer Module` را باز کنید

#### مرحله 3: فعال‌سازی Voice Detection

در Timer Module:
- Settings → AI Settings → Enable Voice Detection
- Microphone Index: `1` (یا Index میکروفون شما)
- Save Settings

#### مرحله 4: شروع Timer

- روی `Start Timer` کلیک کنید
- AI Timer شروع می‌شود و Voice Detection فعال می‌شود

---

## 6. استفاده با کد

### مثال 1: استفاده مستقیم از VoiceActivityDetector

```python
from modules.ai_timing import VoiceActivityDetector

# ایجاد detector
voice_detector = VoiceActivityDetector()

# شروع با میکروفون لپ‌تاپ (Index 1)
if voice_detector.start_detection(microphone_index=1):
    print("✅ Voice Detection شروع شد")
    
    # بررسی وضعیت
    if voice_detector.is_speaking():
        print("🎤 سخنران در حال صحبت است")
    
    # توقف
    voice_detector.stop_detection()
else:
    print("❌ خطا در شروع Voice Detection")
```

### مثال 2: استفاده با AI Integration Controller

```python
from modules.ai_timing import AIIntegrationController

# ایجاد controller
ai_controller = AIIntegrationController()

# شروع با Voice Detection
success = ai_controller.start_ai_timing(
    presenter_camera=0,
    audience_camera=1,
    enable_voice=True  # Voice Detection فعال می‌شود
)

# تنظیم میکروفون خاص (بعد از start)
if success:
    # متوقف کردن و دوباره شروع با میکروفون خاص
    ai_controller.stop_ai_timing()
    
    # استفاده از Voice Detector مستقیم
    ai_controller._voice_detector.start_detection(microphone_index=1)
    
    # دوباره شروع AI Timer
    ai_controller.start_ai_timing(
        presenter_camera=0,
        audience_camera=1,
        enable_voice=False  # چون دستی فعال کردیم
    )
```

### مثال 3: تست میکروفون قبل از استفاده

```python
from modules.utils.device_manager import get_device_manager

# دریافت device manager
device_manager = get_device_manager()

# لیست میکروفون‌ها
microphones = device_manager.get_available_microphones()
for mic in microphones:
    print(f"Microphone {mic['index']}: {mic['name']}")
    
    # تست
    success, error = device_manager.test_microphone(mic['index'])
    if success:
        print(f"  ✅ کار می‌کند")
    else:
        print(f"  ❌ خطا: {error}")

# استفاده از میکروفون که کار می‌کند
working_mic = next(mic for mic in microphones if mic['available'])
print(f"استفاده از: Microphone {working_mic['index']}")
```

---

## 7. مشکلات رایج

### ❌ مشکل 1: میکروفون پیدا نمی‌شود

**راه‌حل:**
1. بررسی کنید میکروفون در Windows فعال است:
   - Settings → Privacy → Microphone → Allow apps to access microphone
2. برنامه را به عنوان Administrator اجرا کنید
3. مطمئن شوید میکروفون توسط برنامه دیگری استفاده نمی‌شود

**کد تست:**
```python
import speech_recognition as sr
mic_list = sr.Microphone.list_microphone_names()
print(f"تعداد میکروفون‌ها: {len(mic_list)}")
for i, name in enumerate(mic_list):
    print(f"{i}: {name}")
```

### ❌ مشکل 2: Voice Detection کار نمی‌کند

**راه‌حل:**
1. مطمئن شوید `SpeechRecognition` نصب است:
   ```bash
   pip install SpeechRecognition pyaudio
   ```
2. Index میکروفون را بررسی کنید:
   ```python
   python test_devices.py
   ```
3. Threshold را تنظیم کنید:
   ```python
   voice_detector._energy_threshold = 300  # بالاتر = حساسیت کمتر
   ```

### ❌ مشکل 3: صدا تشخیص داده نمی‌شود

**راه‌حل:**
1. Threshold را کاهش دهید:
   ```python
   voice_detector._energy_threshold = 200  # پایین‌تر = حساسیت بیشتر
   ```
2. میکروفون را تست کنید:
   ```python
   import speech_recognition as sr
   r = sr.Recognizer()
   mic = sr.Microphone(device_index=1)
   with mic as source:
       r.adjust_for_ambient_noise(source, duration=2)
       print("صحبت کنید...")
       audio = r.listen(source)
       print("✅ صدا دریافت شد!")
   ```

### ❌ مشکل 4: خطای PyAudio

**راه‌حل:**
```bash
# Windows
pip install pipwin
pipwin install pyaudio

# یا از wheel file
# دانلود از: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
```

---

## 8. مثال کامل: استفاده در همایش

```python
from modules.ai_timing import AIIntegrationController
from modules.utils.device_manager import get_device_manager

# 1. پیدا کردن میکروفون لپ‌تاپ
device_manager = get_device_manager()
microphones = device_manager.get_available_microphones()

# پیدا کردن میکروفون لپ‌تاپ (معمولاً شامل "Microphone" یا "Array")
laptop_mic = None
for mic in microphones:
    name_lower = mic['name'].lower()
    if any(word in name_lower for word in ['microphone', 'array', 'built-in']):
        laptop_mic = mic
        break

if laptop_mic:
    mic_index = laptop_mic['index']
    print(f"✅ میکروفون لپ‌تاپ پیدا شد: Index {mic_index}")
    
    # 2. شروع AI Timer
    ai_timer = AIIntegrationController()
    
    success = ai_timer.start_ai_timing(
        presenter_camera=0,
        audience_camera=1,
        enable_voice=True
    )
    
    if success:
        # 3. تنظیم میکروفون لپ‌تاپ
        ai_timer._voice_detector.stop_detection()
        ai_timer._voice_detector.start_detection(microphone_index=mic_index)
        
        print("✅ AI Timer با میکروفون لپ‌تاپ شروع شد!")
        
        # 4. استفاده...
        # ...
        
        # 5. توقف
        ai_timer.stop_ai_timing()
else:
    print("❌ میکروفون لپ‌تاپ پیدا نشد")
```

---

## 📞 پشتیبانی

اگر مشکلی دارید:
1. `test_devices.py` را اجرا کنید
2. لاگ‌های برنامه را بررسی کنید
3. مطمئن شوید مجوزهای Windows فعال هستند
4. میکروفون را در برنامه‌های دیگر تست کنید

---

**آماده استفاده! 🎤**

