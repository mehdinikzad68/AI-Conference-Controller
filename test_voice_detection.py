"""
Test Voice Detection System

تست سیستم تشخیص صدای میکروفون
"""

import sys
import time
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QTextEdit, QProgressBar
from PyQt6.QtCore import Qt
from modules.ai_timing.voice_activity_detector import VoiceActivityDetector
import speech_recognition as sr

class VoiceTestWindow(QMainWindow):
    """پنجره تست Voice Detection"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎤 Voice Detection Test - تست تشخیص صدا")
        self.setMinimumSize(800, 600)
        
        self.voice_detector = VoiceActivityDetector()
        self.is_running = False
        
        self.init_ui()
        self.connect_signals()
    
    def init_ui(self):
        """ساخت رابط کاربری"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # عنوان
        title = QLabel("🎤 سیستم تشخیص صدای میکروفون")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2196F3;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # انتخاب میکروفون
        mic_layout = QHBoxLayout()
        mic_label = QLabel("🎙️ انتخاب میکروفون:")
        mic_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.mic_combo = QComboBox()
        self.detect_microphones()
        mic_layout.addWidget(mic_label)
        mic_layout.addWidget(self.mic_combo)
        mic_layout.addStretch()
        layout.addLayout(mic_layout)
        
        # دکمه‌ها
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶️ شروع تشخیص")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.start_btn.clicked.connect(self.start_detection)
        
        self.stop_btn = QPushButton("⏹️ توقف")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_detection)
        self.stop_btn.setEnabled(False)
        
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        layout.addLayout(button_layout)
        
        # وضعیت
        self.status_label = QLabel("⚪ آماده")
        self.status_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            padding: 15px;
            background-color: #f0f0f0;
            border-radius: 8px;
        """)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # آمار
        stats_layout = QHBoxLayout()
        
        self.silence_label = QLabel("🔇 سکوت: 0 ثانیه")
        self.silence_label.setStyleSheet("font-size: 14px; padding: 10px; background-color: #e3f2fd; border-radius: 5px;")
        
        self.state_label = QLabel("⚪ وضعیت: نامعلوم")
        self.state_label.setStyleSheet("font-size: 14px; padding: 10px; background-color: #e3f2fd; border-radius: 5px;")
        
        stats_layout.addWidget(self.silence_label)
        stats_layout.addWidget(self.state_label)
        layout.addLayout(stats_layout)
        
        # لاگ
        log_label = QLabel("📋 لاگ رویدادها:")
        log_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                font-family: 'Courier New';
                font-size: 12px;
                border: 2px solid #4CAF50;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.log_text)
        
        # راهنما
        help_text = QLabel("""
        📖 راهنما:
        • میکروفون خود را انتخاب کنید
        • دکمه "شروع تشخیص" را بزنید
        • صحبت کنید یا سکوت کنید
        • سیستم به صورت real-time تشخیص می‌دهد
        """)
        help_text.setStyleSheet("""
            font-size: 12px;
            color: #666;
            padding: 10px;
            background-color: #fffde7;
            border-radius: 5px;
        """)
        layout.addWidget(help_text)
    
    def detect_microphones(self):
        """تشخیص میکروفون‌های موجود"""
        try:
            mic_list = sr.Microphone.list_microphone_names()
            self.mic_combo.addItems([f"Mic {i}: {name[:50]}" for i, name in enumerate(mic_list)])
            self.log(f"✅ تعداد میکروفون‌های یافت شده: {len(mic_list)}")
            for i, name in enumerate(mic_list):
                self.log(f"   • Mic {i}: {name}")
        except Exception as e:
            self.log(f"❌ خطا در تشخیص میکروفون‌ها: {e}")
            self.mic_combo.addItem("میکروفون پیش‌فرض")
    
    def connect_signals(self):
        """اتصال سیگنال‌ها"""
        self.voice_detector.presenter_speaking.connect(self.on_speaking)
        self.voice_detector.presenter_silent.connect(self.on_silent)
        self.voice_detector.voice_activity_detected.connect(self.on_activity)
    
    def start_detection(self):
        """شروع تشخیص"""
        mic_index = self.mic_combo.currentIndex()
        self.log(f"▶️ شروع تشخیص با میکروفون {mic_index}...")
        
        # تنظیمات
        self.voice_detector.set_silence_threshold(2)  # 2 ثانیه سکوت
        self.voice_detector.set_energy_threshold(300)
        
        # شروع
        success = self.voice_detector.start_detection(microphone_index=mic_index)
        
        if success:
            self.is_running = True
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText("🟢 در حال گوش دادن...")
            self.status_label.setStyleSheet("""
                font-size: 20px;
                font-weight: bold;
                padding: 15px;
                background-color: #c8e6c9;
                border-radius: 8px;
                color: #2e7d32;
            """)
            self.log("✅ تشخیص صدا شروع شد!")
            self.log("💡 صحبت کنید یا سکوت کنید...")
        else:
            self.log("❌ خطا در شروع تشخیص صدا!")
            self.log("💡 لطفاً میکروفون را بررسی کنید")
    
    def stop_detection(self):
        """توقف تشخیص"""
        self.log("⏹️ توقف تشخیص...")
        self.voice_detector.stop_detection()
        
        self.is_running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("⚪ متوقف شده")
        self.status_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            padding: 15px;
            background-color: #f0f0f0;
            border-radius: 8px;
        """)
        self.log("✅ تشخیص صدا متوقف شد")
    
    def on_speaking(self):
        """زمانی که صحبت تشخیص داده شود"""
        self.status_label.setText("🎤 در حال صحبت...")
        self.status_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            padding: 15px;
            background-color: #4CAF50;
            color: white;
            border-radius: 8px;
        """)
        self.state_label.setText("🎤 وضعیت: صحبت")
        self.log("🎤 صحبت تشخیص داده شد")
    
    def on_silent(self, seconds):
        """زمانی که سکوت تشخیص داده شود"""
        self.status_label.setText(f"🔇 سکوت ({seconds}s)")
        self.status_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            padding: 15px;
            background-color: #FF9800;
            color: white;
            border-radius: 8px;
        """)
        self.silence_label.setText(f"🔇 سکوت: {seconds} ثانیه")
        self.state_label.setText("🔇 وضعیت: سکوت")
        self.log(f"🔇 سکوت برای {seconds} ثانیه")
    
    def on_activity(self, is_speaking):
        """فعالیت صوتی"""
        if is_speaking:
            pass  # handled by on_speaking
        else:
            pass  # handled by on_silent
    
    def log(self, message):
        """اضافه کردن به لاگ"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        # Auto-scroll
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def closeEvent(self, event):
        """هنگام بستن پنجره"""
        if self.is_running:
            self.stop_detection()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # بررسی اولیه
    print("=== Voice Detection Test ===\n")
    print("1. بررسی SpeechRecognition...")
    try:
        import speech_recognition as sr
        print("   ✅ SpeechRecognition نصب شده")
    except ImportError:
        print("   ❌ SpeechRecognition نصب نشده!")
        sys.exit(1)
    
    print("2. بررسی PyAudio...")
    try:
        import pyaudio
        print("   ✅ PyAudio نصب شده")
    except ImportError:
        print("   ❌ PyAudio نصب نشده!")
        sys.exit(1)
    
    print("3. بررسی میکروفون‌ها...")
    try:
        mic_list = sr.Microphone.list_microphone_names()
        print(f"   ✅ تعداد میکروفون: {len(mic_list)}")
        for i, name in enumerate(mic_list):
            print(f"      • Mic {i}: {name}")
    except Exception as e:
        print(f"   ❌ خطا: {e}")
    
    print("\n4. راه‌اندازی رابط گرافیکی...\n")
    
    # راه‌اندازی پنجره
    window = VoiceTestWindow()
    window.show()
    
    sys.exit(app.exec())

