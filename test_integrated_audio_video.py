"""
Integrated Audio-Video Analysis Test

تست یکپارچگی تحلیل صدا و تصویر

ترکیب:
- 🎥 Face AI (تحلیل تصویر دوربین)
- 🎤 Voice Detection (تحلیل صدای میکروفون)
"""

import sys
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QGroupBox, QTextEdit, QComboBox, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from modules.face_ai.face_ai_controller import FaceAIController
from modules.ai_timing.voice_activity_detector import VoiceActivityDetector
import speech_recognition as sr


class IntegratedAnalysisWindow(QMainWindow):
    """پنجره تحلیل یکپارچه صدا و تصویر"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎬 Integrated Audio-Video Analysis - تحلیل یکپارچه")
        self.setMinimumSize(1200, 800)
        
        # Controllers
        self.face_ai = FaceAIController()
        self.voice_detector = VoiceActivityDetector()
        
        # State
        self.is_running = False
        
        # Stats
        self.stats = {
            'video': {
                'faces': 0,
                'attention': 0.0,
                'emotion': 'unknown'
            },
            'audio': {
                'speaking': False,
                'silence_duration': 0
            },
            'combined': {
                'presenter_quality': 0.0,
                'audience_engagement': 0.0
            }
        }
        
        self.init_ui()
        self.connect_signals()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_stats)
        self.update_timer.setInterval(1000)  # هر 1 ثانیه
    
    def init_ui(self):
        """ساخت رابط کاربری"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # عنوان
        title = QLabel("🎬 تحلیل یکپارچه صدا و تصویر")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # تنظیمات
        settings_group = self.create_settings_group()
        layout.addWidget(settings_group)
        
        # آمار
        stats_layout = QHBoxLayout()
        
        # Video stats
        self.video_group = self.create_video_stats_group()
        stats_layout.addWidget(self.video_group)
        
        # Audio stats
        self.audio_group = self.create_audio_stats_group()
        stats_layout.addWidget(self.audio_group)
        
        # Combined stats
        self.combined_group = self.create_combined_stats_group()
        stats_layout.addWidget(self.combined_group)
        
        layout.addLayout(stats_layout)
        
        # لاگ
        log_label = QLabel("📋 لاگ رویدادها:")
        log_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                font-family: 'Courier New';
                font-size: 11px;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.log_text)
    
    def create_settings_group(self):
        """گروه تنظیمات"""
        group = QGroupBox("⚙️ تنظیمات")
        layout = QHBoxLayout()
        
        # Camera
        camera_label = QLabel("🎥 دوربین:")
        self.camera_combo = QComboBox()
        self.camera_combo.addItems(["Camera 0", "Camera 1", "Camera 2"])
        
        # Microphone
        mic_label = QLabel("🎤 میکروفون:")
        self.mic_combo = QComboBox()
        try:
            mics = sr.Microphone.list_microphone_names()
            self.mic_combo.addItems([f"Mic {i}: {name[:40]}" for i, name in enumerate(mics)])
        except:
            self.mic_combo.addItem("میکروفون پیش‌فرض")
        
        # Start/Stop buttons
        self.start_btn = QPushButton("▶️ شروع تحلیل")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        self.start_btn.clicked.connect(self.start_analysis)
        
        self.stop_btn = QPushButton("⏹️ توقف")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #da190b; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        self.stop_btn.clicked.connect(self.stop_analysis)
        self.stop_btn.setEnabled(False)
        
        layout.addWidget(camera_label)
        layout.addWidget(self.camera_combo)
        layout.addWidget(mic_label)
        layout.addWidget(self.mic_combo)
        layout.addStretch()
        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        
        group.setLayout(layout)
        return group
    
    def create_video_stats_group(self):
        """گروه آمار ویدئو"""
        group = QGroupBox("🎥 تحلیل تصویر (Face AI)")
        layout = QVBoxLayout()
        
        self.faces_label = QLabel("👥 چهره‌ها: 0")
        self.faces_label.setFont(QFont("Arial", 14))
        
        self.attention_label = QLabel("📊 توجه: 0%")
        self.attention_label.setFont(QFont("Arial", 14))
        
        self.attention_bar = QProgressBar()
        self.attention_bar.setRange(0, 100)
        self.attention_bar.setValue(0)
        
        self.emotion_label = QLabel("😊 احساس: نامعلوم")
        self.emotion_label.setFont(QFont("Arial", 14))
        
        layout.addWidget(self.faces_label)
        layout.addWidget(self.attention_label)
        layout.addWidget(self.attention_bar)
        layout.addWidget(self.emotion_label)
        layout.addStretch()
        
        group.setLayout(layout)
        return group
    
    def create_audio_stats_group(self):
        """گروه آمار صدا"""
        group = QGroupBox("🎤 تحلیل صدا (Voice Detection)")
        layout = QVBoxLayout()
        
        self.speaking_label = QLabel("🎤 وضعیت: نامعلوم")
        self.speaking_label.setFont(QFont("Arial", 14))
        
        self.silence_label = QLabel("🔇 سکوت: 0 ثانیه")
        self.silence_label.setFont(QFont("Arial", 14))
        
        self.audio_status = QLabel("⚪")
        self.audio_status.setFont(QFont("Arial", 48))
        self.audio_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.speaking_label)
        layout.addWidget(self.silence_label)
        layout.addWidget(self.audio_status)
        layout.addStretch()
        
        group.setLayout(layout)
        return group
    
    def create_combined_stats_group(self):
        """گروه آمار ترکیبی"""
        group = QGroupBox("🎬 تحلیل ترکیبی")
        layout = QVBoxLayout()
        
        self.presenter_quality_label = QLabel("🎤 کیفیت ارائه: 0%")
        self.presenter_quality_label.setFont(QFont("Arial", 14))
        
        self.presenter_quality_bar = QProgressBar()
        self.presenter_quality_bar.setRange(0, 100)
        
        self.engagement_label = QLabel("👥 تعامل مخاطب: 0%")
        self.engagement_label.setFont(QFont("Arial", 14))
        
        self.engagement_bar = QProgressBar()
        self.engagement_bar.setRange(0, 100)
        
        self.recommendation_label = QLabel("💡 توصیه: -")
        self.recommendation_label.setFont(QFont("Arial", 12))
        self.recommendation_label.setWordWrap(True)
        self.recommendation_label.setStyleSheet("""
            background-color: #fffde7;
            padding: 10px;
            border-radius: 5px;
        """)
        
        layout.addWidget(self.presenter_quality_label)
        layout.addWidget(self.presenter_quality_bar)
        layout.addWidget(self.engagement_label)
        layout.addWidget(self.engagement_bar)
        layout.addWidget(self.recommendation_label)
        layout.addStretch()
        
        group.setLayout(layout)
        return group
    
    def connect_signals(self):
        """اتصال سیگنال‌ها"""
        # Voice signals
        self.voice_detector.presenter_speaking.connect(self.on_speaking)
        self.voice_detector.presenter_silent.connect(self.on_silent)
        
        # Face AI signals (if available)
        # Note: Face AI signals are handled in update_stats()
    
    def start_analysis(self):
        """شروع تحلیل"""
        camera_idx = self.camera_combo.currentIndex()
        mic_idx = self.mic_combo.currentIndex()
        
        self.log(f"▶️ شروع تحلیل یکپارچه...")
        self.log(f"   🎥 دوربین: {camera_idx}")
        self.log(f"   🎤 میکروفون: {mic_idx}")
        
        # Start Face AI
        self.log("   🎥 راه‌اندازی Face AI...")
        if self.face_ai.start_analysis(camera_idx, fps=15):
            self.log("   ✅ Face AI شروع شد")
        else:
            self.log("   ❌ خطا در Face AI")
            return
        
        # Start Voice Detection
        self.log("   🎤 راه‌اندازی Voice Detection...")
        if self.voice_detector.start_detection(mic_idx):
            self.log("   ✅ Voice Detection شروع شد")
        else:
            self.log("   ❌ خطا در Voice Detection")
            self.face_ai.stop_analysis()
            return
        
        self.is_running = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.update_timer.start()
        
        self.log("✅ تحلیل یکپارچه شروع شد!")
    
    def stop_analysis(self):
        """توقف تحلیل"""
        self.log("⏹️ توقف تحلیل...")
        
        self.update_timer.stop()
        self.face_ai.stop_analysis()
        self.voice_detector.stop_detection()
        
        self.is_running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        self.log("✅ تحلیل متوقف شد")
    
    def update_stats(self):
        """به‌روزرسانی آمار"""
        if not self.is_running:
            return
        
        # Get video stats
        self.stats['video']['faces'] = self.face_ai.get_face_count()
        self.stats['video']['attention'] = self.face_ai.get_attention_level()
        self.stats['video']['emotion'] = self.face_ai.get_dominant_emotion()
        
        # Get audio stats
        self.stats['audio']['speaking'] = self.voice_detector.is_speaking()
        self.stats['audio']['silence_duration'] = self.voice_detector.get_silence_duration()
        
        # Calculate combined stats
        self.calculate_combined_stats()
        
        # Update UI
        self.update_ui()
    
    def calculate_combined_stats(self):
        """محاسبه آمار ترکیبی"""
        # Presenter Quality = Speaking + Attention
        speaking_score = 1.0 if self.stats['audio']['speaking'] else 0.0
        attention_score = self.stats['video']['attention']
        
        self.stats['combined']['presenter_quality'] = (speaking_score * 0.4 + attention_score * 0.6)
        
        # Audience Engagement = Attention + Positive Emotion
        emotion_score = 0.8 if self.stats['video']['emotion'] in ['happy', 'neutral'] else 0.3
        self.stats['combined']['audience_engagement'] = (attention_score * 0.7 + emotion_score * 0.3)
    
    def update_ui(self):
        """به‌روزرسانی UI"""
        # Video
        self.faces_label.setText(f"👥 چهره‌ها: {self.stats['video']['faces']}")
        attention_pct = int(self.stats['video']['attention'] * 100)
        self.attention_label.setText(f"📊 توجه: {attention_pct}%")
        self.attention_bar.setValue(attention_pct)
        self.emotion_label.setText(f"😊 احساس: {self.stats['video']['emotion']}")
        
        # Audio
        if self.stats['audio']['speaking']:
            self.speaking_label.setText("🎤 وضعیت: در حال صحبت")
            self.audio_status.setText("🎤")
            self.audio_status.setStyleSheet("color: #4CAF50;")
        else:
            self.speaking_label.setText("🔇 وضعیت: سکوت")
            self.audio_status.setText("🔇")
            self.audio_status.setStyleSheet("color: #FF9800;")
        
        self.silence_label.setText(f"🔇 سکوت: {self.stats['audio']['silence_duration']} ثانیه")
        
        # Combined
        presenter_pct = int(self.stats['combined']['presenter_quality'] * 100)
        engagement_pct = int(self.stats['combined']['audience_engagement'] * 100)
        
        self.presenter_quality_label.setText(f"🎤 کیفیت ارائه: {presenter_pct}%")
        self.presenter_quality_bar.setValue(presenter_pct)
        
        self.engagement_label.setText(f"👥 تعامل مخاطب: {engagement_pct}%")
        self.engagement_bar.setValue(engagement_pct)
        
        # Recommendation
        recommendation = self.get_recommendation()
        self.recommendation_label.setText(f"💡 توصیه: {recommendation}")
    
    def get_recommendation(self):
        """دریافت توصیه"""
        speaking = self.stats['audio']['speaking']
        silence_dur = self.stats['audio']['silence_duration']
        attention = self.stats['video']['attention']
        faces = self.stats['video']['faces']
        
        if not speaking and silence_dur > 10:
            return "⚠️ سخنران 10 ثانیه سکوت کرده - لطفاً بررسی کنید"
        
        if attention < 0.3:
            return "⚠️ توجه مخاطبان بسیار پایین - پیشنهاد استراحت"
        
        if attention < 0.5:
            return "⚠️ توجه مخاطبان پایین - تغییر موضوع پیشنهاد می‌شود"
        
        if speaking and attention > 0.7:
            return "✅ عالی! سخنران در حال ارائه و مخاطبان متمرکز"
        
        if faces == 0:
            return "⚠️ هیچ چهره‌ای تشخیص داده نشد - بررسی دوربین"
        
        return "✅ همه چیز عادی است"
    
    def on_speaking(self):
        """هنگام صحبت"""
        self.log("🎤 صحبت شروع شد")
    
    def on_silent(self, seconds):
        """هنگام سکوت"""
        if seconds >= 5:
            self.log(f"🔇 سکوت برای {seconds} ثانیه")
    
    def log(self, message):
        """لاگ"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def closeEvent(self, event):
        """هنگام بستن"""
        if self.is_running:
            self.stop_analysis()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    print("=== Integrated Audio-Video Analysis Test ===\n")
    
    window = IntegratedAnalysisWindow()
    window.show()
    
    sys.exit(app.exec())

