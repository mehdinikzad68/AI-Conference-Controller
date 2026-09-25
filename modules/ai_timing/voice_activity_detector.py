"""
Voice Activity Detection Module

Detects when presenter is speaking using speech recognition or Vosk.
Optional component for enhanced presenter tracking.
"""

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import logging
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import speech recognition libraries
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    logger.warning("speech_recognition not available. Install with: pip install SpeechRecognition")

try:
    import vosk
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    logger.warning("vosk not available. Install with: pip install vosk")


class VoiceState(Enum):
    """Voice activity states."""
    SPEAKING = "speaking"
    SILENT = "silent"
    UNKNOWN = "unknown"


class VoiceActivityDetector(QObject):
    """
    Detects voice activity from microphone input.
    
    Features:
    - Real-time speech detection
    - Silent period detection
    - Configurable silence threshold
    - Optional transcription
    """
    
    # Signals
    presenter_speaking = pyqtSignal()  # Presenter is speaking
    presenter_silent = pyqtSignal(int)  # Emits seconds of silence
    voice_activity_detected = pyqtSignal(bool)  # Emits True if speaking, False if silent
    
    def __init__(self):
        """Initialize voice activity detector."""
        super().__init__()
        
        self._is_detecting = False
        self._microphone_index = None
        self._recognizer = None
        
        # Settings
        self._silence_threshold_seconds = 3  # Seconds of silence before emitting signal
        self._energy_threshold = 300  # Audio energy threshold
        
        # State tracking
        self._current_state = VoiceState.UNKNOWN
        self._silence_duration = 0
        self._last_speech_time = None
        
        # Processing timer
        self._process_timer = QTimer()
        self._process_timer.timeout.connect(self._check_voice_activity)
        self._process_timer.setInterval(500)  # Check every 500ms
        
        # Microphone
        self._microphone = None
    
    def start_detection(self, microphone_index: Optional[int] = None):
        """
        Start voice activity detection.
        
        Args:
            microphone_index: Microphone index (None for default)
            
        Returns:
            True if started successfully, False otherwise
        """
        if self._is_detecting:
            logger.warning("Voice detection already running")
            return False
        
        if not SPEECH_RECOGNITION_AVAILABLE and not VOSK_AVAILABLE:
            logger.error("No voice detection libraries available")
            return False
        
        try:
            if SPEECH_RECOGNITION_AVAILABLE:
                self._recognizer = sr.Recognizer()
                self._microphone = sr.Microphone(device_index=microphone_index)
                
                # Adjust for ambient noise
                with self._microphone as source:
                    self._recognizer.adjust_for_ambient_noise(source, duration=1)
                
                self._recognizer.energy_threshold = self._energy_threshold
                self._microphone_index = microphone_index
                
                self._is_detecting = True
                self._process_timer.start()
                
                logger.info("Started voice activity detection with speech_recognition")
                return True
            elif VOSK_AVAILABLE:
                # Vosk implementation would go here
                logger.info("Vosk available but not yet implemented")
                return False
                
        except Exception as e:
            logger.error(f"Error starting voice detection: {e}")
            return False
    
    def stop_detection(self):
        """Stop voice activity detection."""
        if not self._is_detecting:
            return
        
        self._is_detecting = False
        self._process_timer.stop()
        
        if self._microphone:
            self._microphone = None
        
        self._recognizer = None
        self._current_state = VoiceState.UNKNOWN
        logger.info("Stopped voice activity detection")
    
    def _check_voice_activity(self):
        """Check for voice activity using non-blocking method."""
        if not self._is_detecting or not self._recognizer or not self._microphone:
            return
        
        try:
            # Use listen with timeout for non-blocking detection
            with self._microphone as source:
                try:
                    audio = self._recognizer.listen(source, timeout=0.5, phrase_time_limit=0.5)
                    
                    # Detect speech using energy threshold
                    # If audio is captured, there's likely speech
                    if audio:
                        self._on_speech_detected()
                    else:
                        self._on_silence_detected()
                        
                except sr.WaitTimeoutError:
                    # No speech detected in timeout period
                    self._on_silence_detected()
                    
        except Exception as e:
            logger.error(f"Error checking voice activity: {e}")
            self._on_silence_detected()
    
    def _on_speech_detected(self):
        """Handle speech detected."""
        from datetime import datetime
        self._last_speech_time = datetime.now()
        self._silence_duration = 0
        
        if self._current_state != VoiceState.SPEAKING:
            self._current_state = VoiceState.SPEAKING
            self.presenter_speaking.emit()
            self.voice_activity_detected.emit(True)
    
    def _on_silence_detected(self):
        """Handle silence detected."""
        from datetime import datetime, timedelta
        
        if self._last_speech_time:
            elapsed = (datetime.now() - self._last_speech_time).total_seconds()
            self._silence_duration = int(elapsed)
            
            if self._silence_duration >= self._silence_threshold_seconds:
                if self._current_state != VoiceState.SILENT:
                    self._current_state = VoiceState.SILENT
                    self.presenter_silent.emit(self._silence_duration)
                    self.voice_activity_detected.emit(False)
        else:
            # First check - initialize
            if self._current_state == VoiceState.UNKNOWN:
                self._current_state = VoiceState.SILENT
    
    def is_speaking(self) -> bool:
        """Check if presenter is currently speaking."""
        return self._current_state == VoiceState.SPEAKING
    
    def get_silence_duration(self) -> int:
        """Get current silence duration in seconds."""
        return self._silence_duration
    
    def set_silence_threshold(self, seconds: int):
        """Set silence threshold in seconds."""
        self._silence_threshold_seconds = max(1, seconds)
    
    def set_energy_threshold(self, threshold: int):
        """Set audio energy threshold."""
        self._energy_threshold = max(100, min(5000, threshold))
        if self._recognizer:
            self._recognizer.energy_threshold = self._energy_threshold

