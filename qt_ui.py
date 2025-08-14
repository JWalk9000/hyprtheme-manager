import sys
"""
PyQt6 UI backend for Theme Manager.
Provides cross-platform compatibility using Qt6.
"""

import sys
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QPushButton, QFrame, QScrollArea,
                             QGridLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from app_settings import AppSettings
from color_manager import color_manager
from wallpaper_utils import WallpaperManager

class ThemeManagerWindow(QMainWindow):
    """The main window for the Theme Manager application (Qt version)."""
    def __init__(self, settings: AppSettings, **kwargs):
        super().__init__(**kwargs)
        self.settings = settings
        
        # Configure window properties
        self.setWindowTitle("Theme Manager")
        self.setFixedSize(600, 800)
        
        # Set window to behave like a dialog
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        
        # Initialize wallpaper manager with settings
        self.wallpaper_manager = WallpaperManager(settings=self.settings)
        self.selected_wallpaper = None
        
        self.setup_ui()
        self.apply_colors()
        self.check_wallpaper_directory()

    def apply_colors(self):
        """Apply the current color theme to this window."""
        # Load pywal colors if available, otherwise use defaults
        color_manager.load_pywal_colors()
        
        # Apply colors to the Qt application
        color_manager.apply_colors_to_qt_app(QApplication.instance())

    def setup_ui(self):
        """Initializes the UI components according to the UI plan."""
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # --- Status Section ---
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(8, 8, 8, 8)
        status_layout.setSpacing(8)
        
        status_title = QLabel("Status")
        status_title.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(status_title)
        
        self.current_wallpaper_label = QLabel("Current Wallpaper: None")
        self.current_wallpaper_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        status_layout.addWidget(self.current_wallpaper_label)
        
        # Current palette will be added dynamically in update_status_display
        
        main_layout.addWidget(status_frame)

        # --- Wallpaper Selection Section ---
        wallpaper_frame = QFrame()
        wallpaper_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        wallpaper_layout = QVBoxLayout(wallpaper_frame)
        wallpaper_layout.setContentsMargins(8, 8, 8, 8)
        wallpaper_layout.setSpacing(8)
        
        wallpaper_title = QLabel("Wallpaper Selection")
        wallpaper_title.setStyleSheet("font-weight: bold;")
        wallpaper_layout.addWidget(wallpaper_title)

        # Folder selection row
        folder_row = QHBoxLayout()
        folder_label = QLabel("Folder:")
        folder_label.setMinimumWidth(60)
        self.folder_button = QPushButton("Choose Folder...")
        self.folder_button.clicked.connect(self.on_folder_button_clicked)
        
        # Show current folder
        self.folder_path_label = QLabel(str(self.wallpaper_manager.wallpaper_dir))
        self.folder_path_label.setStyleSheet("color: gray;")
        
        folder_row.addWidget(folder_label)
        folder_row.addWidget(self.folder_button)
        folder_row.addWidget(self.folder_path_label)
        folder_row.addStretch()
        wallpaper_layout.addLayout(folder_row)

                # Wallpaper grid (with scroll area)
        grid_scroll = QScrollArea()
        grid_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        grid_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        grid_scroll.setMinimumHeight(300)
        grid_scroll.setWidgetResizable(True)  # This is important!
        
        self.grid_widget = QWidget()
        self.grid_widget.setMinimumSize(500, 300)  # Ensure minimum size
        self.wallpaper_grid = QGridLayout(self.grid_widget)
        self.wallpaper_grid.setSpacing(8)
        self.wallpaper_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        # Ensure columns have proper sizing
        for col in range(3):
            self.wallpaper_grid.setColumnMinimumWidth(col, 150)
        
        grid_scroll.setWidget(self.grid_widget)
        wallpaper_layout.addWidget(grid_scroll)
        
        main_layout.addWidget(wallpaper_frame)

        # --- Color Preview Section ---
        color_frame = QFrame()
        color_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        color_layout = QVBoxLayout(color_frame)
        color_layout.setContentsMargins(8, 8, 8, 8)
        color_layout.setSpacing(8)

        color_title = QLabel("Color Preview")
        color_title.setStyleSheet("font-weight: bold;")
        color_layout.addWidget(color_title)

        self.color_preview_label = QLabel("Select a wallpaper to preview colors")
        self.color_preview_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        color_layout.addWidget(self.color_preview_label)

        # Color display toggle
        color_toggle_layout = QHBoxLayout()
        color_toggle_label = QLabel("Colors:")
        color_toggle_layout.addWidget(color_toggle_label)
        
        self.color_count_toggle = QPushButton("Show 16 Colors")
        self.color_count_toggle.setCheckable(True)
        self.color_count_toggle.clicked.connect(self.on_color_count_toggled)
        color_toggle_layout.addWidget(self.color_count_toggle)
        color_toggle_layout.addStretch()
        
        color_layout.addLayout(color_toggle_layout)

        # Color swatches - show actual colors from color manager
        # Create a container that can hold multiple rows
        self.color_swatches_container = QVBoxLayout()
        self.show_16_colors = False  # Start with 8 colors
        self.update_color_swatches()
        color_layout.addLayout(self.color_swatches_container)
        
        main_layout.addWidget(color_frame)

        # --- Action Buttons ---
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.apply_wallpaper_btn = QPushButton("Apply Wallpaper")
        self.apply_wallpaper_btn.setEnabled(False)
        self.apply_wallpaper_btn.clicked.connect(self.on_apply_wallpaper_clicked)
        button_layout.addWidget(self.apply_wallpaper_btn)
        
        self.apply_colors_btn = QPushButton("Apply Colors")
        self.apply_colors_btn.setEnabled(False)
        self.apply_colors_btn.clicked.connect(self.on_apply_colors_clicked)
        button_layout.addWidget(self.apply_colors_btn)
        
        self.apply_both_btn = QPushButton("Apply Both")
        self.apply_both_btn.setEnabled(False)
        self.apply_both_btn.clicked.connect(self.on_apply_both_clicked)
        self.apply_both_btn.setStyleSheet("QPushButton { background-color: #0066cc; color: white; font-weight: bold; }")
        button_layout.addWidget(self.apply_both_btn)
        
        # Add Copy Palette button
        self.copy_palette_btn = QPushButton("Copy Palette")
        self.copy_palette_btn.clicked.connect(self.copy_full_palette)
        button_layout.addWidget(self.copy_palette_btn)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        print("ThemeManagerWindow (Qt) UI skeleton complete.")

    def on_color_count_toggled(self):
        """Handle the color count toggle button."""
        self.show_16_colors = self.color_count_toggle.isChecked()
        if self.show_16_colors:
            self.color_count_toggle.setText("Show 8 Colors")
        else:
            self.color_count_toggle.setText("Show 16 Colors")
        self.update_color_swatches()

    def update_color_swatches(self):
        """Update the color swatches with current colors from color manager."""
        # Clear existing swatches
        while self.color_swatches_container.count() > 0:
            child = self.color_swatches_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                # Clear nested layout
                while child.layout().count() > 0:
                    nested_child = child.layout().takeAt(0)
                    if nested_child.widget():
                        nested_child.widget().deleteLater()
        
        # Get current colors
        colors = color_manager.get_all_colors()
        
        # Determine how many colors to show
        color_count = 16 if self.show_16_colors else 8
        colors_per_row = 8
        
        # Create rows of color swatches
        for row_start in range(0, color_count, colors_per_row):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(4)
            
            row_end = min(row_start + colors_per_row, color_count)
            for i in range(row_start, row_end):
                color_key = f'color{i}'
                color_value = colors.get(color_key, '#000000')
                
                swatch = QWidget()
                swatch.setFixedSize(56, 56)  # 40% larger than 40x40
                swatch.setStyleSheet(f"background-color: {color_value}; border: 1px solid #333333;")
                
                # Add click handler for copying color - fix closure issue
                def make_click_handler(color_hex, color_index):
                    def mouse_press_event(event):
                        if event.button() == Qt.MouseButton.LeftButton:
                            # Debug: print what we're actually copying
                            print(f"Copying color{color_index}: {color_hex}")
                            self.copy_color_to_clipboard(color_hex)
                    return mouse_press_event
                
                swatch.mousePressEvent = make_click_handler(color_value, i)
                row_layout.addWidget(swatch)
            
            row_layout.addStretch()
            self.color_swatches_container.addLayout(row_layout)

    def update_status_display(self):
        """Update the current wallpaper and palette status display."""
        from wallpaper_utils import get_current_wallpaper
        
        # Update current wallpaper
        current_wallpaper = get_current_wallpaper()
        if current_wallpaper:
            self.current_wallpaper_label.setText(f"Current Wallpaper: {current_wallpaper.name}")
        else:
            self.current_wallpaper_label.setText("Current Wallpaper: None")
        
        # Update current palette - create visual color swatches from APPLIED colors
        applied_colors = color_manager.get_applied_colors()
        if applied_colors:
            # Remove existing palette display if it exists
            if hasattr(self, 'current_palette_display'):
                self.current_palette_display.setParent(None)
                self.current_palette_display.deleteLater()
            
            # Create a widget to hold the palette display
            self.current_palette_display = QWidget()
            palette_layout = QHBoxLayout(self.current_palette_display)
            palette_layout.setContentsMargins(0, 0, 0, 0)
            palette_layout.setSpacing(2)
            
            # Add "Current Palette:" label
            palette_label = QLabel("Current Palette: ")
            palette_layout.addWidget(palette_label)
            
            # Show first 4 APPLIED colors as small swatches
            for i in range(4):
                color_key = f'color{i}'
                if color_key in applied_colors:
                    color_value = applied_colors[color_key]
                    
                    # Create small square swatch (font height size)
                    swatch = QWidget()
                    swatch.setFixedSize(16, 16)  # Small square, approximately font height
                    swatch.setStyleSheet(f"background-color: {color_value}; border: 0.5px solid #4a4a4a;")
                    palette_layout.addWidget(swatch)
            
            palette_layout.addStretch()
            
            # Add to the status layout
            status_layout = self.current_wallpaper_label.parent().layout()
            status_layout.addWidget(self.current_palette_display)
            
        else:
            # Fallback to text when no colors available
            if hasattr(self, 'current_palette_display'):
                self.current_palette_display.setParent(None)
                self.current_palette_display.deleteLater()
            
            self.current_palette_display = QLabel("Current Palette: None")
            status_layout = self.current_wallpaper_label.parent().layout()
            status_layout.addWidget(self.current_palette_display)

    def check_wallpaper_directory(self):
        """Check if wallpaper directory exists, show folder chooser if not."""
        if not self.wallpaper_manager.directory_exists:
            from PyQt6.QtWidgets import QMessageBox, QFileDialog
            from pathlib import Path
            
            # Show message dialog first
            msg = QMessageBox(self)
            msg.setWindowTitle("Wallpaper Folder Not Found")
            msg.setText(f"The default wallpaper directory '{self.wallpaper_manager.wallpaper_dir}' doesn't exist.")
            msg.setInformativeText("Would you like to choose a different folder?")
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg.setDefaultButton(QMessageBox.StandardButton.Yes)
            
            result = msg.exec()
            if result == QMessageBox.StandardButton.Yes:
                self.show_folder_chooser()
            else:
                # User chose No, try to create default directory
                if self.wallpaper_manager.ensure_wallpaper_directory():
                    self.folder_path_label.setText(str(self.wallpaper_manager.wallpaper_dir))
                    self.load_wallpapers()
                else:
                    # Still failed, show empty state
                    self.load_wallpapers()
        else:
            self.load_wallpapers()
        
        # Update status display and show initial colors
        self.update_status_display()
        self.update_color_swatches()  # Show current palette initially
    
    def show_folder_chooser(self):
        """Show a folder chooser dialog."""
        from PyQt6.QtWidgets import QFileDialog
        from pathlib import Path
        
        # Set initial directory to Pictures if it exists
        initial_dir = self.settings.get('wallpaper.directory', str(Path.home() / "Pictures"))
        
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Choose Wallpaper Folder",
            initial_dir
        )
        
        if folder_path:
            if self.wallpaper_manager.ensure_wallpaper_directory(folder_path):
                self.folder_path_label.setText(str(self.wallpaper_manager.wallpaper_dir))
                self.load_wallpapers()

    def load_wallpapers(self):
        """Load wallpapers into the grid."""
        # Clear existing grid
        while self.wallpaper_grid.count():
            child = self.wallpaper_grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Get wallpapers
        wallpapers = self.wallpaper_manager.get_wallpaper_files()
        
        if not wallpapers:
            # Show "no wallpapers" message
            no_wallpapers = QLabel("No wallpapers found in selected folder")
            no_wallpapers.setStyleSheet("color: gray;")
            no_wallpapers.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.wallpaper_grid.addWidget(no_wallpapers, 0, 0, 1, 3)
            return
        
        # Load all wallpapers
        for i, wallpaper_path in enumerate(wallpapers):
            try:
                wallpaper_widget = self.create_wallpaper_widget(wallpaper_path)
                if wallpaper_widget:
                    row = i // 3
                    col = i % 3
                    self.wallpaper_grid.addWidget(wallpaper_widget, row, col)
            except Exception as e:
                print(f"Error loading wallpaper {wallpaper_path}: {e}")
        
        # Update grid widget size
        self.grid_widget.adjustSize()
        print(f"Qt: Loaded {len(wallpapers)} wallpapers into grid")
    
    def create_wallpaper_widget(self, wallpaper_path):
        """Create a widget for a wallpaper in the grid."""
        from PyQt6.QtWidgets import QVBoxLayout, QSizePolicy
        from PyQt6.QtGui import QPixmap
        
        container = QWidget()
        container.setFixedSize(150, 120)
        container.setStyleSheet("border: 2px solid transparent; background-color: #f0f0f0;")
        container.wallpaper_path = wallpaper_path
        
        # Ensure the container doesn't get resized
        size_policy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        container.setSizePolicy(size_policy)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # Try to get thumbnail
        thumbnail_path = self.wallpaper_manager.get_wallpaper_thumbnail(wallpaper_path)
        
        if thumbnail_path and thumbnail_path.exists():
            try:
                # Load thumbnail image
                pixmap = QPixmap(str(thumbnail_path))
                if not pixmap.isNull():
                    image_label = QLabel()
                    scaled_pixmap = pixmap.scaled(140, 90, 
                                                Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                                                Qt.TransformationMode.SmoothTransformation)
                    image_label.setPixmap(scaled_pixmap)
                    image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    image_label.setMinimumSize(140, 90)
                    image_label.setStyleSheet("border: 1px solid #ccc;")
                    layout.addWidget(image_label)
                    
                    # Add filename label
                    name_label = QLabel(wallpaper_path.stem[:20])
                    name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    name_label.setStyleSheet("color: #333; font-size: 10px;")
                    name_label.setWordWrap(True)
                    layout.addWidget(name_label)
                else:
                    raise Exception("Failed to load pixmap")
            except Exception as e:
                print(f"Error loading thumbnail: {e}")
                # Fallback to label
                fallback = QLabel("Image\nError")
                fallback.setAlignment(Qt.AlignmentFlag.AlignCenter)
                fallback.setStyleSheet("color: gray; border: 1px solid #ccc;")
                fallback.setMinimumSize(140, 90)
                layout.addWidget(fallback)
                
                # Add filename
                name_label = QLabel(wallpaper_path.stem[:20])
                name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                name_label.setStyleSheet("color: #333; font-size: 10px;")
                layout.addWidget(name_label)
        else:
            # Fallback to filename label only
            fallback = QLabel(f"Loading...\n{wallpaper_path.stem[:15]}")
            fallback.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback.setStyleSheet("color: gray; border: 1px solid #ccc;")
            fallback.setMinimumSize(140, 100)
            fallback.setWordWrap(True)
            layout.addWidget(fallback)
        
        # Make clickable
        container.mousePressEvent = lambda event: self.on_wallpaper_selected(wallpaper_path)
        
        return container
    
    def on_folder_button_clicked(self):
        """Handle folder selection button click."""
        self.show_folder_chooser()
    
    def on_wallpaper_selected(self, wallpaper_path):
        """Handle wallpaper selection from the grid."""
        self.selected_wallpaper = wallpaper_path
        print(f"Selected wallpaper: {wallpaper_path.name}")
        
        # Update color preview label
        self.color_preview_label.setText(f"Generating colors from: {wallpaper_path.name}")
        
        # Highlight selected wallpaper
        for i in range(self.wallpaper_grid.count()):
            widget = self.wallpaper_grid.itemAt(i).widget()
            if hasattr(widget, 'wallpaper_path'):
                if widget.wallpaper_path == wallpaper_path:
                    widget.setStyleSheet("border: 2px solid blue;")
                else:
                    widget.setStyleSheet("border: 2px solid transparent;")
        
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
                self.apply_wallpaper_btn.setEnabled(True)
                self.apply_colors_btn.setEnabled(True)
                self.apply_both_btn.setEnabled(True)
                
                print(f"Generated {len(colors)} colors from wallpaper")
            else:
                self.color_preview_label.setText("Failed to generate colors from wallpaper")
                print("Failed to generate colors")
                
        except Exception as e:
            print(f"Error generating colors: {e}")
            self.color_preview_label.setText("Error generating colors")
    
    def refresh_colors(self):
        """Refresh the color theme and update all color displays."""
        # Apply new colors to the application
        color_manager.apply_colors_to_qt_app(QApplication.instance())
        
        # Update the color swatches
        self.update_color_swatches()
        
        # Update the preview label
        self.color_preview_label.setText("Colors updated from current selection")

    def refresh_colors(self):
        """Refresh the color theme and update all color displays."""
        # Apply new colors to the application
        color_manager.apply_colors_to_qt_app(QApplication.instance())
        
        # Update the color swatches
        self.update_color_swatches()
        
        # Update the preview label
        self.color_preview_label.setText("Colors updated from current selection")

    def on_apply_wallpaper_clicked(self):
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
                self.apply_wallpaper_btn.setText("Wallpaper Applied ✓")
                self.apply_wallpaper_btn.setEnabled(False)
                # Re-enable after 2 seconds
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(2000, lambda: [
                    self.apply_wallpaper_btn.setText("Apply Wallpaper"),
                    self.apply_wallpaper_btn.setEnabled(True)
                ])
            else:
                print("❌ Failed to apply wallpaper")
                
        except Exception as e:
            print(f"Error applying wallpaper: {e}")

    def on_apply_colors_clicked(self):
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
                self.apply_colors_btn.setText(f"Colors Applied ({success_count}/{total_count}) ✓")
                self.apply_colors_btn.setEnabled(False)
                # Re-enable after 2 seconds
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(2000, lambda: [
                    self.apply_colors_btn.setText("Apply Colors"),
                    self.apply_colors_btn.setEnabled(True)
                ])
            
        except Exception as e:
            print(f"Error applying colors: {e}")

    def on_apply_both_clicked(self):
        """Handle apply both button click."""
        if not self.selected_wallpaper:
            print("No wallpaper selected")
            return
        
        print("Applying both wallpaper and colors...")
        
        # First apply wallpaper
        self.on_apply_wallpaper_clicked()
        
        # Then apply colors
        self.on_apply_colors_clicked()
        
        # Update main button
        self.apply_both_btn.setText("Theme Applied ✓")
        self.apply_both_btn.setEnabled(False)
        # Re-enable after 3 seconds
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(3000, lambda: [
            self.apply_both_btn.setText("Apply Both"),
            self.apply_both_btn.setEnabled(True)
        ])

    def copy_color_to_clipboard(self, color_hex):
        """Copy a single color to clipboard."""
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(color_hex)
            print(f"Copied color to clipboard: {color_hex}")
            self.show_message(f"Copied: {color_hex}")
        except Exception as e:
            print(f"Error copying color: {e}")

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
            clipboard = QApplication.clipboard()
            clipboard.setText(clipboard_content)
            self.show_message("Full palette copied to clipboard!")
        except Exception as e:
            print(f"Error copying palette: {e}")
            self.show_message("Error copying palette")

    def show_message(self, message):
        """Show a brief message to the user."""
        print(message)  # For now, just print - could be enhanced with status bar

    def copy_color_to_clipboard(self, color_hex):
        """Copy a single color to clipboard."""
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(color_hex)
            print(f"Copied color to clipboard: {color_hex}")
        except Exception as e:
            print(f"Error copying color: {e}")

    def copy_full_palette(self):
        """Copy all current colors to clipboard in various formats."""
        colors = color_manager.get_all_colors()
        if not colors:
            print("No colors to copy")
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
            clipboard = QApplication.clipboard()
            clipboard.setText(clipboard_content)
            print("Full palette copied to clipboard!")
        except Exception as e:
            print(f"Error copying palette: {e}")


class ThemeManagerApplication(QApplication):
    """The main Qt application class."""
    def __init__(self, settings: AppSettings, **kwargs):
        super().__init__(sys.argv, **kwargs)
        self.settings = settings
        self.window = None

    def run(self):
        """Create and show the main window, then start the event loop."""
        self.window = ThemeManagerWindow(settings=self.settings)
        self.window.show()
        print("ThemeManagerApplication (Qt) activated and window presented.")
        return self.exec()


def create_app(settings: AppSettings) -> ThemeManagerApplication:
    """
    Factory function to create and return the Qt application instance.
    
    Args:
        settings: An instance of the AppSettings class.
        
    Returns:
        An instance of ThemeManagerApplication.
    """
    return ThemeManagerApplication(settings=settings)