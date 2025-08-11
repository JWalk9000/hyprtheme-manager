# Theme Manager Project Plan

## Project Overview

Theme Manager is a modern UI application for Linux that creates a seamless wallpaper and color theming experience by automatically generating and applying system-wide colors themes based on wallpapers. The application uses pywal for color extraction and offers a plugin system to extend theme application to various desktop components.

## Core Components

### 1. Wallpaper Management
- Browse and select wallpapers from a configured directory
- Preview wallpapers in the application
- Download additional wallpapers from user chosen repositories
- Cache color schemes extracted from wallpapers for performance

### 2. Theme Generation
- Extract color palettes from wallpapers using pywal
- Create and manage a cache system for quick access to generated colors
- Allow previewing of color schemes before applying them
- Support different theme application modes (wallpaper-only, colors-only, or both)

### 3. Plugin System
- Modular architecture for supporting different applications
- Standardized plugin interface with consistent behavior
- Plugin configuration and management through GUI
- Status tracking for plugin execution

### 4. User Interface
- Modern Libadwaita interface with responsive design
- Interactive color swatch display
- Thumbnail-based wallpaper browser
- Status section showing current theme configuration
- Toast notifications for user feedback

## Technical Features

### Background Processing
- Thread-based non-blocking operations for UI responsiveness
- Progress indicators for long-running tasks
- Proper error handling and user feedback

### System Integration
- Compatibility with various wallpaper setting methods (swww)
- GTK and QT color theme compatible
- Desktop entry for application
- Window manager integration (floating mode support)

### Configuration Management
- YAML-based configuration storage
- User-configurable settings for directories and appearance
- Live preview; reapplies color and/or wallparper if not expressly set when leaving the app.

## Functionality Flow

1. **Initialization**
   - Load configuration settings
   - Initialize plugin system
   - Backup current theme for potential restoration
   - Prepare UI components
   - Check the wallpaper directory for changes and update thumbnails and cached colors if needed.

2. **Wallpaper Selection**
   - Display available wallpapers as thumbnails
   - Allow  selection, in app palette preview, and live preview if enabled. 
   - enable 'Apply Wallpaper', 'Apply Colors', and 'Apply Theme' buttons

3. **Palette Preview**
   - Display extracted colors as interactive swatches.
   - enable 'click to copy-to-clipboard' on each swatch, display color code on mouse-over.
   - Enable 'Copy Palette" button to copy whole palette to clipboard.

4. **Theme Application**
   - Set selected wallpaper to the system
   - Apply color scheme to all configured appications
   - Use plugin system to apply themes to configured applications
   - Provide feedback on success/failure

5. **Configuration**
   - Configure which applications receive theme updates
   - Manage window behavior and appearance
   - Control theme generation parameters

## Future Enhancements

- Additional wallpaper repositories and download sources
- Custom color scheme editing
- Theme scheduling (time-based theme changes)
- More comprehensive plugin management interface
- Theme import/export
- Enhanced GTK/QT theme compatibility

## Development Approach

Unified UI-agnostic core application, follows the K.I.S.S. preinciples. 