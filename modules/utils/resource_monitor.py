"""
Resource Monitor Module

Monitors system resources (RAM, CPU) and provides optimization recommendations.
"""

import psutil
import logging
from typing import Dict, Optional, Callable, Any
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

logger = logging.getLogger(__name__)


class ResourceMonitor(QObject):
    """
    Monitors system resources and provides optimization recommendations.
    
    Features:
    - RAM usage monitoring
    - CPU usage monitoring
    - Automatic resource warnings
    - Memory cleanup recommendations
    """
    
    # Signals
    high_ram_warning = pyqtSignal(float, float, float)  # percent, used_gb, total_gb
    high_cpu_warning = pyqtSignal(float)  # percent
    resource_recovered = pyqtSignal()
    
    def __init__(self, ram_threshold: float = 80.0, cpu_threshold: float = 90.0):
        """
        Initialize resource monitor.
        
        Args:
            ram_threshold: RAM usage threshold percentage (default: 80%)
            cpu_threshold: CPU usage threshold percentage (default: 90%)
        """
        super().__init__()
        
        self._ram_threshold = ram_threshold
        self._cpu_threshold = cpu_threshold
        self._monitoring = False
        self._last_warning_time = 0.0
        self._warning_cooldown = 5.0  # Minimum seconds between warnings
        
        # Monitoring timer
        self._monitor_timer = QTimer()
        self._monitor_timer.timeout.connect(self._check_resources)
        self._monitor_timer.setInterval(2000)  # Check every 2 seconds
        
        # Callbacks for optimization actions
        self._optimization_callbacks: Dict[str, Callable] = {}
    
    def start_monitoring(self, interval_ms: int = 2000):
        """
        Start resource monitoring.
        
        Args:
            interval_ms: Monitoring interval in milliseconds
        """
        if not self._monitoring:
            self._monitor_timer.setInterval(interval_ms)
            self._monitor_timer.start()
            self._monitoring = True
            logger.info("Resource monitoring started")
    
    def stop_monitoring(self):
        """Stop resource monitoring."""
        if self._monitoring:
            self._monitor_timer.stop()
            self._monitoring = False
            logger.info("Resource monitoring stopped")
    
    def _check_resources(self):
        """Check system resources and emit warnings if needed."""
        try:
            # Check RAM
            mem = psutil.virtual_memory()
            ram_percent = mem.percent
            ram_used_gb = mem.used / (1024 ** 3)
            ram_total_gb = mem.total / (1024 ** 3)
            
            if ram_percent >= self._ram_threshold:
                import time
                current_time = time.time()
                # Cooldown to prevent spam
                if current_time - self._last_warning_time >= self._warning_cooldown:
                    self.high_ram_warning.emit(ram_percent, ram_used_gb, ram_total_gb)
                    self._last_warning_time = current_time
                    logger.warning(
                        f"High RAM usage: {ram_percent:.1f}% "
                        f"({ram_used_gb:.1f}GB / {ram_total_gb:.1f}GB)"
                    )
            else:
                # RAM recovered
                if ram_percent < self._ram_threshold - 10:  # 10% below threshold
                    self.resource_recovered.emit()
            
            # Check CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            if cpu_percent >= self._cpu_threshold:
                self.high_cpu_warning.emit(cpu_percent)
                logger.warning(f"High CPU usage: {cpu_percent:.1f}%")
        
        except Exception as e:
            logger.error(f"Error checking resources: {e}")
    
    def get_ram_usage(self) -> Dict[str, float]:
        """
        Get current RAM usage.
        
        Returns:
            Dictionary with 'percent', 'used_gb', 'total_gb', 'available_gb'
        """
        try:
            mem = psutil.virtual_memory()
            return {
                'percent': mem.percent,
                'used_gb': mem.used / (1024 ** 3),
                'total_gb': mem.total / (1024 ** 3),
                'available_gb': mem.available / (1024 ** 3)
            }
        except Exception as e:
            logger.error(f"Error getting RAM usage: {e}")
            return {'percent': 0.0, 'used_gb': 0.0, 'total_gb': 0.0, 'available_gb': 0.0}
    
    def get_cpu_usage(self) -> float:
        """
        Get current CPU usage.
        
        Returns:
            CPU usage percentage
        """
        try:
            return psutil.cpu_percent(interval=0.1)
        except Exception as e:
            logger.error(f"Error getting CPU usage: {e}")
            return 0.0
    
    def is_high_ram_usage(self, threshold: Optional[float] = None) -> bool:
        """
        Check if RAM usage is high.
        
        Args:
            threshold: Custom threshold (uses default if None)
        
        Returns:
            True if RAM usage exceeds threshold
        """
        threshold = threshold or self._ram_threshold
        ram_usage = self.get_ram_usage()
        return ram_usage['percent'] >= threshold
    
    def register_optimization_callback(self, name: str, callback: Callable):
        """
        Register a callback for optimization actions.
        
        Args:
            name: Name of the optimization action
            callback: Callback function to execute
        """
        self._optimization_callbacks[name] = callback
    
    def trigger_optimization(self, action_name: str):
        """
        Trigger an optimization action.
        
        Args:
            action_name: Name of the optimization action to trigger
        """
        if action_name in self._optimization_callbacks:
            try:
                self._optimization_callbacks[action_name]()
                logger.info(f"Optimization action triggered: {action_name}")
            except Exception as e:
                logger.error(f"Error triggering optimization {action_name}: {e}")
    
    def get_recommendations(self) -> list:
        """
        Get optimization recommendations based on current resource usage.
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        ram_usage = self.get_ram_usage()
        cpu_usage = self.get_cpu_usage()
        
        if ram_usage['percent'] >= 80:
            recommendations.append("Consider closing heavy media files")
            recommendations.append("Reduce Face AI processing rate")
            recommendations.append("Clear media cache")
        
        if ram_usage['percent'] >= 90:
            recommendations.append("Stop unnecessary modules")
            recommendations.append("Reduce image/video resolution")
        
        if cpu_usage >= 90:
            recommendations.append("Reduce Face AI FPS")
            recommendations.append("Pause non-critical processing")
        
        return recommendations


# Standalone utility functions for backward compatibility
def get_memory_usage() -> Dict[str, float]:
    """
    Get current RAM usage (standalone function).
    
    Returns:
        Dictionary with 'percent', 'used_gb', 'total_gb', 'available_gb'
    """
    try:
        mem = psutil.virtual_memory()
        return {
            'percent': mem.percent,
            'used_gb': mem.used / (1024 ** 3),
            'total_gb': mem.total / (1024 ** 3),
            'available_gb': mem.available / (1024 ** 3)
        }
    except Exception as e:
        logger.error(f"Error getting RAM usage: {e}")
        return {'percent': 0.0, 'used_gb': 0.0, 'total_gb': 0.0, 'available_gb': 0.0}


def get_cpu_usage(interval: float = 0.1) -> float:
    """
    Get current CPU usage (standalone function).
    
    Args:
        interval: Time interval for CPU measurement in seconds
    
    Returns:
        CPU usage percentage
    """
    try:
        return psutil.cpu_percent(interval=interval)
    except Exception as e:
        logger.error(f"Error getting CPU usage: {e}")
        return 0.0


def check_resource_limits(ram_threshold: float = 80.0, cpu_threshold: float = 90.0) -> Dict[str, Any]:
    """
    Check if system resources exceed thresholds (standalone function).
    
    Args:
        ram_threshold: RAM usage threshold percentage (default: 80%)
        cpu_threshold: CPU usage threshold percentage (default: 90%)
    
    Returns:
        Dictionary with 'ram_ok', 'cpu_ok', 'ram_percent', 'cpu_percent', 'warnings'
    """
    try:
        ram_usage = get_memory_usage()
        cpu_usage = get_cpu_usage()
        
        ram_ok = ram_usage['percent'] < ram_threshold
        cpu_ok = cpu_usage < cpu_threshold
        
        warnings = []
        if not ram_ok:
            warnings.append(f"High RAM usage: {ram_usage['percent']:.1f}%")
        if not cpu_ok:
            warnings.append(f"High CPU usage: {cpu_usage:.1f}%")
        
        return {
            'ram_ok': ram_ok,
            'cpu_ok': cpu_ok,
            'ram_percent': ram_usage['percent'],
            'cpu_percent': cpu_usage,
            'warnings': warnings,
            'ram_used_gb': ram_usage['used_gb'],
            'ram_total_gb': ram_usage['total_gb']
        }
    except Exception as e:
        logger.error(f"Error checking resource limits: {e}")
        return {
            'ram_ok': True,
            'cpu_ok': True,
            'ram_percent': 0.0,
            'cpu_percent': 0.0,
            'warnings': [],
            'ram_used_gb': 0.0,
            'ram_total_gb': 0.0
        }
