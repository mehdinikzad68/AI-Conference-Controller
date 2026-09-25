"""
Face AI module for AI-Symp-Controller.

Provides audience attention and reaction analysis using AI/computer vision.
Uses DeepFace (RetinaFace), FER, and dlib for comprehensive face analysis.
"""

from .face_ai_controller import FaceAIController
from .face_ai_window import FaceAIWindow
from .face_analyzer import FaceAnalyzer
from .head_pose_estimator import HeadPoseEstimator
from .statistics_aggregator import StatisticsAggregator

__all__ = [
    'FaceAIController',
    'FaceAIWindow',
    'FaceAnalyzer',
    'HeadPoseEstimator',
    'StatisticsAggregator'
]

