# AI-Symp-Controller

A highly modular and extensible Python desktop application for presentation control, featuring smart timer functionality, media playback, AI-powered audience analysis, and multi-display management.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [Module Overview](#module-overview)
- [Dependencies](#dependencies)
- [Compatibility](#compatibility)
- [OBS Studio Integration](#obs-studio-integration)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

## Overview

AI-Symp-Controller is designed as a comprehensive presentation management tool for Windows 11. It provides a clean, modular architecture that allows for easy extension and customization of individual components. The application is optimized for use with HP Envy x360 2-in-1 laptops and supports seamless integration with OBS Studio for streaming and recording.

## Features

- **Smart Graphical Timer**: Countdown and count-up timer with visual feedback
- **AI-Driven Adaptive Timing**: Intelligent timer that adapts in real-time based on presenter and audience engagement
- **Media Player**: Support for slides, PDFs, images, videos, and PowerPoint (PPT/PPTX)
- **Symposium Display**: Comprehensive symposium presentation system with agenda, speaker intros, smart timer overlays, and scene switching
- **Face AI Analysis**: Real-time audience attention and reaction analysis using computer vision
- **Display Management**: Multi-display support for projectors and external monitors
- **Modular Architecture**: Clean separation of concerns for easy maintenance and extension

## System Requirements

### Operating System
- Windows 11 (64-bit)

### Hardware
- **Recommended**: HP Envy x360 2-in-1 Laptop
  - Processor: AMD Ryzen 5 8640HS or equivalent
  - Graphics: AMD Radeon 760M or equivalent
  - RAM: 8GB minimum (16GB recommended)
  - Storage: 500MB free space for application and dependencies

### Software
- Python 3.11 or above
- pip (Python package manager)

## Installation

### Step 1: Install Python

1. Download Python 3.11 or later from [python.org](https://www.python.org/downloads/)
2. During installation, ensure you check "Add Python to PATH"
3. Verify installation by opening PowerShell and running:
   ```powershell
   python --version
   ```

### Step 2: Clone or Download the Project

If using Git:
```powershell
git clone <repository-url>
cd AI-Symp-Controler
```

Or extract the project files to your desired location.

### Step 3: Install Dependencies

1. Open PowerShell in the project directory
2. Navigate to the project root:
   ```powershell
   cd D:\AI-Studio\My-Win-App\AI-Symp-Controler
   ```
3. Install all required packages:
   ```powershell
   pip install -r requirements.txt
   ```

   **Note**: If you encounter permission errors, use:
   ```powershell
   pip install --user -r requirements.txt
   ```

### Step 4: Verify Installation

Run the application to verify everything is set up correctly:
```powershell
python main.py
```

The main window should open, displaying the module selection interface.

## Project Structure

```
AI-Symp-Controler/
│
├── modules/                  # Modular components
│   ├── timer/               # Smart graphical timer module
│   │   ├── __init__.py
│   │   ├── timer_controller.py
│   │   ├── circular_timer_widget.py
│   │   ├── timer_window.py
│   │   ├── test_timer.py
│   │   └── generate_sounds.py
│   │
│   ├── media/               # Media/slides/PDF player module
│   │   ├── __init__.py
│   │   └── media_controller.py
│   │
│   ├── face_ai/             # Audience attention/reaction analysis (AI) module
│   │   ├── __init__.py
│   │   └── face_ai_controller.py
│   │
│   ├── display/             # Output management for projector/TVs module
│   │   ├── __init__.py
│   │   └── display_controller.py
│   │
│   ├── config/              # Configuration & asset management
│   │   ├── __init__.py
│   │   ├── config_manager.py
│   │   ├── config_profiles.py
│   │   ├── config_window.py
│   │   └── test_config.py
│   │
│   └── __init__.py
│
├── assets/                   # Logos, icons, images, style sheets, sound files
│   ├── warning_beep.wav      # Warning alert sound (< 2 minutes)
│   └── finished_beep.wav     # Timer finished alert sound
│
├── main.py                   # Application entry point and main window logic
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

### Module Organization

Each module is designed as an independent Python package with:
- `__init__.py`: Package initialization and exports
- Core controller file(s): Main logic and functionality

This structure ensures:
- **Separation of Concerns**: Each module handles its own domain
- **Maintainability**: Easy to locate and modify specific features
- **Extensibility**: New modules can be added without affecting existing ones
- **Testability**: Each module can be tested independently

## Usage

### Launching the Application

1. Open PowerShell in the project directory
2. Run:
   ```powershell
   python main.py
   ```

### Main Window

The main window provides access to all modules through dedicated buttons:
- **Timer Module**: Smart graphical timer functionality
- **AI Timing Module**: AI-driven adaptive timing with presenter and audience tracking
- **Media Player Module**: Media playback and presentation tools
- **Symposium Display**: Comprehensive symposium presentation system with agenda, speaker intros, and smart timing
- **Face AI Analysis Module**: Audience analysis and monitoring
- **Display Management Module**: Multi-display configuration
- **Configuration**: Application settings and preferences

### Menu Bar

- **File > Exit**: Close the application (Ctrl+Q)
- **View > Fullscreen**: Toggle fullscreen mode (F11)
- **Tools > Refresh Displays**: Update list of available displays
- **Help > About**: Application information and version

### Keyboard Shortcuts

- `Ctrl+Q`: Exit application
- `F11`: Toggle fullscreen mode

## Module Overview

### Timer Module (`modules/timer/`)

Provides advanced animated countdown timer functionality with visual feedback, alerts, and multi-timer support.

**Features**:
- **Animated Circular Timer**: Large, visually appealing circular countdown display with smoothly animated progress ring
- **Gradient Color Transitions**: Automatic color changes from green (start) → yellow (middle) → red (warning/critical)
- **Time Input Controls**: Both slider-based and numeric input for setting session duration (0-2 hours)
- **Full Timer Controls**: Start, Pause, Resume, and Reset functionality
- **Multi-Timer Support**: Create and manage multiple timers using tabs (ideal for multiple speakers or panel discussions)
- **Visual Alerts**: 
  - Warning mode when < 2 minutes remaining (red flashing ring, glow effect, shake animation)
  - "TIME ENDING SOON" overlay text
  - Finished state with "END OF SPEECH" display and shake animation
- **Audio Alerts**: Warning beep when < 2 minutes, final alert when timer reaches zero
- **Fullscreen Mode**: Optimized for projector display (F11 to toggle)
- **OBS Studio Optimized**: Designed for seamless window capture

**Files**:
- `timer_controller.py`: Core timer logic with QTimer integration
- `circular_timer_widget.py`: Custom animated circular timer widget
- `timer_window.py`: Main timer window with all controls and UI
- `test_timer.py`: Standalone demo script for testing
- `generate_sounds.py`: Utility to generate alert sound files

**Usage**:
1. Launch the timer module from the main application or run standalone:
   ```powershell
   python modules/timer/test_timer.py
   ```
2. Set the session time using:
   - Minutes and seconds sliders
   - Total time input box (in seconds)
3. Click "Start" to begin countdown
4. Timer will automatically show warnings when < 2 minutes remain
5. Use "+ Add Timer" to create additional timers for multiple speakers
6. Press F11 for fullscreen mode (ideal for projector display)

**Keyboard Shortcuts**:
- `F11`: Toggle fullscreen mode
- `Ctrl+N`: Add new timer
- `Ctrl+Q`: Exit timer window
- `Escape`: Exit fullscreen mode

**Generating Alert Sounds**:
Alert sound files are automatically generated when you first run the application. To regenerate them manually:
```powershell
python modules/timer/generate_sounds.py
```
This creates `warning_beep.wav` and `finished_beep.wav` in the `assets/` directory. You can replace these with custom sound files if desired.

### Media Module (`modules/media/`)

Comprehensive media playback module with high-quality PDF rendering, video playback, and image display.

**Features**:
- **High-Quality PDF Rendering**: Uses PyMuPDF for fast, high-resolution PDF page display (200+ DPI)
- **PDF Navigation**: Previous/Next page buttons with page counter (e.g., "Page 3 / 15")
- **Video Playback**: Smooth MP4, AVI, MOV video playback using PyQt6 Multimedia
- **Image Display**: Support for JPG, PNG, BMP, GIF with aspect ratio preservation
- **Drag-and-Drop Upload**: Easy file upload by dragging files onto the window
- **Advanced Transition Effects**: Choose from Fade, Slide, or Blur animations when switching media
- **Transition Speed Control**: Adjustable animation duration (50-1000ms) for customized pacing
- **File Library**: Visual file list with thumbnails for easy selection
- **Playback Controls**: Play, Pause, Stop, Previous, Next buttons
- **Fullscreen Mode**: Optimized for projector display (F11)
- **OBS Studio Compatible**: Window designed for seamless window capture

**Files**:
- `media_controller.py`: Core media playback logic
- `media_window.py`: Main media player UI with drag-and-drop
- `media_display_widget.py`: Content display widget with transitions
- `media_item.py`: Media file representation with thumbnails
- `pdf_viewer.py`: High-quality PDF rendering component
- `timer_overlay_widget.py`: Timer overlay widget for media content
- `test_media.py`: Standalone demo script
- `test_pdf_viewer.py`: PDF viewer test script
- `test_media_overlay.py`: Timer overlay integration test
- `test_transition_effects.py`: Transition effects demonstration script

**PDF Rendering**:
- Uses PyMuPDF (fitz) for high-performance, high-quality rendering
- Renders at 200 DPI by default (configurable)
- Supports multi-page navigation
- Optimized for 1080p and 4K projector displays
- Instant page transitions, flicker-free

**Usage**:
1. Launch the media module from the main application or run standalone:
   ```powershell
   python modules/media/test_media.py
   ```
2. Drag and drop PDF/image/video files or click "Browse Files..."
3. Select a file from the list to load it
4. Choose transition effect from dropdown (Fade, Slide, Blur, or None)
5. Adjust transition speed if needed (50-1000ms, lower = faster)
6. Navigate between media using Previous/Next buttons to see transitions
7. For PDFs: Use "Previous Page" and "Next Page" buttons to navigate
8. For videos: Use Play/Pause/Stop controls
9. Press F11 for fullscreen mode (ideal for projector display)

**Transition Effects**:
- **Fade**: Smooth opacity transition (default, ~300ms)
  - Best for: General presentations, professional settings
  - Smooth, non-distracting, works with all media types
  
- **Slide**: Horizontal slide animation (~150ms)
  - Best for: Dynamic presentations, fast-paced content
  - Creates sense of movement and progression
  - Works with images, PDFs, and videos
  
- **Blur**: Blur-in effect that clears to reveal content (~200ms)
  - Best for: Elegant transitions, artistic presentations
  - Creates sophisticated visual effect
  - Works with all media types
  
- **None**: Instant switch (no animation)
  - Best for: Technical demos, when speed is critical
  - Zero delay, immediate content change

**Transition Speed**:
- **50-100ms**: Very fast, minimal visual effect (subtle)
- **150-200ms**: Default for Slide/Blur (balanced)
- **300ms**: Default for Fade (smooth and noticeable)
- **500-1000ms**: Slow, dramatic effect (use sparingly)

**Transition Best Practices**:
- Use Fade for most professional presentations
- Use Slide for dynamic, energetic presentations
- Use Blur for elegant, artistic presentations
- Adjust speed based on presentation pace and audience
- Faster transitions (150ms) work well for rapid-fire content
- Slower transitions (300ms+) create more dramatic effect
- Test transitions in fullscreen mode before live presentation
- All transitions work seamlessly with OBS Studio window capture

**PDF Best Practices**:
- **Quality**: PDFs render at high resolution (200 DPI) - suitable for large displays
- **Page Navigation**: Use keyboard arrows (Left/Right) for quick navigation
- **OBS Studio**: Media window is optimized for Window Capture - capture entire window
- **Fullscreen**: Use fullscreen mode (F11) for presentations - PDF scales perfectly
- **File Size**: Large PDFs may take a moment to load first page - subsequent pages are fast

**Timer Overlay Best Practices**:
- **Positioning**: Use "Top Right" or "Top Left" to avoid blocking important content
- **Duration**: Set timer duration before starting (cannot change while running)
- **Auto-Hide**: Timer automatically hides 3 seconds after finishing
- **Dragging**: Click and drag overlay title bar to reposition manually
- **Fullscreen**: Overlay scales correctly in fullscreen mode
- **OBS Capture**: Timer overlay is included automatically in Window Capture of media window

**Troubleshooting Timer Overlay**:
- **Overlay Not Showing**: Ensure "Show Timer Overlay" checkbox is checked
- **Overlay Blocking Content**: Change position using dropdown or drag to reposition
- **Timer Not Updating**: Ensure timer is started with "Start Timer" button
- **Overlay Not Visible in OBS**: Ensure media window is captured, not just media display widget

**Troubleshooting PDF Issues**:
- **Import Error**: Ensure PyMuPDF is installed: `pip install PyMuPDF`
- **Slow Rendering**: First page load may be slow for large PDFs - subsequent pages are cached
- **Missing Pages**: Verify PDF file is not corrupted
- **Low Quality**: PDF renders at 200 DPI - increase DPI in code for higher quality (300+ DPI)

**Timer Overlay Integration**:
- **Show Timer Overlay**: Checkbox to enable/disable timer overlay on media content
- **Position Control**: Dropdown to select overlay position (Top Right, Top Left, Center, etc.)
- **Timer Controls**: Start, Pause, Reset buttons for overlay timer
- **Duration Setting**: Set timer duration in minutes (1-120)
- **Features**:
  - Animated timer with gradient colors (green → yellow → red)
  - Warning alerts when < 2 minutes remaining
  - Auto-hide when timer finishes (after 3 seconds)
  - Draggable overlay for custom positioning
  - Smooth fade in/out animations
  - Works with all media types (video, PDF, images)
  - OBS Studio compatible - appears on top in Window Capture
  - Fullscreen support - overlay scales with media

**Keyboard Shortcuts**:
- `Space`: Play/Pause (videos only)
- `Left/Right Arrow`: Previous/Next media item
- `F11`: Toggle fullscreen
- `Ctrl+O`: Add files
- `Ctrl+Q`: Exit

**Timer Overlay Usage**:
1. Load media content (video, PDF, or image)
2. Check "Show Timer Overlay" checkbox
3. Set timer duration (minutes)
4. Select overlay position from dropdown
5. Click "Start Timer" to begin countdown
6. Timer will display on top of media with all animations
7. Drag overlay to reposition if needed
8. Timer auto-hides 3 seconds after finishing

### Symposium Display Module (`modules/symposium/`)

**Status**: ✅ Fully Implemented

**Description**: Comprehensive symposium presentation system with agenda display, speaker introductions, smart timer overlays with progress bars, and seamless scene switching. Designed for professional symposium management with full OBS Studio integration.

**Features**:
- **Global Agenda Display**: Full event agenda with titles, speaker names, times in clean branded layout
- **Speaker Introduction Slides**: Full-screen intro with photo, name, title, duration before each talk
- **Smart Timer Overlay**: Horizontal progress bar with color transitions (green → yellow → red)
- **20% Warning System**: Visual warning at 20% time remaining with pulsing border, blinking effects, and audio chime
- **Scene Switching**: Seamless transitions between agenda, intro, session, logo, and break screens
- **Session Management**: Automatic timer synchronization, media detection, and session lifecycle control
- **Media Integration**: Works with PDF, PPT, PPTX, videos, and images
- **OBS Studio Optimized**: Window title includes "[OBS]" for easy identification
- **Keyboard Shortcuts**: Quick scene switching and session control (F1-F5, Space, Ctrl+N/P)

**Files**:
- `symposium_window.py`: Main display window with scene management
- `agenda_manager.py`: Agenda and speaker information management
- `session_controller.py`: Session lifecycle and timing control
- `smart_timer_overlay.py`: Enhanced timer overlay with horizontal progress bar
- `scene_manager.py`: Scene switching system
- `agenda_display_widget.py`: Agenda UI display widget
- `speaker_intro_widget.py`: Speaker introduction UI widget
- `test_symposium.py`: Standalone demo script
- `README.md`: Comprehensive module documentation

**Agenda JSON Format**:
```json
{
  "symposium": {
    "title": "AI & Machine Learning Symposium 2025",
    "date": "March 15, 2025",
    "location": "Main Conference Hall",
    "logo_path": "assets/logo.png"
  },
  "agenda": [
    {
      "session_id": "session_01",
      "start_time": "09:00",
      "session_type": "talk",
      "speaker": {
        "name": "Dr. Sarah Johnson",
        "title": "Deep Learning in Computer Vision",
        "organization": "MIT AI Lab",
        "photo_path": "assets/speakers/sarah.jpg",
        "duration_minutes": 30,
        "media_path": "media/session01.pdf"
      }
    }
  ]
}
```

**Keyboard Shortcuts**:
- `F1` - Show Agenda
- `F2` - Show Speaker Intro
- `F3` - Show Session (with media)
- `F4` - Show Logo/Branding
- `F5` - Show Break Screen
- `Space` - Pause/Resume session
- `Ctrl+N` - Next session
- `Ctrl+P` - Previous session

**Usage Workflow**:
1. **Pre-Event**: Create agenda JSON file with speaker info and media paths
2. **Start Event**: Open Symposium Display, load agenda, press F1 to show agenda
3. **During Session**: 
   - Navigate to session (Ctrl+N/Ctrl+P)
   - Speaker intro shows automatically
   - Session starts with timer overlay
   - Warning appears at 20% remaining
   - Media loads if available (otherwise logo shown)
4. **Scene Control**: Use F1-F5 to switch scenes as needed

**Smart Timer Overlay Features**:
- **Progress Bar**: Horizontal bar that fills/shrinks based on time remaining
- **Color Transitions**: 
  - Green (0-50% remaining)
  - Yellow (50-20% remaining)
  - Red (20-0% remaining)
- **Position Presets**: Bottom Center (default), corners, top positions
- **Adjustable**: Width ratio (10-100%), height (30-200px), opacity (0-100%)
- **Warning Effects**: Pulsing border, blinking timer, warning message
- **Time Display**: mm:ss format with color-coded text

**OBS Studio Integration**:
- Window title: "AI-Symp-Controller - Symposium Display [OBS]"
- Use Window Capture in OBS
- All scenes render cleanly for projection
- Timer overlay appears on top
- Smooth transitions between scenes

**Test Script**:
```powershell
python modules/symposium/test_symposium.py
```

**Troubleshooting**:
- **Timer overlay not showing**: Verify session is active (F3), check overlay position/opacity settings
- **Media not loading**: Check file paths in agenda JSON, verify media module dependencies
- **Scene not switching**: Check keyboard shortcuts, verify scene manager state

For complete documentation, see `modules/symposium/README.md`.

### AI Timing Module (`modules/ai_timing/`)

**Status**: ✅ Fully Implemented

**Description**: AI-driven adaptive timing system that intelligently adjusts timer behavior based on real-time presenter tracking and audience engagement analysis. Uses computer vision for face/emotion detection, optional voice activity detection, and automatic timer adaptation.

**Features**:
- **Presenter Tracking**: Face orientation, emotion, engagement state using DeepFace/RetinaFace
- **Voice Activity Detection**: Optional microphone-based speech detection (SpeechRecognition/Vosk)
- **Audience Engagement Analysis**: Real-time attention percentage, emotion distribution, engagement classification (high/medium/low)
- **Adaptive Timer Control**: 
  - Automatically pauses/slows when presenter is away or audience engagement is low
  - Can extend timer when engagement is high (with operator confirmation)
  - Optional timer reduction for extended low engagement
- **Operator Dashboard**: Live metrics, override controls, event logging, confirmation dialogs
- **Post-Session Reporting**: Effective time calculation, engagement timeline, key moments, statistics

**Files**:
- `ai_integration_controller.py`: Main coordinator for all AI components
- `presenter_tracker.py`: Presenter face/orientation/emotion tracking
- `voice_activity_detector.py`: Voice activity detection (optional)
- `engagement_analyzer.py`: Audience engagement classification
- `adaptive_timer_controller.py`: Timer adaptation logic
- `operator_dashboard.py`: Live dashboard UI
- `session_report_generator.py`: Post-session reporting
- `test_ai_timing.py`: Test script
- `README.md`: Complete module documentation

**Prerequisites**:
- Face AI dependencies (DeepFace, dlib, etc.) - already installed
- Optional: SpeechRecognition for voice detection:
  ```bash
  pip install SpeechRecognition
  ```

**Usage**:
1. Create AI integration controller:
   ```python
   from modules.ai_timing import AIIntegrationController
   from modules.timer import TimerController
   
   base_timer = TimerController()
   base_timer.set_time(1800)  # 30 minutes
   
   ai_controller = AIIntegrationController(base_timer)
   ai_controller.start_ai_timing(
       presenter_camera=0,
       audience_camera=1,
       enable_voice=True  # Optional
   )
   ```

2. Use operator dashboard:
   ```python
   from modules.ai_timing import OperatorDashboard
   
   dashboard = OperatorDashboard(ai_controller)
   dashboard.show()
   ```

3. Generate post-session report:
   ```python
   from modules.ai_timing import SessionReportGenerator
   
   report_gen = SessionReportGenerator()
   # Record events during session...
   report = report_gen.generate_report()
   report_gen.save_report("session_report.json")
   ```

**Configuration**:
- **Adaptive Timer**: Pause/slow on low engagement, extension limits, confirmation requirements
- **Presenter Tracker**: Engagement thresholds, orientation thresholds
- **Engagement Analyzer**: High/medium/low classification thresholds
- **Voice Detector**: Silence threshold, energy threshold

**Signals**:
- `presenter_state_changed`: Presenter state updates
- `audience_engagement_changed`: Engagement level changes
- `timer_adaptation_changed`: Timer adaptation mode changes
- `extension_requested`: Requests operator confirmation
- `reduction_requested`: Requests operator confirmation

**Test Script**:
```bash
python modules/ai_timing/test_ai_timing.py
```

**Troubleshooting**:
- **Camera not found**: Check camera permissions and indices
- **Voice detection not working**: Install SpeechRecognition, check microphone permissions
- **Timer not adapting**: Verify AI controller is active, check thresholds
- **High CPU usage**: Reduce FPS, process fewer frames, disable voice if not needed

For complete documentation, see `modules/ai_timing/README.md`.

### Face AI Module (`modules/face_ai/`)

**Status**: ✅ Fully Implemented

**Description**: High-accuracy real-time audience attention and emotion analysis using state-of-the-art AI models. Combines RetinaFace detection, DeepFace emotion/age/gender analysis, FER cross-validation, and dlib head pose estimation for comprehensive audience insights.

**Features**:
- **Multi-Model Face Detection**: RetinaFace backend via DeepFace for best-in-class accuracy
- **Dual Emotion Analysis**: DeepFace (VGG-Face) + FER for cross-validation and reliability
- **Head Pose Estimation**: dlib-based 3D pose estimation (yaw, pitch, roll) for attention direction
- **Real-Time Visualization**: Live camera feed with bounding boxes, emotion labels, and pose arrows
- **Attention Tracking**: Calculates focused vs distracted audience members
- **Comprehensive Statistics**: Tracks emotions, attention, demographics over time
- **Auto-Generated Reports**: Creates pie charts, bar charts, and timeline visualizations
- **Performance Optimized**: Frame sampling and processing rate controls for smooth operation
- **OBS Studio Compatible**: UI window designed for OBS window capture

**AI Models Used**:
- **RetinaFace**: Face detection (via DeepFace backend) - highest accuracy
- **DeepFace (VGG-Face)**: Emotion, age, gender analysis
- **FER (MTCNN)**: Emotion detection cross-validation
- **dlib (68-point landmarks)**: Head pose estimation

**Files**:
- `face_ai_controller.py`: Main controller with camera capture and AI processing pipeline
- `face_ai_window.py`: PyQt6 UI for real-time display and controls
- `face_analyzer.py`: DeepFace and FER integration with preprocessing
- `head_pose_estimator.py`: dlib-based head pose estimation with robust path handling
- `statistics_aggregator.py`: Statistics tracking and chart generation
- `test_face_ai.py`: Standalone demo script
- `test_model_loading.py`: Diagnostic script to verify dlib and model file loading

**Prerequisites**:
1. **Install AI Libraries**:
   ```powershell
   pip install deepface fer dlib insightface
   ```
   
2. **Download dlib Shape Predictor Model**:
   - Download from: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
   - Extract the `.dat` file from the `.bz2` archive
   - **Primary Location (Windows)**: Place in `D:\AI-Studio\My-Win-App\AI-Symp-Controler\assets\models\shape_predictor_68_face_landmarks.dat`
   - **Portable Location**: Place in `assets/models/shape_predictor_68_face_landmarks.dat` (relative to project root)
   - **Alternative Locations**: The module will also check:
     - `modules/face_ai/shape_predictor_68_face_landmarks.dat`
     - `assets/shape_predictor_68_face_landmarks.dat`
   - Without this file, head pose estimation will be disabled (face detection and emotion analysis will still work)
   
   **Path Resolution Order**:
   1. Absolute path: `D:\AI-Studio\My-Win-App\AI-Symp-Controler\assets\models\shape_predictor_68_face_landmarks.dat`
   2. Relative from project root: `assets/models/shape_predictor_68_face_landmarks.dat`
   3. Module-relative: `../assets/models/shape_predictor_68_face_landmarks.dat`
   4. Legacy locations (for backward compatibility)
   
   **Verify Model Loading**:
   ```powershell
   python modules/face_ai/test_model_loading.py
   ```
   This test script verifies dlib installation and model file location.

**Hardware Requirements**:
- Camera (built-in or external USB camera)
- CPU: Multi-core recommended for real-time processing
- RAM: 4GB+ recommended (8GB+ for best performance)
- GPU: Optional but recommended for faster processing

**Usage**:
1. Launch from main application or run standalone:
   ```powershell
   python modules/face_ai/test_face_ai.py
   ```
2. **Select Camera**: Choose camera index (0 for default, 1+ for external cameras)
3. **Adjust Settings**:
   - **FPS**: Target frames per second (5-30, default: 15)
   - **Process Every**: Process every Nth frame (1-5, default: 2) for performance tuning
4. **Start Analysis**: Click "Start Analysis" button
5. **View Real-Time Results**:
   - **Video Feed**: See faces with bounding boxes, emotion labels, and pose arrows
   - **Statistics Panel**: View real-time attention metrics and counts
6. **Stop Analysis**: Click "Stop Analysis" when done
7. **Generate Report**: Click "Generate Report" to create charts and visualizations

**Understanding the Output**:
- **Bounding Box Colors**: Color-coded by emotion (green=happy, blue=sad, red=angry, etc.)
- **Emotion Labels**: Shows detected emotion with confidence percentage
- **Pose Arrows**: Green=focused, Red=distracted, Yellow=partial attention
- **Attention Level**: Overall percentage of audience focused (0-100%)
- **Statistics**: Real-time counts of focused/distracted, emotions, demographics

**Performance Tuning**:
- **Lower FPS** (5-10): Better for slower hardware, reduces CPU usage
- **Higher Process Rate** (3-5): Process fewer frames, improves performance but may miss rapid changes
- **Lower Resolution**: Modify camera resolution in controller for faster processing
- **Frame Sampling**: Automatically processes every Nth frame to balance accuracy and speed

**Troubleshooting**:
- **Camera Not Found**: Check camera permissions, ensure camera is not used by another app
- **Slow Performance**: Reduce FPS or increase "Process Every" value
- **No Face Detection**: Ensure good lighting, check camera focus
- **Head Pose Not Working**: 
  - Verify shape predictor model file is present in expected location
  - Run test script: `python modules/face_ai/test_model_loading.py`
  - Check file permissions (file must be readable)
  - Verify file is not corrupted (re-download if needed)
  - Model file size should be ~99 MB when extracted
- **dlib Installation Issues**:
  - On Windows, may require C++ Build Tools
  - Alternative: Use pre-built wheel from https://github.com/sachadee/Dlib
  - Or install via conda: `conda install -c conda-forge dlib`
- **Import Errors**: Install missing libraries from requirements.txt
- **Model File Not Found**: 
  - Check that file is in `assets/models/` directory
  - Verify absolute path if using Windows deployment
  - Run test script to see all checked locations

**OBS Studio Integration**:
- Face AI window is fully compatible with OBS window capture
- Window title: "Face AI Analysis - AI-Symp-Controller"
- Use Window Capture source in OBS
- Recommended: Capture at 15-30 FPS for smooth display
- Fullscreen mode supported (F11)

### Display Module (`modules/display/`)

Advanced multi-display management system for routing content to projectors, TVs, and external monitors with full OBS Studio integration.

**Features**:
- **Automatic Display Detection**: Detects all connected displays on startup and refresh
- **Display Configuration**: Configure names and roles for each display (Primary, Projector, Left TV, etc.)
- **Content Routing**: Route different modules (Timer, Media Player, Face AI) to specific displays
- **Robust Widget Validation**: Comprehensive validation ensures all widgets are valid before assignment
- **Error Handling**: Clear, actionable error messages when widgets are missing or invalid
- **Real-Time Correction**: Fix widget issues without restarting the application
- **Pre-Launch Validation**: Validate all outputs before starting event/session
- **Preview Mode**: Test each display with test patterns before live operation
- **Fullscreen Support**: Enable fullscreen on individual displays or all displays simultaneously
- **OBS Studio Compatible**: Each display output appears as separate window for easy Window Capture
- **Auto-Scaling**: Automatic content scaling to match display resolution
- **Visual Previews**: Real-time preview thumbnails showing content on each display
- **Display Status**: Real-time status indicators for each connected display

**Files**:
- `display_controller.py`: Core display detection and management logic
- `display_output.py`: Individual display output window class with widget validation
- `display_manager_window.py`: Main management interface with error handling
- `test_display.py`: Standalone demo script
- `test_display_widget_error.py`: Widget error handling demonstration script

**Usage**:
1. Launch the display module from the main application or run standalone:
   ```powershell
   python modules/display/test_display.py
   ```
2. All connected displays will be automatically detected
3. **Open Source Modules First**: Ensure Timer, Media, or Face AI modules are open (if routing content)
4. Select a display from the list
5. Choose content type (Timer, Media, Face AI, or None)
6. Click "Route Content to Display" to send content
   - If widget is missing, you'll see a clear error message with fix instructions
7. Use "Validate All Outputs" button to verify all displays have valid widgets
8. Use "Preview" button to test each display
9. Use "Fullscreen Selected" for projector presentations
   - Invalid widgets will prevent fullscreen with clear error message

**Widget Connection Management**:
- **Validation Before Assignment**: All widgets are validated before being assigned to displays
- **Missing Widget Detection**: Clear error messages when source modules are not open
- **Invalid Widget Detection**: Detection of deleted or corrupted widgets
- **Pre-Launch Validation**: Use "Validate All Outputs" button (Ctrl+V) before starting events
- **Real-Time Correction**: Fix widget issues without restarting - just reassign content
- **Error Messages**: All errors include:
  - Which display is affected
  - What the problem is
  - Step-by-step instructions to fix it

**Widget Validation Checks**:
1. **Widget Presence**: Checks if widget is None before assignment
2. **Widget Type**: Verifies widget is a valid QWidget instance
3. **Widget Validity**: Ensures widget hasn't been deleted or corrupted
4. **Post-Assignment Validation**: Validates widget after routing to catch errors
5. **Fullscreen Validation**: Prevents fullscreen mode if widget is invalid

**Using Widget Validation**:
- **Before Routing**: Ensure source modules (Timer, Media, Face AI) are open
- **After Routing**: Validation happens automatically - errors shown immediately
- **Before Event**: Use "Validate All Outputs" button to check all displays
- **During Event**: Validation prevents invalid displays from entering fullscreen

**Error Scenarios and Solutions**:
- **"Widget Not Available"**: Source module is not open → Open the module and try again
- **"Invalid Widget"**: Widget is corrupted → Close and reopen the source module
- **"Widget Validation Failed"**: Widget was deleted → Re-assign content to the display
- **"Cannot Enter Fullscreen"**: Invalid widget → Fix widget issue, then enter fullscreen

**Keyboard Shortcuts**:
- `Ctrl+R`: Refresh displays
- `Ctrl+V`: Validate all outputs
- `Ctrl+Q`: Exit display manager

**OBS Studio Integration**:
- Each display output window appears with name: "Display Output - [Display Name]"
- Use Window Capture in OBS and select the appropriate display window
- Recommended settings: 1920x1080 resolution, 30 FPS, Window Capture (not Display Capture)
- Put display in fullscreen mode before capturing for best results
- Each display can be captured separately or combined in OBS scenes

**Display Setup Recommendations**:
- **For Conference Halls**: Use extended display mode (not mirror) for different content on different displays
- **Projector**: Typically Display 1 or Primary Display
- **Side TVs**: Additional displays (Display 2, Display 3) for supplementary content
- **Laptop Screen**: Can be used for control interface while projecting to other displays
- **Test Before Live**: Always use Preview mode to verify display connections before presentations
- **Validate Before Start**: Always use "Validate All Outputs" before starting live events
- **Widget Connection Order**: 
  1. Open source modules (Timer, Media, Face AI)
  2. Open Display Manager
  3. Route content to displays
  4. Validate all outputs
  5. Test displays with Preview mode
  6. Start event/session

**Troubleshooting Widget Connection Issues**:
- **"Cannot route content"**: Ensure source module window is open and visible
- **"Widget Not Available"**: Open the module from main application, then route again
- **"Validation Failed"**: Widget was deleted - close and reopen source module, then re-route
- **"Fullscreen Failed"**: Fix widget validation issues first, then try fullscreen
- **All Displays Invalid**: Check that source modules are open and not minimized
- **Widget Deleted During Runtime**: Re-assign content to affected displays without restarting

### Config Module (`modules/config/`)

Comprehensive configuration management system with profile support, asset management, and real-time preview.

**Features**:
- **Tabbed Configuration Interface**: Organized tabs for all module settings
  - Timer Settings: Duration, appearance, warning thresholds
  - Media Settings: Playback defaults, transitions, aspect ratio
  - Face AI Settings: Camera, sampling frequency, analysis options
  - Display Settings: Display mode, target resolution, auto-detection
  - Sound & Alerts: Warning/finished sounds, volumes, custom audio files
  - General Preferences: Language, theme, font size, accessibility
  - Assets: Logo upload, branding colors, custom assets
- **Configuration Profiles**: Save/load multiple profiles for different event types
- **Profile Management**: Create, export, import, delete profiles
- **Real-Time Preview**: Preview configuration changes before applying
- **Asset Management**: Centralized management of logos, sounds, templates
- **Auto-Save**: Automatic configuration backup at configurable intervals
- **Accessibility Options**: High contrast mode, font sizing, projector optimization

**Files**:
- `config_manager.py`: Core configuration management and persistence
- `config_profiles.py`: Profile management (save/load/export/import)
- `config_window.py`: Main configuration UI with all settings tabs
- `test_config.py`: Standalone demo script

**Usage**:
1. Launch the configuration module from the main application or run standalone:
   ```powershell
   python modules/config/test_config.py
   ```
2. Navigate through tabs to configure different modules
3. Change settings and use "Preview Changes" to see effects
4. Click "Save Configuration" to persist changes
5. Create profiles for different event types:
   - Click "New" to create a profile
   - Configure settings for the event type
   - Save the profile
6. Switch between profiles using the profile dropdown
7. Export profiles for backup or sharing with "Export" button

**Configuration Profiles**:
- **Create**: Click "New" button, enter name and description
- **Load**: Select from profile dropdown
- **Export**: Click "Export" to save profile as JSON file
- **Import**: Click "Import" to load profile from JSON file
- **Delete**: Select profile and click "Delete" (Default profile cannot be deleted)

**Settings Categories**:

**Timer Settings**:
- Default duration (1-120 minutes)
- Timer mode (Countdown/Count Up)
- Color scheme (Gradient, Solid, Custom)
- Font size (24-200 pixels)
- Warning threshold and alerts
- Show/hide seconds

**Media Settings**:
- Auto-play on load
- Auto-advance to next
- Default transition (Fade, Slide, Blur, None)
- Maintain aspect ratio
- Fullscreen on play

**Face AI Settings**:
- Enable/disable analysis
- Camera index selection
- Sampling frequency (1-60 seconds)
- Attention threshold (0-100%)
- Emotion detection toggle
- Gaze tracking toggle
- Chart type (Bar, Pie, Line)

**Display Settings**:
- Display mode (Extended/Mirror)
- Auto-detect displays
- Target resolution (width/height)

**Sound & Alerts**:
- Warning sound enable/volume/custom file
- Finished sound enable/volume/custom file
- Test buttons for each sound

**General Preferences**:
- Language selection (English default, extensible)
- Theme (Dark/Light)
- UI font size (8-24 pixels)
- High contrast mode
- Projector optimization
- Auto-save enabled/interval

**Assets**:
- Logo upload and preview
- Branding display toggle
- Custom primary/secondary colors

## Dependencies

### Required Python Packages

All dependencies are listed in `requirements.txt`. Major packages include:

- **PyQt6** (>=6.6.0): UI framework for all interface elements
- **opencv-python** (>=4.8.0): Computer vision and image processing
- **numpy** (>=1.24.0): Numerical operations and array handling
- **Pillow** (>=10.0.0): Image processing and manipulation
- **matplotlib** (>=3.7.0): Data visualization and plotting
- **PyPDF2** (>=3.0.0): PDF file metadata handling
- **PyMuPDF** (>=1.23.0): High-performance PDF rendering (recommended, faster and better quality)
- **pdf2image** (>=1.16.0): Alternative PDF rendering (requires poppler-utils on Windows)
- **deepface** (>=0.0.79): Face analysis, emotion, age, gender detection with RetinaFace backend
- **fer** (>=22.5.0): Facial Emotion Recognition for cross-validation
- **dlib** (>=19.24.0): Face landmarks and head pose estimation (requires C++ build tools on Windows)
- **insightface** (>=0.7.3): Optional advanced face recognition backend

### System Dependencies

**PyMuPDF (Recommended)**: No additional system dependencies required - PyMuPDF includes all native libraries.

**pdf2image (Alternative)**: Requires poppler-utils system dependency on Windows:
- Download from: https://github.com/oschwartz10612/poppler-windows/releases/
- Extract to a folder (e.g., `C:\poppler`)
- Add the `bin` folder to your Windows PATH environment variable
- Restart PowerShell/terminal after adding to PATH

**Note**: PyMuPDF is recommended as it's faster, produces higher quality output, and requires no system dependencies.

## Compatibility

### Tested Hardware

- **HP Envy x360 2-in-1 Laptop**
  - AMD Ryzen 5 8640HS Processor
  - AMD Radeon 760M Graphics
  - Windows 11

### Display Support

The application is designed to work with:
- Built-in laptop displays
- External monitors (HDMI, DisplayPort, USB-C)
- Projectors (via extended display mode)
- Multiple displays simultaneously (extended desktop mode)

### Window Management

All UI windows are:
- Fully resizable
- Support fullscreen mode (F11)
- Compatible with Windows 11 window management features
- Optimized for high-DPI displays

## OBS Studio Integration

AI-Symp-Controller is fully compatible with OBS Studio for streaming and recording presentations. All modules (Timer, Media, Display Manager) are optimized for OBS Studio window capture.

### Setup Instructions

1. **Install OBS Studio**: Download and install OBS Studio from [obsproject.com](https://obsproject.com/)

2. **Timer Module Window Capture**:
   - Launch the Timer Module from the main application
   - Open OBS Studio
   - Create a new Scene (or use existing)
   - Add a new Source: **Window Capture**
   - In the Window Capture properties:
     - Select "AI-Symp-Controller - Smart Timer" from the window dropdown
     - **Window Match Priority**: Select "Match title, otherwise find window of same type"
     - Enable "Capture Cursor" if desired (recommended for presentations)
     - **Compositing**: Use "Alpha" or "Default" depending on your needs
     - Click OK

3. **Recommended OBS Settings for Timer Module**:
   - **Use Window Capture** (not Display Capture) for better performance and cleaner output
   - **Output Resolution**: Match your display/projector resolution (1920x1080 recommended)
   - **Frame Rate**: 30 FPS is sufficient for timer display
   - **Color Format**: NV12 or I420
   - **Filter Settings**: 
     - Add "Color Correction" filter if needed for brightness/contrast
     - Use "Scale Filtering" set to "Lanczos" for best quality
   - **Fullscreen Mode**: 
     - Enter fullscreen in timer window (F11) before starting OBS capture
     - This ensures optimal resolution and prevents window borders

4. **Timer Module Specific Recommendations**:
   - **Window Size**: Resize timer window to match your desired output size before capturing
   - **Background**: The timer window uses a dark theme optimized for projectors and displays
   - **Multi-Timer**: If using multiple timers, consider capturing only the active timer tab
   - **Alert Visibility**: Warning and finished alerts are designed to be clearly visible in OBS
   - **Animation Smoothness**: The circular timer animations are optimized for 30+ FPS capture

5. **Multi-Display Setup**:
   - If using extended displays, you can capture specific windows from each display
   - Create separate scenes for different display configurations
   - Timer module can be moved to projector/secondary display using Windows display settings
   - Use Display Capture for capturing projector output directly (alternative to window capture)

### Tips for Best Results

- **Run OBS Studio as Administrator** for better performance and stability
- **Test Before Live**: Always test your timer capture setup before live presentations
- **Window Visibility**: Ensure timer window is fully visible and not minimized before starting capture
- **Resolution Matching**: Match OBS output resolution to your projector/display for best quality
- **Fullscreen Usage**: Use fullscreen mode (F11) for presentations - timer scales perfectly
- **Multiple Scenes**: Create separate OBS scenes for different timer configurations
- **Performance**: Timer module is lightweight and won't impact OBS performance
- **Color Accuracy**: Timer gradient colors are designed to display accurately in OBS
- **Alert Testing**: Test warning and finished alerts to ensure they're visible in your OBS output

### Display Module OBS Integration

The Display Module provides the most flexible OBS integration:

1. **Individual Display Capture**:
   - Each display output appears as separate window: "Display Output - [Display Name]"
   - Capture individual displays separately in OBS
   - Mix and match displays in different OBS scenes

2. **Multi-Display Scenes**:
   - Create OBS scenes with multiple window captures (one per display)
   - Show timer on one display, media on another simultaneously
   - Perfect for conference halls with multiple projectors/TVs

3. **Display Module Best Practices**:
   - Put displays in fullscreen mode before capturing
   - Use Display Manager's Preview mode to verify before OBS capture
   - Each display can show different content simultaneously

### OBS Scene Composition Tips

1. **Timer Only Scene**: Capture just the timer window for clean, focused display
2. **Media Only Scene**: Capture media player for slide/video presentations
3. **Media + Timer Overlay Scene**: Capture media window with timer overlay enabled - **BEST FOR LIVE PRESENTATIONS**
   - Timer overlay appears automatically on top of media
   - Single window capture captures both media and timer
   - No need for multiple sources or compositing
   - Flicker-free, synchronized updates
4. **Display Output Scene**: Capture specific display outputs from Display Manager
5. **Multi-Display Scene**: Combine multiple display outputs in one scene
6. **Timer + Media Scene**: Use multiple sources to show timer alongside presentation slides (alternative to overlay)
7. **Picture-in-Picture**: Scale timer smaller and position it as overlay on main content
8. **Transition Effects**: Use OBS transitions when switching between scenes
9. **Hotkeys**: Set up OBS hotkeys to quickly switch between scenes during presentations
10. **Display Routing**: Use Display Manager to route different content to different displays, then capture each separately

### Troubleshooting OBS Integration

- **Window Not Found**: Ensure the module window is open and visible before capturing
- **Black Screen**: Try refreshing the window capture source in OBS
- **Performance Issues**: Use Window Capture (not Display Capture) for better performance
- **Resolution Mismatch**: Match OBS output resolution to your display/projector resolution
- **Window Title Changes**: Display output windows have consistent naming for reliable capture

## Development

### Architecture Principles

1. **Modularity**: Each module is independent and can be developed/tested separately
2. **Separation of Concerns**: Controllers handle logic, UI components handle presentation
3. **Extensibility**: New features can be added without modifying existing modules
4. **Clean Code**: Follows Python best practices with comprehensive docstrings

### Adding New Modules

To add a new module:

1. Create a new directory under `modules/`
2. Add `__init__.py` with appropriate exports
3. Create controller file(s) following existing module patterns
4. Import and integrate in `main.py`

### Code Style

- Use English for all code, comments, and UI text
- Follow PEP 8 style guidelines
- Provide docstrings for all classes and functions
- Use type hints where appropriate

## Resource Management & Performance

### Memory Optimization

The application includes several memory optimization features to ensure stable operation even with large media files:

**Image Compression:**
- Large images (>1920px) are automatically downscaled before display
- Reduces RAM usage while maintaining quality for projection
- Compression settings configurable in media settings

**Lazy Loading:**
- PDF pages are loaded on-demand (only current page in memory)
- Images stored as file paths, loaded only when displayed
- Video uses streaming (QMediaPlayer) - doesn't load entire file

**Memory Cleanup:**
- Automatic garbage collection when switching media
- Old pixmaps released before loading new content
- Force cleanup on window close

**Resource Monitoring:**
- Automatic RAM/CPU monitoring (checks every 10 seconds)
- User warnings when resources exceed thresholds (80% RAM, 90% CPU)
- Recommendations displayed when resources are high

### Auto-Backup System

**Automatic Configuration Backups:**
- Backups created periodically (default: every 5 minutes, configurable)
- Rolling backup system: keeps last 10 backups, deletes oldest
- Backups stored in `assets/backups/` directory
- Timestamped backup files: `config_backup_YYYYMMDD_HHMMSS.json`

**Backup Features:**
- Automatic backup before config save
- Manual backup via Config Manager
- Restore from backup option
- Profile backups (separate from config backups)

**Configuring Backup Interval:**
1. Open Configuration window
2. Go to "General" tab
3. Set "Backup Interval" (seconds)
4. Set to 0 to disable auto-backup

### Performance Tips

**For Optimal Performance:**

1. **Large Media Files:**
   - Images larger than 4K are automatically downscaled
   - PDF files: Only current page loaded (lazy loading)
   - Videos: Use streaming format (MP4 recommended)

2. **Face AI Module:**
   - Adjust processing rate if CPU usage is high
   - Lower FPS setting reduces CPU load
   - Process every 2nd or 3rd frame for better performance

3. **Resource Warnings:**
   - If RAM usage exceeds 80%, close unused media windows
   - Stop Face AI analysis if not needed
   - Reduce image/PDF size before loading

4. **Long Sessions:**
   - Restart application every 4-6 hours for optimal memory usage
   - Monitor resource usage in status bar
   - Use stress test script to check for leaks

### Stress Testing

Run the resource stress test to verify memory management:

```powershell
python test_resource_stress.py
```

This script tests:
- Media module load/unload cycles
- Face AI start/stop cycles
- Memory leak detection
- Resource usage monitoring

**Expected Results:**
- Memory leak < 100MB after 10 cycles
- RAM usage stays below 80% under normal load
- CPU usage returns to normal after operations complete

## Troubleshooting

### Common Issues

#### Python Not Found

**Problem**: `python` command not recognized

**Solution**:
1. Ensure Python is installed and added to PATH
2. Use `py` instead of `python` on Windows:
   ```powershell
   py main.py
   ```

#### Module Import Errors

**Problem**: `ModuleNotFoundError` when running the application

**Solution**:
1. Ensure all dependencies are installed:
   ```powershell
   pip install -r requirements.txt
   ```
2. Verify you're in the project root directory
3. Check that `modules/__init__.py` exists

#### PyQt6 Installation Issues

**Problem**: Errors installing PyQt6

**Solution**:
1. Update pip:
   ```powershell
   python -m pip install --upgrade pip
   ```
2. Install PyQt6 with verbose output:
   ```powershell
   pip install -v PyQt6
   ```
3. If issues persist, try installing pre-built wheels:
   ```powershell
   pip install --only-binary :all: PyQt6
   ```

#### Display Not Detected

**Problem**: External displays not showing in display module

**Solution**:
1. Use "Tools > Refresh Displays" in the application
2. Verify display connection in Windows Display Settings
3. Check that display is enabled in Windows settings
4. Restart the application after connecting/disconnecting displays

#### Application Won't Start

**Problem**: Application crashes on startup

**Solution**:
1. Check Python version (must be 3.11+):
   ```powershell
   python --version
   ```
2. Verify all dependencies are installed
3. Check for error messages in PowerShell console
4. Ensure you have write permissions in the project directory (for config files)

#### High Memory Usage

**Problem**: Application uses too much RAM (>80%)

**Solution**:
1. Close unused media windows
2. Stop Face AI analysis if not needed
3. Reduce image/PDF sizes before loading
4. Check for memory leaks with stress test:
   ```powershell
   python test_resource_stress.py
   ```
5. Restart application if usage continues to increase

#### Backup Files Accumulating

**Problem**: Too many backup files in `assets/backups/`

**Solution**:
1. Old backups are automatically deleted (keeps last 10)
2. To reduce backup count:
   - Open Configuration window
   - Adjust "Backup Interval" to less frequent backups
   - Manually delete old backups from `assets/backups/` folder

#### Resource Warnings

**Problem**: Frequent "Resource Warning" dialogs

**Solution**:
1. Close heavy applications running alongside
2. Reduce Face AI processing rate
3. Use smaller media files
4. Increase system RAM if consistently hitting limits
5. Check Task Manager for other resource-heavy processes

### Getting Help

If you encounter issues not covered here:
1. Check the PowerShell console for error messages
2. Verify all installation steps were completed correctly
3. Ensure your system meets the minimum requirements
4. Check that all files from the project are present

## Version History

- **1.0.0** (Current): Initial project structure and skeleton implementation
  - Modular architecture established
  - Basic UI framework with PyQt6
  - Module controllers with placeholder logic
  - Configuration management foundation

## License

[Specify your license here]

## Acknowledgments

Built with PyQt6 for Windows 11 compatibility and optimal performance on HP Envy x360 devices.

---

**Note**: This is Stage 1 of development. The current version provides the foundation and architecture. Full feature implementation will be completed in subsequent stages.

