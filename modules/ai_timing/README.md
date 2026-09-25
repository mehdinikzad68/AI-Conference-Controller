# AI-Driven Adaptive Timing Module

Comprehensive AI-powered timing system that adapts in real-time based on presenter and audience engagement analysis.

## Overview

The AI Timing module integrates computer vision, voice recognition, and machine learning to create an intelligent timer that automatically adjusts based on:
- **Presenter Activity**: Face orientation, emotion, voice activity
- **Audience Engagement**: Attention levels, emotion distribution
- **Real-Time Adaptation**: Pause/slow timer on low engagement, extend on high engagement

## Features

### 1. Presenter Tracking
- **Face Detection**: Tracks presenter's face using DeepFace/RetinaFace
- **Orientation Analysis**: Determines if presenter is looking at audience or screen
- **Emotion Detection**: Analyzes presenter emotion (engaged, bored, etc.)
- **Voice Activity**: Optional microphone-based speech detection
- **Signals**: `presenter_talking`, `presenter_engaged`, `presenter_away`, `presenter_disengaged`

### 2. Audience Engagement Analysis
- **Attention Tracking**: Real-time attention percentage calculation
- **Emotion Analysis**: Tracks audience emotions (happy, neutral, bored, etc.)
- **Engagement Classification**: Categorizes as 'high', 'medium', or 'low'
- **Timeline Tracking**: Maintains engagement history for pattern analysis

### 3. Adaptive Timer Control
- **Smart Pausing**: Automatically pauses when:
  - Presenter is away/disengaged
  - Audience engagement drops to 'low'
- **Slow Mode**: Optional slow-down instead of pause (configurable)
- **Extension**: Can extend timer when engagement is high (with operator confirmation)
- **Reduction**: Optional timer reduction for extended low engagement (with confirmation)
- **Logging**: All AI-driven adjustments logged for transparency

### 4. Operator Dashboard
- **Live Metrics**: Real-time display of:
  - Presenter state
  - Audience engagement level
  - Attention percentage
  - Timer adaptation mode
  - Current timer time
- **Override Controls**: Operator can override AI decisions
- **Event Log**: Real-time log of all AI adjustments
- **Confirmation Dialogs**: Prompts for extension/reduction approvals

### 5. Post-Session Reporting
- **Effective Time**: Calculates actual speaking time (excluding pauses)
- **Engagement Timeline**: Full timeline of engagement levels
- **Key Moments**: Tracks focus drops, extensions, overrides
- **Statistics**: Comprehensive metrics and summaries
- **Export**: Save reports to JSON format

## Architecture

```
AIIntegrationController (Main Coordinator)
├── PresenterTracker (Video + Face Analysis)
├── VoiceActivityDetector (Optional Microphone)
├── FaceAIController (Audience Analysis - Reused)
├── EngagementAnalyzer (Engagement Classification)
└── AdaptiveTimerController (Timer Adaptation Logic)
    └── TimerController (Base Timer)
```

## Usage

### Basic Setup

```python
from modules.ai_timing import AIIntegrationController
from modules.timer import TimerController

# Create base timer
base_timer = TimerController()
base_timer.set_time(1800)  # 30 minutes

# Create AI integration controller
ai_controller = AIIntegrationController(base_timer)

# Start AI timing system
ai_controller.start_ai_timing(
    presenter_camera=0,  # Camera index for presenter
    audience_camera=1,   # Camera index for audience
    enable_voice=True     # Enable voice detection
)

# Start base timer
base_timer.start()
```

### Configuration

```python
# Configure adaptive timer
ai_controller.configure(
    adaptive_timer={
        'pause_on_low_engagement': True,
        'slow_on_low_engagement': False,
        'allow_extensions': True,
        'max_extension_percent': 10,  # Max 10% extension
        'extension_confirmation_required': True
    },
    presenter_tracker={
        'engagement_threshold': 0.5,
        'orientation_threshold': 30.0  # Degrees
    },
    engagement_analyzer={
        'high_threshold': 0.7,  # 70% for "high"
        'medium_threshold': 0.4  # 40% for "medium"
    }
)
```

### Operator Dashboard

```python
from modules.ai_timing import OperatorDashboard

# Create dashboard
dashboard = OperatorDashboard(ai_controller)
dashboard.show()

# Dashboard automatically:
# - Shows live metrics
# - Handles extension/reduction confirmations
# - Displays event log
# - Provides override controls
```

### Post-Session Reporting

```python
from modules.ai_timing import SessionReportGenerator

# Create report generator
report_gen = SessionReportGenerator()
report_gen.start_session()

# During session, record events:
report_gen.record_presenter_state("talking")
report_gen.record_engagement("high", 0.85)
report_gen.record_extension(120, confirmed=True)

# End session and generate report
report_gen.end_session()
report = report_gen.generate_report()

# Save to file
report_gen.save_report("session_report.json")
```

## Signals and Events

### AIIntegrationController Signals
- `presenter_state_changed(str)`: Presenter state ("talking", "engaged", "away", "disengaged")
- `audience_engagement_changed(str)`: Engagement level ("high", "medium", "low")
- `timer_adaptation_changed(str)`: Adaptation mode ("normal", "paused_ai", "slowed_ai", "extended", "reduced")
- `extension_requested(int)`: Request for operator confirmation (seconds)
- `reduction_requested(int)`: Request for operator confirmation (seconds)

### PresenterTracker Signals
- `presenter_talking`: Presenter is actively talking
- `presenter_engaged`: Presenter is visually engaged
- `presenter_away`: Presenter is away from camera
- `presenter_disengaged`: Presenter is disengaged
- `presenter_state_changed(str)`: State change notification

### VoiceActivityDetector Signals
- `presenter_speaking`: Voice activity detected
- `presenter_silent(int)`: Silence duration in seconds
- `voice_activity_detected(bool)`: Speaking (True) or silent (False)

## Configuration Options

### Adaptive Timer
- `pause_on_low_engagement`: Pause timer when engagement is low (default: True)
- `slow_on_low_engagement`: Slow timer instead of pausing (default: False)
- `slow_factor`: Slow factor 0.0-1.0 (default: 0.5)
- `allow_extensions`: Allow AI-driven extensions (default: True)
- `allow_reductions`: Allow AI-driven reductions (default: False)
- `max_extension_percent`: Maximum extension percentage (default: 10)
- `extension_confirmation_required`: Require operator confirmation (default: True)

### Presenter Tracker
- `engagement_threshold`: Face confidence threshold (default: 0.5)
- `orientation_threshold`: Orientation threshold in degrees (default: 30.0)

### Engagement Analyzer
- `high_threshold`: Threshold for "high" engagement (default: 0.7)
- `medium_threshold`: Threshold for "medium" engagement (default: 0.4)

### Voice Detector
- `silence_threshold`: Seconds of silence before signal (default: 3)
- `energy_threshold`: Audio energy threshold (default: 300)

## Testing

Run the test script:

```bash
python modules/ai_timing/test_ai_timing.py
```

This demonstrates:
- AI controller setup
- Dashboard display
- Timer integration
- Live metrics updates

## Integration with Symposium Module

The AI timing system can be integrated with the Symposium module:

```python
from modules.symposium import SymposiumWindow
from modules.ai_timing import AIIntegrationController

# In symposium window, create AI controller
symposium_window = SymposiumWindow()
timer = symposium_window.get_session_controller().get_timer_controller()

ai_controller = AIIntegrationController(timer)
ai_controller.start_ai_timing(presenter_camera=0, audience_camera=1)

# Create dashboard
from modules.ai_timing import OperatorDashboard
dashboard = OperatorDashboard(ai_controller)
dashboard.show()
```

## Dependencies

- **Required**: PyQt6, OpenCV, numpy, DeepFace, dlib
- **Optional**: SpeechRecognition (for voice detection)
- **Optional**: Vosk (alternative voice recognition)

Install optional dependencies:
```bash
pip install SpeechRecognition  # For voice activity detection
```

## Troubleshooting

### Camera Not Found
- Check camera permissions
- Verify camera indices (0, 1, etc.)
- Ensure cameras are not used by other applications

### Voice Detection Not Working
- Install SpeechRecognition: `pip install SpeechRecognition`
- Check microphone permissions
- Adjust energy threshold if too sensitive/insensitive

### Timer Not Adapting
- Verify AI controller is active: `ai_controller.is_active()`
- Check engagement thresholds in configuration
- Review event log in operator dashboard

### High CPU Usage
- Reduce FPS for presenter/audience tracking
- Process fewer frames (increase frame skip)
- Disable voice detection if not needed

## Future Enhancements

- Multi-presenter tracking
- Advanced emotion classification
- Predictive engagement modeling
- Integration with presentation slides
- Real-time audience feedback display
- Export reports to HTML/PDF formats

