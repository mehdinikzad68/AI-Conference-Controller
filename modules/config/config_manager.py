"""
Config Manager Module

Handles application configuration, settings persistence, and asset management.
"""

from PyQt6.QtCore import QObject, QSettings
from pathlib import Path
import json
from .auto_backup import AutoBackupManager


class ConfigManager(QObject):
    """
    Controller for configuration and asset management.
    
    Manages application settings, user preferences, and asset paths.
    """
    
    def __init__(self, config_file: str = "config.json", enable_auto_backup: bool = True):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to the configuration file
            enable_auto_backup: Enable automatic periodic backups (default: True)
        """
        super().__init__()
        self._config_file = Path(config_file)
        self._config_data = {}
        self._assets_path = Path("assets")
        self._settings = QSettings("AI-Symp-Controller", "Settings")
        
        # Initialize auto-backup manager (will be configured after config is loaded)
        self._backup_manager = AutoBackupManager(
            config_file=str(self._config_file),
            backup_dir="assets/backups",
            interval_ms=0,  # Will be set after config load
            max_backups=10
        )
        
    def load_config(self):
        """Load configuration from file."""
        if self._config_file.exists():
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    self._config_data = json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                self._config_data = self._get_default_config()
        else:
            self._config_data = self._get_default_config()
            self.save_config(create_backup=False)  # Don't backup on first creation
        
        # Configure backup interval after config is loaded
        backup_interval = self._get_backup_interval()
        if backup_interval > 0:
            self._backup_manager.set_interval(backup_interval * 1000)
    
    def save_config(self, create_backup: bool = True):
        """
        Save configuration to file.
        
        Args:
            create_backup: Create a backup before saving (default: True)
        """
        try:
            # Create backup before saving if requested
            if create_backup:
                self._backup_manager.create_backup()
            
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config_data, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key: str, default=None):
        """
        Get a configuration value.
        
        Args:
            key: Configuration key (supports dot notation, e.g., "display.mode")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._config_data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value if value is not None else default
    
    def set(self, key: str, value):
        """
        Set a configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self._config_data
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
    
    def get_asset_path(self, asset_name: str) -> Path:
        """
        Get the full path to an asset file.
        
        Args:
            asset_name: Name of the asset file
            
        Returns:
            Path object to the asset
        """
        return self._assets_path / asset_name
    
    def set_assets_path(self, path: str):
        """
        Set the assets directory path.
        
        Args:
            path: Path to the assets directory
        """
        self._assets_path = Path(path)
    
    def get_all_config(self) -> dict:
        """
        Get complete configuration dictionary.
        
        Returns:
            Complete configuration dictionary
        """
        return self._config_data.copy()
    
    def set_all_config(self, config_data: dict):
        """
        Set complete configuration dictionary.
        
        Args:
            config_data: Complete configuration dictionary
        """
        self._config_data = config_data.copy()
    
    def _get_default_config(self) -> dict:
        """
        Get default configuration dictionary.
        
        Returns:
            Dictionary with default configuration values
        """
        return {
            "display": {
                "mode": "extended",
                "primary_screen": 0,
                "fullscreen": False,
                "auto_detect": True,
                "target_resolution": {
                    "width": 1920,
                    "height": 1080
                }
            },
            "timer": {
                "default_duration": 300,  # 5 minutes
                "mode": "countdown",
                "show_warning": True,
                "warning_threshold": 120,  # 2 minutes
                "color_scheme": "gradient",  # gradient, solid, custom
                "font_size": 72,
                "show_seconds": True
            },
            "media": {
                "auto_play": False,
                "auto_advance": False,
                "supported_formats": [".pdf", ".jpg", ".jpeg", ".png", ".mp4", ".avi", ".mov"],
                "default_transition": "fade",
                "maintain_aspect_ratio": True,
                "fullscreen_on_play": False
            },
            "face_ai": {
                "enabled": False,
                "camera_index": 0,
                "attention_threshold": 0.5,
                "sampling_frequency": 2,  # seconds between captures
                "enable_emotion_detection": True,
                "enable_gaze_tracking": False,
                "chart_type": "bar"  # bar, pie, line
            },
            "sound": {
                "warning_enabled": True,
                "warning_volume": 80,
                "finished_enabled": True,
                "finished_volume": 80,
                "custom_warning_sound": "",
                "custom_finished_sound": ""
            },
            "general": {
                "language": "en",
                "theme": "dark",
                "font_size": 12,
                "high_contrast": False,
                "optimize_for_projector": True,
                "auto_save": True,
                "backup_interval": 300  # seconds
            },
            "assets": {
                "logo_path": "",
                "branding_enabled": False,
                "custom_colors": {
                    "primary": "#ffffff",
                    "secondary": "#000000"
                }
            }
        }
    
    def _get_backup_interval(self) -> int:
        """
        Get backup interval from config or return default.
        
        Returns:
            Backup interval in seconds (default: 300 = 5 minutes)
        """
        return self._config_data.get('general', {}).get('backup_interval', 300)
    
    def get_backup_manager(self) -> AutoBackupManager:
        """Get the auto-backup manager instance."""
        return self._backup_manager

