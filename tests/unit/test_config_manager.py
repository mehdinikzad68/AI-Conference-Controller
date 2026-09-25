"""
Unit Tests for Configuration Manager

Tests configuration loading, saving, and management.
"""

import pytest
import json
from pathlib import Path
from modules.config.config_manager import ConfigManager


class TestConfigManager:
    """Test suite for ConfigManager."""
    
    @pytest.fixture
    def config_manager(self, tmp_path):
        """Create a config manager with temporary file."""
        config_file = tmp_path / "test_config.json"
        return ConfigManager(str(config_file), enable_auto_backup=False)
    
    def test_initialization(self, config_manager):
        """Test config manager initializes correctly."""
        assert config_manager is not None
        assert config_manager._config_data is not None
    
    def test_default_config(self, config_manager):
        """Test default configuration is created."""
        config = config_manager.get_all_config()
        assert "timer" in config
        assert "media" in config
        assert "face_ai" in config
        assert "display" in config
    
    def test_set_and_get_simple_value(self, config_manager):
        """Test setting and getting simple values."""
        config_manager.set("test_key", "test_value")
        assert config_manager.get("test_key") == "test_value"
    
    def test_set_and_get_nested_value(self, config_manager):
        """Test setting and getting nested values."""
        config_manager.set("timer.custom_duration", 600)
        assert config_manager.get("timer.custom_duration") == 600
    
    def test_get_with_default(self, config_manager):
        """Test getting with default value."""
        value = config_manager.get("nonexistent.key", default="default_value")
        assert value == "default_value"
    
    def test_get_nested_with_default(self, config_manager):
        """Test getting nested value with default."""
        value = config_manager.get("timer.nonexistent", default=999)
        assert value == 999
    
    def test_save_and_load_config(self, tmp_path):
        """Test saving and loading configuration."""
        config_file = tmp_path / "save_test.json"
        manager1 = ConfigManager(str(config_file), enable_auto_backup=False)
        manager1.set("test_key", "test_value")
        manager1.save_config(create_backup=False)
        
        # Load in new manager
        manager2 = ConfigManager(str(config_file), enable_auto_backup=False)
        manager2.load_config()
        assert manager2.get("test_key") == "test_value"
    
    def test_load_corrupted_config(self, tmp_path):
        """Test loading corrupted config falls back to default."""
        config_file = tmp_path / "corrupted.json"
        with open(config_file, 'w') as f:
            f.write("{ invalid json }")
        
        manager = ConfigManager(str(config_file), enable_auto_backup=False)
        manager.load_config()
        
        # Should have default config
        config = manager.get_all_config()
        assert "timer" in config
    
    def test_asset_path(self, config_manager):
        """Test asset path resolution."""
        path = config_manager.get_asset_path("logo.png")
        assert "logo.png" in str(path)
    
    def test_set_assets_path(self, config_manager):
        """Test setting custom assets path."""
        config_manager.set_assets_path("custom/assets")
        path = config_manager.get_asset_path("test.txt")
        assert "custom/assets" in str(path)
    
    def test_get_all_config(self, config_manager):
        """Test getting complete configuration."""
        config = config_manager.get_all_config()
        assert isinstance(config, dict)
        assert len(config) > 0
    
    def test_set_all_config(self, config_manager):
        """Test setting complete configuration."""
        new_config = {
            "custom_section": {
                "custom_key": "custom_value"
            }
        }
        config_manager.set_all_config(new_config)
        config = config_manager.get_all_config()
        assert "custom_section" in config
        assert config["custom_section"]["custom_key"] == "custom_value"
    
    def test_nested_config_creation(self, config_manager):
        """Test creating nested config paths."""
        config_manager.set("level1.level2.level3.key", "deep_value")
        assert config_manager.get("level1.level2.level3.key") == "deep_value"
    
    def test_backup_interval(self, config_manager):
        """Test getting backup interval."""
        interval = config_manager._get_backup_interval()
        assert isinstance(interval, int)
        assert interval >= 0
    
    def test_config_persistence(self, tmp_path):
        """Test config persists across saves and loads."""
        config_file = tmp_path / "persist_test.json"
        
        # Create and save
        manager1 = ConfigManager(str(config_file), enable_auto_backup=False)
        manager1.set("timer.default_duration", 999)
        manager1.set("media.auto_play", True)
        manager1.save_config(create_backup=False)
        
        # Load and verify
        manager2 = ConfigManager(str(config_file), enable_auto_backup=False)
        manager2.load_config()
        assert manager2.get("timer.default_duration") == 999
        assert manager2.get("media.auto_play") is True
    
    def test_default_values(self, config_manager):
        """Test default configuration values."""
        assert config_manager.get("timer.default_duration") == 300
        assert config_manager.get("timer.mode") == "countdown"
        assert config_manager.get("media.auto_play") is False
        assert config_manager.get("face_ai.enabled") is False

