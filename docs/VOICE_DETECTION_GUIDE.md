# 🎤 راهنمای کامل Voice Detection - تشخیص صدای میکروفون

## 📊 وضعیت: ✅ فعال و آماده استفاده

---

## 📋 فهرست

1. [معرفی](#معرفی)
2. [نصب و راه‌اندازی](#نصب-و-راه‌اندازی)
3. [استفاده اولیه](#استفاده-اولیه)
4. [یکپارچگی با سیستم](#یکپارچگی-با-سیستم)
5. [تنظیمات پیشرفته](#تنظیمات-پیشرفته)
6. [عیب‌یابی](#عیب‌یابی)

---

## 🎯 معرفی

**Voice Activity Detector** یک سیستم تشخیص فعالیت صوتی است که می‌تواند:

✅ **تشخیص صحبت**: تشخیص زمانی که سخنران صحبت می‌کند  
✅ **تشخیص سکوت**: تشخیص زمان‌های سکوت  
✅ **مانیتورینگ real-time**: بررسی لحظه‌ای فعالیت صوتی  
✅ **یکپارچگی با Face AI**: ترکیب تحلیل صدا و تصویر  

### **معماری:**

```
🎤 میکروفون
    ↓
📊 تشخیص سطح انرژی (Energy Threshold)
    ↓
    ├─→ 🎤 صحبت تشخیص داده شد
    └─→ 🔇 سکوت تشخیص داده شد
    ↓
📡 ارسال سیگنال‌های real-time
```

---

## 💻 نصب و راه‌اندازی

### **1. بررسی نصب:**

✅ کتابخانه‌های مورد نیاز از قبل نصب شده‌اند:
- `SpeechRecognition` ✅
- `PyAudio` ✅

### **2. تست سیستم:**

```bash
# اجرای برنامه تست
python test_voice_detection.py
```

این برنامه:
- ✅ لیست میکروفون‌های موجود را نمایش می‌دهد
- ✅ یک رابط گرافیکی برای تست ارائه می‌دهد
- ✅ به صورت real-time وضعیت را نمایش می‌دهد

### **3. تشخیص میکروفون‌ها:**

```python
import speech_recognition as sr

# لیست میکروفون‌ها
mic_list = sr.Microphone.list_microphone_names()

for i, name in enumerate(mic_list):
    print(f"Mic {i}: {name}")
```

**خروجی نمونه:**
```
Mic 0: Microsoft Sound Mapper - Input
Mic 1: Microphone (Realtek High Definition Audio)
Mic 2: Microphone Array (Intel® Smart Sound Technology)
```

---

## 🚀 استفاده اولیه

### **مثال ساده:**

```python
from modules.ai_timing.voice_activity_detector import VoiceActivityDetector

# 1. ساخت detector
voice_detector = VoiceActivityDetector()

# 2. اتصال به سیگنال‌ها
voice_detector.presenter_speaking.connect(
    lambda: print("🎤 در حال صحبت")
)

voice_detector.presenter_silent.connect(
    lambda seconds: print(f"🔇 سکوت برای {seconds} ثانیه")
)

voice_detector.voice_activity_detected.connect(
    lambda is_speaking: print(f"{'🎤' if is_speaking else '🔇'} {'صحبت' if is_speaking else 'سکوت'}")
)

# 3. شروع تشخیص
success = voice_detector.start_detection(microphone_index=0)

if success:
    print("✅ تشخیص صدا شروع شد!")
    
    # نگه داشتن برنامه
    import time
    time.sleep(60)  # 60 ثانیه
    
    # توقف
    voice_detector.stop_detection()
else:
    print("❌ خطا در شروع تشخیص")
```

### **خروجی:**
```
✅ تشخیص صدا شروع شد!
🎤 در حال صحبت
🎤 صحبت
🔇 سکوت برای 3 ثانیه
🔇 سکوت
🎤 در حال صحبت
...
```

---

## 🔗 یکپارچگی با سیستم

### **A) یکپارچگی با Face AI:**

```python
from modules.face_ai.face_ai_controller import FaceAIController
from modules.ai_timing.voice_activity_detector import VoiceActivityDetector

# 1. راه‌اندازی Face AI
face_ai = FaceAIController()
face_ai.start_analysis(camera_index=0, fps=15)

# 2. راه‌اندازی Voice Detection
voice_detector = VoiceActivityDetector()
voice_detector.start_detection(microphone_index=0)

# 3. تحلیل ترکیبی
def combined_analysis():
    # داده‌های تصویر
    attention = face_ai.get_attention_level()      # 0.85 (85%)
    emotion = face_ai.get_dominant_emotion()       # 'happy'
    face_count = face_ai.get_face_count()          # 45
    
    # داده‌های صدا
    is_speaking = voice_detector.is_speaking()     # True
    silence_dur = voice_detector.get_silence_duration()  # 0
    
    # تصمیم‌گیری
    if is_speaking and attention > 0.7:
        print("✅ وضعیت عالی: سخنران در حال صحبت و مخاطبان متمرکز")
    
    elif not is_speaking and silence_dur > 5:
        print("⚠️ هشدار: سخنران 5 ثانیه سکوت کرده")
    
    elif attention < 0.5:
        print("⚠️ هشدار: توجه مخاطبان پایین است")
    
    return {
        'attention': attention,
        'emotion': emotion,
        'face_count': face_count,
        'is_speaking': is_speaking,
        'silence_duration': silence_dur
    }

# اجرا
import time
while True:
    stats = combined_analysis()
    print(stats)
    time.sleep(2)
```

### **B) یکپارچگی با Presenter Tracker:**

```python
from modules.ai_timing.presenter_tracker import PresenterTracker

# ساخت tracker
tracker = PresenterTracker()

# اتصال ماژول‌ها
tracker.set_face_ai_controller(face_ai)
tracker.set_voice_detector(voice_detector)

# شروع tracking
tracker.start_tracking()

# دریافت آمار
stats = tracker.get_presenter_statistics()
print(f"Speaking time: {stats['speaking_time']}s")
print(f"Silent time: {stats['silent_time']}s")
print(f"Attention rate: {stats['attention_rate']:.1f}%")
```

### **C) یکپارچگی با Adaptive Timer:**

```python
from modules.ai_timing.adaptive_timer_controller import AdaptiveTimerController

# ساخت adaptive timer
adaptive_timer = AdaptiveTimerController()

# اتصال voice detector
adaptive_timer.set_voice_detector(voice_detector)
adaptive_timer.set_face_ai_controller(face_ai)

# شروع timer با تنظیم خودکار
adaptive_timer.start_timer(duration=1800)  # 30 دقیقه

# Timer خودکار تنظیم می‌شود بر اساس:
# - سطح توجه مخاطبان (از Face AI)
# - فعالیت صوتی سخنران (از Voice Detector)
# - احساسات مخاطبان (از Face AI)
```

---

## ⚙️ تنظیمات پیشرفته

### **1. تنظیم آستانه سکوت:**

```python
# سکوت بعد از 2 ثانیه تشخیص داده شود
voice_detector.set_silence_threshold(2)

# سکوت بعد از 5 ثانیه
voice_detector.set_silence_threshold(5)
```

**توصیه:**
- 2-3 ثانیه: برای تشخیص سریع
- 5-10 ثانیه: برای محیط‌های عادی

### **2. تنظیم آستانه انرژی:**

```python
# آستانه پایین (حساس‌تر)
voice_detector.set_energy_threshold(200)

# آستانه متوسط (پیش‌فرض)
voice_detector.set_energy_threshold(300)

# آستانه بالا (کم‌حساس‌تر)
voice_detector.set_energy_threshold(500)
```

**توصیه:**
- محیط ساکت: 200-300
- محیط نیمه‌پر سر و صدا: 300-400
- محیط پرسر و صدا: 400-600

### **3. کالیبراسیون خودکار:**

```python
import speech_recognition as sr

recognizer = sr.Recognizer()
microphone = sr.Microphone(device_index=0)

# کالیبراسیون برای نویز محیط
with microphone as source:
    print("🔊 در حال تنظیم برای نویز محیط...")
    recognizer.adjust_for_ambient_noise(source, duration=3)
    print(f"✅ آستانه انرژی: {recognizer.energy_threshold}")
```

### **4. انتخاب میکروفون:**

```python
import speech_recognition as sr

# لیست میکروفون‌ها
mics = sr.Microphone.list_microphone_names()

# انتخاب میکروفون خاص
voice_detector.start_detection(microphone_index=2)
```

---

## 🔧 API کامل

### **کلاس VoiceActivityDetector:**

```python
class VoiceActivityDetector(QObject):
    
    # سیگنال‌ها
    presenter_speaking = pyqtSignal()
    presenter_silent = pyqtSignal(int)  # ثانیه سکوت
    voice_activity_detected = pyqtSignal(bool)  # True/False
    
    def __init__(self):
        """ساخت detector"""
        
    def start_detection(self, microphone_index: Optional[int] = None) -> bool:
        """
        شروع تشخیص
        
        Args:
            microphone_index: شماره میکروفون (None = پیش‌فرض)
        
        Returns:
            True اگر موفق بود
        """
        
    def stop_detection(self):
        """توقف تشخیص"""
        
    def is_speaking(self) -> bool:
        """آیا در حال صحبت است؟"""
        
    def get_silence_duration(self) -> int:
        """مدت سکوت (ثانیه)"""
        
    def set_silence_threshold(self, seconds: int):
        """تنظیم آستانه سکوت"""
        
    def set_energy_threshold(self, threshold: int):
        """تنظیم آستانه انرژی"""
```

---

## 🛠️ عیب‌یابی

### **❌ مشکل 1: میکروفون تشخیص داده نمی‌شود**

**علت:**
- دسترسی به میکروفون مسدود است
- میکروفون متصل نیست
- Driver مشکل دارد

**راه‌حل:**
```python
import speech_recognition as sr

# لیست میکروفون‌ها
try:
    mics = sr.Microphone.list_microphone_names()
    print(f"✅ تعداد: {len(mics)}")
    for i, name in enumerate(mics):
        print(f"Mic {i}: {name}")
except Exception as e:
    print(f"❌ خطا: {e}")
```

**بررسی دسترسی:**
- Windows: Settings → Privacy → Microphone → Allow apps
- بررسی Device Manager → Audio inputs

---

### **❌ مشکل 2: تشخیص کار نمی‌کند**

**علت:**
- نویز محیط زیاد است
- آستانه انرژی نامناسب است

**راه‌حل:**
```python
# کالیبراسیون دوباره
with microphone as source:
    recognizer.adjust_for_ambient_noise(source, duration=5)

# افزایش آستانه برای محیط پر سر و صدا
voice_detector.set_energy_threshold(500)
```

---

### **❌ مشکل 3: تشخیص خیلی حساس است**

**راه‌حل:**
```python
# کاهش حساسیت
voice_detector.set_energy_threshold(400)  # بالاتر
voice_detector.set_silence_threshold(5)   # طولانی‌تر
```

---

### **❌ مشکل 4: خطای PyAudio**

**خطا:**
```
OSError: [Errno -9996] Invalid input device
```

**راه‌حل:**
```python
# تست تک تک میکروفون‌ها
import pyaudio

p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f"✅ Mic {i}: {info['name']}")
```

---

## 📊 مثال‌های کاربردی

### **مثال 1: هشدار سکوت طولانی**

```python
def on_silence(seconds):
    if seconds >= 10:
        print("⚠️ هشدار: سخنران 10 ثانیه سکوت کرده!")
        # ارسال اعلان به operator
        send_notification("سخنران سکوت طولانی دارد")

voice_detector.presenter_silent.connect(on_silence)
```

### **مثال 2: لاگ فعالیت صوتی**

```python
import json
from datetime import datetime

log_file = open("voice_activity_log.json", "a")

def log_activity(is_speaking):
    entry = {
        'timestamp': datetime.now().isoformat(),
        'activity': 'speaking' if is_speaking else 'silent'
    }
    log_file.write(json.dumps(entry) + "\n")
    log_file.flush()

voice_detector.voice_activity_detected.connect(log_activity)
```

### **مثال 3: آمار زمان صحبت**

```python
from datetime import datetime, timedelta

speaking_time = timedelta()
silence_time = timedelta()
last_change = datetime.now()

def update_stats(is_speaking):
    global speaking_time, silence_time, last_change
    
    now = datetime.now()
    elapsed = now - last_change
    
    if is_speaking:
        silence_time += elapsed
    else:
        speaking_time += elapsed
    
    last_change = now
    
    print(f"صحبت: {speaking_time}, سکوت: {silence_time}")

voice_detector.voice_activity_detected.connect(update_stats)
```

---

## 🎓 نکات پیشرفته

### **1. Multi-threading:**

```python
from PyQt6.QtCore import QThread

class VoiceDetectionThread(QThread):
    def __init__(self):
        super().__init__()
        self.detector = VoiceActivityDetector()
    
    def run(self):
        self.detector.start_detection()
```

### **2. بهینه‌سازی:**

```python
# پردازش هر 500ms (به جای 100ms)
self._process_timer.setInterval(500)

# کاهش CPU usage
```

### **3. یکپارچگی با Database:**

```python
import sqlite3

conn = sqlite3.connect('voice_log.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS voice_events (
        id INTEGER PRIMARY KEY,
        timestamp TEXT,
        event_type TEXT,
        duration INTEGER
    )
''')

def log_to_db(is_speaking):
    cursor.execute(
        'INSERT INTO voice_events (timestamp, event_type) VALUES (?, ?)',
        (datetime.now().isoformat(), 'speaking' if is_speaking else 'silent')
    )
    conn.commit()
```

---

## ✅ چک‌لیست راه‌اندازی

- [x] نصب SpeechRecognition ✅
- [x] نصب PyAudio ✅
- [ ] تشخیص میکروفون‌های موجود
- [ ] انتخاب میکروفون مناسب
- [ ] کالیبراسیون برای نویز محیط
- [ ] تنظیم آستانه سکوت
- [ ] تنظیم آستانه انرژی
- [ ] تست تشخیص صحبت
- [ ] تست تشخیص سکوت
- [ ] یکپارچگی با Face AI
- [ ] تست در محیط واقعی

---

## 📞 پشتیبانی

### مشکل دارید؟

1. **اجرای برنامه تست:**
   ```bash
   python test_voice_detection.py
   ```

2. **بررسی لاگ‌ها:**
   ```bash
   tail -f logs/voice_detection.log
   ```

3. **تماس با پشتیبانی:**
   - 📧 Email: support@ai-symp-controller.com
   - 📚 Documentation: `/docs`

---

**نسخه**: 2.0  
**تاریخ**: نوامبر 2025  
**وضعیت**: ✅ فعال و آماده استفاده

🎤 **Voice Detection حالا فعال است!** 🎉

