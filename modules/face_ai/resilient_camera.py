"""
Resilient Camera Manager

Handles camera disconnections gracefully with automatic reconnection.

Features:
- Automatic reconnection on failure
- Exponential backoff
- Health monitoring
- Operator notifications
- Fallback mechanisms

Author: AI-Symp-Controller Team
Date: November 2025
Version: 1.0
"""

import cv2
import time
import logging
from typing import Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from enum import Enum

logger = logging.getLogger(__name__)


class CameraState(Enum):
    """Camera connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"
    RECONNECTING = "reconnecting"


class ResilientCamera(QObject):
    """
    Camera wrapper with automatic reconnection and health monitoring.
    
    Handles disconnections gracefully and attempts reconnection with backoff.
    """
    
    # Signals
    camera_connected = pyqtSignal()
    camera_disconnected = pyqtSignal(str)  # reason
    camera_reconnecting = pyqtSignal(int)  # attempt number
    camera_failed = pyqtSignal(str)  # error message
    frame_read = pyqtSignal(object)  # frame
    
    def __init__(
        self,
        camera_id: int = 0,
        max_reconnect_attempts: int = 10,
        initial_backoff: float = 1.0,
        max_backoff: float = 30.0,
        health_check_interval: int = 5000
    ):
        """
        Initialize resilient camera.
        
        Args:
            camera_id: Camera index or path
            max_reconnect_attempts: Maximum reconnection attempts (-1 for infinite)
            initial_backoff: Initial backoff time (seconds)
            max_backoff: Maximum backoff time (seconds)
            health_check_interval: Health check interval (milliseconds)
        """
        super().__init__()
        
        self._camera_id = camera_id
        self._max_reconnect_attempts = max_reconnect_attempts
        self._initial_backoff = initial_backoff
        self._max_backoff = max_backoff
        
        self._camera: Optional[cv2.VideoCapture] = None
        self._state = CameraState.DISCONNECTED
        self._reconnect_attempts = 0
        self._current_backoff = initial_backoff
        self._last_successful_read = None
        
        # Health monitoring
        self._health_timer = QTimer()
        self._health_timer.timeout.connect(self._check_health)
        self._health_timer.setInterval(health_check_interval)
        
        # Failure tracking
        self._consecutive_failures = 0
        self._max_consecutive_failures = 5
        
        logger.info(f"ResilientCamera initialized for camera {camera_id}")
    
    def connect(self) -> bool:
        """
        Connect to camera.
        
        Returns:
            True if connected successfully
        """
        if self._state == CameraState.CONNECTED:
            logger.warning("Camera already connected")
            return True
        
        self._state = CameraState.CONNECTING
        logger.info(f"Connecting to camera {self._camera_id}...")
        
        try:
            # Open camera
            self._camera = cv2.VideoCapture(self._camera_id)
            
            if not self._camera.isOpened():
                raise RuntimeError(f"Failed to open camera {self._camera_id}")
            
            # Test read
            ret, frame = self._camera.read()
            if not ret or frame is None:
                raise RuntimeError("Failed to read test frame")
            
            # Success
            self._state = CameraState.CONNECTED
            self._reconnect_attempts = 0
            self._current_backoff = self._initial_backoff
            self._consecutive_failures = 0
            self._last_successful_read = time.time()
            
            # Start health monitoring
            self._health_timer.start()
            
            logger.info(f"✅ Camera {self._camera_id} connected successfully")
            self.camera_connected.emit()
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to connect to camera {self._camera_id}: {str(e)}"
            logger.error(error_msg)
            
            self._state = CameraState.DISCONNECTED
            self._cleanup_camera()
            
            return False
    
    def disconnect(self):
        """Disconnect camera."""
        logger.info(f"Disconnecting camera {self._camera_id}...")
        
        self._health_timer.stop()
        self._cleanup_camera()
        self._state = CameraState.DISCONNECTED
        
        logger.info("Camera disconnected")
    
    def _cleanup_camera(self):
        """Clean up camera resources."""
        if self._camera is not None:
            try:
                self._camera.release()
            except Exception as e:
                logger.error(f"Error releasing camera: {e}")
            finally:
                self._camera = None
    
    def read_frame(self) -> tuple[bool, Optional[object]]:
        """
        Read frame from camera with automatic reconnection.
        
        Returns:
            Tuple of (success, frame)
        """
        if self._state != CameraState.CONNECTED:
            return (False, None)
        
        try:
            ret, frame = self._camera.read()
            
            if not ret or frame is None:
                self._consecutive_failures += 1
                logger.warning(f"Failed to read frame (failure {self._consecutive_failures}/{self._max_consecutive_failures})")
                
                # Check if too many failures
                if self._consecutive_failures >= self._max_consecutive_failures:
                    logger.error("Too many consecutive failures - triggering reconnection")
                    self._handle_disconnection("Multiple read failures")
                
                return (False, None)
            
            # Success
            self._consecutive_failures = 0
            self._last_successful_read = time.time()
            
            return (True, frame)
            
        except Exception as e:
            logger.error(f"Exception reading frame: {e}")
            self._handle_disconnection(f"Exception: {str(e)}")
            return (False, None)
    
    def _handle_disconnection(self, reason: str):
        """
        Handle camera disconnection.
        
        Args:
            reason: Reason for disconnection
        """
        if self._state == CameraState.DISCONNECTED:
            return
        
        logger.warning(f"Camera disconnected: {reason}")
        self._state = CameraState.DISCONNECTED
        self._health_timer.stop()
        self._cleanup_camera()
        
        self.camera_disconnected.emit(reason)
        
        # Attempt reconnection
        self._attempt_reconnection()
    
    def _attempt_reconnection(self):
        """Attempt to reconnect with exponential backoff."""
        if self._max_reconnect_attempts != -1 and self._reconnect_attempts >= self._max_reconnect_attempts:
            error_msg = f"Max reconnection attempts ({self._max_reconnect_attempts}) reached"
            logger.error(error_msg)
            self._state = CameraState.FAILED
            self.camera_failed.emit(error_msg)
            return
        
        self._reconnect_attempts += 1
        self._state = CameraState.RECONNECTING
        
        logger.info(f"Reconnection attempt {self._reconnect_attempts}/{self._max_reconnect_attempts} in {self._current_backoff:.1f}s...")
        self.camera_reconnecting.emit(self._reconnect_attempts)
        
        # Wait with backoff
        time.sleep(self._current_backoff)
        
        # Try to connect
        success = self.connect()
        
        if not success:
            # Exponential backoff
            self._current_backoff = min(self._current_backoff * 2, self._max_backoff)
            
            # Try again
            self._attempt_reconnection()
        else:
            logger.info(f"✅ Reconnected successfully after {self._reconnect_attempts} attempts")
    
    def _check_health(self):
        """Periodic health check."""
        if self._state != CameraState.CONNECTED:
            return
        
        # Check if camera is still opened
        if self._camera is None or not self._camera.isOpened():
            logger.warning("Health check failed: camera not opened")
            self._handle_disconnection("Health check failed")
            return
        
        # Check time since last successful read
        if self._last_successful_read:
            time_since_read = time.time() - self._last_successful_read
            if time_since_read > 10.0:  # 10 seconds without successful read
                logger.warning(f"Health check failed: no successful read for {time_since_read:.1f}s")
                self._handle_disconnection("No recent successful reads")
                return
        
        logger.debug("Camera health check: OK")
    
    def get_state(self) -> CameraState:
        """Get current camera state."""
        return self._state
    
    def is_connected(self) -> bool:
        """Check if camera is connected."""
        return self._state == CameraState.CONNECTED
    
    def get_reconnect_attempts(self) -> int:
        """Get number of reconnection attempts."""
        return self._reconnect_attempts
    
    def reset_reconnection(self):
        """Reset reconnection counter."""
        self._reconnect_attempts = 0
        self._current_backoff = self._initial_backoff
        logger.info("Reconnection counter reset")


class CameraPool:
    """
    Pool of cameras with fallback support.
    
    If primary camera fails, automatically switches to backup.
    """
    
    def __init__(self):
        """Initialize camera pool."""
        self._cameras: list[ResilientCamera] = []
        self._active_camera_index = 0
    
    def add_camera(self, camera: ResilientCamera):
        """Add camera to pool."""
        self._cameras.append(camera)
        logger.info(f"Added camera to pool (total: {len(self._cameras)})")
    
    def get_active_camera(self) -> Optional[ResilientCamera]:
        """Get current active camera."""
        if 0 <= self._active_camera_index < len(self._cameras):
            return self._cameras[self._active_camera_index]
        return None
    
    def switch_to_next_camera(self) -> bool:
        """
        Switch to next available camera.
        
        Returns:
            True if switched successfully
        """
        if len(self._cameras) <= 1:
            return False
        
        old_index = self._active_camera_index
        self._active_camera_index = (self._active_camera_index + 1) % len(self._cameras)
        
        logger.info(f"Switching from camera {old_index} to {self._active_camera_index}")
        
        # Try to connect to new camera
        camera = self.get_active_camera()
        if camera and camera.connect():
            logger.info("✅ Successfully switched to backup camera")
            return True
        
        return False


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    print("=== Resilient Camera Test ===\n")
    
    # Create camera
    camera = ResilientCamera(camera_id=0)
    
    # Connect callbacks
    camera.camera_connected.connect(lambda: print("✅ Camera connected"))
    camera.camera_disconnected.connect(lambda reason: print(f"❌ Camera disconnected: {reason}"))
    camera.camera_reconnecting.connect(lambda attempt: print(f"🔄 Reconnecting (attempt {attempt})..."))
    camera.camera_failed.connect(lambda error: print(f"💀 Camera failed: {error}"))
    
    # Connect
    if camera.connect():
        print("Camera connected successfully!")
        
        # Read some frames
        for i in range(10):
            ret, frame = camera.read_frame()
            if ret:
                print(f"Frame {i}: OK")
            else:
                print(f"Frame {i}: FAILED")
            time.sleep(0.1)
    
    # Disconnect
    camera.disconnect()

