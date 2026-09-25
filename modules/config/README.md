# Config Module - دستورالعمل جامع

## 📋 خلاصه

ماژول Config سیستم جامع مدیریت تنظیمات، پروفایل‌ها و دارایی‌های برنامه.

## ✨ قابلیت‌ها

### مدیریت تنظیمات
- **JSON Persistence**: ذخیره‌سازی در فایل JSON
- **Nested Configuration**: پشتیبانی از تنظیمات تو در تو
- **Default Values**: مقادیر پیش‌فرض برای همه ماژول‌ها
- **Hot Reload**: اعمال تغییرات بدون restart

### سیستم پروفایل
- **Create/Load/Delete**: مدیریت کامل پروفایل‌ها
- **Export/Import**: انتقال پروفایل‌ها (JSON)
- **Metadata**: نام، توضیحات، تاریخ
- **Profile Switching**: تعویض سریع بین پروفایل‌ها

### Auto-Backup
- **Rolling Backups**: نگهداری N بکاپ اخیر
- **Timestamped**: نام‌گذاری با تاریخ و ساعت
- **Automatic Cleanup**: حذف خودکار بکاپ‌های قدیمی
- **Configurable Interval**: فاصله زمانی قابل تنظیم

### رابط کاربری
- **Tabbed Interface**: تنظیمات دسته‌بندی شده
- **Real-time Preview**: پیش‌نمایش لحظه‌ای تغییرات
- **Asset Management**: مدیریت لوگو و فایل‌ها
- **Sound Testing**: تست صداهای هشدار

## 🏗️ معماری

```
config/
├── config_manager.py          # مدیریت اصلی
├── config_profiles.py         # مدیریت پروفایل‌ها
├── config_window.py           # رابط کاربری
├── auto_backup.py             # سیستم بکاپ خودکار
└── test_config.py             # تست
```

## 🚀 استفاده

### مدیریت پایه

```python
from modules.config import ConfigManager

# ایجاد manager
config = ConfigManager()
config.load_config()

# دریافت مقدار
duration = config.get("timer.default_duration")
# یا با default
theme = config.get("general.theme", default="dark")

# تنظیم مقدار
config.set("timer.default_duration", 600)
config.save_config()
```

### تنظیمات تو در تو

```python
# ایجاد ساختار تو در تو
config.set("custom.module.setting", "value")

# دریافت با نقطه‌گذاری
value = config.get("custom.module.setting")
```

### مدیریت پروفایل

```python
from modules.config import ProfileManager

profile_mgr = ProfileManager()

# ایجاد پروفایل
profile_mgr.create_profile(
    name="Conference",
    description="Settings for conference events",
    config_data=config.get_all_config()
)

# بارگذاری پروفایل
conf = profile_mgr.load_profile("Conference")
config.set_all_config(conf)

# Export
profile_mgr.export_profile("Conference", "conference_profile.json")

# Import
profile_mgr.import_profile("new_conference.json")
```

### Auto-Backup

```python
from modules.config import AutoBackupManager

backup_mgr = AutoBackupManager(
    config_file="config.json",
    backup_dir="assets/backups",
    interval_ms=300000,  # 5 دقیقه
    max_backups=10
)

# بکاپ دستی
backup_path = backup_mgr.create_backup()

# بازیابی از بکاپ
backup_mgr.restore_backup("assets/backups/config_backup_20251102_123456.json")

# لیست بکاپ‌ها
backups = backup_mgr.get_backup_list()
```

## ⚙️ ساختار config.json

```json
{
  "timer": {
    "default_duration": 300,
    "mode": "countdown",
    "show_warning": true,
    "warning_threshold": 120,
    "color_scheme": "gradient",
    "font_size": 72
  },
  "media": {
    "auto_play": false,
    "auto_advance": false,
    "default_transition": "fade",
    "maintain_aspect_ratio": true
  },
  "face_ai": {
    "enabled": false,
    "camera_index": 0,
    "sampling_frequency": 2,
    "attention_threshold": 0.5
  },
  "display": {
    "mode": "extended",
    "auto_detect": true,
    "target_resolution": {
      "width": 1920,
      "height": 1080
    }
  },
  "sound": {
    "warning_enabled": true,
    "warning_volume": 80,
    "finished_enabled": true,
    "finished_volume": 80
  },
  "general": {
    "language": "en",
    "theme": "dark",
    "font_size": 12,
    "auto_save": true,
    "backup_interval": 300
  },
  "assets": {
    "logo_path": "",
    "branding_enabled": false,
    "custom_colors": {
      "primary": "#ffffff",
      "secondary": "#000000"
    }
  }
}
```

## 🔧 رابط کاربری

### تب‌های تنظیمات

1. **Timer**: مدت، حالت، رنگ‌ها، فونت، هشدارها
2. **Media**: Auto-play, transitions, aspect ratio
3. **Face AI**: دوربین، نمونه‌برداری، آستانه‌ها
4. **Display**: حالت، رزولوشن، تشخیص خودکار
5. **Sound & Alerts**: صداهای هشدار، حجم، فایل‌های سفارشی
6. **General**: زبان، تم، فونت، auto-save
7. **Assets**: لوگو، برند، رنگ‌های سفارشی

### ویژگی‌های UI

- **Real-time Preview**: تغییرات فوری نمایش داده می‌شوند
- **Profile Dropdown**: انتخاب سریع پروفایل
- **Save/Cancel**: ذخیره یا لغو تغییرات
- **Test Buttons**: تست صداها
- **Browse Dialogs**: انتخاب فایل برای لوگو و صداها

## 🎯 بهترین روش‌ها

### سازماندهی پروفایل

```
Default          # تنظیمات عمومی
Conference       # کنفرانس‌های بزرگ
Workshop         # کارگاه‌های کوچک
Webinar          # رویدادهای آنلاین
Testing          # تست و توسعه
```

### فاصله بکاپ توصیه شده

- **Production**: هر 5 دقیقه (300 ثانیه)
- **Development**: هر 2 دقیقه (120 ثانیه)
- **Testing**: غیرفعال (0)

### مدیریت بکاپ

- نگهداری 10 بکاپ اخیر کافی است
- بکاپ‌های قدیمی خودکار حذف می‌شوند
- قبل از تغییرات بزرگ، بکاپ دستی بگیرید

## 📝 API Reference

### ConfigManager

```python
class ConfigManager:
    def load_config() -> None
    def save_config(create_backup: bool = True) -> None
    def get(key: str, default=None) -> Any
    def set(key: str, value: Any) -> None
    def get_all_config() -> dict
    def set_all_config(config_data: dict) -> None
    def get_asset_path(asset_name: str) -> Path
    def set_assets_path(path: str) -> None
```

### ProfileManager

```python
class ProfileManager:
    def create_profile(name: str, description: str, config_data: dict) -> bool
    def load_profile(name: str) -> dict
    def delete_profile(name: str) -> bool
    def list_profiles() -> List[str]
    def export_profile(name: str, export_path: str) -> bool
    def import_profile(import_path: str) -> bool
```

### AutoBackupManager

```python
class AutoBackupManager:
    def create_backup() -> Optional[str]
    def restore_backup(backup_path: str) -> bool
    def get_backup_list() -> List[str]
    def set_interval(interval_ms: int) -> None
    def set_max_backups(max_backups: int) -> None
```

## 🧪 تست

```bash
# تست کامل ماژول
python modules/config/test_config.py

# تست از طریق UI
# 1. اجرای برنامه اصلی
# 2. کلیک Configuration
# 3. تغییر تنظیمات و ذخیره
# 4. تست پروفایل‌ها
```

## 🔄 Migration

### ارتقا از نسخه قدیمی

```python
# بارگذاری config قدیمی
old_config = json.load(open("old_config.json"))

# تبدیل به ساختار جدید
new_config = migrate_config(old_config)

# ذخیره
config.set_all_config(new_config)
config.save_config()
```

## 📚 وابستگی‌ها

- PyQt6 >= 6.6.0
- Python json (built-in)
- pathlib (built-in)

## 🔄 تاریخچه نسخه‌ها

- v1.0.0: پیاده‌سازی اولیه
- v1.1.0: افزودن سیستم پروفایل
- v1.2.0: افزودن auto-backup
- v1.3.0: بهبود رابط کاربری با tabbed interface

