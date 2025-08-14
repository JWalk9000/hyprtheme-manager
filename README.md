
# Theme Manager

Modern theme manager for Linux with dual GTK4/Qt6 interfaces, designed for Hyprland and other compositors.

## Features

- **Dual UI Backends**: GTK4 (native Linux) and Qt6 (cross-platform) interfaces
- **Live Color Extraction**: Automatic palette generation from wallpapers using pywal
- **Live Theme Preview**: Real-time color changes with apply/revert functionality  
- **Plugin System**: Modular application theming with enable/disable controls
- **Wallpaper Management**: Built-in wallpaper browser with thumbnail cache
- **Settings Management**: Live settings changes with GUI configuration
- **Modern UI**: Border radius styling, scroll position preservation, status display

## Installation (Arch Linux)

```bash
git clone https://github.com/yourusername/Theme-Manager.git
cd Theme-Manager
python install.py
```

The installer will:
- Check and install dependencies via pacman
- Set your preferred default UI backend (GTK/Qt6)
- Create desktop launcher and launch script
- Set up proper file permissions

## Usage

```bash
# Launch with default UI (set during installation)
./theme-manager

# Or from Python directly  
python main.py

# Override UI backend for troubleshooting
python main.py --ui gtk
python main.py --ui qt

# From application launcher
Search for "Theme Manager"
```

## Application Support

**Currently Supported:**
- **Waybar**: Status bar styling
- **Kitty**: Terminal color schemes  
- **Wofi**: Application launcher theming
- **Mako**: Notification daemon styling
- **GTK3/4**: System theme integration
- **Qt5**: Qt application theming

**Plugin Management:**
Access via **Settings → Configure Apps** to enable/disable individual application theming.

## Settings

**UI Settings:**
- Backend selection (GTK4/Qt6)
- Window size and floating mode
- Color display (8 vs 16 colors)

**Wallpaper Settings:**  
- Custom wallpaper directory
- Live preview toggle

**Theme Settings:**
- Results dialog display
- Individual app theming control

All settings changes are applied live without requiring restart.

## Configuration Files

- **Settings**: `config/settings.yaml`
- **Applied Colors**: `applied_colors.json` 
- **Templates**: `templates/` directory
- **Default Wallpapers**: `~/Pictures/Wallpapers`

## Troubleshooting

**Installation Issues:**
```bash
# Re-run installer to check dependencies
python install.py

# Check if all Python modules are available
python -c "import PyQt6, gi, yaml, requests, PIL; print('All dependencies OK')"
```

**Runtime Issues:**
```bash
# Force specific UI backend
python main.py --ui gtk   # Use GTK4 backend
python main.py --ui qt    # Use Qt6 backend

# Debug mode (GTK only)
G_MESSAGES_DEBUG=all python main.py --ui gtk
```

**Common Solutions:**
- **UI won't start**: Check dependencies with `python install.py`
- **Wallpapers not loading**: Verify wallpaper directory in Settings
- **Theme not applying**: Check app-specific settings in Configure Apps
- **Settings not saving**: Ensure write permissions in config directory
