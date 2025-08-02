"""
Plugin Manager for Theme Manager Applications
Handles dynamic loading and management of theming plugins
"""

import os
import sys
import importlib
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

class ThemePlugin(ABC):
    """Base class for all theme plugins"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name (e.g., 'waybar', 'kitty')"""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name for UI"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this plugin themes"""
        pass
    
    @property
    @abstractmethod
    def config_path(self) -> str:
        """Default config file path"""
        pass
    
    @property
    @abstractmethod
    def template_name(self) -> str:
        """Template file name (without .template extension)"""
        pass
    
    @property
    def dependencies(self) -> List[str]:
        """List of required system dependencies"""
        return []
    
    @property
    def optional_dependencies(self) -> List[str]:
        """List of optional system dependencies"""
        return []
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the application is available on the system"""
        pass
    
    @abstractmethod
    def apply_theme(self, colors: Dict[str, Any]) -> bool:
        """Apply theme with given colors. Returns True on success"""
        pass
    
    @abstractmethod
    def backup_config(self, backup_dir: str) -> bool:
        """Backup current config. Returns True on success"""
        pass
    
    @abstractmethod
    def restore_config(self, backup_dir: str) -> bool:
        """Restore config from backup. Returns True on success"""
        pass
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get plugin configuration info"""
        return {
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'config_path': self.config_path,
            'template_name': self.template_name,
            'dependencies': self.dependencies,
            'optional_dependencies': self.optional_dependencies,
            'available': self.is_available()
        }

class PluginManager:
    """Manages loading and execution of theme plugins"""
    
    def __init__(self, plugin_dir: str):
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, ThemePlugin] = {}
        self.enabled_plugins: List[str] = []
        self.config_file = os.path.join(os.path.dirname(plugin_dir), 'plugin-config.json')
        
        # Add plugin directory to Python path
        if plugin_dir not in sys.path:
            sys.path.insert(0, plugin_dir)
        
        self.load_plugins()
        self.load_config()
    
    def load_plugins(self):
        """Dynamically load all plugins from the plugin directory"""
        if not os.path.exists(self.plugin_dir):
            return
        
        for filename in os.listdir(self.plugin_dir):
            if filename.endswith('_plugin.py') and not filename.startswith('__'):
                module_name = filename[:-3]  # Remove .py
                try:
                    module = importlib.import_module(module_name)
                    # Look for classes that inherit from ThemePlugin
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            issubclass(attr, ThemePlugin) and 
                            attr != ThemePlugin):
                            plugin = attr()
                            self.plugins[plugin.name] = plugin
                            print(f"Loaded plugin: {plugin.display_name}")
                except Exception as e:
                    print(f"Failed to load plugin {module_name}: {e}")
    
    def load_config(self):
        """Load plugin configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.enabled_plugins = config.get('enabled_plugins', [])
            except Exception as e:
                print(f"Failed to load plugin config: {e}")
                self.enabled_plugins = []
        else:
            # Default to all available plugins
            self.enabled_plugins = [name for name, plugin in self.plugins.items() 
                                  if plugin.is_available()]
            self.save_config()
    
    def save_config(self):
        """Save plugin configuration to file"""
        config = {
            'enabled_plugins': self.enabled_plugins,
            'plugin_info': {name: plugin.get_config_info() 
                          for name, plugin in self.plugins.items()}
        }
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Failed to save plugin config: {e}")
    
    def get_plugin(self, name: str) -> Optional[ThemePlugin]:
        """Get a specific plugin by name"""
        return self.plugins.get(name)
    
    def get_enabled_plugins(self) -> List[ThemePlugin]:
        """Get list of enabled plugins"""
        return [self.plugins[name] for name in self.enabled_plugins 
                if name in self.plugins]
    
    def get_available_plugins(self) -> List[ThemePlugin]:
        """Get list of available plugins (installed on system)"""
        return [plugin for plugin in self.plugins.values() 
                if plugin.is_available()]
    
    def get_all_plugins(self) -> List[ThemePlugin]:
        """Get list of all loaded plugins"""
        return list(self.plugins.values())
    
    def enable_plugin(self, name: str) -> bool:
        """Enable a plugin"""
        if name in self.plugins and name not in self.enabled_plugins:
            self.enabled_plugins.append(name)
            self.save_config()
            return True
        return False
    
    def disable_plugin(self, name: str) -> bool:
        """Disable a plugin"""
        if name in self.enabled_plugins:
            self.enabled_plugins.remove(name)
            self.save_config()
            return True
        return False
    
    def apply_themes(self, colors: Dict[str, Any]) -> Dict[str, bool]:
        """Apply themes to all enabled plugins. Returns success status for each"""
        results = {}
        for plugin in self.get_enabled_plugins():
            try:
                results[plugin.name] = plugin.apply_theme(colors)
            except Exception as e:
                print(f"Failed to apply theme to {plugin.display_name}: {e}")
                results[plugin.name] = False
        return results
    
    def backup_configs(self, backup_dir: str) -> Dict[str, bool]:
        """Backup configs for all enabled plugins"""
        results = {}
        for plugin in self.get_enabled_plugins():
            try:
                results[plugin.name] = plugin.backup_config(backup_dir)
            except Exception as e:
                print(f"Failed to backup {plugin.display_name}: {e}")
                results[plugin.name] = False
        return results
    
    def restore_configs(self, backup_dir: str) -> Dict[str, bool]:
        """Restore configs for all enabled plugins"""
        results = {}
        for plugin in self.get_enabled_plugins():
            try:
                results[plugin.name] = plugin.restore_config(backup_dir)
            except Exception as e:
                print(f"Failed to restore {plugin.display_name}: {e}")
                results[plugin.name] = False
        return results
