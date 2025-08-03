# Theme Manager Plugin System

The Theme Manager now uses a modular plugin architecture that allows you to easily add, remove, and manage theme plugins for different applications.

## Overview

Each application (Waybar, Kitty, Wofi, etc.) is now handled by its own plugin module. This makes the system:

- **Modular**: Each app has its own self-contained plugin
- **Expandable**: Easy to add new applications
- **Maintainable**: Isolated logic for each application
- **User-friendly**: Enable/disable apps through the GUI

## Plugin Architecture

### Base Plugin Class
All plugins inherit from `ThemePlugin` which defines:
- **Metadata**: name, display_name, description
- **Configuration**: config_path, template_name, dependencies
- **Methods**: apply_theme(), backup_config(), restore_config(), is_available()

### Plugin Manager
The `PluginManager` class handles:
- **Discovery**: Automatically loads plugins from the plugins directory
- **Configuration**: Manages enabled/disabled state
- **Execution**: Applies themes to all enabled plugins
- **State Management**: Backup and restore functionality

## Available Plugins

| Plugin | Application | Description |
|--------|-------------|-------------|
| `waybar` | Waybar | Wayland status bar theming |
| `kitty` | Kitty Terminal | Terminal emulator theming |
| `wofi` | Wofi | Application launcher theming |
| `mako` | Mako | Notification daemon theming |
| `gtk` | GTK Themes | GTK 3/4 application theming |

## Managing Plugins

### Through the GUI
1. Open Theme Manager
2. Go to **Preferences** (gear icon)
3. Navigate to **Plugin Management**
4. Click **Configure** to open plugin settings
5. Enable/disable plugins as needed

### Plugin Configuration Window
- **Enable/Disable**: Toggle plugins on/off
- **Plugin Info**: View detailed information about each plugin
- **Status**: See which plugins are available on your system
- **Statistics**: Overview of loaded/enabled plugins

## Creating New Plugins

### Using the Plugin Generator
```bash
cd /home/zeus/.config/Theme-Manager
python create_plugin.py <app_name> <app_title> <description> <config_path> [executable_name]
```

**Example**: Create an Alacritty plugin
```bash
python create_plugin.py alacritty "Alacritty Terminal" "Fast terminal emulator" "~/.config/alacritty/alacritty.yml"
```

This creates:
- `plugins/alacritty_plugin.py` - Plugin logic
- `config/templates/alacritty.template` - Theme template

### Manual Plugin Creation

1. **Create Plugin File**: `plugins/myapp_plugin.py`
```python
from plugin_manager import ThemePlugin

class MyAppPlugin(ThemePlugin):
    @property
    def name(self) -> str:
        return "myapp"
    
    # Implement required methods...
```

2. **Create Template**: `config/templates/myapp.template`
```css
/* Use {{background}}, {{foreground}}, {{color0}}-{{color15}} */
body {
    background: {{background}};
    color: {{foreground}};
}
```

3. **Restart Theme Manager** to load the new plugin

## Template System

### Available Variables
Templates can use these color placeholders:
- `{{background}}` - Main background color
- `{{foreground}}` - Main text color  
- `{{color0}}` to `{{color15}}` - 16-color palette
- `{{cursor}}` - Cursor color

### Template Processing
1. Pywal extracts colors from wallpaper
2. Template engine replaces placeholders with hex values
3. Processed config written to application config file
4. Application reloaded to apply changes

## Plugin Development

### Required Methods
```python
class MyPlugin(ThemePlugin):
    def name(self) -> str:
        return "myapp"
    
    def display_name(self) -> str:
        return "My Application"
    
    def description(self) -> str:
        return "Description of the app"
    
    def config_path(self) -> str:
        return os.path.expanduser("~/.config/myapp/config")
    
    def template_name(self) -> str:
        return "myapp"
    
    def is_available(self) -> bool:
        return shutil.which("myapp") is not None
    
    def apply_theme(self, colors: Dict[str, Any]) -> bool:
        # Apply theme logic
        return True
    
    def backup_config(self, backup_dir: str) -> bool:
        # Backup current config
        return True
    
    def restore_config(self, backup_dir: str) -> bool:
        # Restore from backup
        return True
```

### Best Practices
- **Error Handling**: Always catch exceptions and return success/failure
- **Availability Check**: Use `shutil.which()` to check if app is installed
- **Graceful Degradation**: Don't crash if config files are missing
- **Reload Logic**: Implement proper app reload/refresh mechanism
- **Backup Safety**: Always backup before making changes

## Configuration Files

### Plugin Configuration
- **File**: `plugin-config.json`
- **Contains**: Enabled plugins list and plugin metadata
- **Auto-generated**: Created automatically by Plugin Manager

### Template Directory
- **Location**: `config/templates/`
- **Files**: `*.template` files for each application
- **Format**: Application config with `{{color}}` placeholders

## Troubleshooting

### Plugin Not Loading
1. Check filename ends with `_plugin.py`
2. Ensure class inherits from `ThemePlugin`
3. Check for syntax errors in plugin file
4. Restart Theme Manager

### Theme Not Applying
1. Verify template file exists
2. Check template syntax and placeholders
3. Ensure config path is correct
4. Check if application is running
5. Verify application supports config reloading

### Adding System Dependencies
If your plugin requires system packages, add them to:
- `dependencies.yaml` - For automatic installation
- Plugin's `dependencies` property - For availability checking

## Examples

### Simple Plugin (Alacritty)
```python
def apply_theme(self, colors: Dict[str, Any]) -> bool:
    try:
        template = read_template(self.template_name, template_dir)
        rendered = render_template(template, colors)
        write_config(self.config_path, rendered)
        return True
    except Exception as e:
        print(f"Failed: {e}")
        return False
```

### Plugin with Reload (i3)
```python
def _reload_i3(self):
    try:
        subprocess.run(["i3-msg", "reload"], check=False)
    except Exception:
        pass
```

### Plugin with Multiple Configs (Rofi)
```python
def apply_theme(self, colors: Dict[str, Any]) -> bool:
    # Apply to multiple config files
    configs = [
        "~/.config/rofi/config.rasi",
        "~/.config/rofi/themes/theme.rasi"
    ]
    for config in configs:
        # Process each config...
```

This plugin system makes Theme Manager highly extensible and user-customizable!
