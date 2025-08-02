"""
Waybar Theme Plugin
Handles theming for Waybar status bar
"""

import os
import shutil
import subprocess
from typing import Dict, Any, List
from plugin_manager import ThemePlugin

class WaybarPlugin(ThemePlugin):
    
    @property
    def name(self) -> str:
        return "waybar"
    
    @property
    def display_name(self) -> str:
        return "Waybar"
    
    @property
    def description(self) -> str:
        return "Wayland status bar with workspace and system info"
    
    @property
    def config_path(self) -> str:
        return os.path.expanduser("~/.config/waybar/style.css")
    
    @property
    def template_name(self) -> str:
        return "waybar"
    
    @property
    def dependencies(self) -> List[str]:
        return ["waybar"]
    
    def is_available(self) -> bool:
        """Check if Waybar is installed"""
        return shutil.which("waybar") is not None
    
    def apply_theme(self, colors: Dict[str, Any]) -> bool:
        """Apply theme to Waybar by processing template and reloading"""
        try:
            # Import here to avoid circular imports
            from template_manager import read_template, render_template, write_config
            
            # Get template directory
            template_dir = os.path.join(os.path.dirname(__file__), 'config', 'templates')
            
            # Read and process template
            template = read_template(self.template_name, template_dir)
            if not template:
                print(f"No template found for {self.display_name}")
                return False
            
            # Render template with colors
            rendered = render_template(template, colors)
            
            # Write to config file
            write_config(self.config_path, rendered)
            
            # Reload Waybar
            self._reload_waybar()
            
            return True
            
        except Exception as e:
            print(f"Failed to apply Waybar theme: {e}")
            return False
    
    def backup_config(self, backup_dir: str) -> bool:
        """Backup current Waybar config"""
        try:
            if os.path.exists(self.config_path):
                backup_path = os.path.join(backup_dir, f"waybar-style.css.backup")
                os.makedirs(backup_dir, exist_ok=True)
                shutil.copy2(self.config_path, backup_path)
                return True
            return False
        except Exception as e:
            print(f"Failed to backup Waybar config: {e}")
            return False
    
    def restore_config(self, backup_dir: str) -> bool:
        """Restore Waybar config from backup"""
        try:
            backup_path = os.path.join(backup_dir, f"waybar-style.css.backup")
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, self.config_path)
                self._reload_waybar()
                return True
            return False
        except Exception as e:
            print(f"Failed to restore Waybar config: {e}")
            return False
    
    def _reload_waybar(self):
        """Send reload signal to Waybar"""
        try:
            subprocess.run(["killall", "-SIGUSR2", "waybar"], 
                         capture_output=True, check=False)
        except Exception:
            pass  # Waybar might not be running
