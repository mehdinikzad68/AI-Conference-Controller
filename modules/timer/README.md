# Timer Module

Advanced smart animated timer module for AI-Symp-Controller.

## Quick Start

### Standalone Demo
```powershell
python modules/timer/test_timer.py
```

### From Main Application
1. Launch `python main.py`
2. Click "Timer Module" button
3. Set time and start timer

## Features

- ✅ Animated circular countdown timer with smooth progress ring
- ✅ Gradient color transitions (green → yellow → red)
- ✅ Large digital time display (MM:SS format)
- ✅ Time input controls (slider + numeric input)
- ✅ Full control set (Start, Pause, Resume, Reset)
- ✅ Multi-timer support with tabs
- ✅ **AI-Driven Adaptive Timing (Beta)**:
  - Enable/disable AI Timer toggle
  - Real-time presenter state tracking (speaking, engaged, away)
  - Audience engagement analysis with attention percentage
  - Automatic pause/slow when engagement drops
  - Extension requests for high engagement (with operator confirmation)
  - Manual override controls (Pause, Resume, Override AI)
  - Live event log for AI-driven adjustments
  - Visual alerts for AI actions and warnings
- ✅ Fullscreen mode (F11)
- ✅ Visual alerts:
  - Red flashing ring when < 2 minutes
  - "TIME ENDING SOON" overlay
  - Shake animation effects
  - "END OF SPEECH" display when finished
  - AI-driven warnings and alerts
- ✅ Audio alerts (warning and finished beeps)
- ✅ OBS Studio optimized design

## Files

- `timer_controller.py` - Core timer logic with QTimer
- `circular_timer_widget.py` - Custom animated circular timer widget
- `timer_window.py` - Main window with all UI and controls
- `ai_timer_widget.py` - AI Timer UI component with status, metrics, and controls
- `test_timer.py` - Standalone demo script
- `generate_sounds.py` - Utility to generate alert sounds

## Generating Sounds

Alert sounds are automatically generated on first run. To regenerate manually:

```powershell
python modules/timer/generate_sounds.py
```

This creates:
- `assets/warning_beep.wav` - Warning alert (< 2 minutes)
- `assets/finished_beep.wav` - Timer finished alert

You can replace these with custom sound files.

## Usage Tips

1. **For Projectors**: Use fullscreen mode (F11) for best visibility
2. **Multi-Speaker Events**: Use "+ Add Timer" to create separate timers
3. **OBS Integration**: Capture the timer window using Window Capture
4. **Time Setting**: Use sliders for quick adjustment or input box for precise time
5. **Keyboard Shortcuts**: F11 (fullscreen), Ctrl+N (new timer), Ctrl+Q (exit)

## AI Timer Usage (Beta)

The AI Timer feature provides intelligent, adaptive timing based on presenter and audience engagement.

### Enabling AI Timer

1. Open a timer tab
2. Scroll down to the "AI Timer / Smart Timing (Beta)" section
3. Check "Enable AI Timer" checkbox
4. Ensure camera is connected and Face AI models are loaded

### AI Timer Features

- **AI Status**: Shows current state (Inactive, Waiting, Active)
- **Presenter State**: Real-time tracking of presenter activity (Talking, Engaged, Away, Disengaged)
- **Audience Focus**: Progress bar showing audience attention percentage (0-100%)
- **AI Actions/Alerts**: Messages for pause/resume reasons, extension requests, warnings
- **Manual Controls**:
  - **Pause AI Timer**: Manually pause the timer
  - **Resume AI Timer**: Manually resume the timer
  - **Override AI**: Disable AI adaptation and return to normal operation
- **Event Log**: Scrollable log showing all AI-driven timer adjustments with timestamps

### How AI Timer Works

1. **Presenter Tracking**: Uses Face AI to detect if presenter is looking at audience, speaking, or away
2. **Audience Analysis**: Analyzes audience camera feed for engagement level (high/medium/low)
3. **Adaptive Behavior**:
   - **Pause/Slow**: When presenter is away or audience engagement drops to "low", timer pauses or slows
   - **Extension Requests**: When engagement is consistently high, AI may suggest extending time (requires operator confirmation)
4. **Operator Override**: Operator can always override AI decisions using the override button

### Requirements

- Camera connected and accessible
- Face AI module configured with models loaded
- Voice Activity Detection (optional, can be disabled)

### Troubleshooting

- **"AI Timer Start Failed"**: Check camera connection and Face AI model loading
- **Presenter state stuck on "Unknown"**: Ensure presenter camera feed is working
- **Audience focus at 0%**: Check audience camera feed and Face AI detection

## Technical Details

- Built with PyQt6
- Uses QPropertyAnimation for smooth animations
- Signal-based architecture for event handling
- Responsive design optimized for various screen sizes
- Dark theme optimized for projector displays

