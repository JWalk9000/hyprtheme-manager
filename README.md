
# Theme Manager - GTK4/Libadwaita Edition

A modern, native Linux theme management application built with GTK4 and Libadwaita, providing seamless wallpaper-based theme generation using pywal.

## Features

### 🎨 Modern GTK Interface
- **Native Libadwaita Design**: Clean, modern interface following GNOME design patterns
- **Interactive Color Palette**: Click any color swatch to copy to clipboard
- **Real-time Wallpaper Preview**: Browse and preview wallpapers before applying
- **Application Configuration**: Manage which applications receive theme updates
- **Wallpaper Downloads**: Access curated wallpaper repositories

### 🚀 Core Functionality
- **Automatic Theme Generation**: Uses pywal to extract colors from wallpapers
- **Multi-Application Support**: Themes waybar, wofi, mako, kitty, and more
- **Background Processing**: Non-blocking operations with progress feedback
- **Toast Notifications**: Clear user feedback for all actions
- **Desktop Integration**: Proper .desktop file for application launcher

## Installation

### Prerequisites
```bash
# Install required dependencies
sudo pacman -S python-gobject gtk4 libadwaita python-yaml
```

### Quick Setup
```bash
# Clone or ensure you're in the theme manager directory
cd /home/zeus/.config/Theme-Manager

# Make the GTK launcher executable
chmod +x theme-manager-gtk

# Install desktop entry (optional)
cp theme-manager-gtk.desktop ~/.local/share/applications/
```

## Usage

### Launch the Application
```bash
# Direct launch
./theme-manager-gtk

# Or from application launcher after installing .desktop file
```

### Interface Overview

#### Status Section
- View current theme status
- See active wallpaper information
- Check configured applications count
- Quick access to configuration

#### Wallpaper Selection
- Browse available wallpapers
- Preview wallpapers with external viewer
- Apply themes with progress feedback
- Manage wallpaper directory

#### Color Palette
- View generated pywal colors
- Click any color to copy to clipboard
- Copy all colors at once
- Real-time color updates

#### Header Controls
- **Refresh**: Update wallpaper and color data
- **Download**: Access wallpaper repositories
- **Menu**: Application settings and about dialog

## File Structure

```
Theme-Manager/
├── main.py                     # Main GTK4 application
├── config/
│   └── templates/              # Application templates
│       ├── waybar.template
│       ├── wofi.template
│       ├── mako.template
│       └── kitty.template
├── config_manager.py           # Configuration management
├── template_manager.py         # Template processing
├── wallpaper_utils.py          # Clean wallpaper utilities
├── theme-manager-gtk           # GTK launcher script
├── theme-manager-gtk.desktop   # Desktop integration
├── app-locations.yaml          # App configuration paths
├── dependencies.yaml           # Required packages
└── install.py                  # Installation script
```

## Configuration

### Application Settings
Access via the application menu → "Application Settings" to:
- Enable/disable theming for specific applications
- Configure custom application paths
- Manage application-specific settings

### Wallpaper Management
- Default directory: `~/Pictures/wallpapers`
- Supports common image formats (jpg, png, webp, etc.)
- Download curated collections via the download interface

## Supported Applications

The theme manager can automatically apply themes to:
- **Waybar**: Status bar theming
- **Wofi**: Application launcher theming  
- **Mako**: Notification daemon theming
- **Kitty**: Terminal emulator theming

Additional applications can be added via the configuration interface.

## Development

### Architecture
- **GTK4/Libadwaita**: Modern native Linux UI framework
- **Python 3**: Application logic with proper threading
- **Background Processing**: Non-blocking operations using GLib.idle_add
- **Modular Design**: Separate modules for different functionality

### Key Components
- `ThemeManagerApplication`: Main application controller
- `ThemeManagerWindow`: Primary interface window
- `AppConfigWindow`: Application configuration dialog
- `WallpaperDownloadWindow`: Repository download interface

## Troubleshooting

### Common Issues
1. **Missing Dependencies**: Ensure GTK4 and Libadwaita are installed
2. **Permission Issues**: Make sure the launcher script is executable
3. **Missing Wallpapers**: Check wallpaper directory permissions

### Debug Mode
Run with verbose output:
```bash
G_MESSAGES_DEBUG=all ./theme-manager-gtk
```

## Contributing

This is a complete GTK4/Libadwaita implementation focusing on:
- Modern Linux desktop integration
- Clean, intuitive user experience
- Robust error handling and user feedback
- Extensible architecture for future enhancements

## License

GPL-3.0 - Modern theme management for Linux desktops.
4. The script will:
   - Generate a pywal palette from the wallpaper
   - Render templates with the palette and write to config files
   - Optionally call wofi-wal, waybar-wal, mako-wal if installed
   - Print which configs were updated

## Customization
- Add or edit templates in `config/templates/` to control the look of each app.
- Add more config locations in `app-locations.yaml` as needed.
- Extend the script to support more apps or custom logic.

## Notes
- For best results, ensure all apps are restarted or reloaded after applying a new theme.
- This project is modular and can be extended for other apps or workflows.
