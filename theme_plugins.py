"""
Plugin system for Theme Manager.
Handles application-specific theme updates with safe config management.
"""

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from abc import ABC, abstractmethod
import yaml


class ThemePlugin(ABC):
    """
    Abstract base class for application theme plugins.
    Each plugin handles a specific application's theming.
    """
    
    def __init__(self, name: str, config_path: Path, template_path: Optional[Path] = None):
        self.name = name
        self.config_path = Path(config_path).expanduser()
        self.template_path = template_path
        self.backup_suffix = ".theme-manager-backup"
    
    @abstractmethod
    def detect_installation(self) -> bool:
        """Check if the application is installed and config exists."""
        pass
    
    @abstractmethod
    def apply_theme(self, colors: Dict[str, str]) -> bool:
        """Apply theme colors to the application."""
        pass
    
    def backup_config(self) -> bool:
        """Create a backup of the current config."""
        if not self.config_path.exists():
            return True  # Nothing to backup
        
        backup_path = Path(str(self.config_path) + self.backup_suffix)
        try:
            shutil.copy2(self.config_path, backup_path)
            return True
        except Exception as e:
            print(f"Failed to backup {self.name} config: {e}")
            return False
    
    def restore_config(self) -> bool:
        """Restore config from backup."""
        backup_path = Path(str(self.config_path) + self.backup_suffix)
        if not backup_path.exists():
            print(f"No backup found for {self.name}")
            return False
        
        try:
            shutil.copy2(backup_path, self.config_path)
            return True
        except Exception as e:
            print(f"Failed to restore {self.name} config: {e}")
            return False


class TemplatePlugin(ThemePlugin):
    """
    Plugin that uses template files for theme application.
    Safe method that doesn't modify existing configs directly.
    """
    
    def __init__(self, name: str, config_path: Path, template_path: Path, 
                 restart_command: Optional[str] = None):
        super().__init__(name, config_path, template_path)
        self.restart_command = restart_command
    
    def detect_installation(self) -> bool:
        """Check if template exists and config directory is accessible."""
        if not self.template_path or not self.template_path.exists():
            return False
        
        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        return True
    
    def apply_theme(self, colors: Dict[str, str]) -> bool:
        """Apply theme using template substitution."""
        if not self.template_path.exists():
            print(f"Template not found: {self.template_path}")
            return False
        
        try:
            # Read template
            with open(self.template_path, 'r') as f:
                template_content = f.read()
            
            # Backup existing config
            self.backup_config()
            
            # Substitute template variables
            themed_content = self._substitute_template(template_content, colors)
            
            # Write new config
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                f.write(themed_content)
            
            print(f"Applied theme to {self.name}")
            
            # Restart application if needed
            if self.restart_command:
                self._restart_application()
            
            return True
            
        except Exception as e:
            print(f"Failed to apply theme to {self.name}: {e}")
            return False
    
    def _substitute_template(self, template: str, colors: Dict[str, str]) -> str:
        """Substitute template variables with color values."""
        # Add semantic color mappings
        template_vars = colors.copy()
        template_vars.update({
            'background': colors.get('color0', '#000000'),
            'foreground': colors.get('color7', '#ffffff'),
            'cursor': colors.get('color7', '#ffffff'),
        })
        
        # Substitute {{variable}} patterns
        def replace_var(match):
            var_name = match.group(1)
            return template_vars.get(var_name, match.group(0))
        
        return re.sub(r'\{\{(\w+)\}\}', replace_var, template)
    
    def _restart_application(self):
        """Restart the application to apply changes."""
        try:
            subprocess.run(self.restart_command, shell=True, capture_output=True)
            print(f"Restarted {self.name}")
        except Exception as e:
            print(f"Failed to restart {self.name}: {e}")


class KittyPlugin(TemplatePlugin):
    """Plugin for Kitty terminal."""
    
    def __init__(self):
        super().__init__(
            name="Kitty",
            config_path=Path("~/.config/kitty/theme-manager-colors.conf"),
            template_path=Path("templates/kitty.template"),
            restart_command="pkill -USR1 kitty || true"  # Reload kitty configs, ignore errors
        )
    
    def detect_installation(self) -> bool:
        """Check if Kitty is installed."""
        return shutil.which("kitty") is not None and super().detect_installation()
    
    def apply_theme(self, colors: Dict[str, str]) -> bool:
        """Apply theme and ensure it's included in kitty.conf."""
        if not super().apply_theme(colors):
            return False
        
        # Ensure the theme file is included in main kitty.conf
        main_conf = Path("~/.config/kitty/kitty.conf").expanduser()
        include_line = "include theme-manager-colors.conf"
        
        try:
            if main_conf.exists():
                with open(main_conf, 'r') as f:
                    content = f.read()
                
                if include_line not in content:
                    with open(main_conf, 'a') as f:
                        f.write(f"\n# Theme Manager colors\n{include_line}\n")
                    print("Added theme include to kitty.conf")
                else:
                    print("Kitty theme include already present")
            else:
                # Create minimal kitty.conf
                main_conf.parent.mkdir(parents=True, exist_ok=True)
                with open(main_conf, 'w') as f:
                    f.write(f"# Kitty configuration\n{include_line}\n")
                print("Created kitty.conf with theme include")
            
            # Additional step: try to send reload signal to all kitty instances
            self._reload_kitty()
            
            return True
            
        except Exception as e:
            print(f"Failed to update kitty.conf: {e}")
            return False
    
    def _reload_kitty(self):
        """Send reload signal to all kitty instances."""
        try:
            import subprocess
            # Method 1: Send USR1 signal to reload configs
            result = subprocess.run(['pkill', '-USR1', 'kitty'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("Sent reload signal to Kitty instances")
            
            # Method 2: Alternative approach using kitty remote control (if enabled)
            try:
                subprocess.run(['kitty', '@', 'load-config'], 
                             capture_output=True, text=True, timeout=2)
                print("Attempted Kitty remote reload")
            except:
                pass  # Remote control might not be enabled
                
        except Exception as e:
            print(f"Note: Could not reload Kitty: {e}")
            print("New Kitty instances will pick up the theme automatically")


class WaybarPlugin(TemplatePlugin):
    """Plugin for Waybar."""
    
    def __init__(self):
        super().__init__(
            name="Waybar",
            config_path=Path("~/.config/waybar/theme-manager-style.css"),
            template_path=Path("templates/waybar.template"),
            restart_command=None  # Let user's script handle restart
        )
    
    def detect_installation(self) -> bool:
        """Check if Waybar is installed."""
        return shutil.which("waybar") is not None and super().detect_installation()
    
    def apply_theme(self, colors: Dict[str, str]) -> bool:
        """Apply theme and ensure it's included in waybar style."""
        if not super().apply_theme(colors):
            return False
        
        # Ensure the theme file is included in main waybar style
        main_style = Path("~/.config/waybar/style.css").expanduser()
        include_line = "@import 'theme-manager-style.css';"
        
        try:
            if main_style.exists():
                with open(main_style, 'r') as f:
                    content = f.read()
                
                if include_line not in content:
                    # Find the end of the @define-color section to insert import after
                    lines = content.split('\n')
                    insert_index = 0
                    
                    # Look for the last @define-color line
                    for i, line in enumerate(lines):
                        if line.strip().startswith('@define-color'):
                            insert_index = i + 1
                    
                    # If no @define-color found, add after header comments
                    if insert_index == 0:
                        for i, line in enumerate(lines):
                            if line.strip().startswith('*/'):
                                insert_index = i + 1
                                break
                    
                    # Insert the import after the fallback colors
                    lines.insert(insert_index, '')
                    lines.insert(insert_index + 1, '/* Theme Manager colors (override fallbacks) */')
                    lines.insert(insert_index + 2, include_line)
                    lines.insert(insert_index + 3, '')
                    
                    with open(main_style, 'w') as f:
                        f.write('\n'.join(lines))
                    
                    print("Added theme import after fallback colors in waybar style.css")
            else:
                # Create minimal style.css
                main_style.parent.mkdir(parents=True, exist_ok=True)
                with open(main_style, 'w') as f:
                    f.write(f"/* Waybar configuration */\n{include_line}\n")
                print("Created waybar style.css with theme import")
            
            print("Waybar theme applied - your restart script should handle reload")
            
            # Touch the main style.css file to trigger file watcher
            import time
            main_style.touch()
            print("Touched style.css to trigger restart script")
            
            # Also create a signal file for scripts that watch for it
            signal_file = Path("~/.config/waybar/.theme-updated").expanduser()
            signal_file.touch()
            
            return True
            
        except Exception as e:
            print(f"Failed to update waybar style.css: {e}")
            return False


class MakoPlugin(TemplatePlugin):
    """Plugin for Mako notification daemon."""
    
    def __init__(self):
        super().__init__(
            name="Mako",
            config_path=Path("~/.config/mako/config"),
            template_path=Path("templates/mako.template"),
            restart_command="makoctl reload"
        )
    
    def detect_installation(self) -> bool:
        """Check if Mako is installed."""
        return shutil.which("mako") is not None and super().detect_installation()


class WofiPlugin(TemplatePlugin):
    """Plugin for Wofi launcher."""
    
    def __init__(self):
        super().__init__(
            name="Wofi",
            config_path=Path("~/.config/wofi/theme-manager-style.css"),
            template_path=Path("templates/wofi.template")
        )
    
    def detect_installation(self) -> bool:
        """Check if Wofi is installed."""
        return shutil.which("wofi") is not None and super().detect_installation()


class ThemePluginManager:
    """
    Manages all theme plugins and coordinates theme application.
    """
    
    def __init__(self, templates_dir: Path):
        self.templates_dir = Path(templates_dir)
        self.plugins: List[ThemePlugin] = []
        self._initialize_plugins()
    
    def _initialize_plugins(self):
        """Initialize all available plugins."""
        # Update template paths to be absolute
        template_paths = {
            plugin_class.__name__.replace('Plugin', '').lower(): self.templates_dir / f"{plugin_class.__name__.replace('Plugin', '').lower()}.template"
            for plugin_class in [KittyPlugin, WaybarPlugin, MakoPlugin, WofiPlugin]
        }
        
        # Create plugins with corrected paths
        self.plugins = [
            KittyPlugin(),
            WaybarPlugin(), 
            MakoPlugin(),
            WofiPlugin()
        ]
        
        # Update template paths after creation
        for plugin in self.plugins:
            plugin_name = plugin.name.lower()
            if plugin_name in template_paths:
                plugin.template_path = template_paths[plugin_name]
    
    def get_available_plugins(self) -> List[ThemePlugin]:
        """Get list of plugins for applications that are installed."""
        available = []
        for plugin in self.plugins:
            if plugin.detect_installation():
                available.append(plugin)
            else:
                print(f"Plugin {plugin.name}: Not available (app not installed or template missing)")
        
        return available
    
    def apply_theme_to_all(self, colors: Dict[str, str]) -> Dict[str, bool]:
        """Apply theme to all available applications."""
        results = {}
        available_plugins = self.get_available_plugins()
        
        print(f"Applying theme to {len(available_plugins)} applications...")
        
        for plugin in available_plugins:
            try:
                success = plugin.apply_theme(colors)
                results[plugin.name] = success
                if success:
                    print(f"✅ {plugin.name}: Theme applied")
                else:
                    print(f"❌ {plugin.name}: Failed to apply theme")
            except Exception as e:
                results[plugin.name] = False
                print(f"❌ {plugin.name}: Error - {e}")
        
        return results
    
    def apply_theme_to_specific(self, colors: Dict[str, str], app_names: List[str]) -> Dict[str, bool]:
        """Apply theme to specific applications."""
        results = {}
        available_plugins = {p.name.lower(): p for p in self.get_available_plugins()}
        
        for app_name in app_names:
            app_key = app_name.lower()
            if app_key in available_plugins:
                plugin = available_plugins[app_key]
                try:
                    success = plugin.apply_theme(colors)
                    results[plugin.name] = success
                except Exception as e:
                    results[plugin.name] = False
                    print(f"❌ {plugin.name}: Error - {e}")
            else:
                results[app_name] = False
                print(f"❌ {app_name}: Plugin not available")
        
        return results
    
    def restore_all_configs(self) -> Dict[str, bool]:
        """Restore all application configs from backups."""
        results = {}
        for plugin in self.plugins:
            results[plugin.name] = plugin.restore_config()
        return results
    
    def get_plugin_info(self) -> Dict[str, Dict]:
        """Get information about all plugins."""
        info = {}
        for plugin in self.plugins:
            info[plugin.name] = {
                "installed": plugin.detect_installation(),
                "config_path": str(plugin.config_path),
                "template_path": str(plugin.template_path) if plugin.template_path else None,
                "has_backup": Path(str(plugin.config_path) + plugin.backup_suffix).exists()
            }
        return info


# Global plugin manager instance
plugin_manager = ThemePluginManager(Path(__file__).parent / "templates")
