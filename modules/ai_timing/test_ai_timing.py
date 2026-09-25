"""
AI Timing System Test Script

Demonstrates AI-driven adaptive timing with presenter tracking,
audience analysis, and timer adaptation.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from modules.ai_timing import AIIntegrationController, OperatorDashboard
from modules.timer import TimerController


def main():
    """Run AI timing system test."""
    print("=" * 60)
    print("AI-Symp-Controller - AI Timing System Test")
    print("=" * 60)
    print("\nThis test demonstrates:")
    print("  - Presenter tracking (face orientation, emotion)")
    print("  - Voice activity detection (optional)")
    print("  - Audience engagement analysis")
    print("  - Adaptive timer (pauses/slows on low engagement)")
    print("  - Timer extension/reduction with confirmation")
    print("  - Operator dashboard with live metrics")
    print("  - Post-session reporting")
    print("\nRequirements:")
    print("  - Two cameras (presenter + audience) or use same camera for both")
    print("  - Optional: Microphone for voice detection")
    print("\nFeatures:")
    print("  - Timer pauses when presenter is away/disengaged")
    print("  - Timer pauses when audience engagement is low")
    print("  - Timer can extend when engagement is high (with confirmation)")
    print("  - All adjustments logged for transparency")
    print("  - Operator can override AI decisions")
    print("\n" + "=" * 60)
    
    app = QApplication(sys.argv)
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("AI Timing System Test")
    window.setMinimumSize(800, 600)
    
    # Central widget
    central = QWidget()
    layout = QVBoxLayout(central)
    
    # Title
    title = QLabel("AI-Driven Adaptive Timing System")
    title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
    layout.addWidget(title)
    
    # Create base timer
    base_timer = TimerController()
    base_timer.set_time(300)  # 5 minutes
    
    # Create AI integration controller
    ai_controller = AIIntegrationController(base_timer)
    
    # Create operator dashboard
    dashboard = OperatorDashboard(ai_controller)
    layout.addWidget(dashboard)
    
    # Control buttons
    btn_layout = QVBoxLayout()
    
    start_btn = QPushButton("Start AI Timing System")
    start_btn.clicked.connect(lambda: ai_controller.start_ai_timing(presenter_camera=0, audience_camera=0, enable_voice=False))
    btn_layout.addWidget(start_btn)
    
    stop_btn = QPushButton("Stop AI Timing System")
    stop_btn.clicked.connect(ai_controller.stop_ai_timing)
    btn_layout.addWidget(stop_btn)
    
    timer_start_btn = QPushButton("Start Base Timer")
    timer_start_btn.clicked.connect(base_timer.start)
    btn_layout.addWidget(timer_start_btn)
    
    layout.addLayout(btn_layout)
    
    window.setCentralWidget(central)
    window.show()
    
    print("\nAI Timing System test window displayed.")
    print("Use the buttons to start/stop the system and timer.")
    print("Dashboard shows live metrics and AI-driven adjustments.")
    print("\nClose the window to exit.\n")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

