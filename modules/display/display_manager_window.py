"""
Display Manager Window Module

Main window for managing multiple display outputs and routing content
from different modules (timer, media, face_ai) to different displays.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QGroupBox, QListWidget,
    QListWidgetItem, QMessageBox, QCheckBox, QSpinBox, QFrame,
    QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QScreen, QFont, QPixmap, QPainter, QColor
from typing import List, Dict, Optional
import sys

from .display_controller import DisplayController
from .display_output import DisplayOutput
from modules.utils.theme_manager import ThemeManager
from modules.utils.scrollable_widget import make_responsive
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtWidgets import QScrollArea


class DisplayPreviewWidget(QWidget):
    """Preview widget showing display status and content."""
    
    def __init__(self, display_output: DisplayOutput, parent=None):
        """Initialize preview widget."""
        super().__init__(parent)
        self._display_output = display_output
        self._thumbnail_size = QSize(200, 150)
        
        self.setup_ui()
        self.update_preview()
        
        # Update preview periodically
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self.update_preview)
        self._update_timer.start(1000)  # Update every second
    
    def setup_ui(self):
        """Setup preview UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        
        # Display name
        name_label = QLabel(self._display_output.get_display_name())
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(name_label)
        
        # Thumbnail preview
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setMinimumSize(self._thumbnail_size)
        self.thumbnail_label.setMaximumSize(self._thumbnail_size)
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                border: 2px solid #3d3d3d;
                border-radius: 5px;
                background-color: #1a1a1a;
            }
        """)
        layout.addWidget(self.thumbnail_label)
        
        # Status label
        self.status_label = QLabel("No content")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 11px; color: #999999;")
        layout.addWidget(self.status_label)
        
        # Preview button
        preview_btn = QPushButton("Preview")
        preview_btn.setMaximumHeight(30)
        preview_btn.clicked.connect(self.toggle_preview)
        layout.addWidget(preview_btn)
    
    def update_preview(self):
        """Update preview thumbnail and status."""
        # Update status
        content_type = self._display_output.get_content_type()
        if content_type == DisplayOutput.CONTENT_NONE:
            self.status_label.setText("No content")
            self.status_label.setStyleSheet("font-size: 11px; color: #999999;")
        else:
            self.status_label.setText(f"Content: {content_type.upper()}")
            self.status_label.setStyleSheet("font-size: 11px; color: #00ff00;")
        
        # Generate thumbnail (simplified - in full implementation would capture actual screen)
        pixmap = QPixmap(self._thumbnail_size)
        pixmap.fill(QColor(30, 30, 30))
        
        painter = QPainter(pixmap)
        painter.setPen(QColor(150, 150, 150))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(
            pixmap.rect(),
            Qt.AlignmentFlag.AlignCenter,
            f"{self._display_output.get_display_name()}\n{content_type.upper()}"
        )
        painter.end()
        
        self.thumbnail_label.setPixmap(pixmap)
    
    def toggle_preview(self):
        """Toggle preview mode on display."""
        current_mode = self._display_output.is_preview_mode()
        self._display_output.set_preview_mode(not current_mode)
        self.update_preview()


class DisplayManagerWindow(QMainWindow):
    """
    Main window for display management and content routing.
    
    Features:
    - Automatic display detection
    - Display naming and configuration
    - Content routing (timer, media, face_ai)
    - Preview/test mode
    - OBS Studio compatibility
    - Fullscreen management
    """
    
    def __init__(self, parent=None):
        """Initialize the display manager window."""
        super().__init__(parent)
        
        # Display management
        self._display_controller = DisplayController()
        self._display_outputs: Dict[str, DisplayOutput] = {}
        self._screens: List[QScreen] = []
        
        # Content routing
        self._available_content = {
            DisplayOutput.CONTENT_TIMER: "Timer Module",
            DisplayOutput.CONTENT_MEDIA: "Media Player",
            DisplayOutput.CONTENT_FACE_AI: "Face AI Analytics",
            DisplayOutput.CONTENT_NONE: "None"
        }
        
        # Initialize theme manager
        self._theme_manager = ThemeManager()
        
        # Initialize UI
        self.init_ui()
        
        # Window properties
        self.setWindowTitle("AI-Symp-Controller - Display Manager")
        self.setMinimumSize(850, 600)
        self.resize(1200, 750)
        
        # Make responsive
        make_responsive(self)
        
        # Detect displays on startup
        self.refresh_displays()
        
        # Apply system theme
        self.apply_theme()
        
        # Monitor theme changes
        self._theme_manager.theme_changed.connect(self.apply_theme)
    
    def apply_theme(self):
        """Apply theme based on system settings."""
        stylesheet = self._theme_manager.get_stylesheet()
        self.setStyleSheet(stylesheet)
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel events for scrolling when menu is hidden."""
        central = self.centralWidget()
        if isinstance(central, QScrollArea):
            scrollbar = central.verticalScrollBar()
            if scrollbar.isVisible():
                delta = event.angleDelta().y()
                scrollbar.setValue(scrollbar.value() - delta // 8)
                event.accept()
                return
        event.ignore()
    
    def init_ui(self):
        """Initialize the user interface with scrollable support."""
        # Create scrollable area
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
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Left panel: Display list and controls
        left_panel = self.create_left_panel()
        make_responsive(left_panel)
        main_layout.addWidget(left_panel, stretch=1)
        
        # Right panel: Content routing and previews
        right_panel = self.create_right_panel()
        make_responsive(right_panel)
        main_layout.addWidget(right_panel, stretch=2)
        
        # Menu bar
        self.setup_menu_bar()
        
        # Status bar
        self.statusBar().showMessage("Ready - Displays detected")
        
    def create_left_panel(self) -> QWidget:
        """Create left panel with display list and controls."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        
        # Display detection group
        detect_group = QGroupBox("Display Detection")
        detect_layout = QVBoxLayout()
        
        self.display_count_label = QLabel("Displays: 0")
        self.display_count_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        detect_layout.addWidget(self.display_count_label)
        
        refresh_btn = QPushButton("Refresh Displays")
        refresh_btn.clicked.connect(self.refresh_displays)
        refresh_btn.setToolTip("Detect all connected displays")
        detect_layout.addWidget(refresh_btn)
        
        detect_group.setLayout(detect_layout)
        layout.addWidget(detect_group)
        
        # Display list
        list_group = QGroupBox("Connected Displays")
        list_layout = QVBoxLayout()
        
        self.display_list = QListWidget()
        self.display_list.itemClicked.connect(self.on_display_selected)
        list_layout.addWidget(self.display_list)
        
        # Display controls
        controls_layout = QVBoxLayout()
        
        fullscreen_btn = QPushButton("Fullscreen Selected")
        fullscreen_btn.clicked.connect(self.fullscreen_selected_display)
        fullscreen_btn.setToolTip("Put selected display in fullscreen mode")
        controls_layout.addWidget(fullscreen_btn)
        
        test_all_btn = QPushButton("Test All Displays")
        test_all_btn.clicked.connect(self.test_all_displays)
        test_all_btn.setToolTip("Show test pattern on all displays")
        controls_layout.addWidget(test_all_btn)
        
        validate_btn = QPushButton("Validate All Outputs")
        validate_btn.clicked.connect(self.validate_and_report)
        validate_btn.setToolTip("Check all displays have valid widgets assigned")
        validate_btn.setStyleSheet("""
            QPushButton {
                background-color: #3d5a3d;
                border-color: #4d6a4d;
            }
            QPushButton:hover {
                background-color: #4d6a4d;
            }
        """)
        controls_layout.addWidget(validate_btn)
        
        clear_all_btn = QPushButton("Clear All Content")
        clear_all_btn.clicked.connect(self.clear_all_content)
        clear_all_btn.setToolTip("Remove all content from displays")
        controls_layout.addWidget(clear_all_btn)
        
        list_layout.addLayout(controls_layout)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        layout.addStretch()
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Create right panel with content routing and previews."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        
        # Content routing group
        routing_group = QGroupBox("Content Routing")
        routing_layout = QVBoxLayout()
        
        # Display selection for routing
        display_select_layout = QHBoxLayout()
        display_select_layout.addWidget(QLabel("Display:"))
        
        self.display_combo = QComboBox()
        self.display_combo.setToolTip("Select target display for content")
        display_select_layout.addWidget(self.display_combo)
        
        routing_layout.addLayout(display_select_layout)
        
        # Content selection
        content_select_layout = QHBoxLayout()
        content_select_layout.addWidget(QLabel("Content:"))
        
        self.content_combo = QComboBox()
        for content_id, content_name in self._available_content.items():
            self.content_combo.addItem(content_name, content_id)
        self.content_combo.setToolTip("Select content type to route")
        content_select_layout.addWidget(self.content_combo)
        
        routing_layout.addLayout(content_select_layout)
        
        # Route button
        route_btn = QPushButton("Route Content to Display")
        route_btn.clicked.connect(self.route_content)
        route_btn.setToolTip("Send selected content to selected display")
        routing_layout.addWidget(route_btn)
        
        routing_group.setLayout(routing_layout)
        layout.addWidget(routing_group)
        
        # Display previews
        preview_group = QGroupBox("Display Previews")
        preview_layout = QVBoxLayout()
        
        # Scroll area for previews
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: 1px solid #3d3d3d; border-radius: 5px;")
        
        self.previews_widget = QWidget()
        self.previews_layout = QGridLayout(self.previews_widget)
        self.previews_layout.setSpacing(10)
        
        scroll.setWidget(self.previews_widget)
        preview_layout.addWidget(scroll)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        return panel
    
    def setup_menu_bar(self):
        """Setup the application menu bar."""
        menubar = self.menuBar()
        
        # Display menu
        display_menu = menubar.addMenu("Display")
        
        refresh_action = display_menu.addAction("Refresh Displays")
        refresh_action.setShortcut("Ctrl+R")
        refresh_action.triggered.connect(self.refresh_displays)
        
        display_menu.addSeparator()
        
        validate_action = display_menu.addAction("Validate All Outputs")
        validate_action.setShortcut("Ctrl+V")
        validate_action.triggered.connect(self.validate_and_report)
        
        display_menu.addSeparator()
        
        exit_action = display_menu.addAction("Exit")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        fullscreen_all_action = view_menu.addAction("Fullscreen All")
        fullscreen_all_action.triggered.connect(self.fullscreen_all_displays)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = help_menu.addAction("About Display Manager")
        about_action.triggered.connect(self.show_about)
        
        obs_help_action = help_menu.addAction("OBS Studio Help")
        obs_help_action.triggered.connect(self.show_obs_help)
    
    def refresh_displays(self):
        """Detect and list all connected displays."""
        self._display_controller.refresh_displays()
        self._screens = self._display_controller.get_available_screens()
        
        # Update display count
        screen_count = len(self._screens)
        self.display_count_label.setText(f"Displays: {screen_count}")
        
        # Clear existing outputs
        for output in self._display_outputs.values():
            output.close()
            output.deleteLater()
        self._display_outputs.clear()
        
        # Clear lists
        self.display_list.clear()
        self.display_combo.clear()
        
        # Create display outputs
        for idx, screen in enumerate(self._screens):
            geometry = screen.geometry()
            display_name = f"Display {idx + 1}"
            if idx == 0:
                display_name = "Primary Display"
            
            # Create display output
            output = DisplayOutput(screen, display_name, self)
            output.output_ready.connect(self.on_display_ready)
            self._display_outputs[display_name] = output
            
            # Add to list
            item = QListWidgetItem(f"{display_name}\n{geometry.width()}x{geometry.height()}")
            item.setData(Qt.ItemDataRole.UserRole, display_name)
            self.display_list.addItem(item)
            
            # Add to combo
            self.display_combo.addItem(f"{display_name} ({geometry.width()}x{geometry.height()})", display_name)
        
        # Update previews
        self.update_previews()
        
        self.statusBar().showMessage(f"Detected {screen_count} display(s)", 3000)
    
    def on_display_selected(self, item: QListWidgetItem):
        """Handle display selection."""
        display_name = item.data(Qt.ItemDataRole.UserRole)
        if display_name in self._display_outputs:
            # Select in combo
            index = self.display_combo.findData(display_name)
            if index >= 0:
                self.display_combo.setCurrentIndex(index)
    
    def on_display_ready(self, display_name: str):
        """Handle display ready signal."""
        self.statusBar().showMessage(f"{display_name} ready", 2000)
    
    def route_content(self):
        """Route selected content to selected display."""
        display_name = self.display_combo.currentData()
        content_id = self.content_combo.currentData()
        
        if not display_name or not content_id:
            QMessageBox.warning(self, "Error", "Please select both display and content.")
            return
        
        if display_name not in self._display_outputs:
            QMessageBox.warning(self, "Error", f"Display '{display_name}' not found.")
            return
        
        output = self._display_outputs[display_name]
        
        # Route content based on type
        content_widget = None
        if content_id == DisplayOutput.CONTENT_TIMER:
            content_widget = self.get_timer_widget()
        elif content_id == DisplayOutput.CONTENT_MEDIA:
            content_widget = self.get_media_widget()
        elif content_id == DisplayOutput.CONTENT_FACE_AI:
            content_widget = self.get_face_ai_widget()
        elif content_id == DisplayOutput.CONTENT_NONE:
            # No widget needed
            pass
        else:
            QMessageBox.warning(self, "Error", f"Unknown content type: {content_id}")
            return
        
        # Validate widget if content type requires it
        if content_id != DisplayOutput.CONTENT_NONE:
            if content_widget is None:
                content_name = self.content_combo.currentText()
                QMessageBox.warning(
                    self,
                    "Widget Not Available",
                    f"Cannot route '{content_name}' to {display_name}.\n\n"
                    f"The required widget is not available.\n"
                    f"Please ensure the {content_name} module is open and ready.\n\n"
                    f"To fix:\n"
                    f"1. Open the {content_name} module from the main application\n"
                    f"2. Ensure the module window is visible\n"
                    f"3. Try routing again"
                )
                return
            
            # Additional validation: check if widget is valid
            if not isinstance(content_widget, QWidget):
                content_name = self.content_combo.currentText()
                QMessageBox.warning(
                    self,
                    "Invalid Widget",
                    f"Cannot route '{content_name}' to {display_name}.\n\n"
                    f"The widget is not a valid QWidget instance.\n"
                    f"Please try opening the {content_name} module again."
                )
                return
        
        # Set content with validation
        success = output.set_content(content_id, content_widget)
        if not success:
            content_name = self.content_combo.currentText()
            QMessageBox.warning(
                self,
                "Routing Failed",
                f"Failed to route '{content_name}' to {display_name}.\n\n"
                f"An error occurred while setting the content widget.\n"
                f"Please try again or contact support."
            )
            return
        
        # Validate widget after assignment
        is_valid, error_msg = output.validate_widget()
        if not is_valid:
            QMessageBox.warning(
                self,
                "Widget Validation Failed",
                f"Widget validation failed for {display_name}.\n\n"
                f"Error: {error_msg}\n\n"
                f"Please re-assign content to this display."
            )
            return
        
        # Show output window
        output.show()
        output.raise_()
        
        # Update previews
        self.update_previews()
        
        self.statusBar().showMessage(f"Routed {self.content_combo.currentText()} to {display_name}", 3000)
    
    def get_timer_widget(self) -> Optional[QWidget]:
        """Get timer widget from main application."""
        # In full implementation, would retrieve from main window
        return None
    
    def get_media_widget(self) -> Optional[QWidget]:
        """Get media widget from main application."""
        return None
    
    def get_face_ai_widget(self) -> Optional[QWidget]:
        """Get face AI widget from main application."""
        return None
    
    def initialize_outputs(self) -> tuple[bool, list]:
        """
        Validate all configured outputs before starting event/session.
        
        Returns:
            tuple: (all_valid, error_list)
            - all_valid: True if all outputs are valid, False otherwise
            - error_list: List of error messages for invalid outputs
        """
        errors = []
        all_valid = True
        
        for display_name, output in self._display_outputs.items():
            # Check if display has content assigned
            content_type = output.get_content_type()
            if content_type == DisplayOutput.CONTENT_NONE:
                continue  # Skip displays with no content (not an error)
            
            # Validate widget for displays with content
            is_valid, error_msg = output.validate_widget()
            if not is_valid:
                all_valid = False
                error_text = f"{display_name}: {error_msg}"
                errors.append(error_text)
        
        return (all_valid, errors)
    
    def validate_and_report(self) -> bool:
        """
        Validate all outputs and show error dialog if needed.
        
        Returns:
            bool: True if all outputs are valid, False otherwise
        """
        all_valid, errors = self.initialize_outputs()
        
        if not all_valid:
            error_text = "The following displays have invalid or missing widgets:\n\n"
            error_text += "\n".join(f"• {error}" for error in errors)
            error_text += "\n\nPlease assign valid content modules to these displays before proceeding."
            
            QMessageBox.warning(
                self,
                "Display Validation Failed",
                error_text
            )
        
        return all_valid
    
    def fullscreen_selected_display(self):
        """Put selected display in fullscreen mode."""
        display_name = self.display_combo.currentData()
        if not display_name:
            QMessageBox.warning(self, "Error", "Please select a display first.")
            return
        
        if display_name not in self._display_outputs:
            QMessageBox.warning(self, "Error", f"Display '{display_name}' not found.")
            return
        
        output = self._display_outputs[display_name]
        
        # Validate widget before fullscreen
        if output.get_content_type() != DisplayOutput.CONTENT_NONE:
            is_valid, error_msg = output.validate_widget()
            if not is_valid:
                QMessageBox.warning(
                    self,
                    "Cannot Enter Fullscreen",
                    f"Cannot put {display_name} in fullscreen mode.\n\n"
                    f"Error: {error_msg}\n\n"
                    f"Please assign a valid content widget first."
                )
                return
        
        output.enable_fullscreen()
        self.statusBar().showMessage(f"{display_name} in fullscreen mode", 2000)
    
    def fullscreen_all_displays(self):
        """Put all displays in fullscreen mode."""
        invalid_displays = []
        
        for display_name, output in self._display_outputs.items():
            # Validate widget before fullscreen
            if output.get_content_type() != DisplayOutput.CONTENT_NONE:
                is_valid, error_msg = output.validate_widget()
                if not is_valid:
                    invalid_displays.append((display_name, error_msg))
                    continue
            
            output.enable_fullscreen()
        
        if invalid_displays:
            error_text = "The following displays could not enter fullscreen mode:\n\n"
            error_text += "\n".join(f"• {name}: {error}" for name, error in invalid_displays)
            error_text += "\n\nPlease assign valid content widgets to these displays first."
            
            QMessageBox.warning(
                self,
                "Fullscreen Failed",
                error_text
            )
        else:
            self.statusBar().showMessage("All displays in fullscreen mode", 2000)
    
    def test_all_displays(self):
        """Show test pattern on all displays."""
        for display_name, output in self._display_outputs.items():
            output.set_preview_mode(True)
            output.show()
            output.raise_()
        self.statusBar().showMessage("Test pattern shown on all displays", 2000)
    
    def clear_all_content(self):
        """Clear content from all displays."""
        reply = QMessageBox.question(
            self,
            "Clear All Content",
            "Are you sure you want to clear content from all displays?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for output in self._display_outputs.values():
                output.set_content(DisplayOutput.CONTENT_NONE)
                output.set_preview_mode(False)
            self.update_previews()
            self.statusBar().showMessage("All content cleared", 2000)
    
    def update_previews(self):
        """Update display preview widgets."""
        # Clear existing previews
        while self.previews_layout.count():
            child = self.previews_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
        
        # Create previews for each display
        row = 0
        col = 0
        max_cols = 2
        
        for display_name, output in self._display_outputs.items():
            preview = DisplayPreviewWidget(output, self.previews_widget)
            self.previews_layout.addWidget(preview, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Display Manager",
            "<h2>AI-Symp-Controller - Display Manager</h2>"
            "<p><b>Version 1.0.0</b></p>"
            "<p>Advanced multi-display management with:</p>"
            "<ul>"
            "<li>Automatic display detection</li>"
            "<li>Content routing (timer, media, face AI)</li>"
            "<li>Preview and test modes</li>"
            "<li>Fullscreen support</li>"
            "<li>OBS Studio compatible</li>"
            "<li>Auto-scaling and centering</li>"
            "</ul>"
            "<p>Optimized for Windows 11 and HP Envy x360</p>"
        )
    
    def show_obs_help(self):
        """Show OBS Studio help dialog."""
        help_text = """
        <h3>OBS Studio Integration Guide</h3>
        
        <p><b>Window Capture Setup:</b></p>
        <ol>
        <li>Open OBS Studio</li>
        <li>Create a new Scene (or use existing)</li>
        <li>Add Source → Window Capture</li>
        <li>Select the display window from dropdown:
        <ul>
        <li>"Display Output - Display 1"</li>
        <li>"Display Output - Primary Display"</li>
        <li>etc.</li>
        </ul>
        </li>
        <li>Set Window Match Priority: "Match title, otherwise find window of same type"</li>
        <li>Enable "Capture Cursor" if desired</li>
        <li>Click OK</li>
        </ol>
        
        <p><b>Recommended Settings:</b></p>
        <ul>
        <li>Output Resolution: Match your display resolution (1920x1080 recommended)</li>
        <li>Frame Rate: 30 FPS</li>
        <li>Color Format: NV12 or I420</li>
        <li>Use Window Capture (not Display Capture) for better performance</li>
        </ul>
        
        <p><b>Tips:</b></p>
        <ul>
        <li>Put display in fullscreen mode before capturing for best results</li>
        <li>Test your setup before live presentations</li>
        <li>Each display output appears as separate window for individual capture</li>
        </ul>
        """
        QMessageBox.information(self, "OBS Studio Help", help_text)
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Close all display outputs
        for output in self._display_outputs.values():
            output.close()
        event.accept()

