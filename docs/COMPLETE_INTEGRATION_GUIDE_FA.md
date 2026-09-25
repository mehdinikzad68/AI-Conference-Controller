# 🎯 راهنمای کامل یکپارچه‌سازی همه ماژول‌ها

## 📋 مقدمه

این راهنما نشان می‌دهد چگونه **همه ماژول‌ها** را به صورت **همزمان و هماهنگ** استفاده کنید.

---

## 🎬 سناریوی کامل: همایش با همه ماژول‌ها

### جریان کار:

```
1. راه‌اندازی Unified Controller
   ↓
2. پیدا کردن دستگاه‌ها (دوربین، میکروفون)
   ↓
3. راه‌اندازی همه ماژول‌ها
   ↓
4. شروع همایش
   ↓
5. نظارت و کنترل
   ↓
6. پایان همایش
```

---

## 🚀 روش 1: استفاده از Unified Controller (پیشنهادی)

### گام 1: ایجاد Unified Controller

```python
from modules.operator.unified_controller import UnifiedController

# در main.py یا هر فایل دیگر
unified = UnifiedController()
unified.initialize_modules(
    timer_controller=self.timer_controller,
    media_controller=self.media_controller,
    face_ai_controller=self.face_ai_controller,
    display_controller=self.display_controller
)
```

### گام 2: شروع همایش کامل

```python
import asyncio

async def start_conference():
    success = await unified.start_full_session(
        session_id="conference_001",
        presenter_camera=0,      # دوربین سخنران
        audience_camera=1,      # دوربین حضار
        laptop_microphone=None, # None = خودکار پیدا می‌کند
        enable_ai_timing=True,  # فعال‌سازی AI Timing
        enable_content_automation=True  # فعال‌سازی Content Automation
    )
    
    if success:
        print("✅ همه ماژول‌ها فعال شدند!")

asyncio.run(start_conference())
```

### گام 3: بررسی وضعیت

```python
# دریافت وضعیت همه ماژول‌ها
status = unified.get_module_status()

for module, state in status.items():
    if state.get('active'):
        print(f"✅ {module}: فعال")
    else:
        print(f"❌ {module}: غیرفعال")
```

### گام 4: دریافت آمار یکپارچه

```python
stats = unified.get_unified_stats()

print(f"Engagement: {stats['ai_timing']['engagement']:.1f}%")
print(f"Faces Detected: {stats['face_ai']['faces_detected']}")
print(f"Timer: {stats['modules']['timer']['time_remaining']}s")
```

---

## 🎮 روش 2: استفاده از Unified Dashboard

### گام 1: باز کردن Dashboard

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

### گام 2: استفاده از Dashboard

1. **تب Overview**: نمایش وضعیت همه ماژول‌ها
2. **تب Control**: کنترل دستگاه‌ها و ماژول‌ها
3. **تب Statistics**: آمار یکپارچه
4. **تب Devices**: مدیریت دستگاه‌ها

### گام 3: شروع همایش از Dashboard

1. به تب **Control** بروید
2. دوربین‌ها و میکروفون را انتخاب کنید
3. روی **Start Full Session** کلیک کنید
4. همه ماژول‌ها به صورت خودکار شروع می‌شوند

---

## 🔗 هماهنگی بین ماژول‌ها

### 1. Timer ↔ AI Timing

```
Timer Controller
    ↓ (timer events)
AI Timing Controller
    ↓ (adaptation signals)
Timer Controller (adjusts time)
```

### 2. Face AI ↔ AI Timing

```
Face AI Controller (analyzes audience)
    ↓ (engagement data)
AI Timing Controller
    ↓ (adaptation)
Timer Controller
```

### 3. Voice Detection ↔ AI Timing

```
Voice Activity Detector (laptop microphone)
    ↓ (speaking/silence)
AI Timing Controller
    ↓ (presenter tracking)
Timer Controller
```

### 4. Content Automation ↔ Media + Display

```
Content Automation Engine
    ↓ (schedule triggers)
Media Controller (plays content)
    ↓ (playback events)
Display Controller (shows on screens)
```

### 5. Symposium ↔ Content Automation

```
Symposium (Agenda Manager)
    ↓ (schedule import)
Content Automation (creates schedules)
    ↓ (auto-playback)
Media + Display
```

---

## 📊 مثال کامل: همایش واقعی

```python
"""
مثال کامل: همایش با همه ماژول‌ها
"""

from modules.operator.unified_controller import UnifiedController
from modules.operator.unified_dashboard import UnifiedDashboard
import asyncio

async def real_conference_example():
    """همایش واقعی با همه قابلیت‌ها"""
    
    # 1. ایجاد Unified Controller
    unified = UnifiedController()
    
    # 2. راه‌اندازی
    unified.initialize_modules()
    
    # 3. پیدا کردن دستگاه‌ها
    from modules.utils.device_manager import get_device_manager
    device_manager = get_device_manager()
    
    cameras = device_manager.get_available_cameras(test=True)
    available_cams = [c for c in cameras if c['available']]
    
    presenter_cam = available_cams[0]['index'] if available_cams else 0
    audience_cam = available_cams[1]['index'] if len(available_cams) > 1 else available_cams[0]['index']
    laptop_mic = device_manager.get_laptop_microphone()
    
    print(f"📷 Presenter Camera: {presenter_cam}")
    print(f"📷 Audience Camera: {audience_cam}")
    print(f"🎤 Laptop Microphone: {laptop_mic}")
    
    # 4. شروع همایش
    session_id = f"conference_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    success = await unified.start_full_session(
        session_id=session_id,
        presenter_camera=presenter_cam,
        audience_camera=audience_cam,
        laptop_microphone=laptop_mic,
        enable_ai_timing=True,
        enable_content_automation=True
    )
    
    if not success:
        print("❌ خطا در شروع همایش")
        return
    
    print("✅ همایش شروع شد!")
    
    # 5. نمایش Dashboard
    dashboard = UnifiedDashboard(unified_controller=unified)
    dashboard.show()
    
    # 6. نظارت (در اینجا می‌توانید کارهای دیگر انجام دهید)
    # ...
    
    # 7. پایان (در صورت نیاز)
    # await unified.stop_full_session()

asyncio.run(real_conference_example())
```

---

## 🎯 چک‌لیست استفاده همزمان

### قبل از شروع:

- [ ] همه دستگاه‌ها متصل هستند
- [ ] کتابخانه‌ها نصب هستند
- [ ] Unified Controller ایجاد شده
- [ ] همه ماژول‌ها initialize شده‌اند
- [ ] دستگاه‌ها (دوربین، میکروفون) پیدا شده‌اند

### در حین همایش:

- [ ] Timer فعال است
- [ ] Face AI در حال تحلیل است
- [ ] Voice Detection کار می‌کند
- [ ] AI Timing فعال است
- [ ] Content Automation فعال است
- [ ] Display صحیح است

---

## 📝 استفاده در main.py

```python
# در MainWindow.__init__()
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
    
    # اضافه کردن دکمه برای شروع همایش کامل
    def show_unified_dashboard(self):
        """Show unified dashboard."""
        from modules.operator.unified_dashboard import UnifiedDashboard
        
        if not hasattr(self, '_unified_dashboard'):
            self._unified_dashboard = UnifiedDashboard(
                unified_controller=self.unified_controller
            )
        
        self._unified_dashboard.show()
        self._unified_dashboard.raise_()
        self._unified_dashboard.activateWindow()
```

---

## 🎓 مثال‌های عملی

### مثال 1: همایش ساده (بدون AI)

```python
# فقط Timer + Media
unified = UnifiedController()
unified.initialize_modules()

# شروع فقط Timer
unified.timer_controller.start(300)  # 5 minutes

# پخش رسانه
unified.media_controller.load_media("video.mp4")
unified.media_controller.play()
```

### مثال 2: همایش با AI (بدون Content Automation)

```python
# Timer + AI Timing + Face AI
unified = UnifiedController()
unified.initialize_modules()

# شروع AI Timing
unified.ai_integration_controller.start_ai_timing(
    presenter_camera=0,
    audience_camera=1,
    enable_voice=True
)

# شروع Face AI
unified.face_ai_controller.start_analysis(camera_index=1, fps=15)
```

### مثال 3: همایش کامل

```python
# همه ماژول‌ها
await unified.start_full_session(
    session_id="full_conference",
    presenter_camera=0,
    audience_camera=1,
    enable_ai_timing=True,
    enable_content_automation=True
)
```

---

## 🔧 Troubleshooting

### مشکل: یکی از ماژول‌ها شروع نمی‌شود

```python
status = unified.get_module_status()
for module, state in status.items():
    if not state.get('active'):
        print(f"⚠️ {module} is not active")
        # Check logs
```

### مشکل: هماهنگی بین ماژول‌ها نیست

- مطمئن شوید همه controllers به Unified Controller پاس داده شده‌اند
- از Unified Controller برای شروع استفاده کنید
- Event Bus را بررسی کنید

---

## 📚 فایل‌های مرتبط

1. `modules/operator/unified_controller.py` - کنترلر مرکزی
2. `modules/operator/unified_dashboard.py` - Dashboard یکپارچه
3. `docs/UNIFIED_MODULES_GUIDE.md` - راهنمای کامل
4. `examples/unified_modules_example.py` - مثال‌های کامل

---

**آماده استفاده! 🚀**

