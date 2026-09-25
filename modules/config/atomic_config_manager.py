"""
Atomic Configuration Manager

Provides atomic file operations for configuration management to prevent:
- Race conditions during concurrent writes
- Partial writes due to crashes
- Configuration corruption
- Data loss

Features:
- Atomic writes using temporary files
- File locking for concurrent access
- Automatic rollback on failure
- Backup integration
- Conflict detection

Author: AI-Symp-Controller Team
Date: November 2025
Version: 1.0
"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional, Any, Callable
import logging
import hashlib

try:
    import filelock
    FILELOCK_AVAILABLE = True
except ImportError:
    FILELOCK_AVAILABLE = False
    logging.warning("filelock not available - install with: pip install filelock")

from modules.config.auto_backup import AutoBackupManager

logger = logging.getLogger(__name__)


class AtomicConfigManager:
    """
    Thread-safe and process-safe configuration manager with atomic operations.
    
    Uses:
    - Atomic writes (write to temp, then rename)
    - File locking (prevents concurrent modifications)
    - Version tracking (detects conflicts)
    - Automatic backups
    """
    
    def __init__(
        self,
        config_file: str = "config.json",
        lock_timeout: float = 10.0,
        enable_backups: bool = True
    ):
        """
        Initialize atomic config manager.
        
        Args:
            config_file: Path to configuration file
            lock_timeout: Timeout for acquiring file lock (seconds)
            enable_backups: Enable automatic backups
        """
        self._config_file = Path(config_file)
        self._lock_timeout = lock_timeout
        self._config_data: dict = {}
        
        # Lock file
        self._lock_file = Path(str(self._config_file) + ".lock")
        self._lock = None
        
        if FILELOCK_AVAILABLE:
            self._lock = filelock.FileLock(str(self._lock_file), timeout=lock_timeout)
        
        # Version tracking for conflict detection
        self._config_version = 0
        self._last_modified_time = None
        self._last_file_hash = None
        
        # Backup manager
        self._backup_manager = None
        if enable_backups:
            backup_dir = self._config_file.parent / "backups"
            self._backup_manager = AutoBackupManager(backup_dir)
        
        # Load initial config
        self.load_config()
    
    def load_config(self) -> bool:
        """
        Load configuration from file (thread-safe).
        
        Returns:
            True if loaded successfully
        """
        if not self._config_file.exists():
            logger.info(f"Config file {self._config_file} does not exist, using defaults")
            self._config_data = self._get_default_config()
            return True
        
        try:
            # Acquire lock for reading
            if self._lock:
                with self._lock:
                    return self._load_config_internal()
            else:
                return self._load_config_internal()
                
        except filelock.Timeout:
            logger.error(f"Timeout waiting for lock on {self._config_file}")
            return False
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return False
    
    def _load_config_internal(self) -> bool:
        """Internal config loading (without locking)."""
        try:
            with open(self._config_file, 'r', encoding='utf-8') as f:
                self._config_data = json.load(f)
            
            # Track version and modification time
            self._last_modified_time = self._config_file.stat().st_mtime
            self._config_version = self._config_data.get('__version__', 0)
            
            # Calculate file hash
            self._last_file_hash = self._calculate_file_hash()
            
            logger.info(f"Loaded config version {self._config_version}")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            # Try to restore from backup
            if self._backup_manager:
                logger.info("Attempting to restore from backup...")
                if self._restore_from_backup():
                    return self._load_config_internal()
            return False
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return False
    
    def save_config(
        self,
        create_backup: bool = True,
        validate_callback: Optional[Callable[[dict], bool]] = None
    ) -> bool:
        """
        Save configuration atomically with conflict detection.
        
        Args:
            create_backup: Create backup before saving
            validate_callback: Optional callback to validate config before save
        
        Returns:
            True if saved successfully
        """
        try:
            # Acquire lock for writing
            if self._lock:
                with self._lock:
                    return self._save_config_internal(create_backup, validate_callback)
            else:
                return self._save_config_internal(create_backup, validate_callback)
                
        except filelock.Timeout:
            logger.error(f"Timeout waiting for lock on {self._config_file}")
            self._show_lock_error()
            return False
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def _save_config_internal(
        self,
        create_backup: bool,
        validate_callback: Optional[Callable[[dict], bool]]
    ) -> bool:
        """Internal config saving with atomic write."""
        try:
            # Check for conflicts
            if self._detect_conflict():
                logger.warning("Config file was modified by another process")
                if not self._resolve_conflict():
                    return False
            
            # Create backup
            if create_backup and self._backup_manager:
                backup_path = self._backup_manager.create_backup()
                if backup_path:
                    logger.info(f"Created backup: {backup_path}")
            
            # Increment version
            self._config_version += 1
            self._config_data['__version__'] = self._config_version
            self._config_data['__last_modified__'] = time.time()
            
            # Validate if callback provided
            if validate_callback and not validate_callback(self._config_data):
                logger.error("Config validation failed")
                return False
            
            # Atomic write
            success = self._atomic_write(self._config_data)
            
            if success:
                # Update tracking
                self._last_modified_time = self._config_file.stat().st_mtime
                self._last_file_hash = self._calculate_file_hash()
                logger.info(f"Saved config version {self._config_version}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error in _save_config_internal: {e}")
            # Try to restore from backup
            if self._backup_manager:
                logger.info("Attempting to restore from backup after save failure...")
                self._restore_from_backup()
            return False
    
    def _atomic_write(self, data: dict) -> bool:
        """
        Write data atomically using temp file + rename.
        
        This prevents partial writes and corruption.
        
        Args:
            data: Data to write
        
        Returns:
            True if successful
        """
        temp_fd = None
        temp_path = None
        
        try:
            # Create temporary file in same directory (for atomic rename)
            temp_fd, temp_path = tempfile.mkstemp(
                dir=self._config_file.parent,
                prefix='.tmp_config_',
                suffix='.json',
                text=True
            )
            
            # Write to temp file
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())  # Ensure written to disk
            
            temp_fd = None  # Closed by fdopen context manager
            
            # Atomic rename (replaces old file)
            # On Windows, need to remove target first
            if sys.platform == 'win32' and self._config_file.exists():
                # Backup current file temporarily
                backup_temp = self._config_file.with_suffix('.bak.tmp')
                self._config_file.rename(backup_temp)
                try:
                    Path(temp_path).rename(self._config_file)
                    # Remove backup
                    backup_temp.unlink()
                except Exception:
                    # Restore backup on failure
                    if backup_temp.exists():
                        backup_temp.rename(self._config_file)
                    raise
            else:
                # Unix: atomic rename
                Path(temp_path).rename(self._config_file)
            
            # Set permissions (Unix-like systems)
            if sys.platform != 'win32':
                os.chmod(self._config_file, 0o600)  # Read/write for owner only
            
            logger.debug(f"Atomic write successful: {self._config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Atomic write failed: {e}")
            
            # Cleanup temp file
            if temp_fd is not None:
                try:
                    os.close(temp_fd)
                except:
                    pass
            
            if temp_path and Path(temp_path).exists():
                try:
                    Path(temp_path).unlink()
                except:
                    pass
            
            return False
    
    def _detect_conflict(self) -> bool:
        """
        Detect if config was modified by another process.
        
        Returns:
            True if conflict detected
        """
        if not self._config_file.exists():
            return False
        
        try:
            # Check modification time
            current_mtime = self._config_file.stat().st_mtime
            if self._last_modified_time and current_mtime > self._last_modified_time:
                logger.warning(f"Config file modified: mtime changed from {self._last_modified_time} to {current_mtime}")
                return True
            
            # Check file hash
            current_hash = self._calculate_file_hash()
            if self._last_file_hash and current_hash != self._last_file_hash:
                logger.warning(f"Config file modified: hash changed")
                return True
            
        except Exception as e:
            logger.error(f"Error detecting conflict: {e}")
        
        return False
    
    def _resolve_conflict(self) -> bool:
        """
        Resolve configuration conflict with user.
        
        Returns:
            True if resolved (user chose to overwrite), False to cancel
        """
        # In a GUI app, show dialog to user
        # For now, log warning and allow overwrite
        logger.warning("Config conflict detected - allowing overwrite (TODO: add user dialog)")
        
        # Reload current file
        self._load_config_internal()
        
        # In production, should show dialog:
        # - Show diff between versions
        # - Ask user: Overwrite / Reload / Cancel
        
        return True  # Allow overwrite for now
    
    def _calculate_file_hash(self) -> Optional[str]:
        """Calculate SHA256 hash of config file."""
        if not self._config_file.exists():
            return None
        
        try:
            with open(self._config_file, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"Error calculating file hash: {e}")
            return None
    
    def _restore_from_backup(self) -> bool:
        """Restore config from most recent backup."""
        if not self._backup_manager:
            return False
        
        try:
            backups = self._backup_manager.list_backups()
            if not backups:
                logger.error("No backups available")
                return False
            
            # Get most recent backup
            latest_backup = backups[0]
            logger.info(f"Restoring from backup: {latest_backup}")
            
            # Copy backup to config file
            import shutil
            backup_path = self._backup_manager._backup_dir / latest_backup
            shutil.copy2(backup_path, self._config_file)
            
            logger.info("Successfully restored from backup")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring from backup: {e}")
            return False
    
    def _show_lock_error(self):
        """Show error message about file lock (GUI implementation)."""
        error_msg = (
            "⚠️ Configuration file is locked by another process.\n\n"
            "Another instance of the application may be using it.\n\n"
            "Please close other instances or wait for the lock to be released."
        )
        logger.error(error_msg)
        
        # In GUI app, show QMessageBox
        # For now, just log
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config_data.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value (not saved until save_config called)."""
        self._config_data[key] = value
    
    def get_all(self) -> dict:
        """Get all configuration data."""
        return self._config_data.copy()
    
    def _get_default_config(self) -> dict:
        """Get default configuration."""
        return {
            '__version__': 0,
            '__last_modified__': time.time(),
            # Default settings
            'timer': {
                'default_duration': 1800,
                'warning_threshold': 120
            },
            'display': {
                'fullscreen': False,
                'screen_index': 0
            },
            'face_ai': {
                'enabled': True,
                'process_every_n_frames': 3
            }
        }
    
    def validate_config(self) -> bool:
        """
        Validate current configuration.
        
        Returns:
            True if valid
        """
        try:
            # Check required keys
            required_keys = ['__version__']
            for key in required_keys:
                if key not in self._config_data:
                    logger.error(f"Missing required key: {key}")
                    return False
            
            # Validate version is integer
            if not isinstance(self._config_data['__version__'], int):
                logger.error("Invalid version type")
                return False
            
            # Add more validation as needed
            
            return True
            
        except Exception as e:
            logger.error(f"Config validation error: {e}")
            return False


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    print("=== Atomic Config Manager Test ===\n")
    
    # Create manager
    config = AtomicConfigManager("test_config.json")
    
    # Set some values
    config.set('timer.default_duration', 3600)
    config.set('user_name', 'Test User')
    
    # Save atomically
    print("Saving config...")
    success = config.save_config()
    print(f"Save result: {success}\n")
    
    # Load again
    print("Loading config...")
    config2 = AtomicConfigManager("test_config.json")
    print(f"Loaded duration: {config2.get('timer.default_duration')}")
    print(f"Loaded user: {config2.get('user_name')}")
    
    # Test conflict detection
    print("\n=== Testing Conflict Detection ===")
    config3 = AtomicConfigManager("test_config.json")
    config3.set('test_key', 'value1')
    
    # Simulate external modification
    time.sleep(0.1)
    config4 = AtomicConfigManager("test_config.json")
    config4.set('test_key', 'value2')
    config4.save_config()
    
    # Try to save original - should detect conflict
    print("Attempting save with conflict...")
    config3.save_config()

