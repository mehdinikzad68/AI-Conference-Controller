# Symposium Display & Smart Timing Module

Comprehensive symposium presentation system with agenda display, speaker introductions, smart timer overlays, and seamless scene switching.

## Features

### 1. Global Symposium Agenda Display
- Full event agenda with titles, speaker names, and times
- Clean, professional layout
- Symposium branding (logo, title, date, location)
- Scrollable for long agendas

### 2. Speaker Introduction & Session Transition
- Full-screen speaker intro slide before each talk
- Speaker photo (optional), name, title, duration
- Automatic or manual transition to session media
- Branded logo slide if no speaker media provided

### 3. Dynamic Smart Timer Overlay & Progress Bar
- Horizontal progress bar (fills/shrinks based on time)
- Color transitions: Green (start) → Yellow (middle) → Red (last 20%)
- Precise time display (mm:ss)
- Semi-transparent, non-intrusive design
- Position presets: bottom/top corners, center
- Adjustable size and opacity

### 4. Last 20% Time Warning
- Visual warning at 20% time remaining
- Animated pulsing border
- Blinking timer/bar effect
- Warning message ("X minutes left!")
- Optional audio chime

### 5. Overlay Non-intrusiveness
- Positioned to avoid obscuring content
- Configurable position and transparency
- Auto-hides when not in session

### 6. Full OBS Integration
- Window title includes "[OBS]" for easy identification
- Optimized for Window Capture
- Smooth animations and transitions
- Fullscreen support

### 7. Modular Scene Switching
- Seamless transitions between:
  - Agenda view
  - Speaker intro
  - Active session
  - Logo/branding slide
  - Break/intermission screen
- Keyboard shortcuts for quick switching
- Hotkey support for control room operators

## Usage

### Starting the Symposium Display

1. Click "Symposium Display" button in main window
2. Load agenda from JSON file (see format below)
3. Use keyboard shortcuts or UI controls to navigate

### Keyboard Shortcuts

- **F1** - Show Agenda
- **F2** - Show Speaker Intro
- **F3** - Show Session (with media)
- **F4** - Show Logo/Branding
- **F5** - Show Break Screen
- **Space** - Pause/Resume session
- **Ctrl+N** - Next session
- **Ctrl+P** - Previous session

### Agenda JSON Format

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
        "bio": "Expert in computer vision and deep learning...",
        "duration_minutes": 30,
        "media_path": "media/session01.pdf",
        "email": "sarah@mit.edu"
      },
      "notes": ""
    }
  ]
}
```

### Session Workflow

1. **Load Agenda**: Load JSON file with agenda data
2. **Show Agenda**: Press F1 to display full agenda
3. **Start Session**: Navigate to session and start
4. **Speaker Intro**: Automatically shows intro slide
5. **Session**: Media loads if available, timer starts
6. **Warning**: At 20% remaining, visual/audio warnings activate
7. **End Session**: Timer finishes, returns to logo

### Overlay Configuration

- **Position**: Bottom Center (default), corners, top
- **Width**: 40% of screen width (adjustable)
- **Height**: 60 pixels (adjustable)
- **Opacity**: 85% (adjustable)
- **Warning Threshold**: 20% (configurable)

## File Structure

```
modules/symposium/
├── __init__.py              # Module exports
├── agenda_manager.py        # Agenda and speaker management
├── session_controller.py    # Session lifecycle control
├── smart_timer_overlay.py   # Enhanced timer with progress bar
├── scene_manager.py         # Scene switching system
├── symposium_window.py      # Main display window
├── agenda_display_widget.py # Agenda UI widget
├── speaker_intro_widget.py  # Speaker intro UI widget
├── test_symposium.py        # Test script
└── README.md               # This file
```

## Integration with Other Modules

### Media Module
- Uses `MediaDisplayWidget` for PDF, PPT, video, images
- Automatic media detection and loading
- Fallback to logo slide if no media

### Timer Module
- Uses `TimerController` for timing
- Enhanced with progress bar overlay
- 20% warning threshold support

### Display Module
- OBS-compatible window naming
- Fullscreen support for projectors
- Multi-display ready

## Testing

Run the test script:

```bash
python modules/symposium/test_symposium.py
```

This demonstrates:
- Agenda display
- Speaker intro slides
- Smart timer overlay
- Scene switching
- Warning effects

## Operator Workflow

### Pre-Event Setup
1. Create agenda JSON file
2. Add speaker photos (optional)
3. Add media files (PDF, PPT, videos)
4. Test on projector/OBS

### During Event
1. Open Symposium Display window
2. Load agenda
3. Use F1 to show agenda at start
4. Navigate sessions with Ctrl+N/Ctrl+P
5. Monitor timer and warnings
6. Switch scenes as needed (F1-F5)

### Post-Event
1. Agenda and session data saved
2. Can export session logs
3. Review timing data

## Troubleshooting

### Timer Overlay Not Showing
- Check if session is active (F3)
- Verify overlay position settings
- Check opacity settings

### Media Not Loading
- Verify file paths in agenda JSON
- Check file permissions
- Ensure media module dependencies installed

### Scene Not Switching
- Check keyboard shortcuts
- Verify scene manager state
- Check console for errors

## Future Enhancements

- Live agenda editing
- Speaker Q&A timer
- Networking break timers
- Export session recordings
- Live streaming integration
- Mobile app remote control

