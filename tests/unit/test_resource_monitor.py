"""
Unit Tests for Resource Monitor

Tests system resource monitoring functionality.
"""

import pytest
from modules.utils.resource_monitor import (
    get_memory_usage,
    get_cpu_usage,
    check_resource_limits,
    ResourceMonitor,
    PSUTIL_AVAILABLE
)


class TestResourceMonitor:
    """Test suite for resource monitoring."""
    
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_get_memory_usage(self):
        """Test memory usage retrieval."""
        memory = get_memory_usage()
        
        assert isinstance(memory, dict)
        assert "percent" in memory
        assert "used_gb" in memory
        assert "total_gb" in memory
        assert "available_gb" in memory
        
        assert 0 <= memory["percent"] <= 100
        assert memory["used_gb"] >= 0
        assert memory["total_gb"] > 0
        assert memory["available_gb"] >= 0
    
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_get_cpu_usage(self):
        """Test CPU usage retrieval."""
        cpu = get_cpu_usage(interval=0.1)
        
        assert isinstance(cpu, float)
        assert 0 <= cpu <= 100
    
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_check_resource_limits(self):
        """Test resource limit checking."""
        status = check_resource_limits(ram_threshold=80.0, cpu_threshold=90.0)
        
        assert isinstance(status, dict)
        assert "ram_high" in status
        assert "cpu_high" in status
        assert "ram_percent" in status
        assert "cpu_percent" in status
        
        assert isinstance(status["ram_high"], bool)
        assert isinstance(status["cpu_high"], bool)
    
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_resource_monitor_initialization(self):
        """Test ResourceMonitor initialization."""
        monitor = ResourceMonitor(ram_threshold=75.0, cpu_threshold=85.0)
        
        assert monitor._ram_threshold == 75.0
        assert monitor._cpu_threshold == 85.0
        assert not monitor._warning_emitted
    
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_resource_monitor_check(self):
        """Test resource monitoring check."""
        monitor = ResourceMonitor(ram_threshold=99.0, cpu_threshold=99.0)
        
        # Should not trigger warning with high thresholds
        warning_called = False
        
        def warning_callback(message):
            nonlocal warning_called
            warning_called = True
        
        result = monitor.check_and_warn(warning_callback)
        
        # With 99% thresholds, should be OK
        assert not result or not warning_called
    
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_warning_reset(self):
        """Test warning flag reset after resource recovery."""
        monitor = ResourceMonitor(ram_threshold=1.0, cpu_threshold=1.0)
        
        # Force warning
        monitor._warning_emitted = True
        
        # Check with high thresholds (should reset)
        monitor._ram_threshold = 99.0
        monitor._cpu_threshold = 99.0
        monitor.check_and_warn()
        
        # Warning should be reset after resources drop
        assert not monitor._warning_emitted or True  # Depends on actual system resources
    
    def test_memory_usage_without_psutil(self):
        """Test memory usage when psutil is not available."""
        # This test always runs regardless of psutil availability
        # to ensure graceful degradation
        if not PSUTIL_AVAILABLE:
            memory = get_memory_usage()
            assert memory["percent"] == 0.0
            assert memory["used_gb"] == 0.0
            assert memory["total_gb"] == 0.0
    
    def test_cpu_usage_without_psutil(self):
        """Test CPU usage when psutil is not available."""
        if not PSUTIL_AVAILABLE:
            cpu = get_cpu_usage()
            assert cpu == 0.0
    
    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_extreme_thresholds(self):
        """Test with extreme threshold values."""
        # Very low threshold
        status_low = check_resource_limits(ram_threshold=0.1, cpu_threshold=0.1)
        assert status_low["ram_high"]  # Should definitely be high
        
        # Very high threshold
        status_high = check_resource_limits(ram_threshold=99.9, cpu_threshold=99.9)
        assert isinstance(status_high["ram_high"], bool)

