
# Theme Manager

Modern theme manager with modular plugin system designed for Hyprland, may work for others.

## Features

- **Modular Plugin System**: Add/remove application support dynamically
- **Pywal Integration**: Automatic color extraction from wallpapers
- **GTK4 and QT UI**: Native Linux desktop experience
- **Plugin Management**: Enable/disable application theming via GUI
- **Future - Wallpaper Downloads**: Built-in wallpaper repository access

## Installation

```bash
# Quick install (recommended), gives option for GTK or QT UI, rerun to change/add selection.
python install.py


## Usage

```bash
# Launch application with GTK UI
./theme-manager -g

# Launch application with QT UI
./theme-manager -q

# From application launcher
Search for "Theme Manager"
```

### Plugin System

Access plugin management via **Settings → Configure Apps**:
- Enable/disable application theming
- View available plugins
- Future - Create new plugins with included generator

### Supported Applications

- **Waybar**: Status bar theming
- **Kitty**: Terminal theming
- **Wofi**: Launcher theming
- **Mako**: Notification theming
- **GTK**: System theme integration

## Plugin Development

Create new plugins using the interactive generator:
```bash
python create_plugin.py my_app
```

This creates `plugins/my_app_plugin.py` with the required structure.

## Configuration

Plugin settings: **Settings → Configure Apps**
Defaut Wallpaper directory: `~/Pictures/wallpapers`

## Troubleshooting

**Common Issues:**
- **No launch**: Check dependencies with `python install.py`
- **Missing plugins**: Verify `plugins/` directory exists
- **Theme not applied**: Check application availability in plugin settings

**Debug mode:**
```bash
G_MESSAGES_DEBUG=all ./theme-manager-gtk
```
