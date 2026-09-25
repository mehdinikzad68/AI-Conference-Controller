"""
Main App Integration - Complete integration with main.py

Provides initialization code and integration points.
"""

import asyncio
import logging
from typing import Optional

from ..core.engine import ContentAutomationEngine
from ..ui.operator_dashboard import ContentAutomationDashboard
from ..platforms.local_hall_adapter import LocalHallAdapter
from ..platforms.skyroom_adapter import SkyroomAdapter
from ..integration.symposium_bridge import SymposiumBridge
from ..emergency.manager import EmergencyManager
from ..notifications.notifier import Notifier
from ..reporting.analytics import ReportingAnalytics

logger = logging.getLogger(__name__)


class ContentAutomationIntegration:
    """
    Integration wrapper for Content Automation Module.
    
    Use this in main.py to initialize everything.
    
    Example:
        >>> # In MainWindow.__init__():
        >>> self.content_automation = ContentAutomationIntegration(
        ...     media_controller=self.media_controller,
        ...     display_controller=self.display_controller
        ... )
        >>> asyncio.create_task(self.content_automation.start())
    """
    
    def __init__(
        self,
        media_controller=None,
        display_controller=None,
        agenda_manager=None,
        config: Optional[dict] = None
    ):
        """
        Initialize content automation integration.
        
        Args:
            media_controller: MediaController from main app
            display_controller: DisplayController from main app
            agenda_manager: AgendaManager from symposium module
            config: Configuration dict
        """
        self.media_controller = media_controller
        self.display_controller = display_controller
        self.agenda_manager = agenda_manager
        
        # Core engine
        self.engine = ContentAutomationEngine(config=config or {})
        
        # Additional components
        self.emergency_manager = EmergencyManager(self.engine)
        self.notifier = Notifier()
        self.analytics = ReportingAnalytics()
        
        # Bridges
        self.symposium_bridge = SymposiumBridge(self.engine, agenda_manager)
        
        # UI
        self.dashboard: Optional[ContentAutomationDashboard] = None
        
        # Adapters
        self.hall_adapter: Optional[LocalHallAdapter] = None
        self.skyroom_adapter: Optional[SkyroomAdapter] = None
        
        logger.info("ContentAutomationIntegration initialized")
    
    async def start(self):
        """Start all services."""
        logger.info("Starting Content Automation Module...")
        
        # 1. Initialize adapters
        await self._init_adapters()
        
        # 2. Start engine
        await self.engine.start()
        
        # 3. Import schedule if agenda manager available
        if self.agenda_manager:
            await self.symposium_bridge.import_full_schedule()
        
        logger.info("✅ Content Automation Module started")
    
    async def stop(self):
        """Stop all services."""
        logger.info("Stopping Content Automation Module...")
        await self.engine.stop()
        logger.info("Content Automation Module stopped")
    
    async def _init_adapters(self):
        """Initialize platform adapters."""
        # Local hall
        if self.media_controller and self.display_controller:
            self.hall_adapter = LocalHallAdapter(
                media_controller=self.media_controller,
                display_controller=self.display_controller
            )
            await self.hall_adapter.connect()
            self.engine.register_platform('hall', self.hall_adapter)
            logger.info("✅ Local hall adapter registered")
        
        # Skyroom (if configured)
        # skyroom_config = self.engine._config.get('skyroom', {})
        # if skyroom_config.get('enabled'):
        #     self.skyroom_adapter = SkyroomAdapter(
        #         api_url=skyroom_config['api_url'],
        #         api_key=skyroom_config['api_key'],
        #         room_id=skyroom_config['room_id']
        #     )
        #     await self.skyroom_adapter.connect()
        #     self.engine.register_platform('skyroom', self.skyroom_adapter)
    
    def create_dashboard(self, parent=None) -> ContentAutomationDashboard:
        """
        Create operator dashboard widget.
        
        Returns:
            Dashboard widget (add to main UI)
        """
        if not self.dashboard:
            self.dashboard = ContentAutomationDashboard(self.engine, parent)
        return self.dashboard
    
    def set_agenda_manager(self, agenda_manager):
        """Update agenda manager reference."""
        self.agenda_manager = agenda_manager
        self.symposium_bridge.set_agenda_manager(agenda_manager)
    
    # ========== Convenience Methods ==========
    
    async def schedule_content(
        self,
        path: str,
        start_time,
        platforms: list = None,
        title: str = None
    ):
        """Quick schedule content."""
        from ..models import ContentType, ContentMetadata
        
        # Determine type
        ext = path.split('.')[-1].lower()
        type_map = {
            'mp4': ContentType.VIDEO, 'avi': ContentType.VIDEO,
            'png': ContentType.IMAGE, 'jpg': ContentType.IMAGE,
            'pdf': ContentType.PDF
        }
        content_type = type_map.get(ext, ContentType.VIDEO)
        
        # Add content
        content_id = await self.engine.add_content(
            path=path,
            content_type=content_type,
            metadata=ContentMetadata(title=title or path.split('/')[-1])
        )
        
        # Schedule
        return await self.engine.schedule_content(
            content_id=content_id,
            start_time=start_time,
            platforms=platforms or ['hall'],
            priority='normal'
        )
    
    async def emergency_stop(self):
        """Emergency stop all playback."""
        await self.engine.emergency_stop()
    
    def get_stats(self):
        """Get system statistics."""
        return self.engine.get_stats()


# ========== Integration Code for main.py ==========

INTEGRATION_CODE = '''
# ========== Content Automation Integration (Add to main.py) ==========

# 1. Add import at top
from modules.content_automation.integration.main_app_integration import ContentAutomationIntegration
import asyncio

# 2. In MainWindow.__init__(), after initializing other controllers:
class MainWindow(QMainWindow):
    def __init__(self):
        # ... existing code ...
        
        # Initialize Content Automation (add after other controllers)
        self.content_automation = ContentAutomationIntegration(
            media_controller=self.media_controller,
            display_controller=self.display_controller
        )
        
        # Start in asyncio loop
        asyncio.create_task(self._start_content_automation())
    
    async def _start_content_automation(self):
        """Start content automation module."""
        try:
            await self.content_automation.start()
            print("✅ Content Automation Module started")
        except Exception as e:
            print(f"❌ Content Automation error: {e}")
    
    # 3. Add menu item to open dashboard
    def setup_menu_bar(self):
        # ... existing code ...
        
        # Add to Modules menu
        content_automation_action = QAction("📋 Content Automation", self)
        content_automation_action.triggered.connect(self.show_content_automation)
        modules_menu.addAction(content_automation_action)
    
    def show_content_automation(self):
        """Show content automation dashboard."""
        if not hasattr(self, '_content_automation_dashboard'):
            self._content_automation_dashboard = self.content_automation.create_dashboard()
        
        self._content_automation_dashboard.show()
        self._content_automation_dashboard.raise_()
        self._content_automation_dashboard.activateWindow()
    
    # 4. Connect with Symposium module (if you have symposium_window)
    def show_symposium(self):
        # ... existing code to create symposium_window ...
        
        # Connect agenda manager
        if hasattr(self.symposium_window, 'agenda_manager'):
            self.content_automation.set_agenda_manager(
                self.symposium_window.agenda_manager
            )

# ========== End Integration Code ==========
'''


def get_integration_instructions():
    """Get integration instructions."""
    return INTEGRATION_CODE

