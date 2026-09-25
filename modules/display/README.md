# Display Module - دستورالعمل جامع

## 📋 خلاصه

ماژول Display مسئول مدیریت خروجی به نمایشگرهای خارجی، پروژکتورها و تلویزیون‌ها برای ارائه‌های حرفه‌ای.

## ✨ قابلیت‌ها

### مدیریت نمایشگر
- **تشخیص خودکار**: شناسایی تمام نمایشگرهای متصل
- **روت کردن محتوا**: هدایت هر ماژول به نمایشگر مخصوص
- **پیش‌نمایش**: تست نمایشگرها با الگوهای آزمایشی
- **Fullscreen**: حالت تمام‌صفحه برای هر نمایشگر

### اعتبارسنجی Widget
- **Pre-routing Validation**: بررسی قبل از اختصاص
- **Post-routing Validation**: تایید پس از اختصاص
- **Lifecycle Checks**: بررسی وضعیت widget
- **پیام‌های خطای واضح**: راهنمای گام‌به‌گام رفع مشکل

### یکپارچگی OBS
- **عناوین بهینه**: Window title برای Window Capture
- **تم تاریک**: بهینه برای پروژکتورها
- **مقیاس‌پذیری**: تنظیم خودکار با رزولوشن

## 🏗️ معماری

```
display/
├── display_controller.py         # کنترلر اصلی
├── display_manager_window.py     # رابط مدیریت
├── display_output.py             # پنجره خروجی هر نمایشگر
├── test_display.py               # تست یکپارچگی
└── test_display_widget_error.py  # تست مدیریت خطا
```

## 🚀 استفاده

### شناسایی نمایشگرها

```python
from modules.display import DisplayController

controller = DisplayController()
controller.refresh_displays()

# دریافت لیست نمایشگرها
screens = controller.get_available_screens()
print(f"Found {len(screens)} displays")
```

### روت کردن محتوا

```python
from modules.display import DisplayOutput

# ایجاد خروجی برای نمایشگر 1
output = DisplayOutput(screen_index=1, display_name="Projector")

# روت کردن timer widget
from modules.timer import TimerWindow
timer_window = TimerWindow()
output.route_content(timer_window.timer_widget, "Timer")

# Fullscreen
output.enter_fullscreen()
```

### استفاده از Display Manager

```python
from modules.display import DisplayManagerWindow

manager = DisplayManagerWindow()
manager.show()

# در UI:
# 1. انتخاب نمایشگر از لیست
# 2. انتخاب نوع محتوا (Timer, Media, Face AI)
# 3. کلیک "Route Content"
# 4. استفاده از "Validate All Outputs" قبل از event
```

## ⚙️ تنظیمات

### config.json

```json
{
  "display": {
    "mode": "extended",
    "auto_detect": true,
    "target_resolution": {
      "width": 1920,
      "height": 1080
    }
  }
}
```

## 🔧 عیب‌یابی

### نمایشگر شناسایی نمی‌شود
```python
# Refresh displays
controller.refresh_displays()

# بررسی در Windows Display Settings
# اطمینان از اتصال فیزیکی
# Extend desktop mode (not Mirror)
```

### خطای "Widget Not Available"
1. ماژول منبع (Timer, Media, etc) را باز کنید
2. اطمینان از مشاهده پنجره
3. دوباره محتوا را route کنید

### خطای "Invalid Widget"
1. Close و reopen ماژول منبع
2. Widget را دوباره به display اختصاص دهید
3. از "Validate All Outputs" استفاده کنید

### Fullscreen کار نمی‌کند
- ابتدا widget validation را fix کنید
- سپس fullscreen را فعال کنید
- Esc برای خروج از fullscreen

## 🎯 بهترین روش‌ها

### Setup Workflow

```
1. ماژول‌های منبع را باز کنید (Timer, Media, Face AI)
2. Display Manager را باز کنید
3. محتوا را به نمایشگرها route کنید
4. "Validate All Outputs" را اجرا کنید
5. از Preview mode برای تست استفاده کنید
6. Event را شروع کنید
```

### توصیه‌های سخت‌افزاری

- **Projector**: معمولاً Display 1 یا Primary
- **Side TVs**: Display 2, Display 3 برای محتوای تکمیلی
- **Laptop Screen**: کنترل interface
- **Extended Mode**: نه Mirror mode
- **کابل‌ها**: HDMI یا DisplayPort (نه VGA)

### OBS Studio Integration

```
1. هر Display Output یک Window جداگانه
2. در OBS: Add Source → Window Capture
3. انتخاب "Display Output - [Display Name]"
4. تنظیمات: 1920x1080, 30 FPS
5. نمایشگر را fullscreen کنید قبل از capture
```

## 📝 API Reference

### DisplayController

```python
class DisplayController:
    def refresh_displays() -> None
    def get_available_screens() -> List[QScreen]
    def get_primary_screen() -> QScreen
    def set_extended_mode(enabled: bool) -> None
    def move_window_to_display(window, screen_index: int) -> None
    def setup_fullscreen_on_display(window, screen_index: int) -> None
```

### DisplayOutput

```python
class DisplayOutput(QMainWindow):
    def route_content(widget: QWidget, content_type: str) -> bool
    def validate_widget() -> bool
    def enter_fullscreen() -> bool
    def exit_fullscreen() -> None
    def show_preview() -> None
    def get_display_name() -> str
```

### Signals

```python
display_connected = pyqtSignal(QScreen)
display_disconnected = pyqtSignal(QScreen)
display_mode_changed = pyqtSignal(str)
content_routed = pyqtSignal(str)  # content_type
validation_failed = pyqtSignal(str)  # error_message
```

## 🧪 تست

```bash
# تست کامل با demo content
python modules/display/test_display.py

# تست widget error handling
python modules/display/test_display_widget_error.py

# تست چند نمایشگر
# (نیاز به 2+ نمایشگر متصل)
```

## 🎬 سناریوهای کاربردی

### کنفرانس 2 نمایشگر

```
Display 1 (Projector): Media + Timer Overlay
Display 2 (Side TV): Face AI Statistics
Laptop: Control Interface
```

### کنفرانس 3 نمایشگر

```
Display 1: Main Slides (Media)
Display 2: Timer (Large)
Display 3: Audience Analysis (Face AI)
```

### تک نمایشگر

```
Display 1: Media با Timer Overlay
(همه محتوا در یک نمایشگر)
```

## 📚 وابستگی‌ها

- PyQt6 >= 6.6.0
- (هیچ وابستگی خارجی دیگر)

## 🔄 تاریخچه نسخه‌ها

- v1.0.0: پیاده‌سازی اولیه
- v1.1.0: افزودن widget validation
- v1.2.0: بهبود error handling
- v1.3.0: Pre-launch validation system

