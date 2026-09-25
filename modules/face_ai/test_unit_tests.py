"""
Unit Tests for Face AI Module

Simple unit tests for core functionality validation.
Run with: python -m pytest modules/face_ai/test_unit_tests.py
Or: python modules/face_ai/test_unit_tests.py
"""

import sys
import unittest
from pathlib import Path
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from modules.face_ai.face_analyzer import FaceAnalyzer, DEEPFACE_AVAILABLE, FER_AVAILABLE
    from modules.face_ai.head_pose_estimator import HeadPoseEstimator, DLIB_AVAILABLE
    from modules.face_ai.statistics_aggregator import StatisticsAggregator
    from modules.face_ai.face_ai_controller import FaceAIController
    IMPORTS_OK = True
except ImportError as e:
    print(f"Import error: {e}")
    IMPORTS_OK = False


class TestFaceAnalyzer(unittest.TestCase):
    """Test FaceAnalyzer functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not IMPORTS_OK:
            self.skipTest("Required imports failed")
        self.analyzer = FaceAnalyzer()
    
    def test_initialization(self):
        """Test FaceAnalyzer initialization."""
        self.assertIsNotNone(self.analyzer)
        self.assertEqual(self.analyzer._detector_backend, 'retinaface')
        self.assertEqual(self.analyzer._model_name, 'VGG-Face')
    
    def test_preprocess_frame(self):
        """Test frame preprocessing."""
        # Create a dummy frame (480x640x3)
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        processed = self.analyzer.preprocess_frame(frame)
        
        self.assertIsNotNone(processed)
        self.assertEqual(processed.shape, frame.shape)
        self.assertEqual(processed.dtype, frame.dtype)
    
    def test_analyze_frame_without_dependencies(self):
        """Test analyze_frame gracefully handles missing dependencies."""
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Should not crash even if dependencies missing
        result = self.analyzer.analyze_frame(frame)
        self.assertIsInstance(result, list)
    
    def test_dependency_flags(self):
        """Test dependency availability flags."""
        # These should be booleans
        self.assertIsInstance(DEEPFACE_AVAILABLE, bool)
        self.assertIsInstance(FER_AVAILABLE, bool)


class TestHeadPoseEstimator(unittest.TestCase):
    """Test HeadPoseEstimator functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not IMPORTS_OK:
            self.skipTest("Required imports failed")
        self.estimator = HeadPoseEstimator()
    
    def test_initialization(self):
        """Test HeadPoseEstimator initialization."""
        self.assertIsNotNone(self.estimator)
    
    def test_estimate_pose_without_model(self):
        """Test pose estimation gracefully handles missing model."""
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        face_box = (100, 100, 200, 200)  # x, y, w, h
        
        # Should not crash even if model missing
        result = self.estimator.estimate_pose(frame, face_box)
        self.assertIsInstance(result, dict)
        
        # Should have expected keys (note: key might be 'attention_direction' instead of 'direction')
        self.assertIn('yaw', result)
        self.assertIn('pitch', result)
        self.assertIn('roll', result)
        self.assertIn('confidence', result)
        # Check for either 'direction' or 'attention_direction'
        self.assertTrue('direction' in result or 'attention_direction' in result)


class TestStatisticsAggregator(unittest.TestCase):
    """Test StatisticsAggregator functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not IMPORTS_OK:
            self.skipTest("Required imports failed")
        self.aggregator = StatisticsAggregator()
    
    def test_initialization(self):
        """Test StatisticsAggregator initialization."""
        self.assertIsNotNone(self.aggregator)
        self.assertEqual(self.aggregator._frames_processed, 0)
        self.assertEqual(self.aggregator._total_faces_detected, 0)
    
    def test_start_session(self):
        """Test session start."""
        self.aggregator.start_session()
        self.assertIsNotNone(self.aggregator._session_start)
    
    def test_add_frame_results(self):
        """Test adding frame results."""
        faces = [
            {
                'emotion': 'happy',
                'age': 25,
                'gender': 'Man',
                'emotion_confidence': 0.8
            }
        ]
        head_poses = [
            {
                'direction': 'focused',
                'confidence': 0.9
            }
        ]
        
        self.aggregator.add_frame_results(faces, head_poses)
        self.assertEqual(self.aggregator._frames_processed, 1)
        self.assertEqual(self.aggregator._total_faces_detected, 1)
    
    def test_get_statistics(self):
        """Test getting statistics."""
        stats = self.aggregator.get_statistics()
        self.assertIsInstance(stats, dict)
        self.assertIn('session_duration_seconds', stats)
        self.assertIn('frames_processed', stats)
        self.assertIn('total_faces_detected', stats)
        self.assertIn('average_attention', stats)
        self.assertIn('emotion_distribution', stats)
        self.assertIn('attention_distribution', stats)


class TestFaceAIController(unittest.TestCase):
    """Test FaceAIController functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not IMPORTS_OK:
            self.skipTest("Required imports failed")
        
        try:
            from PyQt6.QtWidgets import QApplication
            import sys
            if not QApplication.instance():
                self.app = QApplication(sys.argv)
            else:
                self.app = QApplication.instance()
        except:
            self.skipTest("QApplication not available")
        
        self.controller = FaceAIController()
    
    def test_initialization(self):
        """Test FaceAIController initialization."""
        self.assertIsNotNone(self.controller)
        self.assertFalse(self.controller._is_analyzing)
        self.assertEqual(self.controller._attention_threshold, 0.5)
    
    def test_process_frame_with_empty_frame(self):
        """Test processing empty frame."""
        empty_frame = None
        result = self.controller.process_frame(empty_frame)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['faces_count'], 0)
        self.assertEqual(result['attention_level'], 0.0)
    
    def test_process_frame_with_valid_frame(self):
        """Test processing valid frame."""
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        result = self.controller.process_frame(frame)
        
        self.assertIsInstance(result, dict)
        self.assertIn('faces_count', result)
        self.assertIn('faces', result)
        self.assertIn('head_poses', result)
        self.assertIn('attention_level', result)
        self.assertIn('reactions', result)
    
    def test_stop_without_starting(self):
        """Test stopping analysis without starting."""
        # Should not crash
        self.controller.stop_analysis()
        self.assertFalse(self.controller._is_analyzing)


class TestErrorHandling(unittest.TestCase):
    """Test error handling robustness."""
    
    def test_invalid_frame_types(self):
        """Test handling of invalid frame types."""
        if not IMPORTS_OK:
            self.skipTest("Required imports failed")
        
        controller = FaceAIController()
        
        # Test None
        result = controller.process_frame(None)
        self.assertIsInstance(result, dict)
        
        # Test empty array
        empty = np.array([])
        result = controller.process_frame(empty)
        self.assertIsInstance(result, dict)
        
        # Test wrong shape (should still try to process)
        wrong_shape = np.random.randint(0, 255, (100,), dtype=np.uint8)
        result = controller.process_frame(wrong_shape)
        self.assertIsInstance(result, dict)


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    if IMPORTS_OK:
        suite.addTests(loader.loadTestsFromTestCase(TestFaceAnalyzer))
        suite.addTests(loader.loadTestsFromTestCase(TestHeadPoseEstimator))
        suite.addTests(loader.loadTestsFromTestCase(TestStatisticsAggregator))
        suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
        
        # Only add controller tests if QApplication available
        try:
            from PyQt6.QtWidgets import QApplication
            suite.addTests(loader.loadTestsFromTestCase(TestFaceAIController))
        except:
            print("Skipping controller tests (QApplication not available)")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

