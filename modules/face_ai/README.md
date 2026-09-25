# Face AI Module - دستورالعمل جامع

## 📋 خلاصه

ماژول Face AI سیستم تحلیل هوشمند احساسات و توجه مخاطبان با استفاده از یادگیری عمیق و بینایی کامپیوتر.

## 🤖 قابلیت‌های هوش مصنوعی

### تشخیص چهره
- **RetinaFace**: بهترین دقت در تشخیص چهره
- **پردازش چندگانه**: تشخیص چند چهره همزمان
- **سرعت بالا**: بهینه‌سازی شده برای real-time

### تحلیل احساسات
- **DeepFace (VGG-Face)**: تشخیص احساسات 7گانه
- **FER (MTCNN)**: Cross-validation احساسات
- **Confidence Scoring**: امتیاز اطمینان برای هر احساس

### Head Pose Estimation
- **dlib 68-point landmarks**: تشخیص نقاط کلیدی صورت
- **زوایای سر**: Yaw, Pitch, Roll
- **جهت توجه**: تشخیص focused/distracted

### آمار و گزارش‌دهی
- **Real-time Statistics**: آمار لحظه‌ای توجه
- **نمودارها**: Pie chart, Bar chart, Timeline
- **Export**: ذخیره گزارش‌ها به عنوان تصویر

## 🏗️ معماری

```
face_ai/
├── face_ai_controller.py        # کنترلر اصلی
├── face_ai_window.py            # رابط کاربری
├── face_analyzer.py             # تحلیلگر DeepFace + FER
├── head_pose_estimator.py       # برآورد وضعیت سر
├── statistics_aggregator.py     # جمع‌آوری آمار
├── dependency_checker.py        # بررسی وابستگی‌ها
└── test_*.py                    # تست‌ها
```

## 🚀 استفاده

### راه‌اندازی اولیه

```python
from modules.face_ai import FaceAIController, FaceAIWindow

# ایجاد کنترلر
controller = FaceAIController()

# شروع تحلیل (دوربین 0، 15 FPS)
controller.start_analysis(camera_index=0, fps=15)

# توقف تحلیل
controller.stop_analysis()
```

### استفاده از رابط کاربری

```python
# ایجاد و نمایش پنجره
face_ai_window = FaceAIWindow(controller=controller)
face_ai_window.show()

# تنظیمات در UI:
# - انتخاب دوربین
# - تنظیم FPS
# - تنظیم نرخ پردازش
```

### دریافت نتایج

```python
# Signal-based results
controller.attention_level_changed.connect(on_attention_change)
controller.faces_detected.connect(on_faces_detected)
controller.frame_analyzed.connect(on_frame_analyzed)

# Direct query
stats = controller.get_statistics()
attention = stats['attention_level']
emotions = stats['emotions']
```

## 📊 خروجی‌ها

### Statistics Dictionary

```python
{
    "attention_level": 0.75,  # 0.0-1.0
    "focused_count": 8,
    "distracted_count": 2,
    "total_faces": 10,
    "emotions": {
        "happy": 5,
        "neutral": 3,
        "sad": 2
    },
    "demographics": {
        "age_avg": 35,
        "gender_male": 6,
        "gender_female": 4
    }
}
```

### Generated Reports

```python
# تولید نمودارها
chart_paths = controller.generate_report_charts("output/reports")

# خروجی:
# - emotion_distribution.png
# - attention_timeline.png
# - demographics_chart.png
```

## ⚙️ تنظیمات

### config.json

```json
{
  "face_ai": {
    "enabled": true,
    "camera_index": 0,
    "sampling_frequency": 2,
    "attention_threshold": 0.5,
    "enable_emotion_detection": true,
    "enable_gaze_tracking": true,
    "chart_type": "bar"
  }
}
```

### بهینه‌سازی عملکرد

```python
# کاهش نرخ پردازش (هر 3 فریم یکبار)
controller.set_processing_rate(3)

# تنظیم FPS پایین‌تر
controller.start_analysis(fps=10)
```

## 🔧 عیب‌یابی

### دوربین یافت نمی‌شود
```bash
# بررسی دسترسی دوربین
python modules/face_ai/test_model_loading.py

# تست دوربین با OpenCV
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

### مدل dlib یافت نمی‌شود
```bash
# دانلود مدل
# از: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
# قرار دهید در: assets/models/shape_predictor_68_face_landmarks.dat
```

### خطای TensorFlow/DeepFace
```bash
# نصب مجدد DeepFace
pip uninstall deepface
pip install deepface --no-cache-dir

# یا استفاده از FER به جای DeepFace
pip install fer
```

### عملکرد پایین
- FPS را کاهش دهید (5-10)
- نرخ پردازش را افزایش دهید (process every 3rd frame)
- رزولوشن دوربین را کم کنید
- از GPU استفاده کنید (اگر موجود است)

## 🎯 بهترین روش‌ها

1. **نور**: نورپردازی مناسب برای تشخیص بهتر
2. **زاویه دوربین**: قرار دادن دوربین روبروی مخاطبان
3. **فاصله**: 1-3 متر فاصله بهینه
4. **FPS**: 10-15 FPS برای real-time کافی است
5. **Confidence**: فقط نتایج با confidence >50% معتبرند

## 📝 API Reference

### FaceAIController

```python
class FaceAIController:
    def start_analysis(camera_index: int, fps: int) -> bool
    def stop_analysis() -> None
    def process_frame(frame: np.ndarray) -> Dict
    def set_attention_threshold(threshold: float) -> None
    def set_processing_rate(n: int) -> None
    def is_analyzing() -> bool
    def get_statistics() -> Dict
    def generate_report_charts(output_dir: str) -> List[str]
```

### Signals

```python
attention_level_changed = pyqtSignal(float)  # 0.0-1.0
reaction_detected = pyqtSignal(str)          # positive/negative/neutral
faces_detected = pyqtSignal(int)             # تعداد چهره
frame_analyzed = pyqtSignal(np.ndarray, list, list)  # فریم و نتایج
statistics_updated = pyqtSignal(dict)        # آمار کامل
```

## 🧪 تست و اعتبارسنجی

```bash
# تست کامل ماژول
python modules/face_ai/test_face_ai.py

# بررسی مدل dlib
python modules/face_ai/test_model_loading.py

# تست واحد
python modules/face_ai/test_unit_tests.py

# بررسی وابستگی‌ها
python modules/face_ai/dependency_checker.py
```

## 📚 وابستگی‌ها

### ضروری
- opencv-python >= 4.8.0
- numpy >= 1.24.0

### هوش مصنوعی
- deepface >= 0.0.79
- fer >= 22.5.0
- dlib >= 19.24.0
- insightface >= 0.7.3 (اختیاری)

### مدل‌های مورد نیاز
- **shape_predictor_68_face_landmarks.dat**: 99 MB
  - محل: `assets/models/`
  - دانلود: http://dlib.net/files/

## 🚨 ملاحظات امنیتی و حریم خصوصی

- **ذخیره‌سازی**: هیچ تصویری ذخیره نمی‌شود (مگر گزارش‌ها)
- **انتقال داده**: تمام پردازش local است
- **رضایت کاربر**: اطمینان از رضایت مخاطبان قبل از تحلیل
- **GDPR**: رعایت قوانین حفاظت از داده‌ها

## 🔄 تاریخچه نسخه‌ها

- v1.0.0: پیاده‌سازی اولیه با DeepFace
- v1.1.0: افزودن FER cross-validation
- v1.2.0: افزودن head pose estimation
- v1.3.0: بهینه‌سازی عملکرد و frame sampling

