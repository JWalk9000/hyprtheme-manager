# Theme Manager Setup

Quick setup guide for the modular GTK4 theme manager.

## Installation

**One-command install:**
```bash
python install.py
```

**Manual setup:**
```bash
# Check dependencies
python install.py deps

# Install desktop entry
python install.py desktop

# Make executable
chmod +x theme-manager-gtk
```

## Dependencies

**Arch Linux:**
```bash
sudo pacman -S gtk4 libadwaita python-gobject python-yaml
```

**Other distributions:**
```bash
# Install GTK4, Libadwaita, Python GTK bindings, and PyYAML
```

## Usage

**Launch:**
```bash
./theme-manager-gtk
```

**Plugin Management:**
- Access via **Settings → Configure Apps**
- Enable/disable application theming
- View plugin status

**Create New Plugin:**
```bash
python create_plugin.py my_app
```

## Plugin System

**Built-in plugins:**
- Waybar (status bar)
- Kitty (terminal)
- Wofi (launcher)
- Mako (notifications)
- GTK (system theme)

**Plugin Structure:**
```python
class MyAppPlugin(ThemePlugin):
    def apply_theme(self, colors):
        # Theme application logic
        pass
```

## Troubleshooting

**App won't start:**
```bash
# Check dependencies
python install.py

# Verify GTK installation
python -c "import gi; gi.require_version('Gtk', '4.0')"
```

**Plugin issues:**
- Check plugin files exist in `plugins/` directory
- Verify application installation (e.g., `which waybar`)
- Review plugin settings in GUI

**Debug mode:**
```bash
G_MESSAGES_DEBUG=all ./theme-manager-gtk
```

## File Structure

```
Theme-Manager/
├── main.py                    # Main application
├── plugin_manager.py          # Plugin system
├── plugins/                   # Application plugins
├── create_plugin.py           # Plugin generator
├── install.py                 # Installer
└── theme-manager-gtk          # Launcher
```
