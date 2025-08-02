"""
GTK Theme Plugin
Handles theming for GTK 3 and GTK 4 applications
"""

import os
import shutil
import subprocess
from typing import Dict, Any, List
from plugin_manager import ThemePlugin

class GtkPlugin(ThemePlugin):
    
    @property
    def name(self) -> str:
        return "gtk"
    
    @property
    def display_name(self) -> str:
        return "GTK Themes"
    
    @property
    def description(self) -> str:
        return "GTK 3 and GTK 4 application theming"
    
    @property
    def config_path(self) -> str:
        return os.path.expanduser("~/.config/gtk-3.0/settings.ini")
    
    @property
    def template_name(self) -> str:
        return "gtk"
    
    @property
    def dependencies(self) -> List[str]:
        return ["gtk3", "gtk4"]
    
    def is_available(self) -> bool:
        """Check if GTK is available"""
        # GTK is almost always available on Linux systems
        return True
    
    def apply_theme(self, colors: Dict[str, Any]) -> bool:
        """Apply GTK theme - this is handled by the main app's GTK functions"""
        try:
            # Import GTK theme functions from main app
            import sys
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            
            # This will use the existing GTK theme management functions
            # from the main application since they're more complex
            return True
            
        except Exception as e:
            print(f"Failed to apply GTK theme: {e}")
            return False
    
    def backup_config(self, backup_dir: str) -> bool:
        """Backup current GTK configs"""
        try:
            success = True
            
            # Backup GTK 3 settings
            gtk3_config = self.config_path
            if os.path.exists(gtk3_config):
                backup_path = os.path.join(backup_dir, "gtk3-settings.ini.backup")
                os.makedirs(backup_dir, exist_ok=True)
                shutil.copy2(gtk3_config, backup_path)
            else:
                success = False
            
            # Backup GTK 4 settings via gsettings (store current theme name)
            try:
                result = subprocess.run(
                    ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
                    capture_output=True, text=True, check=True
                )
                current_theme = result.stdout.strip().strip("'")
                
                backup_file = os.path.join(backup_dir, "gtk4-theme.backup")
                with open(backup_file, 'w') as f:
                    f.write(current_theme)
            except Exception:
                pass  # GTK4 backup not critical
            
            return success
            
        except Exception as e:
            print(f"Failed to backup GTK config: {e}")
            return False
    
    def restore_config(self, backup_dir: str) -> bool:
        """Restore GTK configs from backup"""
        try:
            success = True
            
            # Restore GTK 3 settings
            backup_path = os.path.join(backup_dir, "gtk3-settings.ini.backup")
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, self.config_path)
            else:
                success = False
            
            # Restore GTK 4 settings
            gtk4_backup = os.path.join(backup_dir, "gtk4-theme.backup")
            if os.path.exists(gtk4_backup):
                try:
                    with open(gtk4_backup, 'r') as f:
                        theme_name = f.read().strip()
                    subprocess.run(
                        ["gsettings", "set", "org.gnome.desktop.interface", "gtk-theme", theme_name],
                        capture_output=True, check=True
                    )
                except Exception:
                    pass
            
            return success
            
        except Exception as e:
            print(f"Failed to restore GTK config: {e}")
            return False
