"""
Mako Notification Theme Plugin
Handles theming for Mako notification daemon
"""

import os
import shutil
import subprocess
from typing import Dict, Any, List
from plugin_manager import ThemePlugin

class MakoPlugin(ThemePlugin):
    
    @property
    def name(self) -> str:
        return "mako"
    
    @property
    def display_name(self) -> str:
        return "Mako"
    
    @property
    def description(self) -> str:
        return "Lightweight Wayland notification daemon"
    
    @property
    def config_path(self) -> str:
        return os.path.expanduser("~/.config/mako/config")
    
    @property
    def template_name(self) -> str:
        return "mako"
    
    @property
    def dependencies(self) -> List[str]:
        return ["mako"]
    
    def is_available(self) -> bool:
        """Check if Mako is installed"""
        return shutil.which("mako") is not None
    
    def apply_theme(self, colors: Dict[str, Any]) -> bool:
        """Apply theme to Mako"""
        try:
            from template_manager import read_template, render_template, write_config
            
            template_dir = os.path.join(os.path.dirname(__file__), '..', 'config', 'templates')
            
            template = read_template(self.template_name, template_dir)
            if not template:
                print(f"No template found for {self.display_name}")
                return False
            
            rendered = render_template(template, colors)
            write_config(self.config_path, rendered)
            
            # Reload Mako
            self._reload_mako()
            
            return True
            
        except Exception as e:
            print(f"Failed to apply Mako theme: {e}")
            return False
    
    def backup_config(self, backup_dir: str) -> bool:
        """Backup current Mako config"""
        try:
            if os.path.exists(self.config_path):
                backup_path = os.path.join(backup_dir, f"mako-config.backup")
                os.makedirs(backup_dir, exist_ok=True)
                shutil.copy2(self.config_path, backup_path)
                return True
            return False
        except Exception as e:
            print(f"Failed to backup Mako config: {e}")
            return False
    
    def restore_config(self, backup_dir: str) -> bool:
        """Restore Mako config from backup"""
        try:
            backup_path = os.path.join(backup_dir, f"mako-config.backup")
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, self.config_path)
                self._reload_mako()
                return True
            return False
        except Exception as e:
            print(f"Failed to restore Mako config: {e}")
            return False
    
    def _reload_mako(self):
        """Reload Mako configuration"""
        try:
            subprocess.run(["makoctl", "reload"], capture_output=True, check=False)
        except Exception:
            pass
