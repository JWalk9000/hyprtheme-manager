import os
import yaml
from pathlib import Path

class AppSettings:
    """
    Manages loading, accessing, and saving application settings from a YAML file.
    This class is UI-agnostic.
    """
    def __init__(self, config_file: Path = None):
        self.config_dir = Path.home() / ".config" / "Theme-Manager"
        self.settings_file = config_file or self.config_dir / "config" / "settings.yaml"
        self.settings = self._load_settings()

    def _get_default_settings(self) -> dict:
        """Provides the default structure and values for the application settings."""
        return {
            'ui': {
                'backend': 'gtk',  # 'gtk' or 'qt'
                'window_width': 800,
                'window_height': 600,
                'floating_window': True,
            },
            'wallpaper': {
                'directory': '~/Pictures/Wallpapers',  # Default wallpaper directory
                'live_preview': True,
            },
            'theme': {
                'show_results_dialog': True,
            }
        }

    def _load_settings(self) -> dict:
        """Loads settings from the YAML file, merging with defaults."""
        defaults = self._get_default_settings()
        if not self.settings_file.exists():
            self.settings = defaults
            self.save_settings()
            return defaults

        try:
            with open(self.settings_file, 'r') as f:
                user_settings = yaml.safe_load(f) or {}
            # Deep merge user settings into defaults
            return self._merge_dicts(defaults, user_settings)
        except (yaml.YAMLError, IOError) as e:
            print(f"Warning: Could not load settings from {self.settings_file}. Using defaults. Error: {e}")
            return defaults

    def _merge_dicts(self, base: dict, merge: dict) -> dict:
        """Recursively merges the second dictionary into the first."""
        for key, value in merge.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                base[key] = self._merge_dicts(base[key], value)
            else:
                base[key] = value
        return base

    def save_settings(self):
        """Saves the current settings back to the YAML file."""
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, 'w') as f:
                yaml.safe_dump(self.settings, f, default_flow_style=False, indent=2)
        except IOError as e:
            print(f"Error: Could not save settings to {self.settings_file}. Error: {e}")

    def get(self, key_path: str, default=None):
        """
        Retrieves a setting value using a dot-separated key path.
        Example: get('wallpaper.directory')
        """
        keys = key_path.split('.')
        value = self.settings
        try:
            for key in keys:
                value = value[key]
            
            # Special handling for wallpaper directory - expand tilde
            if key_path == 'wallpaper.directory' and isinstance(value, str):
                return str(Path(value).expanduser())
            
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key_path: str, value):
        """
        Sets a setting value using a dot-separated key path and saves the settings.
        Example: set('ui.backend', 'qt')
        """
        keys = key_path.split('.')
        d = self.settings
        for key in keys[:-1]:
            d = d.setdefault(key, {})
        d[keys[-1]] = value
        self.save_settings()
