"""
Thread Pool Manager Module

Manages thread pools for concurrent operations with resource-aware limits.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Callable
import psutil

logger = logging.getLogger(__name__)


class ThreadPoolManager:
    """
    Manages thread pools with dynamic worker limits based on system resources.
    
    Features:
    - Automatic worker count adjustment based on RAM/CPU
    - Resource-aware task scheduling
    - Memory cleanup after task completion
    """
    
    def __init__(self, max_workers: Optional[int] = None, adaptive: bool = True):
        """
        Initialize thread pool manager.
        
        Args:
            max_workers: Maximum number of workers (auto-calculated if None)
            adaptive: Enable adaptive worker count based on resources
        """
        self._adaptive = adaptive
        self._base_max_workers = max_workers or self._calculate_optimal_workers()
        self._executor: Optional[ThreadPoolExecutor] = None
        self._current_workers = self._base_max_workers
    
    def _calculate_optimal_workers(self) -> int:
        """
        Calculate optimal number of workers based on system resources.
        
        Returns:
            Optimal worker count (typically 2-3 for media/face AI)
        """
        try:
            # Get CPU count
            cpu_count = psutil.cpu_count(logical=False) or 2
            
            # Get RAM info
            mem = psutil.virtual_memory()
            ram_gb = mem.total / (1024 ** 3)
            
            # Calculate based on resources
            # For media/face AI: 2-3 workers is optimal
            if ram_gb < 8:
                # Low RAM: limit workers
                optimal = min(2, cpu_count)
            elif ram_gb < 16:
                # Medium RAM: moderate workers
                optimal = min(3, cpu_count)
            else:
                # High RAM: can use more workers
                optimal = min(4, cpu_count)
            
            logger.info(f"Optimal worker count: {optimal} (CPU: {cpu_count}, RAM: {ram_gb:.1f}GB)")
            return optimal
        
        except Exception as e:
            logger.warning(f"Error calculating optimal workers: {e}, using default: 2")
            return 2
    
    def get_executor(self) -> ThreadPoolExecutor:
        """
        Get or create thread pool executor.
        
        Returns:
            ThreadPoolExecutor instance
        """
        if self._executor is None or self._adaptive:
            # Recalculate if adaptive
            if self._adaptive:
                self._current_workers = self._calculate_optimal_workers()
            
            # Create new executor if needed
            if self._executor is None or self._current_workers != self._base_max_workers:
                if self._executor is not None:
                    self._executor.shutdown(wait=False)
                
                self._executor = ThreadPoolExecutor(max_workers=self._current_workers)
                logger.info(f"Thread pool created with {self._current_workers} workers")
        
        return self._executor
    
    def submit(self, fn: Callable, *args, **kwargs):
        """
        Submit a task to the thread pool.
        
        Args:
            fn: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Future object
        """
        executor = self.get_executor()
        return executor.submit(fn, *args, **kwargs)
    
    def shutdown(self, wait: bool = True):
        """Shutdown thread pool."""
        if self._executor is not None:
            self._executor.shutdown(wait=wait)
            self._executor = None
            logger.info("Thread pool shut down")
    
    def adjust_workers_for_ram(self, ram_percent: float):
        """
        Adjust worker count based on RAM usage.
        
        Args:
            ram_percent: Current RAM usage percentage
        """
        if not self._adaptive:
            return
        
        # Reduce workers if RAM is high
        if ram_percent >= 85:
            new_workers = max(1, self._current_workers - 1)
        elif ram_percent >= 75:
            new_workers = max(2, self._current_workers - 1)
        elif ram_percent < 60:
            # RAM is low, can increase workers
            new_workers = min(self._base_max_workers, self._current_workers + 1)
        else:
            return  # No change needed
        
        if new_workers != self._current_workers:
            logger.info(f"Adjusting workers: {self._current_workers} -> {new_workers} (RAM: {ram_percent:.1f}%)")
            self._current_workers = new_workers
            # Recreate executor with new worker count
            if self._executor is not None:
                self._executor.shutdown(wait=False)
            self._executor = ThreadPoolExecutor(max_workers=self._current_workers)


# Global thread pool manager instance
_thread_pool_manager: Optional[ThreadPoolManager] = None


def get_thread_pool_manager() -> ThreadPoolManager:
    """
    Get global thread pool manager instance.
    
    Returns:
        ThreadPoolManager instance
    """
    global _thread_pool_manager
    if _thread_pool_manager is None:
        _thread_pool_manager = ThreadPoolManager()
    return _thread_pool_manager

