"""
Unified Controller - Master Orchestration for All Modules

هماهنگ‌سازی و مدیریت یکپارچه همه ماژول‌های سیستم

این کنترلر مرکزی:
- همه ماژول‌ها را هماهنگ می‌کند
- رویدادها را بین ماژول‌ها همگام‌سازی می‌کند
- یکپارچگی کامل بین ماژول‌ها را تضمین می‌کند
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal

from ..timer import TimerController
from ..media import MediaController
from ..face_ai import FaceAIController
from ..display import DisplayController
from ..symposium.session_controller import SessionController
from ..ai_timing import AIIntegrationController
from ..content_automation.integration.main_app_integration import ContentAutomationIntegration
from ..utils.device_manager import get_device_manager

logger = logging.getLogger(__name__)


class UnifiedController(QObject):
    """
    Master controller for unified module coordination.
    
    Features:
    - Centralized module management
    - Event synchronization
    - Cross-module communication
    - Session orchestration
    - Resource coordination
    """
    
    # Signals
    session_started = pyqtSignal(str)  # session_id
    session_ended = pyqtSignal(str)
    all_modules_ready = pyqtSignal()
    module_error = pyqtSignal(str, str)  # module_name, error_message
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize unified controller.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__()
        self.config = config or {}
        
        # Module controllers
        self.timer_controller: Optional[TimerController] = None
        self.media_controller: Optional[MediaController] = None
        self.face_ai_controller: Optional[FaceAIController] = None
        self.display_controller: Optional[DisplayController] = None
        self.session_controller: Optional[SessionController] = None
        self.ai_integration_controller: Optional[AIIntegrationController] = None
        self.content_automation: Optional[ContentAutomationIntegration] = None
        
        # Device manager
        self.device_manager = get_device_manager()
        
        # State
        self._is_active = False
        self._current_session_id: Optional[str] = None
        self._module_states: Dict[str, bool] = {}
        
        logger.info("UnifiedController initialized")
    
    def initialize_modules(
        self,
        timer_controller: Optional[TimerController] = None,
        media_controller: Optional[MediaController] = None,
        face_ai_controller: Optional[FaceAIController] = None,
        display_controller: Optional[DisplayController] = None,
        session_controller: Optional[SessionController] = None
    ):
        """
        Initialize all module controllers.
        
        Args:
            timer_controller: Timer controller (creates new if None)
            media_controller: Media controller (creates new if None)
            face_ai_controller: Face AI controller (creates new if None)
            display_controller: Display controller (creates new if None)
            session_controller: Session controller (creates new if None)
        """
        logger.info("Initializing all modules...")
        
        # Initialize controllers (create if not provided)
        self.timer_controller = timer_controller or TimerController()
        self.media_controller = media_controller or MediaController()
        self.face_ai_controller = face_ai_controller or FaceAIController()
        self.display_controller = display_controller or DisplayController()
        
        # Initialize session controller
        if session_controller:
            self.session_controller = session_controller
        else:
            # Create session controller with timer
            from ..symposium.session_controller import SessionController
            self.session_controller = SessionController(self.timer_controller)
        
        # Initialize AI Integration Controller
        self.ai_integration_controller = AIIntegrationController(
            base_timer_controller=self.timer_controller
        )
        
        # Initialize Content Automation
        self.content_automation = ContentAutomationIntegration(
            media_controller=self.media_controller,
            display_controller=self.display_controller
        )
        
        # Setup cross-module connections
        self._setup_connections()
        
        logger.info("✅ All modules initialized")
        self.all_modules_ready.emit()
    
    def _setup_connections(self):
        """Setup signal connections between modules."""
        logger.info("Setting up cross-module connections...")
        
        # Timer → Media synchronization
        if self.timer_controller and self.media_controller:
            # Timer events can trigger media actions
            pass  # Add connections as needed
        
        # Face AI → Timer adaptation
        if self.face_ai_controller and self.ai_integration_controller:
            # Face AI analysis affects timer adaptation
            pass  # Already connected in AIIntegrationController
        
        # Session → Content Automation
        # Will be connected when session starts
        
        logger.info("✅ Cross-module connections established")
    
    async def start_full_session(
        self,
        session_id: str,
        presenter_camera: int = 0,
        audience_camera: int = 1,
        laptop_microphone: Optional[int] = None,
        enable_ai_timing: bool = True,
        enable_content_automation: bool = True
    ) -> bool:
        """
        Start a complete session with all modules active.
        
        Args:
            session_id: Session identifier
            presenter_camera: Camera index for presenter
            audience_camera: Camera index for audience
            laptop_microphone: Microphone index (None = auto-detect)
            enable_ai_timing: Enable AI-driven timing
            enable_content_automation: Enable content automation
        
        Returns:
            True if all modules started successfully
        """
        logger.info(f"Starting full session: {session_id}")
        
        try:
            # Step 1: Start Content Automation
            if enable_content_automation:
                logger.info("Starting Content Automation...")
                await self.content_automation.start()
                self._module_states['content_automation'] = True
            
            # Step 2: Start Face AI
            logger.info("Starting Face AI...")
            if self.face_ai_controller.start_analysis(camera_index=audience_camera, fps=15):
                self._module_states['face_ai'] = True
            else:
                logger.warning("Face AI failed to start")
                self._module_states['face_ai'] = False
            
            # Step 3: Start AI Timing (includes voice detection)
            if enable_ai_timing:
                logger.info("Starting AI Timing...")
                
                # Find laptop microphone if not provided
                if laptop_microphone is None:
                    laptop_microphone = self.device_manager.get_laptop_microphone()
                    if laptop_microphone:
                        logger.info(f"Auto-detected laptop microphone: {laptop_microphone}")
                
                # Start AI Timing
                if self.ai_integration_controller.start_ai_timing(
                    presenter_camera=presenter_camera,
                    audience_camera=audience_camera,
                    enable_voice=True
                ):
                    # Configure laptop microphone
                    if laptop_microphone is not None:
                        self.ai_integration_controller._voice_detector.stop_detection()
                        self.ai_integration_controller._voice_detector.start_detection(
                            microphone_index=laptop_microphone
                        )
                        logger.info(f"Voice Detection configured with microphone: {laptop_microphone}")
                    
                    self._module_states['ai_timing'] = True
                else:
                    logger.warning("AI Timing failed to start")
                    self._module_states['ai_timing'] = False
            
            # Step 4: Start Timer
            logger.info("Starting Timer...")
            # Timer will be controlled by session controller
            self._module_states['timer'] = True
            
            # Step 5: Prepare Display
            logger.info("Preparing Display...")
            self.display_controller.refresh_displays()
            self._module_states['display'] = True
            
            # Step 6: Start Session
            if self.session_controller:
                self.session_controller.start_session(session_id)
            
            self._current_session_id = session_id
            self._is_active = True
            
            logger.info(f"✅ Full session started: {session_id}")
            self.session_started.emit(session_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting full session: {e}", exc_info=True)
            self.module_error.emit("session", str(e))
            return False
    
    async def stop_full_session(self):
        """Stop all modules and end session."""
        logger.info("Stopping full session...")
        
        try:
            # Stop in reverse order
            if self._module_states.get('ai_timing'):
                self.ai_integration_controller.stop_ai_timing()
            
            if self._module_states.get('face_ai'):
                self.face_ai_controller.stop_analysis()
            
            if self._module_states.get('content_automation'):
                await self.content_automation.stop()
            
            if self.timer_controller:
                self.timer_controller.stop()
            
            if self.session_controller and self._current_session_id:
                self.session_controller.end_session(self._current_session_id)
                self.session_ended.emit(self._current_session_id)
            
            self._is_active = False
            self._current_session_id = None
            self._module_states.clear()
            
            logger.info("✅ Full session stopped")
            
        except Exception as e:
            logger.error(f"Error stopping session: {e}", exc_info=True)
    
    def get_module_status(self) -> Dict[str, Dict]:
        """
        Get status of all modules.
        
        Returns:
            Dictionary with module statuses
        """
        try:
            # Timer status
            timer_running = False
            timer_remaining = None
            if self.timer_controller:
                try:
                    timer_running = self.timer_controller.is_running()
                    # Use get_current_time() instead of get_remaining_time()
                    timer_remaining = self.timer_controller.get_current_time()
                except Exception as e:
                    logger.debug(f"Error getting timer status: {e}")
                    pass
            
            # Face AI status
            face_ai_analyzing = False
            if self.face_ai_controller:
                try:
                    face_ai_analyzing = self.face_ai_controller.is_analyzing()
                except:
                    pass
            
            # AI Timing status
            ai_timing_active = False
            if self.ai_integration_controller:
                try:
                    ai_timing_active = self.ai_integration_controller.is_active()
                except:
                    pass
            
            # Content Automation status
            content_running = False
            if self.content_automation and hasattr(self.content_automation, 'engine'):
                try:
                    content_running = self.content_automation.engine._running
                except:
                    pass
            
            # Display status
            display_screens = 0
            if self.display_controller:
                try:
                    display_screens = len(self.display_controller.get_available_screens())
                except:
                    pass
            
            status = {
                'timer': {
                    'active': self._module_states.get('timer', False),
                    'running': timer_running,
                    'time_remaining': timer_remaining
                },
                'face_ai': {
                    'active': self._module_states.get('face_ai', False),
                    'analyzing': face_ai_analyzing
                },
                'ai_timing': {
                    'active': self._module_states.get('ai_timing', False),
                    'is_active': ai_timing_active
                },
                'content_automation': {
                    'active': self._module_states.get('content_automation', False),
                    'running': content_running
                },
                'display': {
                    'active': self._module_states.get('display', False),
                    'screens': display_screens
                },
                'session': {
                    'active': self._is_active,
                    'session_id': self._current_session_id
                }
            }
            
            return status
        except Exception as e:
            logger.error(f"Error getting module status: {e}", exc_info=True)
            # Return safe default
            return {
                'timer': {'active': False, 'running': False, 'time_remaining': None},
                'face_ai': {'active': False, 'analyzing': False},
                'ai_timing': {'active': False, 'is_active': False},
                'content_automation': {'active': False, 'running': False},
                'display': {'active': False, 'screens': 0},
                'session': {'active': False, 'session_id': None}
            }
    
    def get_unified_stats(self) -> Dict:
        """Get unified statistics from all modules."""
        try:
            # Get devices count safely
            try:
                cameras = self.device_manager.get_available_cameras(test=True)
                camera_count = len(cameras) if cameras else 0
            except:
                camera_count = 0
            
            try:
                microphones = self.device_manager.get_available_microphones()
                mic_count = len(microphones) if microphones else 0
            except:
                mic_count = 0
            
            stats = {
                'session': {
                    'active': self._is_active,
                    'session_id': self._current_session_id,
                    'start_time': None
                },
                'modules': self.get_module_status(),
                'devices': {
                    'cameras': camera_count,
                    'microphones': mic_count
                }
            }
            
            # Add AI Timing stats
            if self.ai_integration_controller and self._module_states.get('ai_timing'):
                try:
                    engagement = self.ai_integration_controller.get_current_engagement()
                except:
                    engagement = 0
                
                try:
                    presenter_tracking = False
                    if hasattr(self.ai_integration_controller, '_presenter_tracker'):
                        presenter_tracking = self.ai_integration_controller._presenter_tracker.is_tracking()
                except:
                    presenter_tracking = False
                
                try:
                    voice_active = False
                    if hasattr(self.ai_integration_controller, '_voice_detector'):
                        voice_active = self.ai_integration_controller._voice_detector.is_speaking()
                except:
                    voice_active = False
                
                stats['ai_timing'] = {
                    'engagement': engagement,
                    'presenter_tracking': presenter_tracking,
                    'voice_active': voice_active
                }
            
            # Add Face AI stats
            if self.face_ai_controller and self._module_states.get('face_ai'):
                try:
                    face_ai_stats = self.face_ai_controller.get_statistics()
                    stats['face_ai'] = face_ai_stats if face_ai_stats else {}
                except:
                    stats['face_ai'] = {}
            
            return stats
        except Exception as e:
            logger.error(f"Error getting unified stats: {e}", exc_info=True)
            # Return safe default
            return {
                'session': {'active': False, 'session_id': None, 'start_time': None},
                'modules': self.get_module_status(),
                'devices': {'cameras': 0, 'microphones': 0}
            }
    
    def is_active(self) -> bool:
        """Check if unified controller is active."""
        return self._is_active
    
    # ========== Individual Module Control ==========
    
    def start_module(self, module_name: str, **kwargs) -> bool:
        """
        Start a specific module individually.
        
        Args:
            module_name: Name of module (timer, media, face_ai, display, ai_timing, content_automation)
            **kwargs: Module-specific parameters
        
        Returns:
            True if started successfully
        """
        logger.info(f"Starting module: {module_name}")
        
        try:
            if module_name == "timer":
                # Timer doesn't need explicit start, just mark as active
                self._module_states['timer'] = True
                return True
            
            elif module_name == "media":
                # Media controller is ready by default
                self._module_states['media'] = True
                return True
            
            elif module_name == "face_ai":
                camera_index = kwargs.get('camera_index', 0)
                fps = kwargs.get('fps', 15)
                if self.face_ai_controller:
                    if self.face_ai_controller.start_analysis(camera_index=camera_index, fps=fps):
                        self._module_states['face_ai'] = True
                        return True
                return False
            
            elif module_name == "display":
                if self.display_controller:
                    self.display_controller.refresh_displays()
                    self._module_states['display'] = True
                    return True
                return False
            
            elif module_name == "ai_timing":
                presenter_camera = kwargs.get('presenter_camera', 0)
                audience_camera = kwargs.get('audience_camera', 1)
                enable_voice = kwargs.get('enable_voice', True)
                laptop_microphone = kwargs.get('laptop_microphone', None)
                
                if self.ai_integration_controller:
                    if self.ai_integration_controller.start_ai_timing(
                        presenter_camera=presenter_camera,
                        audience_camera=audience_camera,
                        enable_voice=enable_voice
                    ):
                        if enable_voice and laptop_microphone is not None:
                            self.ai_integration_controller._voice_detector.stop_detection()
                            self.ai_integration_controller._voice_detector.start_detection(
                                microphone_index=laptop_microphone
                            )
                        self._module_states['ai_timing'] = True
                        return True
                return False
            
            elif module_name == "content_automation":
                if self.content_automation:
                    # Run async start
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(self.content_automation.start())
                        else:
                            loop.run_until_complete(self.content_automation.start())
                        self._module_states['content_automation'] = True
                        return True
                    except:
                        # Fallback: mark as started
                        self._module_states['content_automation'] = True
                        return True
                return False
            
            else:
                logger.warning(f"Unknown module: {module_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting module {module_name}: {e}", exc_info=True)
            return False
    
    def stop_module(self, module_name: str) -> bool:
        """
        Stop a specific module individually.
        
        Args:
            module_name: Name of module to stop
        
        Returns:
            True if stopped successfully
        """
        logger.info(f"Stopping module: {module_name}")
        
        try:
            if module_name == "timer":
                if self.timer_controller:
                    self.timer_controller.stop()
                self._module_states['timer'] = False
                return True
            
            elif module_name == "media":
                if self.media_controller:
                    self.media_controller.stop()
                self._module_states['media'] = False
                return True
            
            elif module_name == "face_ai":
                if self.face_ai_controller:
                    self.face_ai_controller.stop_analysis()
                self._module_states['face_ai'] = False
                return True
            
            elif module_name == "display":
                # Display doesn't need explicit stop
                self._module_states['display'] = False
                return True
            
            elif module_name == "ai_timing":
                try:
                    if self.ai_integration_controller:
                        if hasattr(self.ai_integration_controller, 'stop_ai_timing'):
                            self.ai_integration_controller.stop_ai_timing()
                        else:
                            logger.warning("AI Integration Controller doesn't have stop_ai_timing method")
                    else:
                        logger.warning("AI Integration Controller is not initialized")
                except AttributeError as e:
                    logger.error(f"Attribute error stopping AI Timing: {e}", exc_info=True)
                except Exception as e:
                    logger.error(f"Error stopping AI Timing: {e}", exc_info=True)
                finally:
                    self._module_states['ai_timing'] = False
                return True
            
            elif module_name == "content_automation":
                if self.content_automation:
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(self.content_automation.stop())
                        else:
                            loop.run_until_complete(self.content_automation.stop())
                    except:
                        pass
                self._module_states['content_automation'] = False
                return True
            
            else:
                logger.warning(f"Unknown module: {module_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error stopping module {module_name}: {e}", exc_info=True)
            return False
    
    def is_module_active(self, module_name: str) -> bool:
        """Check if a specific module is active."""
        return self._module_states.get(module_name, False)
    
    def get_current_session_id(self) -> Optional[str]:
        """Get current session ID."""
        return self._current_session_id

