"""
Device Manager - لیست و مدیریت دستگاه‌های میکروفون و دوربین

Provides utilities for:
- Listing available cameras
- Listing available microphones
- Testing device connectivity
- Device selection helpers
"""

import cv2
import logging
from typing import List, Dict, Optional, Tuple
import platform

logger = logging.getLogger(__name__)

# Try to import microphone-related libraries
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    logger.warning("speech_recognition not available - microphone listing will be limited")

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    logger.warning("pyaudio not available - using alternative microphone detection")


class DeviceManager:
    """
    Manager for camera and microphone devices.
    
    Provides methods to list, test, and select devices.
    """
    
    def __init__(self):
        """Initialize device manager."""
        self._camera_cache: Optional[List[Dict]] = None
        self._microphone_cache: Optional[List[Dict]] = None
    
    def get_available_cameras(self, test: bool = True) -> List[Dict]:
        """
        Get list of available cameras.
        
        Args:
            test: If True, test each camera to verify it works
        
        Returns:
            List of camera info dictionaries with keys:
            - index: Camera index
            - name: Camera name (if available)
            - available: Whether camera is accessible
            - resolution: Detected resolution (if test=True)
        """
        cameras = []
        
        # Try up to 10 camera indices
        for i in range(10):
            try:
                if test:
                    # Test camera by opening it
                    cap = cv2.VideoCapture(i)
                    if cap.isOpened():
                        # Get camera properties
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        
                        # Try to get camera name (OS-specific)
                        name = self._get_camera_name(i)
                        
                        cameras.append({
                            'index': i,
                            'name': name,
                            'available': True,
                            'resolution': f"{width}x{height}",
                            'fps': fps
                        })
                        cap.release()
                    else:
                        # Camera index exists but cannot open
                        cameras.append({
                            'index': i,
                            'name': f'Camera {i}',
                            'available': False,
                            'resolution': None,
                            'fps': None
                        })
                else:
                    # Just list potential indices without testing
                    cameras.append({
                        'index': i,
                        'name': f'Camera {i}',
                        'available': None,  # Unknown
                        'resolution': None,
                        'fps': None
                    })
            except Exception as e:
                logger.debug(f"Error checking camera {i}: {e}")
                continue
        
        self._camera_cache = cameras
        return cameras
    
    def get_available_microphones(self) -> List[Dict]:
        """
        Get list of available microphones.
        
        Returns:
            List of microphone info dictionaries with keys:
            - index: Microphone index
            - name: Microphone name
            - available: Whether microphone is accessible
        """
        microphones = []
        
        if SPEECH_RECOGNITION_AVAILABLE:
            try:
                # Use speech_recognition to list microphones
                mic_list = sr.Microphone.list_microphone_names()
                for i, name in enumerate(mic_list):
                    microphones.append({
                        'index': i,
                        'name': name,
                        'available': True
                    })
            except Exception as e:
                logger.error(f"Error listing microphones: {e}")
        
        elif PYAUDIO_AVAILABLE:
            try:
                # Use pyaudio to list microphones
                audio = pyaudio.PyAudio()
                device_count = audio.get_device_count()
                
                for i in range(device_count):
                    try:
                        info = audio.get_device_info_by_index(i)
                        if info['maxInputChannels'] > 0:  # Is input device
                            microphones.append({
                                'index': i,
                                'name': info.get('name', f'Microphone {i}'),
                                'available': True
                            })
                    except Exception as e:
                        logger.debug(f"Error getting mic info {i}: {e}")
                        continue
                
                audio.terminate()
            except Exception as e:
                logger.error(f"Error listing microphones with pyaudio: {e}")
        
        else:
            # Fallback: try default microphone
            logger.warning("No microphone library available - using default")
            microphones.append({
                'index': None,  # Default
                'name': 'Default Microphone',
                'available': True
            })
        
        self._microphone_cache = microphones
        return microphones
    
    def test_camera(self, index: int) -> Tuple[bool, Optional[str]]:
        """
        Test if a camera is accessible.
        
        Args:
            index: Camera index
        
        Returns:
            (success, error_message)
        """
        try:
            cap = cv2.VideoCapture(index)
            if not cap.isOpened():
                return False, f"Camera {index} cannot be opened"
            
            # Try to read a frame
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return False, f"Camera {index} opened but cannot read frames"
            
            return True, None
            
        except Exception as e:
            return False, f"Error testing camera {index}: {e}"
    
    def test_microphone(self, index: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        Test if a microphone is accessible.
        
        Args:
            index: Microphone index (None for default)
        
        Returns:
            (success, error_message)
        """
        if not SPEECH_RECOGNITION_AVAILABLE:
            return False, "speech_recognition library not available"
        
        try:
            recognizer = sr.Recognizer()
            microphone = sr.Microphone(device_index=index)
            
            # Try to adjust for ambient noise (quick test)
            with microphone as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            return True, None
            
        except Exception as e:
            return False, f"Error testing microphone: {e}"
    
    def get_default_camera(self) -> Optional[int]:
        """Get default camera index (usually 0)."""
        cameras = self.get_available_cameras(test=True)
        for cam in cameras:
            if cam['available']:
                return cam['index']
        return None
    
    def get_default_microphone(self) -> Optional[int]:
        """Get default microphone index."""
        microphones = self.get_available_microphones()
        if microphones:
            return microphones[0]['index']
        return None
    
    def get_laptop_microphone(self) -> Optional[int]:
        """
        Get laptop/internal microphone index.
        
        Searches for microphones with keywords like:
        - "microphone", "array", "built-in", "internal", "laptop"
        
        Returns:
            Microphone index if found, None otherwise
        """
        microphones = self.get_available_microphones()
        
        # Keywords to identify laptop microphones
        keywords = ['microphone', 'array', 'built-in', 'internal', 'laptop', 
                   'amd', 'realtek', 'intel']
        
        # First, try to find microphone with keywords
        for mic in microphones:
            name_lower = mic['name'].lower()
            if any(keyword in name_lower for keyword in keywords):
                # Test if it works
                success, _ = self.test_microphone(mic['index'])
                if success:
                    logger.info(f"Found laptop microphone: {mic['index']} ({mic['name']})")
                    return mic['index']
        
        # Fallback: return first available microphone
        if microphones:
            default = microphones[0]['index']
            logger.info(f"Using default microphone: {default}")
            return default
        
        return None
    
    def _get_camera_name(self, index: int) -> str:
        """Get camera name (OS-specific)."""
        try:
            if platform.system() == "Windows":
                # On Windows, camera names are usually just "Camera {index}"
                # Could use DirectShow backend for better names
                cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
                if cap.isOpened():
                    # Try to get backend-specific info
                    backend_name = cap.getBackendName()
                    cap.release()
                    return f"Camera {index} ({backend_name})"
            elif platform.system() == "Linux":
                # On Linux, check /dev/video*
                return f"/dev/video{index}"
            elif platform.system() == "Darwin":  # macOS
                return f"Camera {index}"
        except:
            pass
        
        return f"Camera {index}"
    
    def print_device_list(self):
        """Print formatted list of all devices."""
        print("\n" + "="*60)
        print("📷 Available Cameras:")
        print("="*60)
        
        cameras = self.get_available_cameras(test=True)
        if cameras:
            for cam in cameras:
                status = "✅" if cam['available'] else "❌"
                print(f"  {status} Index {cam['index']}: {cam['name']}")
                if cam['available'] and cam['resolution']:
                    print(f"      Resolution: {cam['resolution']}, FPS: {cam['fps']:.1f}")
        else:
            print("  No cameras found")
        
        print("\n" + "="*60)
        print("🎤 Available Microphones:")
        print("="*60)
        
        microphones = self.get_available_microphones()
        if microphones:
            for mic in microphones:
                print(f"  ✅ Index {mic['index']}: {mic['name']}")
        else:
            print("  No microphones found")
        
        print("="*60 + "\n")


# Singleton instance
_device_manager = None

def get_device_manager() -> DeviceManager:
    """Get singleton DeviceManager instance."""
    global _device_manager
    if _device_manager is None:
        _device_manager = DeviceManager()
    return _device_manager

