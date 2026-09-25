"""
Smart Notification System

Intelligent notification panel with actionable alerts, timeline view,
and automatic prioritization.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette
from datetime import datetime
from typing import Optional, List, Callable
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class NotificationLevel(Enum):
    """Notification severity levels."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationAction:
    """Action button for notification."""
    
    def __init__(self, label: str, callback: Callable, icon: Optional[str] = None):
        """
        Initialize action.
        
        Args:
            label: Button label
            callback: Function to call when clicked
            icon: Optional icon name
        """
        self.label = label
        self.callback = callback
        self.icon = icon


class Notification:
    """Individual notification data."""
    
    def __init__(
        self,
        title: str,
        message: str,
        level: NotificationLevel = NotificationLevel.INFO,
        actions: Optional[List[NotificationAction]] = None,
        auto_dismiss: bool = True,
        dismiss_delay: int = 5000,  # milliseconds
        timestamp: Optional[datetime] = None
    ):
        """
        Initialize notification.
        
        Args:
            title: Notification title
            message: Notification message
            level: Severity level
            actions: Optional list of actions
            auto_dismiss: Auto-dismiss after delay
            dismiss_delay: Auto-dismiss delay in milliseconds
            timestamp: Optional timestamp (defaults to now)
        """
        self.id = id(self)  # Unique ID
        self.title = title
        self.message = message
        self.level = level
        self.actions = actions or []
        self.auto_dismiss = auto_dismiss
        self.dismiss_delay = dismiss_delay
        self.timestamp = timestamp or datetime.now()
        self.dismissed = False


class NotificationWidget(QFrame):
    """Widget for displaying a single notification."""
    
    dismissed = pyqtSignal(int)  # notification_id
    action_clicked = pyqtSignal(int, str)  # notification_id, action_label
    
    def __init__(self, notification: Notification, parent=None):
        """
        Initialize notification widget.
        
        Args:
            notification: Notification data
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.notification = notification
        self._setup_ui()
        self._apply_style()
        
        # Auto-dismiss timer
        if notification.auto_dismiss:
            QTimer.singleShot(notification.dismiss_delay, self._auto_dismiss)
    
    def _setup_ui(self):
        """Setup UI components."""
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setLineWidth(2)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(8)
        
        # Header row (icon, title, time, close button)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        # Level icon/indicator
        level_label = QLabel(self._get_level_icon())
        level_label.setFont(QFont("Arial", 14))
        header_layout.addWidget(level_label)
        
        # Title
        title_label = QLabel(self.notification.title)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(10)
        title_label.setFont(title_font)
        title_label.setWordWrap(True)
        header_layout.addWidget(title_label, stretch=1)
        
        # Timestamp
        time_label = QLabel(self._format_time())
        time_label.setStyleSheet("color: gray; font-size: 9px;")
        header_layout.addWidget(time_label)
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 18px;
                font-weight: bold;
                color: #666;
            }
            QPushButton:hover {
                color: #000;
                background: #f0f0f0;
                border-radius: 10px;
            }
        """)
        close_btn.clicked.connect(self._on_dismiss)
        header_layout.addWidget(close_btn)
        
        main_layout.addLayout(header_layout)
        
        # Message
        message_label = QLabel(self.notification.message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("color: #333; font-size: 9px;")
        main_layout.addWidget(message_label)
        
        # Actions
        if self.notification.actions:
            actions_layout = QHBoxLayout()
            actions_layout.setSpacing(8)
            actions_layout.addStretch()
            
            for action in self.notification.actions:
                btn = QPushButton(action.label)
                btn.setStyleSheet("""
                    QPushButton {
                        background: #007bff;
                        color: white;
                        border: none;
                        padding: 5px 15px;
                        border-radius: 3px;
                        font-size: 9px;
                    }
                    QPushButton:hover {
                        background: #0056b3;
                    }
                """)
                btn.clicked.connect(lambda checked, a=action: self._on_action(a))
                actions_layout.addWidget(btn)
            
            main_layout.addLayout(actions_layout)
    
    def _apply_style(self):
        """Apply style based on notification level."""
        colors = {
            NotificationLevel.INFO: "#d1ecf1",
            NotificationLevel.SUCCESS: "#d4edda",
            NotificationLevel.WARNING: "#fff3cd",
            NotificationLevel.ERROR: "#f8d7da",
            NotificationLevel.CRITICAL: "#f5c6cb"
        }
        
        border_colors = {
            NotificationLevel.INFO: "#bee5eb",
            NotificationLevel.SUCCESS: "#c3e6cb",
            NotificationLevel.WARNING: "#ffeaa7",
            NotificationLevel.ERROR: "#f5c6cb",
            NotificationLevel.CRITICAL: "#f1b0b7"
        }
        
        bg_color = colors.get(self.notification.level, "#f8f9fa")
        border_color = border_colors.get(self.notification.level, "#dee2e6")
        
        self.setStyleSheet(f"""
            NotificationWidget {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 5px;
            }}
        """)
    
    def _get_level_icon(self) -> str:
        """Get icon for notification level."""
        icons = {
            NotificationLevel.INFO: "ℹ️",
            NotificationLevel.SUCCESS: "✅",
            NotificationLevel.WARNING: "⚠️",
            NotificationLevel.ERROR: "❌",
            NotificationLevel.CRITICAL: "🔴"
        }
        return icons.get(self.notification.level, "📢")
    
    def _format_time(self) -> str:
        """Format timestamp."""
        now = datetime.now()
        diff = now - self.notification.timestamp
        
        if diff.seconds < 60:
            return "Just now"
        elif diff.seconds < 3600:
            minutes = diff.seconds // 60
            return f"{minutes}m ago"
        else:
            hours = diff.seconds // 3600
            return f"{hours}h ago"
    
    def _on_dismiss(self):
        """Handle dismiss button click."""
        self.notification.dismissed = True
        self.dismissed.emit(self.notification.id)
    
    def _auto_dismiss(self):
        """Auto-dismiss after delay."""
        if not self.notification.dismissed:
            self._on_dismiss()
    
    def _on_action(self, action: NotificationAction):
        """Handle action button click."""
        try:
            action.callback()
            self.action_clicked.emit(self.notification.id, action.label)
            # Auto-dismiss after action
            self._on_dismiss()
        except Exception as e:
            logger.error(f"Error executing notification action: {e}", exc_info=True)


class NotificationPanel(QWidget):
    """
    Smart notification panel with timeline view.
    
    Features:
    - Automatic notification queueing
    - Priority-based ordering
    - Auto-dismiss with configurable delay
    - Action buttons
    - Timeline view
    - Filtering by level
    """
    
    notification_dismissed = pyqtSignal(int)  # notification_id
    
    def __init__(self, parent=None):
        """Initialize notification panel."""
        super().__init__(parent)
        
        self.notifications: List[Notification] = []
        self._notification_widgets = {}
        
        self._setup_ui()
        
        logger.info("Notification Panel initialized")
    
    def _setup_ui(self):
        """Setup UI components."""
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedWidth(350)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setStyleSheet("background: #343a40; color: white;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 8, 10, 8)
        
        title_label = QLabel("Notifications")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Clear all button
        clear_btn = QPushButton("Clear All")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: white;
                border: 1px solid white;
                padding: 3px 10px;
                border-radius: 3px;
                font-size: 9px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
        """)
        clear_btn.clicked.connect(self.clear_all)
        header_layout.addWidget(clear_btn)
        
        main_layout.addWidget(header)
        
        # Scroll area for notifications
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setFrameStyle(QFrame.Shape.NoFrame)
        
        # Container for notification widgets
        self.notifications_container = QWidget()
        self.notifications_layout = QVBoxLayout(self.notifications_container)
        self.notifications_layout.setContentsMargins(5, 5, 5, 5)
        self.notifications_layout.setSpacing(8)
        self.notifications_layout.addStretch()
        
        scroll_area.setWidget(self.notifications_container)
        main_layout.addWidget(scroll_area)
    
    def add_notification(self, notification: Notification):
        """
        Add a notification to the panel.
        
        Args:
            notification: Notification to add
        """
        self.notifications.insert(0, notification)  # Add to top
        
        # Create widget
        widget = NotificationWidget(notification)
        widget.dismissed.connect(self._on_notification_dismissed)
        widget.action_clicked.connect(self._on_action_clicked)
        
        self._notification_widgets[notification.id] = widget
        
        # Add to layout (at top)
        self.notifications_layout.insertWidget(0, widget)
        
        # Animate in
        self._animate_in(widget)
        
        logger.info(f"Notification added: {notification.title}")
    
    def _animate_in(self, widget: QWidget):
        """Animate notification widget appearing."""
        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(300)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        start_pos = widget.pos() + QPoint(-50, 0)
        end_pos = widget.pos()
        
        animation.setStartValue(start_pos)
        animation.setEndValue(end_pos)
        animation.start()
    
    def _on_notification_dismissed(self, notification_id: int):
        """Handle notification dismissal."""
        if notification_id in self._notification_widgets:
            widget = self._notification_widgets[notification_id]
            
            # Animate out
            animation = QPropertyAnimation(widget, b"maximumHeight")
            animation.setDuration(200)
            animation.setStartValue(widget.height())
            animation.setEndValue(0)
            animation.finished.connect(lambda: self._remove_widget(notification_id))
            animation.start()
            
            self.notification_dismissed.emit(notification_id)
    
    def _remove_widget(self, notification_id: int):
        """Remove widget from layout."""
        if notification_id in self._notification_widgets:
            widget = self._notification_widgets[notification_id]
            self.notifications_layout.removeWidget(widget)
            widget.deleteLater()
            del self._notification_widgets[notification_id]
            
            # Remove from notifications list
            self.notifications = [n for n in self.notifications if n.id != notification_id]
    
    def _on_action_clicked(self, notification_id: int, action_label: str):
        """Handle action button click."""
        logger.info(f"Notification action clicked: {action_label}")
    
    def clear_all(self):
        """Clear all notifications."""
        for notification_id in list(self._notification_widgets.keys()):
            self._on_notification_dismissed(notification_id)
        
        logger.info("All notifications cleared")
    
    def get_notification_count(self) -> int:
        """Get current notification count."""
        return len(self.notifications)


# Global notification manager
_notification_panel: Optional[NotificationPanel] = None


def get_notification_panel() -> NotificationPanel:
    """
    Get global notification panel instance.
    
    Returns:
        NotificationPanel instance
    """
    global _notification_panel
    if _notification_panel is None:
        _notification_panel = NotificationPanel()
    return _notification_panel


def notify(
    title: str,
    message: str,
    level: NotificationLevel = NotificationLevel.INFO,
    actions: Optional[List[NotificationAction]] = None,
    auto_dismiss: bool = True,
    dismiss_delay: int = 5000
):
    """
    Show a notification (convenience function).
    
    Args:
        title: Notification title
        message: Notification message
        level: Severity level
        actions: Optional list of actions
        auto_dismiss: Auto-dismiss after delay
        dismiss_delay: Auto-dismiss delay in milliseconds
    """
    notification = Notification(
        title=title,
        message=message,
        level=level,
        actions=actions,
        auto_dismiss=auto_dismiss,
        dismiss_delay=dismiss_delay
    )
    
    panel = get_notification_panel()
    panel.add_notification(notification)
    
    # Show panel if not visible
    if not panel.isVisible():
        panel.show()
        panel.raise_()


def notify_info(title: str, message: str, **kwargs):
    """Show info notification."""
    notify(title, message, NotificationLevel.INFO, **kwargs)


def notify_success(title: str, message: str, **kwargs):
    """Show success notification."""
    notify(title, message, NotificationLevel.SUCCESS, **kwargs)


def notify_warning(title: str, message: str, **kwargs):
    """Show warning notification."""
    notify(title, message, NotificationLevel.WARNING, **kwargs)


def notify_error(title: str, message: str, **kwargs):
    """Show error notification."""
    notify(title, message, NotificationLevel.ERROR, **kwargs)


def notify_critical(title: str, message: str, **kwargs):
    """Show critical notification."""
    notify(title, message, NotificationLevel.CRITICAL, **kwargs)

