"""
Auto-Backup Module

Handles automatic periodic backup of configuration files and profiles with rolling backup management.
"""

from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from pathlib import Path
import shutil
import json
from datetime import datetime
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AutoBackupManager(QObject):
    """
    Manages automatic periodic backups of configuration and profiles.
    
    Features:
    - Scheduled backups using QTimer
    - Rolling backup system (keeps N backups, deletes oldest)
    - Timestamped backup files
    - Automatic backup on config save
    """
    
    # Signal emitted when backup is created
    backup_created = pyqtSignal(str)  # Emits backup file path
    
    def __init__(
        self,
        config_file: str = "config.json",
        backup_dir: str = "assets/backups",
        interval_ms: int = 3600000,  # 1 hour default
        max_backups: int = 10
    ):
        """
        Initialize auto-backup manager.
        
        Args:
            config_file: Path to configuration file to backup
            backup_dir: Directory to store backups
            interval_ms: Backup interval in milliseconds (default: 3600000 = 1 hour)
            max_backups: Maximum number of backups to keep (default: 10)
        """
        super().__init__()
        self._config_file = Path(config_file)
        self._backup_dir = Path(backup_dir)
        self._interval_ms = interval_ms
        self._max_backups = max_backups
        
        # Create backup directory if it doesn't exist
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup timer for periodic backups
        self._backup_timer = QTimer()
        self._backup_timer.timeout.connect(self.create_backup)
        self._backup_timer.setSingleShot(False)
        
        # Start timer if interval > 0
        if interval_ms > 0:
            self._backup_timer.start(interval_ms)
            logger.info(f"Auto-backup started: interval={interval_ms}ms, max_backups={max_backups}")
    
    def create_backup(self) -> Optional[str]:
        """
        Create a backup of the current configuration file.
        
        Returns:
            Path to created backup file, or None on error
        """
        if not self._config_file.exists():
            logger.warning(f"Config file not found: {self._config_file}")
            return None
        
        try:
            # Generate timestamped backup filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"config_backup_{timestamp}.json"
            backup_path = self._backup_dir / backup_filename
            
            # Copy config file to backup location
            shutil.copy2(self._config_file, backup_path)
            
            logger.info(f"Backup created: {backup_path}")
            self.backup_created.emit(str(backup_path))
            
            # Clean up old backups
            self._cleanup_old_backups()
            
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None
    
    def _cleanup_old_backups(self):
        """Remove oldest backups if exceeding max_backups limit."""
        try:
            # Get all backup files sorted by modification time
            backup_files = sorted(
                self._backup_dir.glob("config_backup_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True  # Newest first
            )
            
            # Remove oldest backups if exceeding limit
            if len(backup_files) > self._max_backups:
                files_to_delete = backup_files[self._max_backups:]
                for backup_file in files_to_delete:
                    try:
                        backup_file.unlink()
                        logger.info(f"Deleted old backup: {backup_file}")
                    except Exception as e:
                        logger.error(f"Error deleting backup {backup_file}: {e}")
        
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
    
    def backup_profile(self, profile_name: str, profile_data: dict) -> Optional[str]:
        """
        Create a backup of a specific profile.
        
        Args:
            profile_name: Name of the profile
            profile_data: Profile data dictionary
            
        Returns:
            Path to created backup file, or None on error
        """
        try:
            # Generate timestamped backup filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_name = profile_name.replace(' ', '_').replace('/', '_')
            backup_filename = f"profile_{safe_name}_{timestamp}.json"
            backup_path = self._backup_dir / backup_filename
            
            # Save profile data to backup file
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=4)
            
            logger.info(f"Profile backup created: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Error creating profile backup: {e}")
            return None
    
    def set_interval(self, interval_ms: int):
        """
        Set backup interval.
        
        Args:
            interval_ms: New interval in milliseconds (0 to disable)
        """
        self._interval_ms = interval_ms
        self._backup_timer.stop()
        
        if interval_ms > 0:
            self._backup_timer.start(interval_ms)
            logger.info(f"Backup interval changed to {interval_ms}ms")
        else:
            logger.info("Auto-backup disabled")
    
    def set_max_backups(self, max_backups: int):
        """
        Set maximum number of backups to keep.
        
        Args:
            max_backups: Maximum number of backups (minimum 1)
        """
        self._max_backups = max(1, max_backups)
        self._cleanup_old_backups()
        logger.info(f"Maximum backups set to {self._max_backups}")
    
    def get_backup_list(self) -> list:
        """
        Get list of available backup files.
        
        Returns:
            List of backup file paths, sorted by date (newest first)
        """
        try:
            backup_files = sorted(
                self._backup_dir.glob("config_backup_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            return [str(f) for f in backup_files]
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return []
    
    def restore_backup(self, backup_path: str) -> bool:
        """
        Restore configuration from a backup file.
        
        Args:
            backup_path: Path to backup file to restore
            
        Returns:
            True if successful, False otherwise
        """
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Create a backup of current config before restoring
            current_backup = self.create_backup()
            if current_backup:
                logger.info(f"Created safety backup before restore: {current_backup}")
            
            # Restore from backup
            shutil.copy2(backup_file, self._config_file)
            logger.info(f"Configuration restored from: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False
    
    def stop(self):
        """Stop automatic backups."""
        self._backup_timer.stop()
        logger.info("Auto-backup stopped")
    
    def start(self, interval_ms: Optional[int] = None):
        """
        Start automatic backups.
        
        Args:
            interval_ms: Optional interval override (uses current interval if None)
        """
        if interval_ms is not None:
            self._interval_ms = interval_ms
        
        if self._interval_ms > 0:
            self._backup_timer.start(self._interval_ms)
            logger.info(f"Auto-backup started with interval {self._interval_ms}ms")

