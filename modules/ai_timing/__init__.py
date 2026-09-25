"""
AI-Driven Adaptive Timing Module

Smart timer and presentation system with AI-based attention/emotion analysis
and real-time adaptive timing based on presenter and audience engagement.
"""

from .ai_integration_controller import AIIntegrationController
from .presenter_tracker import PresenterTracker
from .voice_activity_detector import VoiceActivityDetector
from .adaptive_timer_controller import AdaptiveTimerController
from .engagement_analyzer import EngagementAnalyzer
from .operator_dashboard import OperatorDashboard
from .session_report_generator import SessionReportGenerator

__all__ = [
    'AIIntegrationController',
    'PresenterTracker',
    'VoiceActivityDetector',
    'AdaptiveTimerController',
    'EngagementAnalyzer',
    'OperatorDashboard',
    'SessionReportGenerator'
]
