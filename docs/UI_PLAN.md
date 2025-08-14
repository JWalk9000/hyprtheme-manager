# Theme Manager UI Plan (GTK first, Qt-ready)

## Goals
- Keep core logic UI-agnostic; expose services for any UI backend.
- Provide a modern UX with responsive layout and clear workflows.
- Make wallpaper → colors → theme application fast, transparent, and undo-friendly.

## Architecture Overview
- Core modules
  - `app_settings.AppSettings`: UI-agnostic settings (selected backend, layout sizes, etc.).
  - `wallpaper_utils`: Filesystem + wallpaper helpers (dir, list, apply, preview path), pywal colors read.
  - `color_cache`: Isolated pywal generation for previews; YAML cache at `~/.config/Theme-Manager/colors_cache.yaml`.
  - `plugin_manager`: Apply colors to configured apps (API already exists).
- Backends
  - GTK: `gdk_ui.create_app(settings, services)` returns `ThemeManagerApplication` (Adw.Application).
  - Qt: `qt_ui.create_app(settings, services)` stub with same interface (to implement later).
- main: Selects backend (`--ui` or `settings.yaml`), builds services, calls backend factory.

## Decisions (from user feedback)
- Working folder: user selects a single active wallpaper folder at a time; app uses that folder for listing, caching, and previews. Switching the folder is supported at any time.
- Thumbnails: at a minimum window width of ~600px, show 3 tiles per row. Each tile is ~100–120px wide (content area), preserves image aspect ratio, and includes the filename and a row of mini color swatches below the image.
- Live preview: supported exactly as intended; generate colors and preview without permanently applying theme unless confirmed.
- Default plugins: only the UI framework in use (GTK when running GTK UI; Qt when running Qt UI). Users enable others in settings.
- Results dialog: show per-plugin success/failure dialog is configurable; enabled for debugging, disabled for normal usage.
- Notifications: use unobtrusive in-window notifications (GTK: Adw.ToastOverlay; we’ll refer to them as "notifications" here for clarity).
- Layout: single-page flow for wallpaper and color theme. Future tabs may be added for additional UI elements.
- Shortcuts: no additional shortcuts beyond the basics for now.

## Windows and Navigation
- Main Window (ThemeManagerWindow)
  - Header Bar
    - App title
    - Menu: Preferences (Settings), Plugins, Download Wallpapers
    - Exit Button
  - Content Layout (single page for MVP)
    1) Status Section (top)
       - Current wallpaper name
       - Current theme status (active/inactive)
       - Plugins enabled count and list
    2) Wallpaper Section
       - Directory row (shows active folder + choose button)
       - Scrollable Grid of thumbnails (scrollable). At ≥600px, 3 columns; reflow responsively at larger widths
       - Cache progress bar (hidden unless active)
    3) Colors Section
       - Current Colors (from pywal)
       - Preview Colors (shows all grey until new wallpaper is selected)
       - Actions: Copy Palette (Colors)
    4) Action Buttons
       - Primary actions: Apply Theme, Apply Colors, Apply Wallpaper

- Dialogs
  - Preferences (AppConfigWindow): wallpaper folder selection, UI backend, window behavior, debugging options (results dialog toggle).
  - Plugins (PluginConfigWindow): enable/disable, per-plugin config (future).
  - GTK Theme Selection (GtkThemeSelectionDialog): helper for GTK theme matching.
  - Wallpaper Download (WallpaperDownloadWindow): curated repos (future real download).

## Data Flow and Services
- Servicespassed to UI
  - color_cache
    - `is_wallpaper_cached(name_or_path)`
    - `get_cached_colors(name_or_path)`
    - `cache_wallpaper_colors(name_or_path, path)`
    - `scan_and_cache_missing_wallpapers([names])`
    - `generate_preview_colors_cached(name_or_path, path)`
  - plugin_manager
- UI retrieves wallpapers via `wallpaper_utils.list_wallpapers()` and builds the grid for the active folder.
- Selecting a wallpaper triggers background preview generation using `color_cache.generate_preview_colors_cached`.
- Applying colors triggers `plugin_manager.apply_themes(colors)`.
- Applying wallpaper triggers `wallpaper_utils.apply_wallpaper()` or `set_wallpaper_swww()`.

## Startup Workflow
1) Load settings (`AppSettings`).
2) Ensure selected wallpapers folder exists (`setup_wallpapers_dir`) or prompt to choose.
3) Load wallpaper list from the active folder and populate grid.
4) Read current colors from pywal and populate Current Colors section.
5) Optionally scan/cache missing wallpapers in background and update indicators.

## Wallpaper Section (GTK implementation details)
- Grid: `Gtk.FlowBox` inside `Gtk.ScrolledWindow`.
  - Tile content:
    - Thumbnail image (keep aspect ratio; fit width ~100–120px)
    - Filename label (ellipsize if long)
    - Swatch row: 6–8 small squares from cached colors (use preview cache; gray placeholders until available)
    - Cache indicator (success/warning icon) if needed
  - FlowBox settings: max_children_per_line dynamic; at ≥600px width use 3 columns minimum. Recalculate on window resize.
  - Preview: optional button/double-click to open external preview (feh), non-blocking.
- Background tasks
  - Cache generation thread with progress bar; uses `GLib.idle_add` to update UI.
  - Remove entries from cache if files were deleted.

## Colors Section
- Preview Colors: 8 swatches built from preview colors dict (color0..color7).
- Current Colors: read from `~/.cache/wal/colors.json`.
- Copy buttons: copy single swatch (on click) or all current colors to clipboard.
- Live preview: supported. Use isolated pywal for preview generation, only apply system-wide on confirmation.

## Theme Application
- Wallpaper-only: set wallpaper (show notification on success/failure).
- Colors-only: run pywal (non-isolated for real apply), then apply plugins.
- Full theme: set wallpaper, run pywal (real), apply plugins, suggest GTK theme via brightness heuristic.
- Results dialog: show per-plugin results when the debugging toggle is enabled; otherwise rely on notifications.

## Preferences
- Wallpaper folder chooser (sets active folder; triggers list refresh).
- UI backend selector: gtk/qt.
- Window behavior (width/height/floating) saved back to `AppSettings`.
- Debugging: toggle for per-plugin results dialog.

## Background and Error Handling
- Use `threading.Thread(daemon=True)` for long-running work.
- Communicate back via `GLib.idle_add`.
- Wrap subprocess calls; capture stderr; display concise notifications.

## Accessibility and Keyboard
- Ensure labels for buttons and images.
- Arrow navigation in FlowBox.
- Basic shortcuts only for now (copy/apply as implemented by widgets).

## Style and Theming
- Resolve Adwaita warning: use `Adw.StyleManager.get_default().set_color_scheme(...)` for dark/light.
- Keep spacing/sizing from `AppSettings` to allow easy tweaks.

## Caching Strategy (implementation notes)
- Colors: store by absolute wallpaper path to support switching folders without collisions. YAML at `~/.config/Theme-Manager/colors_cache.yaml`.
- Thumbnails: store in `~/.cache/Theme-Manager/thumbs/` using a hash of absolute path + mtime to refresh when changed. Generate asynchronously.
- Tile swatches use cached colors when available; otherwise display placeholders and update when ready.

## Implementation Mapping (current code)
- `gdk_ui.ThemeManagerApplication` and `create_app` exist.
- `ThemeManagerWindow.setup_ui` to implement: sections, grid, signals, notifications, and resize behavior for 3 columns at ≥600px.
- Utilities exist in `wallpaper_utils` and `color_cache` for core workflows; adjust color_cache keys to absolute paths.
- `main.py` selects backend and launches.

## MVP Checklist
- [ ] Load wallpapers and render grid with cache indicators and swatch rows
- [ ] Select wallpaper → generate preview colors (background) → display swatches
- [ ] Apply wallpaper-only
- [ ] Apply colors-only (real pywal + plugins)
- [ ] Apply full theme (wallpaper + colors + plugins)
- [ ] Preferences dialog saves wallpaper folder and UI backend + debugging toggle
- [ ] Notifications and optional results dialog for major actions

## Follow-ups
- I will update `color_cache` to key by absolute path and add a thumbnail cache helper.
- I will implement the GTK grid tiles (image + filename + swatches), folder chooser, and background cache/update flow.
