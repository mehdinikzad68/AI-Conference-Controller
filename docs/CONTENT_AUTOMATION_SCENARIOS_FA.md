# 🎬 سناریوهای عملی Content Automation

## 📅 سناریو 1: همایش یک روزه (Hybrid)

### برنامه همایش:
```
09:00 - افتتاحیه
09:15 - سخنرانی اول
10:30 - استراحت
10:45 - سخنرانی دوم
12:00 - ناهار
13:30 - سخنرانی سوم
15:00 - اختتامیه
```

### پیکربندی Content Automation:

#### 1. کلیپ افتتاحیه (09:00)
```
محتوا: opening-clip.mp4
Platform: hall+skyroom
Priority: high
Time: 2025-11-04 09:00:00

📊 دلیل انتخاب:
- همه شرکت‌کنندگان (حضوری + آنلاین) باید ببینند
- محتوای رسمی و مهم
- نیاز به همگام‌سازی دقیق
```

#### 2. لوگوی حامیان (09:14)
```
محتوا: sponsors-logo.png
Platform: hall+skyroom
Priority: normal
Time: 2025-11-04 09:14:00
Duration: 1 min

📊 دلیل انتخاب:
- نمایش به همه شرکت‌کنندگان
- برندینگ و تبلیغات
```

#### 3. اسلاید سخنرانی اول (09:15)
```
محتوا: presentation-1.pdf
Platform: hall
Priority: high
Time: 2025-11-04 09:15:00

📊 دلیل انتخاب:
- سخنران در سالن حضور دارد
- شرکت‌کنندگان آنلاین سخنران را می‌بینند
- اسلایدها فقط برای حضار سالن
```

#### 4. ویدیو استراحت (10:30)
```
محتوا: break-video.mp4
Platform: hall+skyroom
Priority: normal
Time: 2025-11-04 10:30:00
Duration: 15 min

📊 دلیل انتخاب:
- زمان استراحت
- محتوای سرگرم‌کننده برای همه
```

#### 5. اعلان اضطراری (در صورت نیاز)
```
محتوا: emergency-announcement.mp4
Platform: hall+skyroom
Priority: emergency
Action: Play Now (فوری)

📊 دلیل انتخاب:
- اطلاع‌رسانی فوری
- باید فوراً پخش شود
- همه باید ببینند
```

---

## 🎓 سناریو 2: کارگاه آموزشی آنلاین

### وضعیت:
- همه شرکت‌کنندگان آنلاین
- بدون حضار فیزیکی
- محتوای آموزشی ویدیویی

### پیکربندی:

#### 1. ویدیو معرفی (14:00)
```
محتوا: intro-video.mp4
Platform: skyroom
Priority: high
Time: 2025-11-04 14:00:00
```

#### 2. ویدیو آموزشی 1 (14:05)
```
محتوا: tutorial-1.mp4
Platform: skyroom
Priority: high
Time: 2025-11-04 14:05:00
Duration: 20 min
```

#### 3. ویدیو آموزشی 2 (14:25)
```
محتوا: tutorial-2.mp4
Platform: skyroom
Priority: high
Time: 2025-11-04 14:25:00
Duration: 20 min
```

#### 4. Q&A Session (14:45)
```
محتوا: qa-guidelines.pdf
Platform: skyroom
Priority: normal
Time: 2025-11-04 14:45:00
```

---

## 🏢 سناریو 3: همایش چند سالنی

### وضعیت:
- 3 سالن فیزیکی
- شرکت‌کنندگان آنلاین
- محتوای مشترک + اختصاصی

### پیکربندی:

#### محتوای مشترک (همه سالن‌ها + آنلاین):

```
1. افتتاحیه (09:00)
   Platform: hall+skyroom
   نمایش در: سالن A, B, C + Skyroom

2. کلیپ حامیان (09:15)
   Platform: hall+skyroom
   نمایش در: سالن A, B, C + Skyroom
```

#### محتوای اختصاصی:

**سالن A (تخصصی):**
```
محتوا: presentation-tech.pdf
Platform: hall
Time: 10:00
نمایش فقط در: سالن A
```

**سالن B (عمومی):**
```
محتوا: presentation-general.pdf
Platform: hall
Time: 10:00
نمایش فقط در: سالن B
```

**آنلاین:**
```
محتوا: online-presentation.pdf
Platform: skyroom
Time: 10:00
نمایش فقط در: Skyroom
```

---

## 🚨 سناریو 4: مدیریت بحران

### موقعیت:
- در وسط سخنرانی مشکلی پیش آمده
- نیاز به اطلاع‌رسانی فوری

### اقدامات:

#### 1. توقف محتوای جاری
```
Dashboard → EMERGENCY STOP
```

#### 2. پخش اطلاعیه
```
محتوا: emergency-notice.mp4
Platform: hall+skyroom
Priority: emergency
Action: Play Now

نتیجه:
- فوراً پخش می‌شود
- همه (حضوری + آنلاین) می‌بینند
- Schedule های دیگر متوقف می‌شوند
```

#### 3. بازگشت به برنامه عادی
```
- EMERGENCY STOP را لغو کنید
- Schedule های بعدی ادامه می‌یابند
```

---

## 📊 سناریو 5: همایش با استراحت‌های برنامه‌ریزی شده

### برنامه:
```
09:00 - شروع
10:30 - استراحت 1 (15 دقیقه)
12:00 - ناهار (60 دقیقه)
14:00 - ادامه
15:30 - استراحت 2 (15 دقیقه)
17:00 - پایان
```

### محتوای استراحت‌ها:

#### استراحت 1 (10:30)
```
1. لوگوی حامیان
   Platform: hall+skyroom
   Time: 10:30:00
   Duration: 5 min

2. ویدیو تبلیغاتی
   Platform: hall+skyroom
   Time: 10:35:00
   Duration: 3 min

3. اسلایدشو تصاویر
   Platform: hall+skyroom
   Time: 10:38:00
   Duration: 7 min
```

#### ناهار (12:00)
```
1. موسیقی ملایم (صدا)
   Platform: hall+skyroom
   Time: 12:00:00
   Duration: 60 min

2. اسلایدشو طبیعت
   Platform: hall+skyroom
   Time: 12:00:00
   Duration: 60 min
```

---

## 🎯 بهترین روش‌ها (Best Practices)

### 1. زمان‌بندی
```
✅ DO: 
- 2-3 دقیقه قبل از شروع محتوا را schedule کنید
- Buffer time در نظر بگیرید

❌ DON'T:
- دقیقاً در زمان شروع schedule نکنید
- محتوای پشت سر هم بدون فاصله
```

### 2. Priority Management
```
Priority: emergency
- فقط برای موارد واقعاً اضطراری
- اعلان‌های فوری
- مشکلات بحرانی

Priority: high
- محتوای رسمی همایش
- کلیپ افتتاحیه/اختتامیه
- ویدیوهای اصلی

Priority: normal
- اسلایدها
- تصاویر
- محتوای معمولی
```

### 3. Platform Selection
```
hall+skyroom:
✅ محتوای رسمی
✅ کلیپ افتتاحیه/اختتامیه
✅ اطلاعیه‌های مهم
✅ محتوای تبلیغاتی

hall:
✅ اسلایدهای سخنرانی حضوری
✅ محتوای تعاملی سالن
✅ نمایش محلی

skyroom:
✅ محتوای آموزشی آنلاین
✅ ویدیوهای اختصاصی آنلاین
✅ پرسش و پاسخ آنلاین
```

---

## 📋 Checklist قبل از همایش

### یک روز قبل:
- [ ] همه محتواها آپلود شده
- [ ] محتواها validate شده (بدون خطا)
- [ ] Schedule های اصلی ایجاد شده
- [ ] Platform انتخاب شده (hall/skyroom/hall+skyroom)
- [ ] Priority تنظیم شده

### صبح روز همایش:
- [ ] تست Hall (پروژکتور/نمایشگر)
- [ ] تست Skyroom (اتصال API)
- [ ] همگام‌سازی زمانی
- [ ] محتوای اضطراری آماده

### حین همایش:
- [ ] Event Log را monitor کنید
- [ ] آماده باش برای Play Now
- [ ] محتوای اضطراری در دسترس
- [ ] EMERGENCY STOP در صورت نیاز

---

## 🔧 Template های آماده

### Template 1: همایش ساده (3 ساعته)
```
09:00 | opening.mp4      | hall+skyroom | high
09:05 | sponsors.png     | hall+skyroom | normal
09:10 | talk-1.pdf       | hall         | high
10:00 | break-video.mp4  | hall+skyroom | normal
10:15 | talk-2.pdf       | hall         | high
11:00 | closing.mp4      | hall+skyroom | high
```

### Template 2: وبینار آنلاین (2 ساعته)
```
14:00 | intro.mp4        | skyroom | high
14:05 | tutorial-1.mp4   | skyroom | high
14:30 | break-slide.png  | skyroom | normal
14:35 | tutorial-2.mp4   | skyroom | high
15:00 | qa-guide.pdf     | skyroom | normal
15:45 | outro.mp4        | skyroom | high
```

### Template 3: همایش چند روزه
```
Day 1:
09:00 | day1-opening.mp4  | hall+skyroom | high
...
17:00 | day1-closing.mp4  | hall+skyroom | high

Day 2:
09:00 | day2-opening.mp4  | hall+skyroom | high
...
17:00 | day2-closing.mp4  | hall+skyroom | high
```

---

**آماده برگزاری همایش! 🎉**

