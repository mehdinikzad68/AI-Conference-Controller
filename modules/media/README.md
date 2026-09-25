# Media Module - دستورالعمل جامع

## 📋 خلاصه

ماژول Media مسئول پخش و نمایش انواع محتوای چندرسانه‌ای شامل ویدیو، تصاویر، PDF و ارائه‌ها است.

## ✨ قابلیت‌ها

### پخش رسانه‌ها
- **ویدیو**: پشتیبانی از MP4, AVI, MOV
- **تصاویر**: JPG, PNG, BMP, GIF
- **PDF**: رندرینگ با کیفیت بالا (200+ DPI)
- **PowerPoint**: پشتیبانی محدود (نیاز به تبدیل)

### افکت‌های انتقال
- **Fade**: انتقال نرم با تغییر شفافیت
- **Slide**: انیمیشن کشویی افقی
- **Blur**: افکت محو شدن و واضح شدن
- **سرعت قابل تنظیم**: 50-1000ms

### Timer Overlay
- **نمایش تایمر روی محتوا**: قابلیت اضافه کردن تایمر شناور
- **موقعیت‌های از پیش تعریف شده**: 6 حالت مختلف
- **قابل کشیدن**: تغییر موقعیت با drag-and-drop
- **خودکار پنهان‌سازی**: پس از اتمام تایمر

## 🏗️ معماری

```
media/
├── media_controller.py          # کنترلر اصلی
├── media_window.py              # رابط کاربری
├── media_display_widget.py      # ویجت نمایش
├── media_item.py                # مدل آیتم‌های رسانه
├── pdf_viewer.py                # رندرینگ PDF
├── timer_overlay_widget.py      # overlay تایمر
└── test_*.py                    # تست‌ها
```

## 🚀 استفاده

### بارگذاری فایل

```python
from modules.media import MediaController, MediaWindow

# ایجاد کنترلر
media_controller = MediaController()

# بارگذاری فایل
media_controller.load_file("path/to/video.mp4")

# شروع پخش
media_controller.play()
```

### استفاده از رابط کاربری

```python
media_window = MediaWindow()
media_window.show()
# Drag and drop فایل‌ها یا Browse Files کلیک کنید
```

### افکت‌های انتقال

```python
# تنظیم نوع افکت
media_display.set_transition_type("fade")  # یا "slide", "blur", "none"

# تنظیم سرعت (میلی‌ثانیه)
media_display.set_transition_duration(300)
```

## 📊 مثال‌های کاربردی

### پخش PDF

```python
# بارگذاری PDF
media_controller.load_file("presentation.pdf")

# ناوبری صفحات
media_window.next_page()      # صفحه بعد
media_window.previous_page()  # صفحه قبل
```

### Timer Overlay

```python
# فعال‌سازی overlay
media_window.show_timer_overlay(True)

# تنظیم موقعیت
media_window.set_overlay_position("top_right")

# شروع تایمر (30 دقیقه)
media_window.start_overlay_timer(30)
```

## ⚙️ تنظیمات

### config.json

```json
{
  "media": {
    "auto_play": false,
    "auto_advance": false,
    "fullscreen_on_play": false,
    "default_transition": "fade",
    "maintain_aspect_ratio": true
  }
}
```

## 🔧 عیب‌یابی

### مشکلات رایج

**PDF نمایش داده نمی‌شود**
- اطمینان حاصل کنید PyMuPDF نصب است: `pip install PyMuPDF`
- فایل PDF معتبر و سالم است

**ویدیو پخش نمی‌شود**
- کدک‌های مورد نیاز نصب باشند
- از فرمت‌های استاندارد (MP4, H.264) استفاده کنید

**افکت‌های انتقال کند هستند**
- سرعت انتقال را کاهش دهید
- اندازه تصاویر را کوچک‌تر کنید

## 🎯 بهترین روش‌ها

1. **فرمت‌ها**: ترجیحاً از MP4 و PDF استفاده کنید
2. **اندازه فایل**: تصاویر بزرگ خودکار فشرده می‌شوند
3. **Fullscreen**: F11 برای حالت تمام‌صفحه
4. **OBS Integration**: Window Capture از Media Window

## 📝 API Reference

### MediaController

```python
class MediaController:
    def load_file(path: str) -> None
    def play() -> None
    def pause() -> None
    def stop() -> None
    def next_slide() -> None
    def previous_slide() -> None
    def is_playing() -> bool
    def get_current_file() -> str
```

### MediaWindow

```python
class MediaWindow(QMainWindow):
    def show_timer_overlay(enabled: bool) -> None
    def set_transition_type(type: str) -> None
    def next_page() -> None
    def previous_page() -> None
```

## 🧪 تست

```bash
# تست standalone
python modules/media/test_media.py

# تست PDF viewer
python modules/media/test_pdf_viewer.py

# تست افکت‌های انتقال
python modules/media/test_transition_effects.py

# تست timer overlay
python modules/media/test_media_overlay.py
```

## 📚 وابستگی‌ها

- PyQt6 >= 6.6.0
- PyQt6-Multimedia >= 6.6.0
- PyMuPDF >= 1.23.0
- opencv-python >= 4.8.0
- Pillow >= 10.0.0

## 🔄 تاریخچه نسخه‌ها

- v1.0.0: پیاده‌سازی اولیه با پشتیبانی کامل
- v1.1.0: افزودن Timer Overlay
- v1.2.0: افزودن افکت‌های انتقال پیشرفته

