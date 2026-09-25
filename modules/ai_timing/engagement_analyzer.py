"""
Engagement Analyzer Module

Analyzes audience engagement level from face AI controller results.
Categorizes engagement as 'high', 'medium', or 'low' based on attention and emotion metrics.
"""

from PyQt6.QtCore import QObject, pyqtSignal
import logging
from typing import Dict, List
from enum import Enum

logger = logging.getLogger(__name__)


class EngagementLevel(Enum):
    """Engagement level categories."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class EngagementAnalyzer(QObject):
    """
    Analyzes audience engagement from face AI analysis results.
    
    Features:
    - Real-time engagement level calculation
    - Attention-based categorization
    - Emotion-based weighting
    - Threshold-based classification
    """
    
    # Signals
    engagement_level_changed = pyqtSignal(str)  # Emits "high", "medium", or "low"
    attention_percentage_changed = pyqtSignal(float)  # Emits 0.0-1.0
    emotion_distribution_changed = pyqtSignal(dict)  # Emits emotion counts
    
    def __init__(self):
        """Initialize engagement analyzer."""
        super().__init__()
        
        # Thresholds
        self._high_threshold = 0.7  # 70% attention for "high"
        self._medium_threshold = 0.4  # 40% attention for "medium"
        
        # Current state
        self._current_level = EngagementLevel.UNKNOWN
        self._current_attention_percentage = 0.0
        self._emotion_distribution = {}
        
        # History for stability
        self._attention_history = []
        self._history_size = 10
    
    def analyze_frame(self, attention_level: float, emotion_counts: Dict[str, int], face_count: int):
        """
        Analyze engagement from frame results.
        
        Args:
            attention_level: Overall attention level (0.0-1.0)
            emotion_counts: Dictionary of emotion counts
            face_count: Number of faces detected
        """
        # Update attention history
        self._attention_history.append(attention_level)
        if len(self._attention_history) > self._history_size:
            self._attention_history.pop(0)
        
        # Calculate smoothed attention (average of recent frames)
        if self._attention_history:
            smoothed_attention = sum(self._attention_history) / len(self._attention_history)
        else:
            smoothed_attention = attention_level
        
        self._current_attention_percentage = smoothed_attention
        
        # Update emotion distribution
        self._emotion_distribution = emotion_counts.copy()
        
        # Calculate engagement level
        engagement_level = self._calculate_engagement_level(smoothed_attention, emotion_counts, face_count)
        
        # Emit signals if changed
        if engagement_level != self._current_level:
            self._current_level = engagement_level
            self.engagement_level_changed.emit(engagement_level.value)
        
        self.attention_percentage_changed.emit(smoothed_attention)
        self.emotion_distribution_changed.emit(emotion_counts)
    
    def _calculate_engagement_level(self, attention: float, emotions: Dict[str, int], face_count: int) -> EngagementLevel:
        """
        Calculate engagement level from metrics.
        
        Args:
            attention: Attention percentage (0.0-1.0)
            emotions: Emotion distribution
            face_count: Number of faces
            
        Returns:
            EngagementLevel enum
        """
        if face_count == 0:
            return EngagementLevel.UNKNOWN
        
        # Calculate positive emotion ratio
        positive_emotions = ['happy', 'surprise']
        negative_emotions = ['sad', 'angry', 'fear']
        
        total_emotions = sum(emotions.values())
        if total_emotions > 0:
            positive_ratio = sum(emotions.get(e, 0) for e in positive_emotions) / total_emotions
            negative_ratio = sum(emotions.get(e, 0) for e in negative_emotions) / total_emotions
        else:
            positive_ratio = 0.0
            negative_ratio = 0.0
        
        # Weight attention with emotion
        # Positive emotions boost engagement, negative reduce it
        adjusted_attention = attention * (1.0 + positive_ratio * 0.2 - negative_ratio * 0.3)
        adjusted_attention = max(0.0, min(1.0, adjusted_attention))
        
        # Classify based on thresholds
        if adjusted_attention >= self._high_threshold:
            return EngagementLevel.HIGH
        elif adjusted_attention >= self._medium_threshold:
            return EngagementLevel.MEDIUM
        else:
            return EngagementLevel.LOW
    
    def get_current_level(self) -> str:
        """Get current engagement level as string."""
        return self._current_level.value
    
    def get_attention_percentage(self) -> float:
        """Get current attention percentage."""
        return self._current_attention_percentage
    
    def is_high_engagement(self) -> bool:
        """Check if engagement is high."""
        return self._current_level == EngagementLevel.HIGH
    
    def is_medium_or_high(self) -> bool:
        """Check if engagement is medium or high."""
        return self._current_level in [EngagementLevel.MEDIUM, EngagementLevel.HIGH]
    
    def set_high_threshold(self, threshold: float):
        """Set high engagement threshold."""
        self._high_threshold = max(0.0, min(1.0, threshold))
    
    def set_medium_threshold(self, threshold: float):
        """Set medium engagement threshold."""
        self._medium_threshold = max(0.0, min(1.0, threshold))

