# Theme Manager GTK Setup Guide

A modern GTK4/Libadwaita theme and wallpaper manager designed for ML4W Hyprland environments.

## Quick Installation

1. **Install dependencies:**
   ```bash
   sudo pacman -S gtk4 libadwaita python python-gobject python-cairo python-requests python-yaml python-pillow
   ```

2. **Run the installer:**
   ```bash
   cd /home/zeus/.config/Theme-Manager
   python install.py
   ```

3. **Launch the application:**
   ```bash
   ./theme-manager-gtk
   ```

## Manual Setup

### Prerequisites
- Arch Linux or compatible system with pacman
- Python 3.8 or higher
- GTK4 development libraries

### Installation Steps

1. **Check dependencies:**
   ```bash
   python install.py deps
   ```

2. **Install desktop integration:**
   ```bash
   python install.py desktop
   ```

3. **Make launcher executable:**
   ```bash
   chmod +x theme-manager-gtk
   ```

## Features

### 🎨 Theme Management
- Browse and apply system themes
- Real-time preview of color schemes
- Interactive color palette viewer
- Automatic theme detection

### 🖼️ Wallpaper Management
- Download wallpapers from multiple sources
- Background download with progress tracking
- Automatic wallpaper application
- Preview before applying

### ⚙️ Application Configuration
- Configure supported applications (Hyprland, Waybar, Mako, etc.)
- Selective application of theme changes
- Real-time configuration updates

### 🎯 ML4W Integration
- Designed for ML4W Hyprland setups
- Seamless integration with existing configurations
- Follows ML4W design principles

## Usage

### Launching
- **From terminal:** `./theme-manager-gtk`
- **From application menu:** Search for "Theme Manager"
- **Keyboard shortcut:** Add to Hyprland config:
  ```
  bind = SUPER, T, exec, /home/zeus/.config/Theme-Manager/theme-manager-gtk
  ```

### Navigation
- **Main Window:** Browse themes and wallpapers
- **Settings:** Configure applications and preferences
- **Download Manager:** Manage wallpaper downloads

## Configuration

The application stores its configuration in:
- Main config: `~/.config/Theme-Manager/config.yaml`
- Application settings: `~/.config/Theme-Manager/app_config.yaml`
- Downloaded wallpapers: `~/.config/Theme-Manager/wallpapers/`

## Troubleshooting

### Common Issues

**Application won't start:**
```bash
# Check dependencies
python install.py deps

# Verify GTK installation
python -c "import gi; gi.require_version('Gtk', '4.0'); from gi.repository import Gtk"
```

**Missing themes:**
- Ensure theme directories exist in `~/.config/Theme-Manager/`
- Check permissions on theme files

**Wallpaper downloads fail:**
- Verify internet connection
- Check that `python-requests` is installed

### Debug Mode
Run with debug output:
```bash
G_MESSAGES_DEBUG=all ./theme-manager-gtk
```

## Development

### Project Structure
```
Theme-Manager/
├── main.py              # Main GTK application
├── theme-manager-gtk    # Launcher script
├── config_manager.py    # Configuration handling
├── wallpaper_utils.py   # Clean wallpaper utilities
├── theme_manager.py     # Theme operations
└── install.py          # Installation script
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Test with the GTK application
4. Submit a pull request

## Requirements

### System Dependencies
- `gtk4` - GTK4 framework
- `libadwaita` - Modern GTK widgets
- `python` - Python 3 interpreter
- `python-gobject` - Python GTK bindings
- `python-cairo` - Cairo graphics bindings

### Python Dependencies
- `gi` - PyGObject for GTK access
- `yaml` - Configuration file parsing
- `requests` - HTTP downloads
- `PIL` - Image processing

### Optional Dependencies
- `gvfs` - Enhanced file operations
- `xdg-utils` - Desktop integration
- `swww` - Wayland wallpaper setting
- `hyprpaper` - Alternative wallpaper daemon
