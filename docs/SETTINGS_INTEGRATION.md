# Settings Integration - Theme Manager

## Overview
The Theme Manager now uses a proper settings system that eliminates wallpaper directory detection and uses a clean configuration file approach.

## Key Changes

### 1. Settings System (`config/settings.yaml`)
- **Default wallpaper directory**: `~/Pictures/Wallpapers` (no auto-detection)
- **Configurable UI backend**: GTK or Qt
- **Persistent settings**: Changes saved automatically to YAML file
- **User-friendly format**: Easy to edit manually

### 2. WallpaperManager Integration
- **Settings-driven**: Uses `AppSettings` instance for configuration
- **No auto-detection**: Relies on explicit directory setting
- **Graceful fallbacks**: Handles missing directories elegantly
- **Directory validation**: Checks existence before operations

### 3. UI Integration (Both GTK & Qt)
- **First-run folder chooser**: Automatically shown if default directory doesn't exist
- **Manual folder selection**: "Choose Folder" button available anytime
- **Settings persistence**: User selections automatically saved
- **Clean UI flow**: No confusing auto-detection messages

## How It Works

### Directory Resolution Priority:
1. **User-configured**: Setting in `config/settings.yaml`
2. **Default fallback**: `~/Pictures/Wallpapers`
3. **User selection**: Folder chooser dialog if directory missing
4. **Auto-creation**: Attempt to create default directory if possible

### Settings File Structure:
```yaml
ui:
  backend: gtk  # 'gtk' or 'qt'
  window_width: 800
  window_height: 600
  floating_window: true

wallpaper:
  directory: ~/Pictures/Wallpapers  # Default wallpaper directory
  live_preview: true

theme:
  show_results_dialog: true
```

## User Experience

### First Run:
1. If `~/Pictures/Wallpapers` doesn't exist
2. Dialog: "Wallpaper Folder Not Found - Choose different folder?"
3. User can:
   - **Yes**: Open folder chooser to select directory
   - **No**: Auto-create default directory (if possible)

### Ongoing Use:
- Settings persist between sessions
- "Choose Folder" button available for changing directory
- Manual edits to `settings.yaml` respected (after restart)

## Benefits

### ✅ Simplified:
- No complex directory detection logic
- Clear default behavior
- Predictable directory resolution

### ✅ User-Controlled:
- Explicit configuration in settings file
- Easy manual editing
- User choice preserved

### ✅ Robust:
- Graceful handling of missing directories
- Fallback mechanisms
- Clear error states

### ✅ Maintainable:
- Single source of truth (settings.yaml)
- Clean separation of concerns
- UI-agnostic wallpaper management

## Migration Notes

### From Previous Version:
- Wallpaper directory auto-detection **removed**
- Default changed from `~/Pictures/wallpapers` to `~/Pictures/Wallpapers`
- Settings file now properly populated and used
- First-run experience improved with folder chooser

### For Users:
- Check `config/settings.yaml` for current settings
- Modify `wallpaper.directory` to change default folder
- Restart app for manual setting changes to take effect
