"""
Kitty Terminal Theme Plugin
Handles theming for Kitty terminal emulator
"""

import os
import shutil
import subprocess
from typing import Dict, Any, List
from plugin_manager import ThemePlugin

class KittyPlugin(ThemePlugin):
    
    @property
    def name(self) -> str:
        return "kitty"
    
    @property
    def display_name(self) -> str:
        return "Kitty Terminal"
    
    @property
    def description(self) -> str:
        return "Fast, feature-rich GPU-accelerated terminal emulator"
    
    @property
    def config_path(self) -> str:
        return os.path.expanduser("~/.config/kitty/pywal.conf")
    
    @property
    def template_name(self) -> str:
        return "kitty"
    
    @property
    def dependencies(self) -> List[str]:
        return ["kitty"]
    
    def is_available(self) -> bool:
        """Check if Kitty is installed"""
        return shutil.which("kitty") is not None
    
    def apply_theme(self, colors: Dict[str, Any]) -> bool:
        """Apply theme to Kitty"""
        try:
            from template_manager import read_template, render_template, write_config
            
            template_dir = os.path.join(os.path.dirname(__file__), '..', 'config', 'templates')
            
            template = read_template(self.template_name, template_dir)
            if not template:
                print(f"No template found for {self.display_name}")
                return False
            
            rendered = render_template(template, colors)
            write_config(self.config_path, rendered)
            
            # Update main kitty config to include pywal.conf if not already included
            self._update_kitty_config()
            
            # Reload Kitty instances
            self._reload_kitty()
            
            return True
            
        except Exception as e:
            print(f"Failed to apply Kitty theme: {e}")
            return False
    
    def backup_config(self, backup_dir: str) -> bool:
        """Backup current Kitty theme config"""
        try:
            if os.path.exists(self.config_path):
                backup_path = os.path.join(backup_dir, f"kitty-pywal.conf.backup")
                os.makedirs(backup_dir, exist_ok=True)
                shutil.copy2(self.config_path, backup_path)
                return True
            return False
        except Exception as e:
            print(f"Failed to backup Kitty config: {e}")
            return False
    
    def restore_config(self, backup_dir: str) -> bool:
        """Restore Kitty config from backup"""
        try:
            backup_path = os.path.join(backup_dir, f"kitty-pywal.conf.backup")
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, self.config_path)
                self._reload_kitty()
                return True
            return False
        except Exception as e:
            print(f"Failed to restore Kitty config: {e}")
            return False
    
    def _update_kitty_config(self):
        """Ensure main kitty config includes pywal.conf"""
        main_config = os.path.expanduser("~/.config/kitty/kitty.conf")
        include_line = "include pywal.conf"
        
        try:
            # Check if include line already exists
            if os.path.exists(main_config):
                with open(main_config, 'r') as f:
                    content = f.read()
                if include_line in content:
                    return
            
            # Add include line
            os.makedirs(os.path.dirname(main_config), exist_ok=True)
            with open(main_config, 'a') as f:
                f.write(f"\n# Pywal colors\n{include_line}\n")
                
        except Exception as e:
            print(f"Failed to update Kitty main config: {e}")
    
    def _reload_kitty(self):
        """Reload Kitty configuration"""
        try:
            # Send signal to reload config
            subprocess.run(["killall", "-SIGUSR1", "kitty"], 
                         capture_output=True, check=False)
        except Exception:
            pass
