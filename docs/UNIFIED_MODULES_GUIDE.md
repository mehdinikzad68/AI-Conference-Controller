# 🎯 راهنمای استفاده همزمان و یکپارچه همه ماژول‌ها

## 📋 فهرست مطالب

1. [معرفی Unified Controller](#1-معرفی-unified-controller)
2. [سناریوهای استفاده](#2-سناریوهای-استفاده)
3. [راه‌اندازی کامل](#3-راه‌اندازی-کامل)
4. [مثال‌های عملی](#4-مثال‌های-عملی)
5. [هماهنگی بین ماژول‌ها](#5-هماهنگی-بین-ماژول‌ها)
6. [Dashboard یکپارچه](#6-dashboard-یکپارچه)

---

## 1. معرفی Unified Controller

`UnifiedController` یک کنترلر مرکزی است که همه ماژول‌ها را هماهنگ می‌کند:

### ماژول‌های تحت مدیریت:

- ✅ **Timer Module** - مدیریت زمان
- ✅ **Media Player** - پخش رسانه
- ✅ **Face AI** - تحلیل حضار
- ✅ **Display Management** - مدیریت نمایشگرها
- ✅ **AI Timing** - زمان‌بندی هوشمند (Presenter + Voice + Audience)
- ✅ **Content Automation** - اتوماسیون محتوا
- ✅ **Symposium** - مدیریت همایش

---

## 2. سناریوهای استفاده

### سناریو 1: همایش کامل با همه ماژول‌ها

**هدف**: استفاده از تمام قابلیت‌ها به صورت همزمان

```
┌─────────────────────────────────────────┐
│  Unified Controller                      │
│  ┌───────────────────────────────────┐  │
│  │  Timer + AI Timing                │  │
│  │  ├─ Presenter Tracking (Camera 0) │  │
│  │  ├─ Voice Detection (Laptop Mic)  │  │
│  │  └─ Audience Analysis (Camera 1)  │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  Content Automation               │  │
│  │  ├─ Schedule Management            │  │
│  │  ├─ Media Playback                 │  │
│  │  └─ Multi-Platform Sync            │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  Face AI + Display                 │  │
│  │  ├─ Audience Engagement            │  │
│  │  └─ Multi-Display Output           │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### سناریو 2: همایش ساده (بدون AI)

**هدف**: فقط Timer + Media + Display

### سناریو 3: همایش با AI (بدون Content Automation)

**هدف**: Timer + AI Timing + Face AI

---

## 3. راه‌اندازی کامل

### روش 1: استفاده از Unified Controller (پیشنهادی)

```python
from modules.operator.unified_controller import UnifiedController
import asyncio

# ایجاد Unified Controller
unified = UnifiedController()

# راه‌اندازی همه ماژول‌ها
unified.initialize_modules()

# شروع همایش کامل
async def start_conference():
    success = await unified.start_full_session(
        session_id="session_001",
        presenter_camera=0,      # دوربین سخنران
        audience_camera=1,      # دوربین حضار
        laptop_microphone=None, # None = auto-detect
        enable_ai_timing=True,
        enable_content_automation=True
    )
    
    if success:
        print("✅ همه ماژول‌ها فعال شدند!")
        
        # دریافت وضعیت
        status = unified.get_module_status()
        print(f"Timer: {status['timer']['active']}")
        print(f"Face AI: {status['face_ai']['active']}")
        print(f"AI Timing: {status['ai_timing']['active']}")
        print(f"Content Automation: {status['content_automation']['active']}")

# اجرا
asyncio.run(start_conference())
```

### روش 2: استفاده دستی (برای کنترل بیشتر)

```python
from modules.timer import TimerController
from modules.media import MediaController
from modules.face_ai import FaceAIController
from modules.display import DisplayController
from modules.ai_timing import AIIntegrationController
from modules.content_automation.integration.main_app_integration import ContentAutomationIntegration
from modules.utils.device_manager import get_device_manager

# 1. پیدا کردن دستگاه‌ها
device_manager = get_device_manager()
presenter_camera = 0
audience_camera = 1
laptop_mic = device_manager.get_laptop_microphone()

# 2. ایجاد controllers
timer = TimerController()
media = MediaController()
face_ai = FaceAIController()
display = DisplayController()
ai_timing = AIIntegrationController(timer)
content_automation = ContentAutomationIntegration(
    media_controller=media,
    display_controller=display
)

# 3. شروع همه به صورت همزمان
async def start_all():
    # Content Automation
    await content_automation.start()
    
    # Face AI
    face_ai.start_analysis(camera_index=audience_camera, fps=15)
    
    # AI Timing
    ai_timing.start_ai_timing(
        presenter_camera=presenter_camera,
        audience_camera=audience_camera,
        enable_voice=True
    )
    
    # Configure microphone
    if laptop_mic:
        ai_timing._voice_detector.stop_detection()
        ai_timing._voice_detector.start_detection(microphone_index=laptop_mic)
    
    # Display
    display.refresh_displays()
    
    print("✅ همه ماژول‌ها فعال شدند!")

asyncio.run(start_all())
```

---

## 4. مثال‌های عملی

### مثال 1: همایش کامل (Full Conference)

```python
"""
مثال کامل: همایش با همه ماژول‌ها
"""

from modules.operator.unified_controller import UnifiedController
import asyncio

async def full_conference_example():
    """همایش کامل با همه قابلیت‌ها"""
    
    # ایجاد Unified Controller
    unified = UnifiedController()
    
    # راه‌اندازی
    unified.initialize_modules()
    
    # شروع همایش
    success = await unified.start_full_session(
        session_id="conference_2025_11_04",
        presenter_camera=0,
        audience_camera=1,
        laptop_microphone=None,  # Auto-detect
        enable_ai_timing=True,
        enable_content_automation=True
    )
    
    if not success:
        print("❌ خطا در شروع همایش")
        return
    
    print("✅ همایش شروع شد!")
    print("\n📊 وضعیت ماژول‌ها:")
    
    status = unified.get_module_status()
    for module, state in status.items():
        if isinstance(state, dict) and 'active' in state:
            icon = "✅" if state['active'] else "❌"
            print(f"  {icon} {module}: {state['active']}")
    
    # دریافت آمار یکپارچه
    stats = unified.get_unified_stats()
    print(f"\n📈 آمار:")
    print(f"  Engagement: {stats.get('ai_timing', {}).get('engagement', 'N/A')}")
    print(f"  Faces Detected: {stats.get('face_ai', {}).get('faces_detected', 0)}")
    
    # ... کار با همایش ...
    
    # توقف
    await unified.stop_full_session()
    print("✅ همایش پایان یافت")

# اجرا
asyncio.run(full_conference_example())
```

### مثال 2: همایش با کنترل دستی

```python
"""
مثال: کنترل دستی همه ماژول‌ها
"""

from modules.timer import TimerController
from modules.media import MediaController
from modules.face_ai import FaceAIController
from modules.ai_timing import AIIntegrationController
from modules.content_automation.integration.main_app_integration import ContentAutomationIntegration
from modules.utils.device_manager import get_device_manager
import asyncio

async def manual_control_example():
    """کنترل دستی همه ماژول‌ها"""
    
    # پیدا کردن دستگاه‌ها
    device_manager = get_device_manager()
    laptop_mic = device_manager.get_laptop_microphone()
    
    print(f"🎤 میکروفون لپ‌تاپ: Index {laptop_mic}")
    
    # ایجاد controllers
    timer = TimerController()
    media = MediaController()
    face_ai = FaceAIController()
    ai_timing = AIIntegrationController(timer)
    content_automation = ContentAutomationIntegration(
        media_controller=media,
        display_controller=None
    )
    
    # شروع به ترتیب
    print("\n1. شروع Content Automation...")
    await content_automation.start()
    
    print("2. شروع Face AI...")
    face_ai.start_analysis(camera_index=1, fps=15)
    
    print("3. شروع AI Timing...")
    ai_timing.start_ai_timing(
        presenter_camera=0,
        audience_camera=1,
        enable_voice=True
    )
    
    if laptop_mic:
        print(f"4. تنظیم میکروفون لپ‌تاپ (Index {laptop_mic})...")
        ai_timing._voice_detector.stop_detection()
        ai_timing._voice_detector.start_detection(microphone_index=laptop_mic)
    
    print("\n✅ همه ماژول‌ها فعال شدند!")
    
    # استفاده...
    import time
    time.sleep(10)  # مثال: 10 ثانیه
    
    # توقف
    print("\n⏹️ توقف همه ماژول‌ها...")
    ai_timing.stop_ai_timing()
    face_ai.stop_analysis()
    await content_automation.stop()
    
    print("✅ همه ماژول‌ها متوقف شدند")

asyncio.run(manual_control_example())
```

---

## 5. هماهنگی بین ماژول‌ها

### Event-Driven Communication

همه ماژول‌ها از Event Bus استفاده می‌کنند:

```python
from modules.content_automation.sync.event_bus import get_event_bus, EventType

event_bus = get_event_bus()

# گوش دادن به رویدادها
def on_timer_completed(event):
    print("Timer completed!")
    # می‌توانید محتوای بعدی را پخش کنید
    # content_automation.schedule_next_content()

event_bus.subscribe(EventType.TIMER_COMPLETED, on_timer_completed)
```

### جریان داده بین ماژول‌ها:

```
Timer Controller
    ↓ (time events)
AI Timing Controller
    ↓ (adaptation signals)
Timer Controller
    ↓ (timer updates)
Media Controller
    ↓ (playback events)
Content Automation
    ↓ (schedule events)
Display Controller
```

---

## 6. Dashboard یکپارچه

### استفاده از Unified Dashboard

```python
from modules.operator.unified_dashboard import UnifiedDashboard
from modules.operator.unified_controller import UnifiedController

# ایجاد Unified Controller
unified = UnifiedController()
unified.initialize_modules()

# ایجاد Dashboard
dashboard = UnifiedDashboard(unified_controller=unified)
dashboard.show()
```

### ویژگی‌های Dashboard:

- ✅ نمایش وضعیت همه ماژول‌ها
- ✅ کنترل مرکزی
- ✅ آمار یکپارچه
- ✅ مدیریت Session
- ✅ Emergency Controls

---

## 7. راهنمای سریع (Quick Start)

### گام 1: نصب وابستگی‌ها

```bash
pip install SpeechRecognition pyaudio aiohttp qasync
```

### گام 2: اجرای برنامه

```bash
python main.py
```

### گام 3: استفاده از Unified Controller

```python
# در main.py یا فایل جدید
from modules.operator.unified_controller import UnifiedController

unified = UnifiedController()
unified.initialize_modules()

# شروع همایش
await unified.start_full_session(
    session_id="my_session",
    presenter_camera=0,
    audience_camera=1,
    enable_ai_timing=True,
    enable_content_automation=True
)
```

---

## 8. چک‌لیست استفاده

### قبل از شروع همایش:

- [ ] همه دستگاه‌ها متصل هستند (دوربین، میکروفون)
- [ ] کتابخانه‌ها نصب هستند
- [ ] مجوزهای Windows فعال هستند
- [ ] محتوای همایش آماده است
- [ ] برنامه زمان‌بندی تنظیم شده است

### در حین همایش:

- [ ] همه ماژول‌ها فعال هستند
- [ ] Timer در حال اجراست
- [ ] Face AI در حال تحلیل است
- [ ] Voice Detection کار می‌کند
- [ ] Content Automation فعال است
- [ ] Display صحیح است

---

## 9. Troubleshooting

### مشکل: یکی از ماژول‌ها شروع نمی‌شود

**راه‌حل:**
```python
status = unified.get_module_status()
for module, state in status.items():
    if not state.get('active'):
        print(f"⚠️ {module} is not active")
        # Check logs for errors
```

### مشکل: هماهنگی بین ماژول‌ها

**راه‌حل:**
- مطمئن شوید Event Bus کار می‌کند
- بررسی کنید همه controllers به درستی initialize شده‌اند
- از Unified Controller استفاده کنید برای هماهنگی خودکار

---

## 10. مثال کامل: یکپارچه‌سازی در main.py

```python
# در main.py
from modules.operator.unified_controller import UnifiedController

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # ... existing code ...
        
        # Initialize Unified Controller
        self.unified_controller = UnifiedController()
        self.unified_controller.initialize_modules(
            timer_controller=self.timer_controller,
            media_controller=self.media_controller,
            face_ai_controller=self.face_ai_controller,
            display_controller=self.display_controller
        )
    
    async def start_conference(self):
        """شروع همایش کامل"""
        success = await self.unified_controller.start_full_session(
            session_id=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            presenter_camera=0,
            audience_camera=1,
            enable_ai_timing=True,
            enable_content_automation=True
        )
        
        if success:
            self.statusBar().showMessage("✅ Conference started with all modules")
        else:
            self.statusBar().showMessage("❌ Failed to start conference")
    
    async def stop_conference(self):
        """توقف همایش"""
        await self.unified_controller.stop_full_session()
        self.statusBar().showMessage("Conference stopped")
```

---

## 📞 پشتیبانی

برای سوالات و مشکلات:
1. بررسی لاگ‌های برنامه
2. استفاده از `get_module_status()` برای تشخیص مشکل
3. تست تک تک ماژول‌ها
4. مراجعه به مستندات هر ماژول

---

**آماده استفاده! 🚀**

