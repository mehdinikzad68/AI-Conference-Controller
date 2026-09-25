"""
Comprehensive Load Testing Suite

Tests system behavior under heavy load and stress conditions.

Features:
- Concurrent user simulation
- Memory leak detection
- Performance benchmarks
- Stress testing
- Endurance testing

Author: AI-Symp-Controller Team
Date: November 2025
Version: 1.0
"""

import pytest
import time
import threading
import logging
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import os

logger = logging.getLogger(__name__)


class LoadTestResults:
    """Container for load test results."""
    
    def __init__(self):
        self.total_operations = 0
        self.successful_operations = 0
        self.failed_operations = 0
        self.total_time = 0.0
        self.min_time = float('inf')
        self.max_time = 0.0
        self.errors: List[str] = []
        self.memory_before = 0
        self.memory_after = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_operations == 0:
            return 0.0
        return (self.successful_operations / self.total_operations) * 100
    
    @property
    def avg_time(self) -> float:
        """Calculate average time."""
        if self.total_operations == 0:
            return 0.0
        return self.total_time / self.total_operations
    
    @property
    def memory_increase_mb(self) -> float:
        """Calculate memory increase in MB."""
        return (self.memory_after - self.memory_before) / (1024 * 1024)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'total_operations': self.total_operations,
            'successful': self.successful_operations,
            'failed': self.failed_operations,
            'success_rate': f"{self.success_rate:.1f}%",
            'avg_time': f"{self.avg_time:.3f}s",
            'min_time': f"{self.min_time:.3f}s",
            'max_time': f"{self.max_time:.3f}s",
            'memory_increase_mb': f"{self.memory_increase_mb:.2f} MB",
            'error_count': len(self.errors)
        }


class LoadTester:
    """
    Load testing framework.
    """
    
    def __init__(self):
        """Initialize load tester."""
        self.process = psutil.Process(os.getpid())
    
    def run_concurrent_test(
        self,
        operation: callable,
        num_threads: int = 10,
        iterations_per_thread: int = 100,
        operation_name: str = "operation"
    ) -> LoadTestResults:
        """
        Run concurrent load test.
        
        Args:
            operation: Function to test
            num_threads: Number of concurrent threads
            iterations_per_thread: Iterations per thread
            operation_name: Name for logging
        
        Returns:
            LoadTestResults
        """
        logger.info(f"Starting load test: {operation_name}")
        logger.info(f"Threads: {num_threads}, Iterations/thread: {iterations_per_thread}")
        
        results = LoadTestResults()
        
        # Measure initial memory
        results.memory_before = self.process.memory_info().rss
        
        def worker(thread_id: int):
            """Worker thread."""
            thread_results = {
                'success': 0,
                'failed': 0,
                'times': [],
                'errors': []
            }
            
            for i in range(iterations_per_thread):
                start_time = time.time()
                
                try:
                    operation()
                    thread_results['success'] += 1
                except Exception as e:
                    thread_results['failed'] += 1
                    thread_results['errors'].append(str(e))
                    logger.error(f"Thread {thread_id}, iteration {i}: {e}")
                
                elapsed = time.time() - start_time
                thread_results['times'].append(elapsed)
            
            return thread_results
        
        # Run threads
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, i) for i in range(num_threads)]
            
            for future in as_completed(futures):
                thread_result = future.result()
                results.successful_operations += thread_result['success']
                results.failed_operations += thread_result['failed']
                results.errors.extend(thread_result['errors'])
                
                for t in thread_result['times']:
                    results.total_time += t
                    results.min_time = min(results.min_time, t)
                    results.max_time = max(results.max_time, t)
        
        total_elapsed = time.time() - start_time
        results.total_operations = results.successful_operations + results.failed_operations
        
        # Measure final memory
        results.memory_after = self.process.memory_info().rss
        
        # Log results
        logger.info(f"Load test completed in {total_elapsed:.2f}s")
        logger.info(f"Operations: {results.total_operations}")
        logger.info(f"Success rate: {results.success_rate:.1f}%")
        logger.info(f"Avg time: {results.avg_time:.3f}s")
        logger.info(f"Memory increase: {results.memory_increase_mb:.2f} MB")
        
        return results
    
    def stress_test(
        self,
        operation: callable,
        duration_seconds: int = 60,
        target_ops_per_sec: int = 100,
        operation_name: str = "operation"
    ) -> LoadTestResults:
        """
        Run stress test (sustained load over time).
        
        Args:
            operation: Function to test
            duration_seconds: Test duration
            target_ops_per_sec: Target operations per second
            operation_name: Name for logging
        
        Returns:
            LoadTestResults
        """
        logger.info(f"Starting stress test: {operation_name}")
        logger.info(f"Duration: {duration_seconds}s, Target: {target_ops_per_sec} ops/s")
        
        results = LoadTestResults()
        results.memory_before = self.process.memory_info().rss
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        operation_interval = 1.0 / target_ops_per_sec if target_ops_per_sec > 0 else 0
        
        while time.time() < end_time:
            op_start = time.time()
            
            try:
                operation()
                results.successful_operations += 1
            except Exception as e:
                results.failed_operations += 1
                results.errors.append(str(e))
            
            op_time = time.time() - op_start
            results.total_time += op_time
            results.min_time = min(results.min_time, op_time)
            results.max_time = max(results.max_time, op_time)
            
            # Sleep to maintain target rate
            sleep_time = operation_interval - op_time
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        results.total_operations = results.successful_operations + results.failed_operations
        results.memory_after = self.process.memory_info().rss
        
        actual_duration = time.time() - start_time
        actual_ops_per_sec = results.total_operations / actual_duration
        
        logger.info(f"Stress test completed")
        logger.info(f"Actual ops/s: {actual_ops_per_sec:.1f}")
        logger.info(f"Success rate: {results.success_rate:.1f}%")
        
        return results


# ===== Test Cases =====

class TestAgendaManagerLoad:
    """Load tests for AgendaManager."""
    
    @pytest.fixture
    def agenda_manager(self):
        """Create AgendaManager."""
        from modules.symposium.agenda_manager import AgendaManager
        return AgendaManager()
    
    def test_concurrent_add_sessions(self, agenda_manager):
        """Test adding sessions concurrently."""
        from modules.symposium.agenda_manager import AgendaItem, SpeakerInfo
        
        counter = {'value': 0}
        lock = threading.Lock()
        
        def add_session():
            with lock:
                session_id = f"session_{counter['value']:04d}"
                counter['value'] += 1
            
            item = AgendaItem(
                session_id=session_id,
                start_time=f"09:{counter['value'] % 60:02d}",
                speaker=SpeakerInfo(
                    name=f"Speaker {session_id}",
                    title=f"Talk {session_id}",
                    duration_minutes=30
                )
            )
            
            agenda_manager.add_agenda_item(item, validate=False)
        
        tester = LoadTester()
        results = tester.run_concurrent_test(
            add_session,
            num_threads=10,
            iterations_per_thread=50,
            operation_name="add_session"
        )
        
        # Assertions
        assert results.success_rate > 95.0, f"Success rate too low: {results.success_rate}%"
        assert results.memory_increase_mb < 50, f"Memory leak suspected: {results.memory_increase_mb} MB"
        
        print("\n=== Concurrent Add Sessions Results ===")
        print(results.to_dict())


class TestConfigManagerLoad:
    """Load tests for ConfigManager."""
    
    @pytest.fixture
    def config_manager(self, tmp_path):
        """Create ConfigManager."""
        from modules.config.config_manager import ConfigManager
        config_file = tmp_path / "test_config.json"
        return ConfigManager(str(config_file))
    
    def test_concurrent_read_write(self, config_manager):
        """Test concurrent read/write operations."""
        
        counter = {'value': 0}
        
        def read_write_operation():
            # Write
            config_manager.set('test_key', f"value_{counter['value']}")
            counter['value'] += 1
            
            # Read
            _ = config_manager.get('test_key', 'default')
        
        tester = LoadTester()
        results = tester.run_concurrent_test(
            read_write_operation,
            num_threads=20,
            iterations_per_thread=100,
            operation_name="config_read_write"
        )
        
        # Assertions
        assert results.success_rate > 95.0
        assert results.avg_time < 0.01  # Should be fast
        
        print("\n=== Concurrent Read/Write Results ===")
        print(results.to_dict())


class TestTimeValidatorLoad:
    """Load tests for TimeValidator."""
    
    def test_validation_performance(self):
        """Test time validation performance under load."""
        from modules.symposium.time_validator import TimeValidator
        
        times = [f"{h:02d}:{m:02d}" for h in range(24) for m in range(0, 60, 5)]
        idx = {'value': 0}
        
        def validate_time():
            time_str = times[idx['value'] % len(times)]
            idx['value'] += 1
            
            TimeValidator.validate_time_format(time_str)
            TimeValidator.normalize_time(time_str)
        
        tester = LoadTester()
        results = tester.stress_test(
            validate_time,
            duration_seconds=10,
            target_ops_per_sec=1000,
            operation_name="time_validation"
        )
        
        # Assertions
        assert results.success_rate == 100.0
        assert results.avg_time < 0.001  # Should be very fast
        
        print("\n=== Time Validation Performance ===")
        print(results.to_dict())


class TestMemoryLeaks:
    """Tests for memory leak detection."""
    
    def test_timer_controller_memory(self):
        """Test timer controller for memory leaks."""
        from modules.timer.timer_controller import TimerController
        from PyQt6.QtCore import QCoreApplication
        
        # Need QApplication for QTimer
        import sys
        app = QCoreApplication.instance()
        if app is None:
            app = QCoreApplication(sys.argv)
        
        process = psutil.Process(os.getpid())
        
        # Measure baseline
        baseline = process.memory_info().rss / (1024 * 1024)
        
        # Create and destroy many timers
        for i in range(100):
            controller = TimerController()
            controller.start_timer(60)
            time.sleep(0.01)
            controller.stop_timer()
            del controller
        
        # Measure after
        after = process.memory_info().rss / (1024 * 1024)
        
        increase = after - baseline
        
        print(f"\n=== Memory Leak Test ===")
        print(f"Baseline: {baseline:.2f} MB")
        print(f"After 100 cycles: {after:.2f} MB")
        print(f"Increase: {increase:.2f} MB")
        
        # Should not increase by more than 10 MB
        assert increase < 10, f"Memory leak detected: {increase:.2f} MB increase"


# Run all tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

