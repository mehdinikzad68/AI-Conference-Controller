"""
Theme Manager Module

Detects system theme (light/dark) and applies appropriate theme to application.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QColor
import sys
import logging

logger = logging.getLogger(__name__)

try:
    import winreg
    WINDOWS_REGISTRY_AVAILABLE = True
except ImportError:
    WINDOWS_REGISTRY_AVAILABLE = False


class ThemeManager(QObject):
    """
    Manages application theme based on system settings.
    
    Detects Windows light/dark mode and applies appropriate theme colors.
    """
    
    # Signal emitted when system theme changes
    theme_changed = pyqtSignal(str)  # Emits "light" or "dark"
    
    def __init__(self):
        """Initialize theme manager."""
        super().__init__()
        self._current_theme = self.detect_system_theme()
    
    def detect_system_theme(self) -> str:
        """
        Detect current Windows theme (light or dark).
        
        Returns:
            "light" or "dark"
        """
        if sys.platform != 'win32':
            # Default to dark for non-Windows
            return "dark"
        
        if not WINDOWS_REGISTRY_AVAILABLE:
            logger.warning("Windows registry not available, defaulting to dark theme")
            return "dark"
        
        try:
            # Check Windows 10/11 theme preference
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            )
            
            try:
                # AppsUseLightTheme: 0 = dark, 1 = light
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                winreg.CloseKey(key)
                return "light" if value == 1 else "dark"
            except FileNotFoundError:
                # Key doesn't exist, try alternative method
                winreg.CloseKey(key)
                return self._detect_theme_alternative()
        except Exception as e:
            logger.error(f"Error detecting system theme: {e}")
            return self._detect_theme_alternative()
    
    def _detect_theme_alternative(self) -> str:
        """Alternative theme detection method."""
        # Default to dark if detection fails
        return "dark"
    
    def get_current_theme(self) -> str:
        """Get currently detected theme."""
        return self._current_theme
    
    def refresh_theme(self):
        """Refresh theme detection (call when system theme changes)."""
        new_theme = self.detect_system_theme()
        if new_theme != self._current_theme:
            self._current_theme = new_theme
            self.theme_changed.emit(new_theme)
        return new_theme
    
    def get_color_scheme(self) -> dict:
        """
        Get color scheme for current theme.
        
        Returns:
            Dictionary with color definitions
        """
        if self._current_theme == "light":
            return {
                'background': QColor(255, 255, 255),
                'background_alt': QColor(245, 245, 245),
                'text': QColor(0, 0, 0),
                'text_secondary': QColor(60, 60, 60),
                'border': QColor(200, 200, 200),
                'button': QColor(240, 240, 240),
                'button_hover': QColor(220, 220, 220),
                'button_pressed': QColor(200, 200, 200),
                'accent': QColor(0, 120, 215),
                'accent_hover': QColor(0, 100, 180)
            }
        else:  # dark
            return {
                'background': QColor(30, 30, 30),
                'background_alt': QColor(45, 45, 45),
                'text': QColor(255, 255, 255),
                'text_secondary': QColor(200, 200, 200),
                'border': QColor(60, 60, 60),
                'button': QColor(50, 50, 50),
                'button_hover': QColor(70, 70, 70),
                'button_pressed': QColor(40, 40, 40),
                'accent': QColor(0, 120, 215),
                'accent_hover': QColor(0, 150, 255)
            }
    
    def get_text_color(self) -> str:
        """
        Get text color as CSS color string based on current theme.
        
        Returns:
            CSS color string (#000000 for light, #ffffff for dark)
        """
        if self._current_theme == "light":
            return "#000000"
        else:
            return "#ffffff"
    
    def get_text_color_rgb(self) -> str:
        """
        Get text color as RGB CSS string based on current theme.
        
        Returns:
            CSS RGB color string (rgb(0, 0, 0) for light, rgb(255, 255, 255) for dark)
        """
        if self._current_theme == "light":
            return "rgb(0, 0, 0)"
        else:
            return "rgb(255, 255, 255)"
    
    def get_text_color_qcolor(self) -> QColor:
        """
        Get text color as QColor object based on current theme.
        
        Returns:
            QColor object (black for light, white for dark)
        """
        if self._current_theme == "light":
            return QColor(0, 0, 0)
        else:
            return QColor(255, 255, 255)
    
    def get_stylesheet(self) -> str:
        """
        Get Qt stylesheet for current theme.
        
        Returns:
            CSS-style stylesheet string
        """
        colors = self.get_color_scheme()
        bg = colors['background']
        bg_alt = colors['background_alt']
        text = colors['text']
        text_secondary = colors['text_secondary']
        border = colors['border']
        button = colors['button']
        button_hover = colors['button_hover']
        button_pressed = colors['button_pressed']
        accent = colors['accent']
        accent_hover = colors['accent_hover']
        
        return f"""
            QMainWindow {{
                background-color: rgb({bg.red()}, {bg.green()}, {bg.blue()});
                color: rgb({text.red()}, {text.green()}, {text.blue()});
            }}
            QWidget {{
                background-color: rgb({bg.red()}, {bg.green()}, {bg.blue()});
                color: rgb({text.red()}, {text.green()}, {text.blue()});
                font-size: 11px;
            }}
            QPushButton {{
                background-color: rgb({button.red()}, {button.green()}, {button.blue()});
                border: 2px solid rgb({border.red()}, {border.green()}, {border.blue()});
                border-radius: 5px;
                padding: 6px;
                font-size: 11px;
                font-weight: bold;
                min-height: 28px;
                color: rgb({text.red()}, {text.green()}, {text.blue()});
            }}
            QPushButton:hover {{
                background-color: rgb({button_hover.red()}, {button_hover.green()}, {button_hover.blue()});
                border-color: rgb({accent.red()}, {accent.green()}, {accent.blue()});
            }}
            QPushButton:pressed {{
                background-color: rgb({button_pressed.red()}, {button_pressed.green()}, {button_pressed.blue()});
            }}
            QPushButton:disabled {{
                background-color: rgb({bg_alt.red()}, {bg_alt.green()}, {bg_alt.blue()});
                border-color: rgb({border.red()}, {border.green()}, {border.blue()});
                color: rgb({text_secondary.red()}, {text_secondary.green()}, {text_secondary.blue()});
            }}
            QSlider::groove:horizontal {{
                border: 1px solid rgb({border.red()}, {border.green()}, {border.blue()});
                height: 8px;
                background: rgb({bg_alt.red()}, {bg_alt.green()}, {bg_alt.blue()});
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: rgb({accent.red()}, {accent.green()}, {accent.blue()});
                border: 2px solid rgb({border.red()}, {border.green()}, {border.blue()});
                width: 18px;
                height: 18px;
                border-radius: 9px;
                margin: -5px 0;
            }}
            QSlider::handle:horizontal:hover {{
                background: rgb({accent_hover.red()}, {accent_hover.green()}, {accent_hover.blue()});
            }}
            QSpinBox {{
                background-color: rgb({bg_alt.red()}, {bg_alt.green()}, {bg_alt.blue()});
                border: 2px solid rgb({border.red()}, {border.green()}, {border.blue()});
                border-radius: 4px;
                padding: 4px;
                font-size: 11px;
                color: rgb({text.red()}, {text.green()}, {text.blue()});
            }}
            QGroupBox {{
                border: 2px solid rgb({border.red()}, {border.green()}, {border.blue()});
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
                font-size: 11px;
                font-weight: bold;
                color: rgb({text.red()}, {text.green()}, {text.blue()});
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            QLabel {{
                color: rgb({text.red()}, {text.green()}, {text.blue()});
            }}
            QCheckBox {{
                color: rgb({text.red()}, {text.green()}, {text.blue()});
                spacing: 6px;
                font-size: 11px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid rgb({border.red()}, {border.green()}, {border.blue()});
                border-radius: 3px;
                background-color: rgb({bg_alt.red()}, {bg_alt.green()}, {bg_alt.blue()});
            }}
            QCheckBox::indicator:hover {{
                border-color: rgb({accent.red()}, {accent.green()}, {accent.blue()});
                background-color: rgb({button_hover.red()}, {button_hover.green()}, {button_hover.blue()});
            }}
            QCheckBox::indicator:checked {{
                background-color: rgb({accent.red()}, {accent.green()}, {accent.blue()});
                border-color: rgb({accent.red()}, {accent.green()}, {accent.blue()});
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTMuMzMzMyA0TDYgMTJMMi42NjY2NyA4LjY2NjY3IiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjwvc3ZnPg==);
            }}
            QCheckBox::indicator:checked:hover {{
                background-color: rgb({accent_hover.red()}, {accent_hover.green()}, {accent_hover.blue()});
                border-color: rgb({accent_hover.red()}, {accent_hover.green()}, {accent_hover.blue()});
            }}
            QCheckBox::indicator:indeterminate {{
                background-color: rgb({accent.red()}, {accent.green()}, {accent.blue()});
                border-color: rgb({accent.red()}, {accent.green()}, {accent.blue()});
            }}
            QCheckBox:disabled {{
                color: rgb({text_secondary.red()}, {text_secondary.green()}, {text_secondary.blue()});
            }}
            QCheckBox::indicator:disabled {{
                background-color: rgb({bg_alt.red()}, {bg_alt.green()}, {bg_alt.blue()});
                border-color: rgb({border.red()}, {border.green()}, {border.blue()});
                opacity: 0.5;
            }}
            QTextEdit {{
                color: rgb({text.red()}, {text.green()}, {text.blue()});
            }}
            QTextEdit:focus {{
                color: rgb({text.red()}, {text.green()}, {text.blue()});
            }}
            QTabWidget::pane {{
                border: 1px solid rgb({border.red()}, {border.green()}, {border.blue()});
                background: rgb({bg.red()}, {bg.green()}, {bg.blue()});
            }}
            QTabBar::tab {{
                background: rgb({bg_alt.red()}, {bg_alt.green()}, {bg_alt.blue()});
                color: rgb({text.red()}, {text.green()}, {text.blue()});
                border: 1px solid rgb({border.red()}, {border.green()}, {border.blue()});
                padding: 6px 12px;
                font-size: 11px;
            }}
            QTabBar::tab:selected {{
                background: rgb({bg.red()}, {bg.green()}, {bg.blue()});
                border-bottom: 2px solid rgb({accent.red()}, {accent.green()}, {accent.blue()});
            }}
            QStatusBar {{
                background-color: rgb({bg_alt.red()}, {bg_alt.green()}, {bg_alt.blue()});
                color: rgb({text.red()}, {text.green()}, {text.blue()});
            }}
        """

