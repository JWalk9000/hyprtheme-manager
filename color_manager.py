"""
Shared color management system for both GTK and Qt UI backends.
This module provides a unified way to manage and apply color themes.
"""

from pathlib import Path
from typing import Dict


class ColorManager:
    """
    Manages color themes for both GTK and Qt backends.
    Provides methods to load pywal colors and generate UI-specific stylesheets.
    """
    
    def __init__(self):
        self.current_colors: Dict[str, str] = {}
        self.applied_colors: Dict[str, str] = {}  # Track actually applied colors
        self.load_default_colors()
        self._load_applied_colors()  # Load last applied colors
    
    def load_default_colors(self):
        """Load default colors as fallback."""
        self.current_colors = {
            'color0': '#1e1e1e',   # background
            'color1': '#ff5555',   # red
            'color2': '#50fa7b',   # green
            'color3': '#f1fa8c',   # yellow
            'color4': '#bd93f9',   # blue
            'color5': '#ff79c6',   # magenta
            'color6': '#8be9fd',   # cyan
            'color7': '#f8f8f2',   # foreground
            'color8': '#6272a4',   # bright black
            # Standard colors for UI consistency (9-15)
            'color9': '#ff4444',   # Bright Red - errors, danger
            'color10': '#44ff44',  # Bright Green - success, safe
            'color11': '#ffff44',  # Bright Yellow - warnings, caution
            'color12': '#4444ff',  # Bright Blue - info, links
            'color13': '#ff44ff',  # Bright Magenta - highlights
            'color14': '#44ffff',  # Bright Cyan - accents
            'color15': '#ffffff',  # Pure White - text, backgrounds
        }
    
    def load_pywal_colors(self) -> bool:
        """
        Load colors from pywal cache.
        Returns True if successful, False if pywal colors not found.
        """
        pywal_cache = Path.home() / '.cache' / 'wal' / 'colors.json'
        
        if not pywal_cache.exists():
            print("Pywal colors not found, using defaults")
            return False
        
        try:
            import json
            with open(pywal_cache, 'r') as f:
                pywal_data = json.load(f)
            
            # pywal stores colors as a dict with 'colors' key
            if 'colors' in pywal_data:
                self.current_colors.update(pywal_data['colors'])
                
                # Ensure positions 9-15 are reliable standard colors
                self._set_standard_colors()
                
                return True
                
        except Exception as e:
            print(f"Error loading pywal colors: {e}")
        
        return False
    
    def _set_standard_colors(self):
        """
        Set positions 9-15 to reliable standard colors for UI consistency.
        
        Standard Color Assignments:
        - color9:  #ff4444 (Bright Red)    - errors, danger, warnings
        - color10: #44ff44 (Bright Green)  - success, safe, positive actions  
        - color11: #ffff44 (Bright Yellow) - caution, pending, highlights
        - color12: #4444ff (Bright Blue)   - info, links, primary actions
        - color13: #ff44ff (Bright Magenta)- special highlights, selection
        - color14: #44ffff (Bright Cyan)   - accents, secondary actions
        - color15: #ffffff (Pure White)    - text, clean backgrounds
        
        This ensures predictable colors for UI elements while keeping
        colors 0-8 dynamic based on the wallpaper via pywal.
        """
        standard_colors = {
            'color9':  '#ff4444',  # Bright Red - errors, danger
            'color10': '#44ff44',  # Bright Green - success, safe
            'color11': '#ffff44',  # Bright Yellow - warnings, caution  
            'color12': '#4444ff',  # Bright Blue - info, links
            'color13': '#ff44ff',  # Bright Magenta - highlights
            'color14': '#44ffff',  # Bright Cyan - accents
            'color15': '#ffffff'   # Pure White - text, backgrounds
        }
        
        # Override positions 9-15 with our standard colors
        for color_key, color_value in standard_colors.items():
            self.current_colors[color_key] = color_value
        
        print("Applied standard colors to positions 9-15 for UI consistency")

    def _load_applied_colors(self):
        """Load the last actually applied colors from our own cache."""
        applied_cache = Path.home() / '.config' / 'Theme-Manager' / 'applied_colors.json'
        
        if applied_cache.exists():
            try:
                import json
                with open(applied_cache, 'r') as f:
                    self.applied_colors = json.load(f)
                print(f"Loaded applied colors cache with {len(self.applied_colors)} colors")
            except Exception as e:
                print(f"Error loading applied colors cache: {e}")
                self.applied_colors = {}
        else:
            # Initialize with current pywal colors if no cache exists
            self.applied_colors = self.get_pywal_colors_raw()
            print("Initialized applied colors from current pywal cache")

    def _save_applied_colors(self):
        """Save the currently applied colors to our own cache."""
        applied_cache = Path.home() / '.config' / 'Theme-Manager' / 'applied_colors.json'
        
        try:
            # Ensure directory exists
            applied_cache.parent.mkdir(parents=True, exist_ok=True)
            
            import json
            with open(applied_cache, 'w') as f:
                json.dump(self.applied_colors, f, indent=2)
            print(f"Saved applied colors cache with {len(self.applied_colors)} colors")
        except Exception as e:
            print(f"Error saving applied colors cache: {e}")

    def mark_colors_as_applied(self, colors: Dict[str, str]):
        """Mark these colors as actually applied to the system."""
        self.applied_colors = colors.copy()
        self._save_applied_colors()
        print("Colors marked as applied to system")

    def get_pywal_colors_raw(self) -> Dict[str, str]:
        """Get raw colors from pywal cache without any modifications."""
        pywal_cache = Path.home() / '.cache' / 'wal' / 'colors.json'
        
        if not pywal_cache.exists():
            return {}
        
        try:
            import json
            with open(pywal_cache, 'r') as f:
                pywal_data = json.load(f)
            return pywal_data.get('colors', {})
        except Exception as e:
            print(f"Error loading raw pywal colors: {e}")
            return {}

    def get_applied_colors(self) -> Dict[str, str]:
        """
        Get the currently applied system colors.
        These are the colors that were actually applied with the "Apply" button,
        not preview colors or colors from wallpaper selection.
        
        Returns:
            Dictionary of actually applied colors
        """
        return self.applied_colors.copy()

    def load_applied_colors_as_current(self) -> bool:
        """
        Load the applied system colors as current colors for UI theming.
        This ensures UIs use the actually applied colors, not preview colors.
        
        Returns:
            True if applied colors were loaded, False if using defaults
        """
        if self.applied_colors:
            self.current_colors = self.applied_colors.copy()
            print(f"Loaded {len(self.applied_colors)} applied colors as current colors")
            return True
        else:
            # Fallback to pywal colors if no applied colors exist
            return self.load_pywal_colors()

    def get_color(self, color_key: str) -> str:
        """Get a specific color by key (e.g., 'color0', 'color1')."""
        return self.current_colors.get(color_key, '#000000')
    
    def get_all_colors(self) -> Dict[str, str]:
        """Get all current colors."""
        return self.current_colors.copy()
    
    def get_semantic_colors(self) -> Dict[str, str]:
        """
        Get colors with semantic names for easier UI usage.
        This maps pywal colors to meaningful names.
        """
        return {
            # Core colors
            'background': self.get_color('color0'),
            'foreground': self.get_color('color7'),
            'foreground_dim': self.get_color('color8'),
            'foreground_bright': self.get_color('color15'),
            
            # Standard colors
            'red': self.get_color('color1'),
            'green': self.get_color('color2'),
            'yellow': self.get_color('color3'),
            'blue': self.get_color('color4'),
            'magenta': self.get_color('color5'),
            'cyan': self.get_color('color6'),
            
            # Bright variants
            'bright_red': self.get_color('color9'),
            'bright_green': self.get_color('color10'),
            'bright_yellow': self.get_color('color11'),
            'bright_blue': self.get_color('color12'),
            'bright_magenta': self.get_color('color13'),
            'bright_cyan': self.get_color('color14'),
        }
    
    def get_template_colors(self) -> Dict[str, str]:
        """
        Get colors formatted for template substitution.
        Includes both semantic names and color0-color15 for templates.
        """
        template_colors = self.current_colors.copy()
        template_colors.update(self.get_semantic_colors())
        return template_colors
    
    def generate_gtk_css(self) -> str:
        """
        Generate GTK CSS with current colors.
        This updates the style.css content with actual color values.
        """
        colors = self.get_semantic_colors()
        
        css_template = f"""
/* Pywal Color Definitions - Auto-generated */

/* Core Colors */
@define-color background {colors['background']};
@define-color foreground {colors['foreground']};
@define-color cursor {colors['foreground']};

/* Dim/Bright Variations */
@define-color foreground-dim {colors['foreground_dim']};
@define-color foreground-bright {colors['foreground_bright']};

/* Standard ANSI Colors */
@define-color color-red {colors['red']};
@define-color color-green {colors['green']};
@define-color color-yellow {colors['yellow']};
@define-color color-blue {colors['blue']};
@define-color color-magenta {colors['magenta']};
@define-color color-cyan {colors['cyan']};

/* Bright ANSI Colors */
@define-color color-bright-red {colors['bright_red']};
@define-color color-bright-green {colors['bright_green']};
@define-color color-bright-yellow {colors['bright_yellow']};
@define-color color-bright-blue {colors['bright_blue']};
@define-color color-bright-magenta {colors['bright_magenta']};
@define-color color-bright-cyan {colors['bright_cyan']};

/* Application-Specific Aliases */
@define-color window-bg @background;
@define-color window-fg @foreground;
@define-color text-primary @foreground;
@define-color text-secondary @foreground-dim;
@define-color text-accent @color-blue;
@define-color button-bg @foreground-dim;
@define-color button-fg @foreground-bright;
@define-color button-hover-bg @color-blue;
@define-color selection-bg @color-blue;
@define-color selection-fg @background;

/* GTK Widget Styling */

/* Main Window */
window {{
    background-color: @background;
    color: @foreground;
}}

/* Header Bar */
headerbar {{
    background-color: @foreground-dim;
    color: @foreground-bright;
    border-bottom: 1px solid @color-blue;
}}

/* Labels */
label {{
    color: @foreground;
}}

label.dim-label {{
    color: @foreground-dim;
}}

/* Buttons */
button {{
    background-color: @button-bg;
    color: @button-fg;
    border: 1px solid @color-blue;
    border-radius: 4px;
    padding: 8px;
}}

button:hover {{
    background-color: @button-hover-bg;
    color: @selection-fg;
}}

button:active {{
    background-color: @color-green;
    color: @background;
}}

button.suggested-action {{
    background-color: @color-blue;
    color: @background;
}}

button.suggested-action:hover {{
    background-color: @color-bright-blue;
}}

/* Frames */
frame {{
    background-color: @background;
    border: 1px solid @foreground-dim;
    border-radius: 4px;
}}

frame > border {{
    border: 1px solid @foreground-dim;
}}

/* Scroll Areas */
scrolledwindow {{
    background-color: @background;
    border: 1px solid @foreground-dim;
}}

/* Flow Box (wallpaper grid) */
flowbox {{
    background-color: @background;
}}

flowbox flowboxchild {{
    background-color: transparent;
    border: 2px solid transparent;
    border-radius: 4px;
}}

flowbox flowboxchild:selected {{
    border-color: @color-blue;
    background-color: alpha(@selection-bg, 0.3);
}}

/* Box containers */
box {{
    background-color: transparent;
}}
"""
        return css_template
    
    def generate_qt_stylesheet(self) -> str:
        """
        Generate Qt stylesheet with current colors.
        This creates QSS styles using the current color palette.
        """
        colors = self.get_semantic_colors()
        
        qss_template = f"""
/* Qt Stylesheet - Auto-generated from pywal colors */

/* Main Window */
QMainWindow {{
    background-color: {colors['background']};
    color: {colors['foreground']};
}}

/* Frames and Groups */
QFrame {{
    background-color: {colors['background']};
    color: {colors['foreground']};
    border: 1px solid {colors['foreground_dim']};
}}

/* Labels */
QLabel {{
    color: {colors['foreground']};
    background-color: transparent;
}}

/* Buttons */
QPushButton {{
    background-color: {colors['foreground_dim']};
    color: {colors['foreground_bright']};
    border: 1px solid {colors['blue']};
    padding: 8px;
    border-radius: 4px;
}}

QPushButton:hover {{
    background-color: {colors['blue']};
    color: {colors['background']};
}}

QPushButton:pressed {{
    background-color: {colors['green']};
    color: {colors['background']};
}}

QPushButton:disabled {{
    background-color: {colors['foreground_dim']};
    color: {colors['foreground_dim']};
    border: 1px solid {colors['foreground_dim']};
}}

/* Scroll Areas */
QScrollArea {{
    background-color: {colors['background']};
    border: 1px solid {colors['foreground_dim']};
}}

/* Selection and highlights */
QWidget:focus {{
    outline: 2px solid {colors['blue']};
}}
"""
        return qss_template
    
    def apply_colors_to_gtk_app(self, app):
        """
        Apply the current color scheme to a GTK application.
        This loads the CSS and applies it via a CssProvider.
        """
        try:
            from gi.repository import Gtk, Gdk
            
            css = self.generate_gtk_css()
            
            # Remove any existing providers first
            display = Gdk.Display.get_default()
            
            # Create and load CSS provider
            css_provider = Gtk.CssProvider()
            css_provider.load_from_data(css.encode('utf-8'))
            
            # Apply to all screens with high priority
            Gtk.StyleContext.add_provider_for_display(
                display, 
                css_provider, 
                Gtk.STYLE_PROVIDER_PRIORITY_USER
            )
            
            # Force a style update on all windows
            if hasattr(app, 'get_windows'):
                for window in app.get_windows():
                    if window:
                        window.queue_draw()
            
            print("Applied GTK color theme with refresh")
            return True
            
        except Exception as e:
            print(f"Error applying GTK colors: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def apply_colors_to_qt_app(self, app):
        """
        Apply the current color scheme to a Qt application.
        This generates and sets the application stylesheet.
        """
        try:
            qss = self.generate_qt_stylesheet()
            app.setStyleSheet(qss)
            print("Applied Qt color theme")
            return True
            
        except Exception as e:
            print(f"Error applying Qt colors: {e}")
            return False


    def refresh_colors_from_wallpaper(self, wallpaper_path: str) -> bool:
        """
        Generate new colors from a wallpaper using pywal.
        Returns True if successful, False otherwise.
        """
        try:
            import subprocess
            import json
            
            # Run pywal to generate colors from wallpaper
            result = subprocess.run([
                'wal', '-i', wallpaper_path, '-n'  # -n = don't set wallpaper, just generate colors
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Reload the generated colors
                return self.load_pywal_colors()
            else:
                print(f"Pywal failed: {result.stderr}")
                return False
                
        except FileNotFoundError:
            print("Pywal not found, using default colors")
            return False
        except Exception as e:
            print(f"Error generating colors from wallpaper: {e}")
            return False


# Global color manager instance
color_manager = ColorManager()
