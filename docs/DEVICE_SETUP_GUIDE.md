# 📷🎤 راهنمای اتصال میکروفون و دوربین

## 📋 فهرست مطالب

1. [بررسی دستگاه‌های موجود](#1-بررسی-دستگاه‌های-موجود)
2. [اتصال دوربین](#2-اتصال-دوربین)
3. [اتصال میکروفون](#3-اتصال-میکروفون)
4. [استفاده در Face AI Module](#4-استفاده-در-face-ai-module)
5. [استفاده در Voice Detection](#5-استفاده-در-voice-detection)
6. [مشکلات رایج و راه‌حل](#6-مشکلات-رایج-و-راه‌حل)

---

## 1. بررسی دستگاه‌های موجود

### روش 1: استفاده از Device Manager

```python
from modules.utils.device_manager import get_device_manager

# دریافت manager
device_manager = get_device_manager()

# لیست دوربین‌ها
cameras = device_manager.get_available_cameras(test=True)
for cam in cameras:
    if cam['available']:
        print(f"Camera {cam['index']}: {cam['name']} ({cam['resolution']})")

# لیست میکروفون‌ها
microphones = device_manager.get_available_microphones()
for mic in microphones:
    print(f"Microphone {mic['index']}: {mic['name']}")
```

### روش 2: استفاده از اسکریپت تست

```bash
python test_devices.py
```

---

## 2. اتصال دوربین

### در Face AI Module:

1. **از منوی اصلی**: `Face AI Analysis Module` را باز کنید
2. **انتخاب دوربین**: در قسمت Settings، Camera Index را انتخاب کنید
   - معمولاً Camera 0 = دوربین پیش‌فرض
   - Camera 1, 2, ... = دوربین‌های اضافی
3. **شروع تحلیل**: روی دکمه `Start Analysis` کلیک کنید

### با کد Python:

```python
from modules.face_ai import FaceAIController

# ایجاد controller
face_ai = FaceAIController()

# شروع با دوربین پیش‌فرض (index 0)
face_ai.start_analysis(camera_index=0, fps=15)

# یا با دوربین خاص
face_ai.start_analysis(camera_index=1, fps=15)
```

### بررسی دوربین‌های موجود:

```python
import cv2

# تست دوربین‌ها
for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"✅ Camera {i} is available")
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"   Resolution: {width}x{height}")
        cap.release()
    else:
        print(f"❌ Camera {i} is not available")
```

---

## 3. اتصال میکروفون

### نصب کتابخانه‌های مورد نیاز:

```bash
pip install SpeechRecognition pyaudio
```

### در Voice Detection:

1. **از منوی اصلی**: `Face AI Analysis Module` را باز کنید
2. **فعال‌سازی Voice Detection**: در Settings، گزینه Voice Detection را فعال کنید
3. **انتخاب میکروفون**: Microphone Index را انتخاب کنید

### با کد Python:

```python
from modules.ai_timing import VoiceActivityDetector

# ایجاد detector
voice_detector = VoiceActivityDetector()

# شروع با میکروفون پیش‌فرض
voice_detector.start_detection()

# یا با میکروفون خاص
voice_detector.start_detection(microphone_index=1)
```

### بررسی میکروفون‌های موجود:

```python
import speech_recognition as sr

# لیست میکروفون‌ها
mic_list = sr.Microphone.list_microphone_names()
for i, name in enumerate(mic_list):
    print(f"Microphone {i}: {name}")
```

---

## 4. استفاده در Face AI Module

### از طریق UI:

1. **باز کردن Face AI Module**:
   - از صفحه اصلی: کلیک روی `Face AI Analysis Module`
   
2. **تنظیمات دوربین**:
   - در بخش Settings، Camera Index را تنظیم کنید
   - معمولاً 0 برای دوربین اول، 1 برای دوربین دوم
   
3. **شروع تحلیل**:
   - کلیک روی `Start Analysis`
   - تصویر دوربین در پنجره نمایش داده می‌شود
   - نتایج تحلیل (چهره‌ها، احساسات، توجه) نمایش داده می‌شود

### از طریق کد:

```python
# در main.py یا هر فایل دیگر
from modules.face_ai import FaceAIController

# در MainWindow.__init__()
self.face_ai_controller = FaceAIController()

# شروع تحلیل
def start_face_analysis(self, camera_index=0):
    if self.face_ai_controller.start_analysis(camera_index=camera_index, fps=15):
        print("✅ Face AI started successfully")
    else:
        print("❌ Failed to start Face AI")

# توقف تحلیل
def stop_face_analysis(self):
    self.face_ai_controller.stop_analysis()
```

---

## 5. استفاده در Voice Detection

### از طریق UI:

1. **باز کردن Face AI Module** (Voice Detection در همین ماژول است)
2. **فعال‌سازی Voice Detection**:
   - در Settings، گزینه `Enable Voice Detection` را فعال کنید
   - Microphone Index را انتخاب کنید
3. **شروع**: Voice Detection به صورت خودکار شروع می‌شود

### از طریق کد:

```python
from modules.ai_timing import VoiceActivityDetector

# ایجاد detector
voice_detector = VoiceActivityDetector()

# شروع
if voice_detector.start_detection(microphone_index=None):  # None = default
    print("✅ Voice Detection started")
    
    # بررسی وضعیت
    if voice_detector.is_speaking():
        print("🎤 Speaking detected")
    
    # توقف
    voice_detector.stop_detection()
```

---

## 6. مشکلات رایج و راه‌حل

### ❌ مشکل: دوربین پیدا نمی‌شود

**راه‌حل‌ها:**
1. بررسی کنید که دوربین به کامپیوتر متصل است
2. مطمئن شوید که دوربین توسط برنامه دیگری استفاده نمی‌شود
3. Camera Index را تغییر دهید (0, 1, 2, ...)
4. در Windows، دوربین را از Device Manager بررسی کنید
5. برنامه را به عنوان Administrator اجرا کنید

**کد تست:**
```python
import cv2
cap = cv2.VideoCapture(0)
if cap.isOpened():
    print("✅ Camera works")
    cap.release()
else:
    print("❌ Camera not accessible")
```

### ❌ مشکل: میکروفون کار نمی‌کند

**راه‌حل‌ها:**
1. بررسی کنید که میکروفون در تنظیمات Windows فعال است
2. مجوز دسترسی به میکروفون را به برنامه بدهید
3. Microphone Index را تغییر دهید
4. `SpeechRecognition` و `PyAudio` را نصب کنید:
   ```bash
   pip install SpeechRecognition pyaudio
   ```

**کد تست:**
```python
import speech_recognition as sr
r = sr.Recognizer()
mic = sr.Microphone()
with mic as source:
    r.adjust_for_ambient_noise(source)
    print("✅ Microphone works")
```

### ❌ مشکل: کیفیت تصویر پایین است

**راه‌حل:**
```python
# تنظیم رزولوشن بالاتر
face_ai_controller.start_analysis(
    camera_index=0,
    fps=15
)

# در FaceAIController، می‌توانید رزولوشن را تغییر دهید:
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
```

### ❌ مشکل: تاخیر در پردازش

**راه‌حل:**
- FPS را کاهش دهید: `fps=10` به جای `fps=30`
- رزولوشن را کاهش دهید
- Frame skip را افزایش دهید

---

## 7. مثال کامل: استفاده همزمان از دوربین و میکروفون

```python
from modules.face_ai import FaceAIController
from modules.ai_timing import VoiceActivityDetector

# ایجاد controllers
face_ai = FaceAIController()
voice_detector = VoiceActivityDetector()

# شروع دوربین
if face_ai.start_analysis(camera_index=0, fps=15):
    print("✅ Camera started")

# شروع میکروفون
if voice_detector.start_detection(microphone_index=None):
    print("✅ Microphone started")

# استفاده
# ... کار با هر دو ...

# توقف
face_ai.stop_analysis()
voice_detector.stop_detection()
```

---

## 8. تست سریع دستگاه‌ها

یک اسکریپت تست ایجاد کنید:

```python
# test_devices.py
from modules.utils.device_manager import get_device_manager

device_manager = get_device_manager()
device_manager.print_device_list()

# تست دوربین
cameras = device_manager.get_available_cameras(test=True)
for cam in cameras:
    if cam['available']:
        success, error = device_manager.test_camera(cam['index'])
        if success:
            print(f"✅ Camera {cam['index']} works: {cam['name']}")
        else:
            print(f"❌ Camera {cam['index']} failed: {error}")

# تست میکروفون
microphones = device_manager.get_available_microphones()
for mic in microphones:
    success, error = device_manager.test_microphone(mic['index'])
    if success:
        print(f"✅ Microphone {mic['index']} works: {mic['name']}")
    else:
        print(f"❌ Microphone {mic['index']} failed: {error}")
```

---

## 📞 پشتیبانی

اگر مشکلی دارید:
1. لاگ‌های برنامه را بررسی کنید
2. از `test_devices.py` استفاده کنید
3. مجوزهای سیستم را بررسی کنید (خصوصاً در Windows)
4. مطمئن شوید که کتابخانه‌های مورد نیاز نصب هستند

---

**آماده استفاده! 🚀**

