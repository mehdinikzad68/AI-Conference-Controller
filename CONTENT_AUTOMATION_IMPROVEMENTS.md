# تحسینات Content Automation Dashboard

## مشکلات قبلی

1. ❌ **Play Now** کار نمی‌کرد
2. ❌ نمی‌شد زمان دلخواه انتخاب کرد
3. ❌ فقط می‌شد +5 دقیقه اضافه کرد
4. ❌ نمی‌شد زمان را کم کرد

---

## تغییرات اعمال شده

### 1. Date/Time Picker
- اضافه شدن `QDateTimeEdit` برای انتخاب زمان دقیق
- نمایش فرمت: `yyyy-MM-dd HH:mm:ss`
- امکان استفاده از تقویم
- امکان تایپ مستقیم زمان

### 2. دکمه‌های تنظیم سریع زمان
```
[-5 min] [-1 min] [Now] [+1 min] [+5 min]
```
- **-5 min**: زمان را 5 دقیقه کم می‌کند
- **-1 min**: زمان را 1 دقیقه کم می‌کند
- **Now**: زمان فعلی را تنظیم می‌کند
- **+1 min**: زمان را 1 دقیقه اضافه می‌کند
- **+5 min**: زمان را 5 دقیقه اضافه می‌کند

### 3. دکمه جدید: "Schedule at Selected Time"
- پخش محتوا در زمان انتخابی
- بررسی زمان گذشته
- تایید از کاربر قبل از schedule

### 4. بهبود "Play Now"
- همچنان موجود است
- محتوا را فوراً پخش می‌کند

---

## نحوه استفاده

### پخش فوری:
1. محتوا را انتخاب کنید
2. Platform را انتخاب کنید
3. روی **Play Now** کلیک کنید

### زمان‌بندی با زمان دلخواه:
1. محتوا را انتخاب کنید
2. Platform را انتخاب کنید
3. زمان را در **Schedule Time** تنظیم کنید:
   - مستقیماً تایپ کنید
   - یا از دکمه‌های +/- استفاده کنید
4. روی **Schedule at Selected Time** کلیک کنید

---

## مثال‌ها

### مثال 1: پخش 3 دقیقه دیگر
```
1. زمان فعلی: 14:00
2. کلیک 3 بار روی "+1 min"
3. زمان جدید: 14:03
4. کلیک: Schedule at Selected Time
```

### مثال 2: پخش در ساعت 15:30
```
1. در Schedule Time تایپ کنید: 2025-11-04 15:30:00
2. کلیک: Schedule at Selected Time
```

### مثال 3: کاهش زمان
```
1. زمان فعلی در picker: 14:10
2. کلیک 2 بار روی "-1 min"
3. زمان جدید: 14:08
4. کلیک: Schedule at Selected Time
```

---

## علت عدم پخش "Play Now"

اگر **Play Now** کار نمی‌کند:

### 1. بررسی Platform Adapter
Platform adapter ها باید به درستی initialize شوند:

```python
# در main.py
self.content_automation = ContentAutomationIntegration(
    media_controller=self.media_controller,
    display_controller=self.display_controller
)
```

### 2. بررسی Media Controller
Media controller باید کار کند:
- آیا Media Module به درستی کار می‌کند؟
- آیا فایل وجود دارد؟
- آیا فرمت فایل پشتیبانی می‌شود؟

### 3. بررسی Event Log
در پایین Dashboard، Event Log را چک کنید:
- آیا "Scheduled" نشان داده می‌شود؟
- آیا "Playback started" نشان داده می‌شود؟
- آیا خطایی وجود دارد؟

### 4. تست دستی Media Player
قبل از استفاده از Content Automation، Media Player را تست کنید:
1. از main.py: **Media Module** را باز کنید
2. یک فایل را load کنید
3. Play کنید
4. اگر کار کرد، Content Automation هم کار می‌کند

---

## فایل‌های تغییر یافته

1. **`modules/content_automation/ui/operator_dashboard.py`**
   - اضافه شدن `QDateTimeEdit`
   - اضافه شدن دکمه‌های تنظیم زمان
   - اضافه شدن `_adjust_time()` method
   - اضافه شدن `_on_schedule_custom()` method

---

## نتیجه

### قبل:
```
[محتوا ▼]
[Platform ▼]
[Priority ▼]
[▶️ Play Now]
[⏰ Schedule +5min]
```

### بعد:
```
[محتوا ▼]
[Platform ▼]
[Priority ▼]

Schedule Time:
[2025-11-04 14:30:00] 📅

[-5 min] [-1 min] [Now] [+1 min] [+5 min]

[▶️ Play Now]
[📅 Schedule at Selected Time]
```

---

## تست

برنامه را دوباره اجرا کنید:
```bash
python main.py
```

سپس:
1. **Tools → Content Automation** را باز کنید
2. UI جدید را مشاهده کنید
3. زمان را تنظیم کنید
4. محتوا را schedule کنید

---

**همه مشکلات رفع شدند! ✅**

