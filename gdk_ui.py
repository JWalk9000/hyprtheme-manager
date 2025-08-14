import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio
from pathlib import Path
import json

from app_settings import AppSettings
from color_manager import color_manager
from wallpaper_utils import WallpaperManager

class ThemeManagerWindow(Gtk.ApplicationWindow):
    """The main window for the Theme Manager application."""
    def __init__(self, app, settings: AppSettings, **kwargs):
        super().__init__(application=app, **kwargs)
        self.settings = settings

        # --- Set window to behave like a dialog ---
        # This makes the window float and stay on top of its parent.
        self.set_transient_for(app.get_active_window())
        self.set_modal(True)
        # ---

        # Configure window properties
        self.set_title("Theme Manager")
        self.set_default_size(600, 800)
        self.set_resizable(False)

        # Initialize wallpaper manager with settings
        self.wallpaper_manager = WallpaperManager(settings=self.settings)
        self.selected_wallpaper = None

        self.setup_ui()
        self.apply_colors()
        self.check_wallpaper_directory()

    def apply_colors(self):
        """Apply the current color theme to this window."""
        # Load applied colors (not preview colors) for UI theming
        color_manager.load_applied_colors_as_current()
        
        # Apply colors to the entire GTK application
        color_manager.apply_colors_to_gtk_app(self.get_application())

    def setup_ui(self):
        """Initializes the UI components according to the UI plan."""
        # Main vertical container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(main_box)

        # Header Bar
        header = Gtk.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Theme Manager"))
        
        # Settings menu button
        settings_button = Gtk.Button()
        settings_button.set_icon_name("preferences-system-symbolic")
        settings_button.set_tooltip_text("Settings")
        settings_button.connect("clicked", self.on_settings_clicked)
        header.pack_end(settings_button)
        
        main_box.append(header)

        # Main content area with padding
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content_box.set_margin_top(16)
        content_box.set_margin_bottom(16)
        content_box.set_margin_start(16)
        content_box.set_margin_end(16)
        main_box.append(content_box)

        # --- Status Section ---
        status_frame = Gtk.Frame()
        status_frame.set_label("Status")
        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        status_box.set_margin_top(8)
        status_box.set_margin_bottom(8)
        status_box.set_margin_start(8)
        status_box.set_margin_end(8)
        
        self.current_wallpaper_label = Gtk.Label(label="Current Wallpaper: None")
        self.current_wallpaper_label.set_halign(Gtk.Align.START)
        status_box.append(self.current_wallpaper_label)
        
        # Current palette will be added dynamically in update_status_display
        
        status_frame.set_child(status_box)
        content_box.append(status_frame)

        # --- Wallpaper Selection Section ---
        wallpaper_frame = Gtk.Frame()
        wallpaper_frame.set_label("Wallpaper Selection")
        wallpaper_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        wallpaper_box.set_margin_top(8)
        wallpaper_box.set_margin_bottom(8)
        wallpaper_box.set_margin_start(8)
        wallpaper_box.set_margin_end(8)

        # Folder selection row
        folder_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        folder_label = Gtk.Label(label="Folder:")
        folder_label.set_size_request(60, -1)
        
        # Show current folder first, then button
        self.folder_path_label = Gtk.Label(label=str(self.wallpaper_manager.wallpaper_dir))
        self.folder_path_label.set_ellipsize(3)  # ELLIPSIZE_END
        self.folder_path_label.add_css_class("dim-label")
        
        self.folder_button = Gtk.Button(label="Choose Folder...")
        self.folder_button.connect("clicked", self.on_folder_button_clicked)
        
        folder_row.append(folder_label)
        folder_row.append(self.folder_path_label)
        folder_row.append(self.folder_button)
        wallpaper_box.append(folder_row)

        # Wallpaper grid with real content
        grid_scroll = Gtk.ScrolledWindow()
        grid_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        grid_scroll.set_min_content_height(300)
        
        self.wallpaper_grid = Gtk.FlowBox()
        self.wallpaper_grid.set_homogeneous(True)
        self.wallpaper_grid.set_max_children_per_line(3)
        self.wallpaper_grid.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.wallpaper_grid.connect("child-activated", self.on_wallpaper_selected)
        
        grid_scroll.set_child(self.wallpaper_grid)
        wallpaper_box.append(grid_scroll)
        
        wallpaper_frame.set_child(wallpaper_box)
        content_box.append(wallpaper_frame)

        # --- Color Preview Section ---
        color_frame = Gtk.Frame()
        color_frame.set_label("Color Preview")
        color_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        color_box.set_margin_top(8)
        color_box.set_margin_bottom(8)
        color_box.set_margin_start(8)
        color_box.set_margin_end(8)

        self.color_preview_label = Gtk.Label(label="Select a wallpaper to preview colors")
        self.color_preview_label.set_halign(Gtk.Align.START)
        color_box.append(self.color_preview_label)

        # Color display toggle
        color_toggle_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        color_toggle_box.set_halign(Gtk.Align.START)
        
        color_toggle_label = Gtk.Label(label="Colors:")
        color_toggle_box.append(color_toggle_label)
        
        self.color_count_toggle = Gtk.ToggleButton(label="Show 16 Colors")
        self.color_count_toggle.connect("toggled", self.on_color_count_toggled)
        color_toggle_box.append(self.color_count_toggle)
        
        color_box.append(color_toggle_box)

        # Color swatches - show actual colors from color manager
        # Create a container that can hold multiple rows
        self.color_swatches_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.show_16_colors = self.settings.get('ui.show_all_colors', False)  # Load from settings
        
        # Set initial toggle state and text to match settings
        self.color_count_toggle.set_active(self.show_16_colors)
        if self.show_16_colors:
            self.color_count_toggle.set_label("Show 8 Colors")
        else:
            self.color_count_toggle.set_label("Show 16 Colors")
            
        self.update_color_swatches()
        color_box.append(self.color_swatches_container)
        
        color_frame.set_child(color_box)
        content_box.append(color_frame)

        # --- Action Buttons ---
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_halign(Gtk.Align.CENTER)
        
        self.apply_wallpaper_btn = Gtk.Button(label="Apply Wallpaper")
        self.apply_wallpaper_btn.set_sensitive(False)
        self.apply_wallpaper_btn.connect("clicked", self.on_apply_wallpaper_clicked)
        button_box.append(self.apply_wallpaper_btn)
        
        self.apply_colors_btn = Gtk.Button(label="Apply Colors")
        self.apply_colors_btn.set_sensitive(False)
        self.apply_colors_btn.connect("clicked", self.on_apply_colors_clicked)
        button_box.append(self.apply_colors_btn)
        
        self.apply_both_btn = Gtk.Button(label="Apply Both")
        self.apply_both_btn.set_sensitive(False)
        self.apply_both_btn.connect("clicked", self.on_apply_both_clicked)
        self.apply_both_btn.add_css_class("suggested-action")
        button_box.append(self.apply_both_btn)
        
        # Add Copy Palette button
        self.copy_palette_btn = Gtk.Button(label="Copy Palette")
        self.copy_palette_btn.connect("clicked", lambda btn: self.copy_full_palette())
        button_box.append(self.copy_palette_btn)
        
        content_box.append(button_box)

        print("ThemeManagerWindow UI skeleton complete.")

    def on_color_count_toggled(self, toggle_button):
        """Handle the color count toggle button."""
        self.show_16_colors = toggle_button.get_active()
        if self.show_16_colors:
            toggle_button.set_label("Show 8 Colors")
        else:
            toggle_button.set_label("Show 16 Colors")
        
        # Save the setting
        self.settings.set('ui.show_all_colors', self.show_16_colors)
        self.settings.save_settings()
        
        self.update_color_swatches()

    def update_status_display(self):
        """Update the current wallpaper and palette status display."""
        from wallpaper_utils import get_current_wallpaper
        
        # Update current wallpaper
        current_wallpaper = get_current_wallpaper()
        if current_wallpaper:
            self.current_wallpaper_label.set_text(f"Current Wallpaper: {current_wallpaper.name}")
        else:
            self.current_wallpaper_label.set_text("Current Wallpaper: None")
        
        # Update current palette - create visual color swatches from APPLIED colors
        applied_colors = color_manager.get_applied_colors()
        if applied_colors:
            # Create a horizontal box for color swatches in status
            status_colors_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
            status_colors_box.set_halign(Gtk.Align.START)
            
            # Add "Current Palette:" label
            palette_label = Gtk.Label(label="Current Palette: ")
            status_colors_box.append(palette_label)
            
            # Show first 4 APPLIED colors as small swatches
            for i in range(4):
                color_key = f'color{i}'
                if color_key in applied_colors:
                    color_value = applied_colors[color_key]
                    
                    # Create small square swatch (font height size)
                    swatch = Gtk.DrawingArea()
                    swatch.set_size_request(16, 16)  # Small square, approximately font height
                    
                    # Parse color value to RGB
                    try:
                        hex_color = color_value.lstrip('#')
                        r = int(hex_color[0:2], 16) / 255.0
                        g = int(hex_color[2:4], 16) / 255.0
                        b = int(hex_color[4:6], 16) / 255.0
                        
                        def make_status_draw_func(red, green, blue):
                            def draw_status_swatch(area, cr, width, height, user_data=None):
                                # Fill with the color
                                cr.set_source_rgb(red, green, blue)
                                cr.rectangle(0, 0, width, height)
                                cr.fill()
                                
                                # Add thin border
                                cr.set_source_rgb(0.3, 0.3, 0.3)
                                cr.set_line_width(0.5)
                                cr.rectangle(0, 0, width, height)
                                cr.stroke()
                            return draw_status_swatch
                        
                        swatch.set_draw_func(make_status_draw_func(r, g, b))
                        status_colors_box.append(swatch)
                        
                    except Exception as e:
                        print(f"Error creating status swatch for {color_value}: {e}")
            
            # Replace the current palette label with the color swatch box
            # First remove the existing label if it exists
            if hasattr(self, 'current_palette_display'):
                self.current_palette_display.get_parent().remove(self.current_palette_display)
            
            # Add the new color swatch box
            self.current_palette_display = status_colors_box
            # Find the status box and add after wallpaper label
            status_box = self.current_wallpaper_label.get_parent()
            status_box.append(self.current_palette_display)
            
        else:
            # Fallback to text when no colors available
            if hasattr(self, 'current_palette_display'):
                self.current_palette_display.get_parent().remove(self.current_palette_display)
            
            # Add simple text label
            self.current_palette_display = Gtk.Label(label="Current Palette: None")
            self.current_palette_display.set_halign(Gtk.Align.START)
            status_box = self.current_wallpaper_label.get_parent()
            status_box.append(self.current_palette_display)

    def update_color_swatches(self, show_current_palette=True):
        """
        Update the color swatches.
        
        Args:
            show_current_palette: If True, show current palette colors. If False, show gray placeholders.
        """
        # Clear existing swatches
        child = self.color_swatches_container.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.color_swatches_container.remove(child)
            child = next_child
        
        if show_current_palette:
            # Get current colors from color manager
            colors = color_manager.get_all_colors()
        else:
            # Show gray placeholders
            colors = {f'color{i}': '#808080' for i in range(16)}  # Gray colors
        
        # Determine how many colors to show
        color_count = 16 if self.show_16_colors else 8
        colors_per_row = 8
        
        # Create rows of color swatches
        for row_start in range(0, color_count, colors_per_row):
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            row_box.set_halign(Gtk.Align.START)
            
            row_end = min(row_start + colors_per_row, color_count)
            for i in range(row_start, row_end):
                color_key = f'color{i}'
                color_value = colors.get(color_key, '#808080')  # Default to gray
                
                # Use DrawingArea for direct color rendering
                swatch = Gtk.DrawingArea()
                swatch.set_size_request(56, 56)
                
                # Parse color value to RGB
                try:
                    # Remove # if present
                    hex_color = color_value.lstrip('#')
                    # Convert to RGB values (0-1 range for Cairo)
                    r = int(hex_color[0:2], 16) / 255.0
                    g = int(hex_color[2:4], 16) / 255.0
                    b = int(hex_color[4:6], 16) / 255.0
                    
                    # Set the draw function
                    def make_draw_func(red, green, blue):
                        def draw_swatch(area, cr, width, height, user_data=None):
                            # Fill with the color
                            cr.set_source_rgb(red, green, blue)
                            cr.rectangle(0, 0, width, height)
                            cr.fill()
                            
                            # Add border
                            cr.set_source_rgb(0.2, 0.2, 0.2)  # Dark gray border
                            cr.set_line_width(1)
                            cr.rectangle(0, 0, width, height)
                            cr.stroke()
                        return draw_swatch
                    
                    swatch.set_draw_func(make_draw_func(r, g, b))
                    
                    # Add click handler for copying color
                    def make_click_handler(color_hex):
                        def on_click(gesture, n_press, x, y):
                            try:
                                # Copy to clipboard
                                clipboard = self.get_clipboard()
                                clipboard.set(color_hex)
                                print(f"Copied color to clipboard: {color_hex}")
                                
                                # Show brief notification (you could enhance this with a toast)
                                self.show_message(f"Copied: {color_hex}")
                            except Exception as e:
                                print(f"Error copying color: {e}")
                        return on_click
                    
                    # Create gesture controller for click
                    click_gesture = Gtk.GestureClick()
                    click_gesture.connect("pressed", make_click_handler(color_value))
                    swatch.add_controller(click_gesture)
                    
                except Exception as e:
                    print(f"Error creating swatch for {color_value}: {e}")
                    # Fallback: create a simple gray box
                    def draw_fallback(area, cr, width, height, user_data=None):
                        cr.set_source_rgb(0.5, 0.5, 0.5)
                        cr.rectangle(0, 0, width, height)
                        cr.fill()
                    swatch.set_draw_func(draw_fallback)
                
                row_box.append(swatch)
            
            self.color_swatches_container.append(row_box)

    def show_message(self, message):
        """Show a brief message to the user."""
        print(message)  # For now, just print - could be enhanced with toast notifications

    def copy_full_palette(self):
        """Copy all current colors to clipboard in various formats."""
        colors = color_manager.get_all_colors()
        if not colors:
            self.show_message("No colors to copy")
            return
        
        # Format as both hex list and JSON
        hex_list = [colors.get(f'color{i}', '#000000') for i in range(16)]
        json_format = {f'color{i}': colors.get(f'color{i}', '#000000') for i in range(16)}
        
        # Create formatted clipboard content
        clipboard_content = f"""# Theme Manager Color Palette
Hex Colors: {', '.join(hex_list)}

JSON Format:
{json.dumps(json_format, indent=2)}

Individual Colors:
{chr(10).join([f'color{i}: {colors.get(f"color{i}", "#000000")}' for i in range(16)])}
"""
        
        try:
            clipboard = self.get_clipboard()
            clipboard.set(clipboard_content)
            self.show_message("Full palette copied to clipboard!")
        except Exception as e:
            print(f"Error copying palette: {e}")
            self.show_message("Error copying palette")

    def refresh_colors(self):
        """Refresh the color theme and update all color displays."""
        # Apply new colors to the application
        color_manager.apply_colors_to_gtk_app(self.get_application())
        
        # Update the color swatches
        self.update_color_swatches()
        
        # Force a redraw of the entire window
        self.queue_draw()
        
        # Update the preview label
        self.color_preview_label.set_text("Colors updated from current selection")

    def check_wallpaper_directory(self):
        """Check if wallpaper directory exists, show folder chooser if not."""
        if not self.wallpaper_manager.directory_exists:
            # Show message dialog first
            dialog = Gtk.MessageDialog(
                transient_for=self,
                modal=True,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK_CANCEL,
                text="Wallpaper Folder Not Found"
            )
            dialog.set_secondary_text(
                f"The default wallpaper directory '{self.wallpaper_manager.wallpaper_dir}' "
                "doesn't exist. Would you like to choose a different folder?"
            )
            
            dialog.connect("response", self.on_directory_dialog_response)
            dialog.present()
        else:
            self.load_wallpapers()
        
        # Update status display and show initial gray colors
        self.update_status_display()
        self.update_color_swatches(show_current_palette=True)  # Show current palette initially
    
    def on_directory_dialog_response(self, dialog, response):
        """Handle the response from the directory info dialog."""
        dialog.destroy()
        
        if response == Gtk.ResponseType.OK:
            # Show folder chooser
            self.show_folder_chooser()
        else:
            # User cancelled, try to create default directory
            if self.wallpaper_manager.ensure_wallpaper_directory():
                self.folder_path_label.set_text(str(self.wallpaper_manager.wallpaper_dir))
                self.load_wallpapers()
            else:
                # Still failed, show empty state
                self.load_wallpapers()
    
    def show_folder_chooser(self):
        """Show a folder chooser dialog."""
        dialog = Gtk.FileDialog()
        dialog.set_title("Choose Wallpaper Folder")
        
        # Set initial folder to Pictures if it exists
        pictures_folder = self.settings.get('wallpaper.directory', str(Path.home() / "Pictures"))
        if Path(pictures_folder).exists():
            dialog.set_initial_folder(Gio.File.new_for_path(pictures_folder))
        
        dialog.select_folder(self, None, self.on_folder_selected)
    
    def on_folder_selected(self, dialog, result):
        """Handle folder selection."""
        try:
            folder = dialog.select_folder_finish(result)
            if folder:
                folder_path = folder.get_path()
                # Use same pattern as Qt - save setting and refresh
                self.settings.set('wallpaper.directory', folder_path)
                self.settings.save_settings()
                
                # Update wallpaper manager to use new directory
                self.wallpaper_manager.set_wallpaper_directory(folder_path)
                
                # Update the display
                self.folder_path_label.set_text(str(self.wallpaper_manager.wallpaper_dir))
                
                # Refresh using same method as color toggle
                self.load_wallpapers()
        except Exception as e:
            print(f"Error selecting folder: {e}")

    def load_wallpapers(self):
        """Load wallpapers into the grid."""
        # Clear existing grid
        while True:
            child = self.wallpaper_grid.get_first_child()
            if child is None:
                break
            self.wallpaper_grid.remove(child)
        
        # Get wallpapers
        wallpapers = self.wallpaper_manager.get_wallpaper_files()
        
        if not wallpapers:
            # Show "no wallpapers" message
            no_wallpapers = Gtk.Label(label="No wallpapers found in selected folder")
            no_wallpapers.add_css_class("dim-label")
            self.wallpaper_grid.append(no_wallpapers)
            return
        
        # Load all wallpapers
        for wallpaper_path in wallpapers:
            try:
                wallpaper_widget = self.create_wallpaper_widget(wallpaper_path)
                if wallpaper_widget:
                    self.wallpaper_grid.append(wallpaper_widget)
            except Exception as e:
                print(f"Error loading wallpaper {wallpaper_path}: {e}")
    
    def create_wallpaper_widget(self, wallpaper_path):
        """Create a widget for a wallpaper in the grid."""
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        container.set_size_request(150, 120)
        
        # Try to get thumbnail
        thumbnail_path = self.wallpaper_manager.get_wallpaper_thumbnail(wallpaper_path)
        
        if thumbnail_path and thumbnail_path.exists():
            try:
                # Load thumbnail image
                image = Gtk.Picture.new_for_filename(str(thumbnail_path))
                image.set_size_request(140, 90)
                image.set_content_fit(Gtk.ContentFit.COVER)
                container.append(image)
                
                # Add filename label below image
                name_label = Gtk.Label(label=wallpaper_path.stem[:20])
                name_label.set_wrap(True)
                name_label.set_max_width_chars(20)
                name_label.set_ellipsize(3)  # ELLIPSIZE_END
                name_label.set_size_request(140, 25)
                container.append(name_label)
            except Exception as e:
                print(f"Error loading thumbnail: {e}")
                # Fallback to label
                fallback = Gtk.Label(label="Image\nError")
                fallback.set_size_request(140, 90)
                fallback.add_css_class("dim-label")
                container.append(fallback)
                
                # Add filename
                name_label = Gtk.Label(label=wallpaper_path.stem[:20])
                name_label.set_size_request(140, 25)
                container.append(name_label)
        else:
            # Fallback to filename label
            fallback = Gtk.Label(label=f"Loading...\n{wallpaper_path.stem[:15]}")
            fallback.set_size_request(140, 90)
            fallback.add_css_class("dim-label")
            container.append(fallback)
            
            # Add filename below
            name_label = Gtk.Label(label=wallpaper_path.stem[:20])
            name_label.set_size_request(140, 25)
            container.append(name_label)
        
        # Store wallpaper path as data
        container.wallpaper_path = wallpaper_path
        
        return container
    
    def on_folder_button_clicked(self, button):
        """Handle folder selection button click."""
        self.show_folder_chooser()
    
    def on_wallpaper_selected(self, flowbox, child):
        """Handle wallpaper selection from the grid."""
        if hasattr(child.get_child(), 'wallpaper_path'):
            wallpaper_path = child.get_child().wallpaper_path
            self.selected_wallpaper = wallpaper_path
            print(f"Selected wallpaper: {wallpaper_path.name}")
            
            # Update color preview label
            self.color_preview_label.set_text(f"Generating colors from: {wallpaper_path.name}")
            
            # Generate colors in background
            self.generate_colors_from_wallpaper(wallpaper_path)
    
    def generate_colors_from_wallpaper(self, wallpaper_path):
        """Generate colors from selected wallpaper and update UI."""
        try:
            # Get colors for wallpaper (this may take a moment)
            colors = self.wallpaper_manager.get_wallpaper_colors(wallpaper_path)
            
            if colors:
                # Update color manager with new colors
                color_manager.current_colors.update(colors)
                
                # Refresh the UI colors
                self.refresh_colors()
                
                # Update status display with new palette
                self.update_status_display()
                
                # Enable apply buttons
                self.apply_wallpaper_btn.set_sensitive(True)
                self.apply_colors_btn.set_sensitive(True)
                self.apply_both_btn.set_sensitive(True)
                
                print(f"Generated {len(colors)} colors from wallpaper")
            else:
                self.color_preview_label.set_text("Failed to generate colors from wallpaper")
                print("Failed to generate colors")
                
        except Exception as e:
            print(f"Error generating colors: {e}")
            self.color_preview_label.set_text("Error generating colors")

    def on_apply_wallpaper_clicked(self, button):
        """Handle wallpaper apply button click."""
        if not self.selected_wallpaper:
            print("No wallpaper selected")
            return
        
        print(f"Applying wallpaper: {self.selected_wallpaper}")
        
        try:
            from wallpaper_utils import set_wallpaper
            success = set_wallpaper(self.selected_wallpaper)
            
            if success:
                print("✅ Wallpaper applied successfully")
                # Update status display to reflect the change
                self.update_status_display()
                # Update button to show success
                button.set_label("Wallpaper Applied ✓")
                button.set_sensitive(False)
                # Re-enable after 2 seconds
                def reset_button():
                    button.set_label("Apply Wallpaper")
                    button.set_sensitive(True)
                    return False
                from gi.repository import GLib
                GLib.timeout_add_seconds(2, reset_button)
            else:
                print("❌ Failed to apply wallpaper")
                
        except Exception as e:
            print(f"Error applying wallpaper: {e}")

    def on_apply_colors_clicked(self, button):
        """Handle colors apply button click."""
        if not self.selected_wallpaper:
            print("No wallpaper selected (needed for colors)")
            return
        
        print("Applying colors to all applications...")
        
        try:
            from theme_plugins import plugin_manager
            
            # Get current colors
            colors = color_manager.get_template_colors()
            
            # Apply to all available applications
            results = plugin_manager.apply_theme_to_all(colors)
            
            # Mark these colors as applied to the system
            color_manager.mark_colors_as_applied(color_manager.get_all_colors())
            
            # Update status display to show the newly applied colors
            self.update_status_display()
            
            # Show results
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            
            print(f"Applied colors to {success_count}/{total_count} applications")
            
            # Update button
            if success_count > 0:
                button.set_label(f"Colors Applied ({success_count}/{total_count}) ✓")
                button.set_sensitive(False)
                # Re-enable after 2 seconds
                def reset_button():
                    button.set_label("Apply Colors")
                    button.set_sensitive(True)
                    return False
                from gi.repository import GLib
                GLib.timeout_add_seconds(2, reset_button)
            
        except Exception as e:
            print(f"Error applying colors: {e}")

    def on_apply_both_clicked(self, button):
        """Handle apply both button click."""
        if not self.selected_wallpaper:
            print("No wallpaper selected")
            return
        
        print("Applying both wallpaper and colors...")
        
        # First apply wallpaper
        self.on_apply_wallpaper_clicked(self.apply_wallpaper_btn)
        
        # Then apply colors
        self.on_apply_colors_clicked(self.apply_colors_btn)
        
        # Update main button
        button.set_label("Theme Applied ✓")
        button.set_sensitive(False)
        # Re-enable after 3 seconds
        def reset_button():
            button.set_label("Apply Both")
            button.set_sensitive(True)
            return False
        from gi.repository import GLib
        GLib.timeout_add_seconds(3, reset_button)

    def on_settings_clicked(self, button):
        """Show the settings dialog."""
        dialog = SettingsDialog(self.settings, self)
        dialog.present()


class SettingsDialog(Gtk.Window):
    """Settings/Preferences dialog for Theme Manager."""
    
    def __init__(self, settings: AppSettings, parent=None):
        super().__init__()
        self.settings = settings
        self.parent_window = parent
        
        self.set_title("Theme Manager Settings")
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_default_size(500, 600)
        self.set_resizable(False)
        
        # Keep on top of parent window
        if parent:
            self.set_transient_for(parent)
            self.set_modal(True)
        
        self.setup_ui()
        self.load_current_settings()
    
    def setup_ui(self):
        """Setup the settings dialog UI."""
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(main_box)
        
        # Header bar for dialog
        header = Gtk.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Settings"))
        
        # Cancel button
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda btn: self.close())
        header.pack_start(cancel_button)
        
        # Save button
        save_button = Gtk.Button(label="Save")
        save_button.add_css_class("suggested-action")
        save_button.connect("clicked", self.on_save_clicked)
        header.pack_end(save_button)
        
        main_box.append(header)
        
        # Content area with padding
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content_box.set_margin_top(16)
        content_box.set_margin_bottom(16)
        content_box.set_margin_start(16)
        content_box.set_margin_end(16)
        main_box.append(content_box)
        
        # General Settings
        general_frame = Gtk.Frame()
        general_frame.set_label("General Settings")
        general_grid = Gtk.Grid()
        general_grid.set_margin_top(8)
        general_grid.set_margin_bottom(8)
        general_grid.set_margin_start(8)
        general_grid.set_margin_end(8)
        general_grid.set_column_spacing(12)
        general_grid.set_row_spacing(12)
        
        # Wallpaper Directory
        general_grid.attach(Gtk.Label(label="Wallpaper Directory:", halign=Gtk.Align.END), 0, 0, 1, 1)
        wallpaper_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.wallpaper_dir_label = Gtk.Label()
        self.wallpaper_dir_label.set_ellipsize(3)  # ELLIPSIZE_END
        wallpaper_browse_btn = Gtk.Button(label="Browse...")
        wallpaper_browse_btn.connect("clicked", self.on_browse_wallpaper_directory)
        wallpaper_box.append(self.wallpaper_dir_label)
        wallpaper_box.append(wallpaper_browse_btn)
        general_grid.attach(wallpaper_box, 1, 0, 1, 1)
        
        # UI Backend
        general_grid.attach(Gtk.Label(label="UI Backend:", halign=Gtk.Align.END), 0, 1, 1, 1)
        self.ui_backend_combo = Gtk.ComboBoxText()
        self.ui_backend_combo.append("gtk", "GTK")
        self.ui_backend_combo.append("qt", "Qt")
        general_grid.attach(self.ui_backend_combo, 1, 1, 1, 1)
        
        # Checkboxes
        self.floating_window_check = Gtk.CheckButton(label="Floating Window")
        general_grid.attach(self.floating_window_check, 1, 2, 1, 1)
        
        self.show_results_dialog_check = Gtk.CheckButton(label="Show Results Dialog")
        general_grid.attach(self.show_results_dialog_check, 1, 3, 1, 1)
        
        self.show_all_colors_check = Gtk.CheckButton(label="Show 16 Colors (vs 8)")
        self.show_all_colors_check.connect("toggled", self.on_show_all_colors_changed)
        general_grid.attach(self.show_all_colors_check, 1, 4, 1, 1)
        
        self.live_preview_check = Gtk.CheckButton(label="Live Preview")
        general_grid.attach(self.live_preview_check, 1, 5, 1, 1)
        
        general_frame.set_child(general_grid)
        content_box.append(general_frame)
        
        # Managed Apps
        apps_frame = Gtk.Frame()
        apps_frame.set_label("Managed Applications")
        apps_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        apps_box.set_margin_top(8)
        apps_box.set_margin_bottom(8)
        apps_box.set_margin_start(8)
        apps_box.set_margin_end(8)
        
        # Create checkboxes for each managed app
        self.app_checkboxes = {}
        managed_apps = self.settings.get('managed_apps', {})
        
        for app_name, app_config in managed_apps.items():
            checkbox = Gtk.CheckButton(label=f"{app_name.title()} ({app_config.get('location', 'Unknown')})")
            checkbox.set_active(app_config.get('enabled', True))
            self.app_checkboxes[app_name] = checkbox
            apps_box.append(checkbox)
        
        apps_frame.set_child(apps_box)
        content_box.append(apps_frame)
    
    def load_current_settings(self):
        """Load current settings into the form."""
        # Wallpaper directory
        wallpaper_dir = self.settings.get('wallpaper.directory', '~/Pictures/Wallpapers')
        self.wallpaper_dir_label.set_text(str(wallpaper_dir))
        
        # UI Backend
        backend = self.settings.get('ui.backend', 'gtk')
        self.ui_backend_combo.set_active_id(backend)
        
        # Checkboxes
        self.floating_window_check.set_active(self.settings.get('ui.floating_window', True))
        self.show_results_dialog_check.set_active(self.settings.get('theme.show_results_dialog', True))
        self.show_all_colors_check.set_active(self.settings.get('ui.show_all_colors', True))
        self.live_preview_check.set_active(self.settings.get('wallpaper.live_preview', True))
    
    def on_browse_wallpaper_directory(self, button):
        """Open file dialog to select wallpaper directory."""
        dialog = Gtk.FileDialog()
        dialog.set_title("Select Wallpaper Directory")
        
        def on_response(source, result):
            try:
                folder = dialog.select_folder_finish(result)
                if folder:
                    directory = folder.get_path()
                    self.wallpaper_dir_label.set_text(directory)
                    
                    # Use same pattern as Qt - save setting and refresh
                    self.settings.set('wallpaper.directory', directory)
                    self.settings.save_settings()
                    
                    # Apply the change immediately to the main window
                    parent = self.get_transient_for()
                    if parent and hasattr(parent, 'wallpaper_manager') and hasattr(parent, 'load_wallpapers'):
                        # Update wallpaper manager to use new directory
                        parent.wallpaper_manager.set_wallpaper_directory(directory)
                        
                        # Update main window display
                        parent.folder_path_label.set_text(str(parent.wallpaper_manager.wallpaper_dir))
                        
                        # Refresh using same method as color toggle
                        parent.load_wallpapers()
            except Exception as e:
                print(f"Error selecting directory: {e}")
        
        dialog.select_folder(self, None, on_response)

    def on_show_all_colors_changed(self, check_button):
        """Handle live change of show all colors setting."""
        checked = check_button.get_active()
        
        # Save the setting immediately
        self.settings.set('ui.show_all_colors', checked)
        self.settings.save_settings()
        
        # Apply the change to the main window if it exists
        parent = self.get_transient_for()
        if parent and hasattr(parent, 'show_16_colors') and hasattr(parent, 'update_color_swatches'):
            # Update main window state
            parent.show_16_colors = checked
            
            # Update the toggle button text and state
            if hasattr(parent, 'color_count_toggle'):
                parent.color_count_toggle.set_active(checked)
                if checked:
                    parent.color_count_toggle.set_label("Show 8 Colors")
                else:
                    parent.color_count_toggle.set_label("Show 16 Colors")
            
            # Refresh the color swatches display
            parent.update_color_swatches()
    
    def on_save_clicked(self, button):
        """Save settings and close dialog."""
        # Save basic settings
        self.settings.set('wallpaper.directory', self.wallpaper_dir_label.get_text())
        self.settings.set('ui.backend', self.ui_backend_combo.get_active_id())
        self.settings.set('ui.floating_window', self.floating_window_check.get_active())
        self.settings.set('theme.show_results_dialog', self.show_results_dialog_check.get_active())
        self.settings.set('ui.show_all_colors', self.show_all_colors_check.get_active())
        self.settings.set('wallpaper.live_preview', self.live_preview_check.get_active())
        
        # Save managed apps settings
        for app_name, checkbox in self.app_checkboxes.items():
            self.settings.set(f'managed_apps.{app_name}.enabled', checkbox.get_active())
        
        # Save to file
        self.settings.save_settings()
        
        # Refresh parent window if possible
        if self.parent_window and hasattr(self.parent_window, 'check_wallpaper_directory'):
            self.parent_window.check_wallpaper_directory()
            self.parent_window.load_wallpapers()
        
        self.close()


class ThemeManagerApplication(Gtk.Application):
    """The main GTK application class."""
    def __init__(self, settings: AppSettings, **kwargs):
        # The application ID is still useful for D-Bus and identification
        super().__init__(application_id="Theme-Manager", **kwargs)
        self.settings = settings

    def do_activate(self):
        """Called when the application is activated."""
        win = self.props.active_window
        if not win:
            win = ThemeManagerWindow(app=self, settings=self.settings)
        win.present()
        print("ThemeManagerApplication activated and window presented.")


def create_app(settings: AppSettings) -> ThemeManagerApplication:
    """
    Factory function to create and return the GTK application instance.
    
    Args:
        settings: An instance of the AppSettings class.
        
    Returns:
        An instance of ThemeManagerApplication.
    """
    return ThemeManagerApplication(settings=settings)
