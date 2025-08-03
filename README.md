
# Theme Manager

Modern GTK4 theme manager with modular plugin system for Linux desktop environments.

## Features

- **Modular Plugin System**: Add/remove application support dynamically
- **Pywal Integration**: Automatic color extraction from wallpapers
- **GTK4/Libadwaita UI**: Native Linux desktop experience
- **Plugin Management**: Enable/disable application theming via GUI
- **Wallpaper Downloads**: Built-in wallpaper repository access

## Installation

```bash
# Quick install (recommended)
python install.py

# Manual install
chmod +x theme-manager-gtk
python install.py desktop
```

## Usage

```bash
# Launch application
./theme-manager-gtk

# From application menu
Search for "Theme Manager"
```

### Plugin System

Access plugin management via **Settings → Configure Apps**:
- Enable/disable application theming
- View available plugins
- Create new plugins with included generator

### Supported Applications

- **Waybar**: Status bar theming
- **Kitty**: Terminal theming
- **Wofi**: Launcher theming
- **Mako**: Notification theming
- **GTK**: System theme integration

## Plugin Development

Create new plugins using the generator:
```bash
python create_plugin.py my_app
```

This creates `plugins/my_app_plugin.py` with the required structure.

## File Structure

```
Theme-Manager/
├── main.py                    # Main application
├── plugin_manager.py          # Plugin system core
├── plugins/                   # Application plugins
│   ├── waybar_plugin.py
│   ├── kitty_plugin.py
│   ├── wofi_plugin.py
│   ├── mako_plugin.py
│   └── gtk_plugin.py
├── config/templates/          # Theme templates
├── create_plugin.py           # Plugin generator
├── theme-manager-gtk          # Launcher
└── install.py                 # Installer
```

## Configuration

Plugin settings: **Settings → Configure Apps**
Wallpaper directory: `~/Pictures/wallpapers`

## Troubleshooting

**Common Issues:**
- **No launch**: Check dependencies with `python install.py`
- **Missing plugins**: Verify `plugins/` directory exists
- **Theme not applied**: Check application availability in plugin settings

**Debug mode:**
```bash
G_MESSAGES_DEBUG=all ./theme-manager-gtk
```
