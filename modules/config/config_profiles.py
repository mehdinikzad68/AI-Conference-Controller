"""
Configuration Profiles Module

Manages multiple configuration profiles for different event types.
"""

from pathlib import Path
import json
from typing import Dict, List, Optional
from datetime import datetime


class ConfigProfile:
    """Represents a single configuration profile."""
    
    def __init__(self, name: str, config_data: dict, description: str = ""):
        """
        Initialize configuration profile.
        
        Args:
            name: Profile name
            config_data: Configuration data dictionary
            description: Optional description of the profile
        """
        self.name = name
        self.config_data = config_data
        self.description = description
        self.created = datetime.now().isoformat()
        self.modified = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        """Convert profile to dictionary."""
        return {
            'name': self.name,
            'description': self.description,
            'created': self.created,
            'modified': self.modified,
            'config': self.config_data
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ConfigProfile':
        """Create profile from dictionary."""
        profile = cls(
            data['name'],
            data['config'],
            data.get('description', '')
        )
        profile.created = data.get('created', profile.created)
        profile.modified = data.get('modified', profile.modified)
        return profile


class ProfileManager:
    """Manages configuration profiles."""
    
    def __init__(self, profiles_dir: Path = None):
        """
        Initialize profile manager.
        
        Args:
            profiles_dir: Directory to store profiles (default: profiles/ in project root)
        """
        if profiles_dir is None:
            profiles_dir = Path(__file__).parent.parent.parent / "profiles"
        self._profiles_dir = Path(profiles_dir)
        self._profiles_dir.mkdir(exist_ok=True)
        
    def list_profiles(self) -> List[str]:
        """
        List all available profile names.
        
        Returns:
            List of profile names
        """
        profiles = []
        for file in self._profiles_dir.glob("*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    profiles.append(data.get('name', file.stem))
            except Exception:
                continue
        return sorted(profiles)
    
    def load_profile(self, profile_name: str) -> Optional[ConfigProfile]:
        """
        Load a configuration profile.
        
        Args:
            profile_name: Name of the profile to load
            
        Returns:
            ConfigProfile object or None if not found
        """
        profile_file = self._profiles_dir / f"{profile_name}.json"
        if not profile_file.exists():
            return None
        
        try:
            with open(profile_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return ConfigProfile.from_dict(data)
        except Exception as e:
            print(f"Error loading profile {profile_name}: {e}")
            return None
    
    def save_profile(self, profile: ConfigProfile) -> bool:
        """
        Save a configuration profile.
        
        Args:
            profile: ConfigProfile object to save
            
        Returns:
            True if successful, False otherwise
        """
        profile.modified = datetime.now().isoformat()
        profile_file = self._profiles_dir / f"{profile.name}.json"
        
        try:
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile.to_dict(), f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving profile {profile.name}: {e}")
            return False
    
    def delete_profile(self, profile_name: str) -> bool:
        """
        Delete a configuration profile.
        
        Args:
            profile_name: Name of the profile to delete
            
        Returns:
            True if successful, False otherwise
        """
        profile_file = self._profiles_dir / f"{profile_name}.json"
        if profile_file.exists():
            try:
                profile_file.unlink()
                return True
            except Exception as e:
                print(f"Error deleting profile {profile_name}: {e}")
                return False
        return False
    
    def export_profile(self, profile_name: str, export_path: Path) -> bool:
        """
        Export a profile to a file.
        
        Args:
            profile_name: Name of the profile to export
            export_path: Path to export file
            
        Returns:
            True if successful, False otherwise
        """
        profile = self.load_profile(profile_name)
        if not profile:
            return False
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(profile.to_dict(), f, indent=4)
            return True
        except Exception as e:
            print(f"Error exporting profile {profile_name}: {e}")
            return False
    
    def import_profile(self, import_path: Path) -> bool:
        """
        Import a profile from a file.
        
        Args:
            import_path: Path to import file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                profile = ConfigProfile.from_dict(data)
                return self.save_profile(profile)
        except Exception as e:
            print(f"Error importing profile: {e}")
            return False

