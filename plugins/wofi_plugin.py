"""
Wofi Theme Plugin
Handles theming for Wofi application launcher
"""

import os
import shutil
import subprocess
from typing import Dict, Any, List
from plugin_manager import ThemePlugin

class WofiPlugin(ThemePlugin):
    
    @property
    def name(self) -> str:
        return "wofi"
    
    @property
    def display_name(self) -> str:
        return "Wofi"
    
    @property
    def description(self) -> str:
        return "Wayland application launcher and dmenu replacement"
    
    @property
    def config_path(self) -> str:
        return os.path.expanduser("~/.config/wofi/style.css")
    
    @property
    def template_name(self) -> str:
        return "wofi"
    
    @property
    def dependencies(self) -> List[str]:
        return ["wofi"]
    
    @property
    def optional_dependencies(self) -> List[str]:
        return ["wofi-wal"]
    
    def is_available(self) -> bool:
        """Check if Wofi is installed"""
        return shutil.which("wofi") is not None
    
    def apply_theme(self, colors: Dict[str, Any]) -> bool:
        """Apply theme to Wofi"""
        try:
            from template_manager import read_template, render_template, write_config
            
            template_dir = os.path.join(os.path.dirname(__file__), '..', 'config', 'templates')
            
            template = read_template(self.template_name, template_dir)
            if not template:
                print(f"No template found for {self.display_name}")
                return False
            
            rendered = render_template(template, colors)
            write_config(self.config_path, rendered)
            
            # Try to use wofi-wal if available
            self._apply_wofi_wal()
            
            return True
            
        except Exception as e:
            print(f"Failed to apply Wofi theme: {e}")
            return False
    
    def backup_config(self, backup_dir: str) -> bool:
        """Backup current Wofi config"""
        try:
            if os.path.exists(self.config_path):
                backup_path = os.path.join(backup_dir, f"wofi-style.css.backup")
                os.makedirs(backup_dir, exist_ok=True)
                shutil.copy2(self.config_path, backup_path)
                return True
            return False
        except Exception as e:
            print(f"Failed to backup Wofi config: {e}")
            return False
    
    def restore_config(self, backup_dir: str) -> bool:
        """Restore Wofi config from backup"""
        try:
            backup_path = os.path.join(backup_dir, f"wofi-style.css.backup")
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, self.config_path)
                return True
            return False
        except Exception as e:
            print(f"Failed to restore Wofi config: {e}")
            return False
    
    def _apply_wofi_wal(self):
        """Apply wofi-wal if available"""
        try:
            if shutil.which("wofi-wal"):
                subprocess.run(["wofi-wal"], capture_output=True, check=False)
        except Exception:
            pass
