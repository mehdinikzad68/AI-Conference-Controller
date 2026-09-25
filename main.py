"""
AI-Symp-Controller - Main Application Entry Point

A modular desktop application for presentation control with timer, media playback,
audience analysis, and multi-display management.

Author: AI-Symp-Controller Development Team
Version: 1.0.0
"""

import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QStackedWidget,
    QMenuBar,
    QMenu,
    QStatusBar,
    QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QAction

# Import modules
from modules.timer import TimerController, TimerWindow
from modules.media import MediaController, MediaWindow
from modules.face_ai import FaceAIController, FaceAIWindow
from modules.display import DisplayController, DisplayManagerWindow
from modules.config import ConfigManager, ConfigWindow
from modules.symposium import SymposiumWindow
from modules.utils.resource_monitor import ResourceMonitor, get_memory_usage, get_cpu_usage
from modules.utils.theme_manager import ThemeManager
from modules.utils.scrollable_widget import make_responsive
from modules.content_automation.integration.main_app_integration import ContentAutomationIntegration
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QWheelEvent
import asyncio
import qasync


class MainWindow(QMainWindow):
    """
    Main application window.
    
    Provides the central hub for all module functionality with a modular interface.
    """
    
    def __init__(self):
        """Initialize the main window and all modules."""
        super().__init__()
        
        # Initialize configuration manager
        self.config_manager = ConfigManager()
        self.config_manager.load_config()
        
        # Initialize theme manager
        self._theme_manager = ThemeManager()
        self.apply_theme()
        
        # Initialize resource monitor
        self._resource_monitor = ResourceMonitor(ram_threshold=80.0, cpu_threshold=90.0)
        self._resource_monitor.high_ram_warning.connect(self._on_high_ram_warning)
        self._resource_monitor.high_cpu_warning.connect(self._on_high_cpu_warning)
        self._resource_monitor.resource_recovered.connect(self._on_resource_recovered)
        
        # Start monitoring
        self._resource_monitor.start_monitoring(interval_ms=2000)  # Check every 2 seconds
        
        # Register optimization callbacks
        self._resource_monitor.register_optimization_callback(
            "clear_media_cache",
            self._optimize_clear_media_cache
        )
        self._resource_monitor.register_optimization_callback(
            "reduce_face_ai_rate",
            self._optimize_reduce_face_ai_rate
        )
        
        # Monitor theme changes
        self._theme_manager.theme_changed.connect(self.apply_theme)
        
        # Initialize module controllers
        # Note: Module windows are created lazily when requested
        self._timer_window = None
        self._media_window = None
        self._face_ai_window = None
        self._display_manager_window = None
        self._config_window = None
        self._content_automation_dashboard = None
        self._unified_dashboard = None
        self.timer_controller = TimerController()
        self.media_controller = MediaController()
        self.face_ai_controller = FaceAIController()
        self.display_controller = DisplayController()
        
        # Connect resource monitoring to controllers
        self._setup_resource_monitoring()
        
        # Initialize Content Automation Module
        self.content_automation = ContentAutomationIntegration(
            media_controller=self.media_controller,
            display_controller=self.display_controller
        )
        
        # Initialize Unified Controller
        from modules.operator.unified_controller import UnifiedController
        self.unified_controller = UnifiedController()
        self.unified_controller.initialize_modules(
            timer_controller=self.timer_controller,
            media_controller=self.media_controller,
            face_ai_controller=self.face_ai_controller,
            display_controller=self.display_controller
        )
        
        # Content Automation will start in showEvent after window is shown
        
        # Initialize UI
        self.init_ui()
        self.setup_menu_bar()
        self.setup_status_bar()
        
        # Window properties
        self.setWindowTitle("AI-Symp-Controller")
        self.setMinimumSize(700, 500)
        self.resize(1000, 700)
        
        # Make window responsive
        make_responsive(self)
    
    def _setup_resource_monitoring(self):
        """Setup resource monitoring connections."""
        # Set RAM check callback for MediaController
        self.media_controller.set_ram_check_callback(
            lambda: self._resource_monitor.is_high_ram_usage()
        )
        
        # Set RAM check callback for FaceAIController
        self.face_ai_controller.set_ram_check_callback(
            lambda: self._resource_monitor.is_high_ram_usage()
        )
        
    def init_ui(self):
        """Initialize the user interface."""
        # Central widget with scroll support
        from PyQt6.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        
        # Content widget
        central_widget = QWidget()
        make_responsive(central_widget)
        scroll_area.setWidget(central_widget)
        self.setCentralWidget(scroll_area)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Title label
        title_label = QLabel("AI-Symp-Controller")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 8px;")
        main_layout.addWidget(title_label)
        
        # Module buttons layout
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(15)
        
        # Timer module button
        timer_btn = QPushButton("Timer Module")
        timer_btn.setMinimumHeight(35)
        timer_btn.clicked.connect(self.show_timer_module)
        buttons_layout.addWidget(timer_btn)
        
        # Media module button
        media_btn = QPushButton("Media Player Module")
        media_btn.setMinimumHeight(35)
        media_btn.clicked.connect(self.show_media_module)
        buttons_layout.addWidget(media_btn)
        
        # Face AI module button
        face_ai_btn = QPushButton("Face AI Analysis Module")
        face_ai_btn.setMinimumHeight(35)
        face_ai_btn.clicked.connect(self.show_face_ai_module)
        buttons_layout.addWidget(face_ai_btn)
        
        # Display module button
        display_btn = QPushButton("Display Management Module")
        display_btn.setMinimumHeight(35)
        display_btn.clicked.connect(self.show_display_module)
        buttons_layout.addWidget(display_btn)
        
        # Config module button
        config_btn = QPushButton("Configuration")
        config_btn.setMinimumHeight(35)
        config_btn.clicked.connect(self.show_config_module)
        buttons_layout.addWidget(config_btn)
        
        # Symposium module button
        symposium_btn = QPushButton("Symposium Display")
        symposium_btn.setMinimumHeight(35)
        symposium_btn.clicked.connect(self.show_symposium_module)
        buttons_layout.addWidget(symposium_btn)
        
        # Content Automation module button
        content_automation_btn = QPushButton("📋 Content Automation Module")
        content_automation_btn.setMinimumHeight(35)
        content_automation_btn.clicked.connect(self.show_content_automation)
        content_automation_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        buttons_layout.addWidget(content_automation_btn)
        
        main_layout.addLayout(buttons_layout)
        main_layout.addStretch()
        
        # Status info label
        status_info = QLabel("Application initialized. Select a module to begin.")
        status_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_info.setStyleSheet("color: gray; font-style: italic; margin-top: 20px;")
        main_layout.addWidget(status_info)
        
    def setup_menu_bar(self):
        """Setup the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        fullscreen_action = QAction("Fullscreen", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        display_refresh_action = QAction("Refresh Displays", self)
        display_refresh_action.triggered.connect(self.refresh_displays)
        tools_menu.addAction(display_refresh_action)
        
        content_automation_action = QAction("📋 Content Automation", self)
        content_automation_action.triggered.connect(self.show_content_automation)
        tools_menu.addAction(content_automation_action)
        
        unified_dashboard_action = QAction("🎯 Unified Control Dashboard", self)
        unified_dashboard_action.triggered.connect(self.show_unified_dashboard)
        tools_menu.addAction(unified_dashboard_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_status_bar(self):
        """Setup the application status bar."""
        self.statusBar().showMessage("Ready")
        
    def show_timer_module(self):
        """Show timer module interface."""
        # Check if timer window already exists
        if not hasattr(self, '_timer_window') or self._timer_window is None:
            self._timer_window = TimerWindow(self)
        
        self._timer_window.show()
        self._timer_window.raise_()
        self._timer_window.activateWindow()
        
    def show_media_module(self):
        """Show media module interface."""
        # Check if media window already exists
        if not hasattr(self, '_media_window') or self._media_window is None:
            # Pass timer controller for overlay integration
            self._media_window = MediaWindow(self, timer_controller=self.timer_controller)
        
        self._media_window.show()
        self._media_window.raise_()
        self._media_window.activateWindow()
        
    def show_face_ai_module(self):
        """Show face AI module interface."""
        # Check if face AI window already exists
        if not hasattr(self, '_face_ai_window') or self._face_ai_window is None:
            self._face_ai_window = FaceAIWindow(self, controller=self.face_ai_controller)
        
        self._face_ai_window.show()
        self._face_ai_window.raise_()
        self._face_ai_window.activateWindow()
        
    def show_display_module(self):
        """Show display module interface."""
        # Check if display manager window already exists
        if not hasattr(self, '_display_manager_window') or self._display_manager_window is None:
            self._display_manager_window = DisplayManagerWindow(self)
        
        self._display_manager_window.show()
        self._display_manager_window.raise_()
        self._display_manager_window.activateWindow()
        
    def show_config_module(self):
        """Show configuration module interface."""
        # Check if config window already exists
        if not hasattr(self, '_config_window') or self._config_window is None:
            self._config_window = ConfigWindow(self)
            # Connect config changed signal
            self._config_window.config_changed.connect(self.on_config_changed)
        
        self._config_window.show()
        self._config_window.raise_()
        self._config_window.activateWindow()
    
    def on_config_changed(self, config: dict):
        """Handle configuration changes."""
        # Update config manager
        self.config_manager.set_all_config(config)
        self.config_manager.save_config()
        self.statusBar().showMessage("Configuration updated", 3000)
    
    def show_symposium_module(self):
        """Show symposium display module interface."""
        # Check if symposium window already exists
        if not hasattr(self, '_symposium_window') or self._symposium_window is None:
            self._symposium_window = SymposiumWindow(self)
            
            # Connect Content Automation with Symposium
            if hasattr(self._symposium_window, 'agenda_manager'):
                self.content_automation.set_agenda_manager(self._symposium_window.agenda_manager)
        
        self._symposium_window.show()
        self._symposium_window.raise_()
        self._symposium_window.activateWindow()
    
    def show_content_automation(self):
        """Show content automation dashboard."""
        if not self._content_automation_dashboard:
            self._content_automation_dashboard = self.content_automation.create_dashboard()
        
        self._content_automation_dashboard.show()
        self._content_automation_dashboard.raise_()
        self._content_automation_dashboard.activateWindow()
    
    def showEvent(self, event):
        """Handle window show event - start Content Automation after window is shown."""
        super().showEvent(event)
        # Start Content Automation after window is shown (event loop is running)
        if not hasattr(self, '_content_automation_started'):
            self._content_automation_started = True
            # Use QTimer to ensure event loop is fully running
            QTimer.singleShot(100, self._start_content_automation_delayed)
    
    def _start_content_automation_delayed(self):
        """Start content automation module after event loop is running."""
        try:
            # Try to get running event loop
            try:
                loop = asyncio.get_running_loop()
                # Event loop is running, create task
                asyncio.create_task(self._start_content_automation())
            except RuntimeError:
                # No running loop, try to get event loop
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(self._start_content_automation())
                    else:
                        # Loop exists but not running - use asyncio.run
                        asyncio.run(self._start_content_automation())
                except RuntimeError:
                    # No event loop at all - use QTimer to retry later
                    print("Warning: No event loop available, will retry...")
                    QTimer.singleShot(500, self._start_content_automation_delayed)
        except Exception as e:
            print(f"Error starting Content Automation: {e}")
            self.statusBar().showMessage(f"Content Automation Error: {e}")
    
    async def _start_content_automation(self):
        """Start content automation module."""
        try:
            await self.content_automation.start()
            print("✅ Content Automation Module started")
            self.statusBar().showMessage("Content Automation Ready")
        except Exception as e:
            print(f"❌ Content Automation error: {e}")
            self.statusBar().showMessage(f"Content Automation Error: {e}")
    
    def show_unified_dashboard(self):
        """Show unified control dashboard."""
        try:
            if not self._unified_dashboard:
                from modules.operator.unified_dashboard import UnifiedDashboard
                
                # Ensure unified_controller is initialized
                if not hasattr(self, 'unified_controller') or self.unified_controller is None:
                    from modules.operator.unified_controller import UnifiedController
                    self.unified_controller = UnifiedController()
                    self.unified_controller.initialize_modules(
                        timer_controller=self.timer_controller,
                        media_controller=self.media_controller,
                        face_ai_controller=self.face_ai_controller,
                        display_controller=self.display_controller
                    )
                
                self._unified_dashboard = UnifiedDashboard(
                    unified_controller=self.unified_controller
                )
            
            self._unified_dashboard.show()
            self._unified_dashboard.raise_()
            self._unified_dashboard.activateWindow()
            
        except Exception as e:
            print(f"Error opening Unified Dashboard: {e}")
            import traceback
            traceback.print_exc()
            
            # Show error message to user
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open Unified Dashboard:\n{str(e)}\n\nCheck console for details."
            )
        
    def toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
            
    def refresh_displays(self):
        """Refresh available displays."""
        self.display_controller.refresh_displays()
        screens = self.display_controller.get_available_screens()
        self.statusBar().showMessage(f"Refreshed displays: {len(screens)} screen(s) detected", 3000)
        
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About AI-Symp-Controller",
            "<h2>AI-Symp-Controller</h2>"
            "<p>Version 1.0.0</p>"
            "<p>A modular desktop application for presentation control with:</p>"
            "<ul>"
            "<li>Smart graphical timer</li>"
            "<li>Media and slide playback</li>"
            "<li>Audience attention analysis (AI)</li>"
            "<li>Multi-display management</li>"
            "</ul>"
            "<p>Built with PyQt6 for Windows 11</p>"
            "<p>Optimized for HP Envy x360 (AMD Ryzen 5, Radeon 760M)</p>"
        )
        
    def apply_theme(self):
        """Apply system theme to main window."""
        stylesheet = self._theme_manager.get_stylesheet()
        self.setStyleSheet(stylesheet)
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel events for scrolling when menu is hidden."""
        # Forward to central widget's scroll area if it exists
        from PyQt6.QtWidgets import QScrollArea
        central = self.centralWidget()
        if isinstance(central, QScrollArea):
            scrollbar = central.verticalScrollBar()
            if scrollbar.isVisible():
                delta = event.angleDelta().y()
                scrollbar.setValue(scrollbar.value() - delta // 8)
                event.accept()
                return
        event.ignore()
    
    def _on_high_ram_warning(self, ram_percent: float, used_gb: float, total_gb: float):
        """Handle high RAM usage warning."""
        from modules.utils.resource_warning_dialog import ResourceWarningDialog
        
        dialog = ResourceWarningDialog(self)
        dialog.show_ram_warning(ram_percent, used_gb, total_gb)
        
        # Auto-optimize if RAM is very high (>85%)
        if ram_percent > 85:
            logger.warning("Very high RAM usage detected. Auto-optimizing...")
            self._optimize_clear_media_cache()
            self._optimize_reduce_face_ai_rate()
    
    def _on_high_cpu_warning(self, cpu_percent: float):
        """Handle high CPU usage warning."""
        logger.warning(f"High CPU usage: {cpu_percent:.1f}%")
        # Can reduce processing rate if needed
    
    def _on_resource_recovered(self):
        """Handle resource recovery."""
        logger.info("System resources recovered")
    
    def _optimize_clear_media_cache(self):
        """Optimization: Clear media cache."""
        try:
            if self.media_controller:
                self.media_controller.clear_all_cache()
                logger.info("Media cache cleared for optimization")
        except Exception as e:
            logger.error(f"Error clearing media cache: {e}")
    
    def _optimize_reduce_face_ai_rate(self):
        """Optimization: Reduce Face AI processing rate."""
        try:
            if self.face_ai_controller and self.face_ai_controller.is_analyzing():
                current_rate = self.face_ai_controller._process_every_n_frames
                new_rate = min(current_rate * 2, 8)  # Double skipping, max 8
                self.face_ai_controller.set_processing_rate(new_rate)
                
                # Also reduce resolution if needed
                self.face_ai_controller.set_max_resolution(480, 360)  # Lower resolution
                
                logger.info(f"Face AI processing rate reduced: {current_rate} -> {new_rate}")
        except Exception as e:
            logger.error(f"Error reducing Face AI rate: {e}")
    
    def closeEvent(self, event):
        """Handle window close event with proper resource cleanup."""
        # Stop resource monitoring
        if hasattr(self, '_resource_monitor'):
            self._resource_monitor.stop_monitoring()
        
        # Stop Face AI if running
        if self.face_ai_controller.is_analyzing():
            self.face_ai_controller.stop_analysis()
        
        # Stop Content Automation
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self.content_automation.stop())
        except RuntimeError:
            # No running loop, try to stop synchronously
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.content_automation.stop())
                else:
                    loop.run_until_complete(self.content_automation.stop())
            except Exception:
                pass  # Ignore errors during shutdown
        
        # Save configuration before closing
        self.config_manager.save_config()
        
        # Close all module windows
        if self._timer_window:
            self._timer_window.close()
        if self._media_window:
            self._media_window.close()
        if self._face_ai_window:
            self._face_ai_window.close()
        if self._display_manager_window:
            self._display_manager_window.close()
        if self._config_window:
            self._config_window.close()
        if hasattr(self, '_symposium_window') and self._symposium_window:
            self._symposium_window.close()
        
        event.accept()


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("AI-Symp-Controller")
    app.setOrganizationName("AI-Symp-Controller")
    
    # Try to use qasync event loop for async support
    try:
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Run with async support
        # Note: app.exec() is not a coroutine, so we need to run it differently
        with loop:
            # Start the Qt event loop
            app.exec()
    except (ImportError, NameError):
        # Fallback to standard Qt event loop (async features will log warnings)
        print("⚠️ qasync not available - using standard event loop")
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Run application
        sys.exit(app.exec())


if __name__ == "__main__":
    main()

