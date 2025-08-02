#!/usr/bin/env python3

import sys
import os
import gi
import subprocess
import threading
import yaml
from pathlib import Path

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, Gdk, GLib

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config_manager import load_theme_manager_config, load_config_locations, save_config_locations, default_app_locations
from template_manager import read_pywal_colors, set_wallpaper_swww, apply_wofi_wal, apply_waybar_wal, apply_mako_wal
from wallpaper_utils import get_wallpaper_dir, list_wallpapers, setup_wallpapers_dir, apply_wallpaper, get_wallpaper_preview_path
from plugin_manager import PluginManager
from plugin_config_window import PluginConfigWindow

# GTK Theme Management Functions
def get_available_gtk_themes():
    """Get list of available GTK themes"""
    themes = []
    theme_dirs = [
        "/usr/share/themes",
        "/usr/local/share/themes",
        os.path.expanduser("~/.themes"),
        os.path.expanduser("~/.local/share/themes")
    ]
    
    for theme_dir in theme_dirs:
        if os.path.exists(theme_dir):
            for theme_name in os.listdir(theme_dir):
                theme_path = os.path.join(theme_dir, theme_name)
                if os.path.isdir(theme_path):
                    # Check if it has GTK 3 or GTK 4 support
                    has_gtk3 = os.path.exists(os.path.join(theme_path, "gtk-3.0"))
                    has_gtk4 = os.path.exists(os.path.join(theme_path, "gtk-4.0"))
                    
                    if has_gtk3 or has_gtk4:
                        themes.append({
                            'name': theme_name,
                            'path': theme_path,
                            'gtk3': has_gtk3,
                            'gtk4': has_gtk4
                        })
    
    # Remove duplicates and sort
    seen = set()
    unique_themes = []
    for theme in themes:
        if theme['name'] not in seen:
            seen.add(theme['name'])
            unique_themes.append(theme)
    
    return sorted(unique_themes, key=lambda x: x['name'])

def get_current_gtk3_theme():
    """Get current GTK 3 theme from settings.ini"""
    try:
        settings_file = os.path.expanduser("~/.config/gtk-3.0/settings.ini")
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                for line in f:
                    if line.startswith('gtk-theme-name='):
                        return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading GTK 3 theme: {e}")
    return "Adwaita"

def set_gtk3_theme(theme_name):
    """Set GTK 3 theme in settings.ini"""
    try:
        settings_file = os.path.expanduser("~/.config/gtk-3.0/settings.ini")
        config_dir = os.path.dirname(settings_file)
        
        # Create config directory if it doesn't exist
        os.makedirs(config_dir, exist_ok=True)
        
        # Read existing settings
        settings = {}
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        settings[key] = value
        
        # Update theme
        settings['gtk-theme-name'] = theme_name
        
        # Write back
        with open(settings_file, 'w') as f:
            f.write("[Settings]\n")
            for key, value in settings.items():
                f.write(f"{key}={value}\n")
        
        return True
    except Exception as e:
        print(f"Error setting GTK 3 theme: {e}")
        return False

def set_gtk4_theme_via_gsettings(theme_name):
    """Set GTK 4 theme via gsettings"""
    try:
        # GTK 4 themes are managed through gsettings
        result = subprocess.run([
            'gsettings', 'set', 'org.gnome.desktop.interface', 'gtk-theme', theme_name
        ], capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error setting GTK 4 theme via gsettings: {e}")
        return False

def apply_gtk_theme(theme_name):
    """Apply theme to both GTK 3 and GTK 4"""
    gtk3_success = set_gtk3_theme(theme_name)
    gtk4_success = set_gtk4_theme_via_gsettings(theme_name)
    
    return gtk3_success or gtk4_success
# Wallpaper download repositories and functionality
WALLPAPER_REPOS = {
    "Minimal Wallpapers": "abhiTronix/minimal-wallpapers",
    "Nature Collection": "nature-wallpapers/collection", 
    "Dark Themes": "dark-wallpapers/collection"
}

def download_wallpapers_from_repo(repo, target_dir):
    """Download wallpapers from a repository (simplified implementation)"""
    print(f"Downloading from {repo} to {target_dir}")
    # Basic implementation - in a real app this would use git clone or API calls
    return False


class GtkThemeSelectionDialog(Adw.Window):
    """Dialog for selecting GTK themes"""
    
    def __init__(self, parent_window, **kwargs):
        super().__init__(**kwargs)
        self.set_transient_for(parent_window)
        self.set_modal(True)
        self.set_default_size(600, 400)
        self.set_title("Select GTK Theme")
        
        self.parent_window = parent_window
        self.setup_ui()
        self.load_themes()
    
    def setup_ui(self):
        """Setup the theme selection dialog"""
        # Toast overlay
        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)
        
        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.toast_overlay.set_child(main_box)
        
        # Header bar
        header_bar = Adw.HeaderBar()
        main_box.append(header_bar)
        
        # Content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        main_box.append(content_box)
        
        # Theme selection group
        theme_group = Adw.PreferencesGroup()
        theme_group.set_title("Available GTK Themes")
        theme_group.set_description("Select a theme compatible with GTK 3 and/or GTK 4")
        content_box.append(theme_group)
        
        # Theme list
        self.theme_listbox = Gtk.ListBox()
        self.theme_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.theme_listbox.add_css_class("boxed-list")
        self.theme_listbox.connect("row-activated", self.on_theme_activated)
        theme_group.add(self.theme_listbox)
    
    def load_themes(self):
        """Load available GTK themes"""
        themes = get_available_gtk_themes()
        current_theme = get_current_gtk3_theme()
        
        for theme in themes:
            row = Adw.ActionRow()
            row.set_title(theme['name'])
            
            # Compatibility info
            compat = []
            if theme['gtk3']:
                compat.append("GTK 3")
            if theme['gtk4']:
                compat.append("GTK 4")
            row.set_subtitle(f"Compatible with: {', '.join(compat)}")
            
            # Theme icon
            theme_icon = Gtk.Image()
            if theme['name'] == current_theme:
                theme_icon.set_from_icon_name("emblem-ok-symbolic")
                row.add_css_class("accent")
            else:
                theme_icon.set_from_icon_name("preferences-desktop-theme-symbolic")
            row.add_prefix(theme_icon)
            
            # Store theme data
            row.theme_data = theme
            
            self.theme_listbox.append(row)
    
    def on_theme_activated(self, listbox, row):
        """Handle theme selection"""
        theme_name = row.theme_data['name']
        if hasattr(self.parent_window, 'on_gtk_theme_selected'):
            self.parent_window.on_gtk_theme_selected(self, theme_name)
        self.close()
    
    def show_toast(self, message):
        """Show a toast notification"""
        toast = Adw.Toast()
        toast.set_title(message)
        toast.set_timeout(3)
        self.toast_overlay.add_toast(toast)


class AppConfigWindow(Adw.PreferencesDialog):
    def __init__(self, parent_window, **kwargs):
        super().__init__(**kwargs)
        # Use present() with parent instead of set_transient_for
        self.parent_window = parent_window
        
        self.setup_ui()
        self.load_app_configs()
    
    def present_dialog(self):
        """Present the dialog with proper parent relationship"""
        if self.parent_window:
            self.present(self.parent_window)
        else:
            self.present()
    
    def setup_ui(self):
        """Setup the app configuration dialog"""
        self.set_title("Application Configuration")
        
        # Main page
        page = Adw.PreferencesPage()
        page.set_title("Applications")
        page.set_icon_name("applications-system-symbolic")
        self.add(page)
        
        # App configuration group
        self.apps_group = Adw.PreferencesGroup()
        self.apps_group.set_title("Managed Applications")
        self.apps_group.set_description("Configure which applications receive automatic theme updates")
        page.add(self.apps_group)
        
        # Preview settings group
        self.preview_group = Adw.PreferencesGroup()
        self.preview_group.set_title("Preview Settings")
        self.preview_group.set_description("Control how wallpaper previews affect your system")
        page.add(self.preview_group)
        
        # Enable preview row
        self.preview_row = Adw.ActionRow()
        self.preview_row.set_title("Enable Live Preview")
        self.preview_row.set_subtitle("Apply color changes to system while browsing wallpapers")
        
        self.preview_switch = Gtk.Switch()
        self.preview_switch.set_active(True)  # Default enabled
        self.preview_switch.set_valign(Gtk.Align.CENTER)
        self.preview_switch.connect("notify::active", self.on_preview_setting_changed)
        self.preview_row.add_suffix(self.preview_switch)
        
        preview_icon = Gtk.Image()
        preview_icon.set_from_icon_name("image-x-generic-symbolic")
        self.preview_row.add_prefix(preview_icon)
        
        self.preview_group.add(self.preview_row)
        
        # GTK Theme settings group
        self.gtk_theme_group = Adw.PreferencesGroup()
        self.gtk_theme_group.set_title("GTK Theme Settings")
        self.gtk_theme_group.set_description("Configure GTK themes for compatibility with both GTK 3 and GTK 4 applications")
        page.add(self.gtk_theme_group)
        
        # Current GTK theme row
        self.current_theme_row = Adw.ActionRow()
        self.current_theme_row.set_title("Current GTK Theme")
        self.update_current_theme_display()
        
        theme_icon = Gtk.Image()
        theme_icon.set_from_icon_name("preferences-desktop-theme-symbolic")
        self.current_theme_row.add_prefix(theme_icon)
        
        # Theme selection button
        self.theme_button = Gtk.Button()
        self.theme_button.set_label("Change Theme")
        self.theme_button.set_valign(Gtk.Align.CENTER)
        self.theme_button.connect("clicked", self.on_select_gtk_theme)
        self.current_theme_row.add_suffix(self.theme_button)
        
        self.gtk_theme_group.add(self.current_theme_row)
        
        # Plugin Management group
        self.plugin_group = Adw.PreferencesGroup()
        self.plugin_group.set_title("Plugin Management")
        self.plugin_group.set_description("Manage theme plugins and extensions")
        page.add(self.plugin_group)
        
        # Plugin configuration row
        self.plugin_config_row = Adw.ActionRow()
        self.plugin_config_row.set_title("Configure Plugins")
        self.plugin_config_row.set_subtitle("Enable/disable theme plugins and view plugin information")
        
        plugin_icon = Gtk.Image()
        plugin_icon.set_from_icon_name("extension-symbolic")
        self.plugin_config_row.add_prefix(plugin_icon)
        
        # Plugin config button
        self.plugin_config_button = Gtk.Button()
        self.plugin_config_button.set_label("Configure")
        self.plugin_config_button.set_valign(Gtk.Align.CENTER)
        self.plugin_config_button.connect("clicked", self.on_configure_plugins)
        self.plugin_config_row.add_suffix(self.plugin_config_button)
        
        self.plugin_group.add(self.plugin_config_row)
        
        # Plugin statistics row
        if hasattr(self.parent_window, 'plugin_manager'):
            total_plugins = len(self.parent_window.plugin_manager.get_all_plugins())
            enabled_plugins = len(self.parent_window.plugin_manager.get_enabled_plugins())
            
            self.plugin_stats_row = Adw.ActionRow()
            self.plugin_stats_row.set_title("Plugin Status")
            self.plugin_stats_row.set_subtitle(f"{enabled_plugins} of {total_plugins} plugins enabled")
            
            stats_icon = Gtk.Image()
            stats_icon.set_from_icon_name("folder-symbolic")
            self.plugin_stats_row.add_prefix(stats_icon)
            
            self.plugin_group.add(self.plugin_stats_row)
    
    def load_app_configs(self):
        """Load application configurations"""
        app_configs = load_config_locations()
        
        for app_name, config in app_configs.items():
            self.create_app_row(app_name, config)
        
        # Load preview setting
        self.load_preview_setting()
    
    def load_preview_setting(self):
        """Load the preview setting from config"""
        try:
            config_dir = os.path.expanduser("~/.config/Theme-Manager")
            settings_file = os.path.join(config_dir, "app_settings.yaml")
            
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = yaml.safe_load(f) or {}
                    preview_enabled = settings.get('live_preview_enabled', True)
                    self.preview_switch.set_active(preview_enabled)
        except Exception as e:
            print(f"Error loading preview setting: {e}")
    
    def save_preview_setting(self, enabled):
        """Save the preview setting to config"""
        try:
            config_dir = os.path.expanduser("~/.config/Theme-Manager")
            os.makedirs(config_dir, exist_ok=True)
            settings_file = os.path.join(config_dir, "app_settings.yaml")
            
            # Load existing settings
            settings = {}
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = yaml.safe_load(f) or {}
            
            # Update preview setting
            settings['live_preview_enabled'] = enabled
            
            # Save settings
            with open(settings_file, 'w') as f:
                yaml.dump(settings, f)
        except Exception as e:
            print(f"Error saving preview setting: {e}")
    
    def on_preview_setting_changed(self, switch, _pspec):
        """Handle preview setting change"""
        enabled = switch.get_active()
        self.save_preview_setting(enabled)
        
        # Update parent window
        if hasattr(self.parent_window, 'set_preview_enabled'):
            self.parent_window.set_preview_enabled(enabled)
            
            # If live preview was just enabled and there's a selected wallpaper, apply it
            if enabled and hasattr(self.parent_window, 'selected_wallpaper') and self.parent_window.selected_wallpaper:
                wallpaper_path = os.path.join(get_wallpaper_dir(), self.parent_window.selected_wallpaper)
                self.parent_window.apply_live_preview(wallpaper_path)
            
            # If live preview was disabled, restore original theme
            elif not enabled:
                if hasattr(self.parent_window.get_application(), 'restore_original_theme'):
                    self.parent_window.get_application().restore_original_theme()
    
    def update_current_theme_display(self):
        """Update the current theme display"""
        current_theme = get_current_gtk3_theme()
        self.current_theme_row.set_subtitle(f"GTK 3/4: {current_theme}")
    
    def on_select_gtk_theme(self, button):
        """Open GTK theme selection dialog"""
        dialog = GtkThemeSelectionDialog(self)
        dialog.present()
    
    def on_configure_plugins(self, button):
        """Open plugin configuration window"""
        plugin_window = PluginConfigWindow(self.parent_window)
        plugin_window.present()
    
    def on_gtk_theme_selected(self, dialog, theme_name):
        """Handle GTK theme selection"""
        success = apply_gtk_theme(theme_name)
        if success:
            self.update_current_theme_display()
            if hasattr(self.parent_window, 'show_toast'):
                self.parent_window.show_toast(f"Applied GTK theme: {theme_name}")
        else:
            if hasattr(self.parent_window, 'show_toast'):
                self.parent_window.show_toast(f"Failed to apply theme: {theme_name}")
    
    def create_app_row(self, app_name, config):
        """Create a row for app configuration"""
        row = Adw.ExpanderRow()
        row.set_title(app_name.title())
        row.set_subtitle("Configure theming for this application")
        
        # Enable/disable switch
        enable_switch = Gtk.Switch()
        enable_switch.set_active(config.get('enabled', False))
        enable_switch.set_valign(Gtk.Align.CENTER)
        enable_switch.connect("notify::active", self.on_app_enabled_changed, app_name)
        row.add_suffix(enable_switch)
        
        # Status icon
        status_icon = Gtk.Image()
        if config.get('enabled', False):
            status_icon.set_from_icon_name("emblem-ok-symbolic")
        else:
            status_icon.set_from_icon_name("action-unavailable-symbolic")
        row.add_prefix(status_icon)
        
        self.apps_group.add(row)
    
    def on_app_enabled_changed(self, switch, _pspec, app_name):
        """Handle app enable/disable"""
        app_configs = load_config_locations()
        app_configs[app_name]['enabled'] = switch.get_active()
        save_config_locations(app_configs)


class WindowSettingsDialog(Adw.PreferencesDialog):
    def __init__(self, parent_window, **kwargs):
        super().__init__(**kwargs)
        self.parent_window = parent_window
        
        self.setup_ui()
        self.load_settings()
    
    def present_dialog(self):
        """Present the dialog with proper parent relationship"""
        if self.parent_window:
            self.present(self.parent_window)
        else:
            self.present()
    
    def setup_ui(self):
        """Setup the window settings dialog"""
        self.set_title("Window Settings")
        
        # Main page
        page = Adw.PreferencesPage()
        page.set_title("Window")
        page.set_icon_name("preferences-desktop-theme")
        self.add(page)
        
        # Size settings group
        size_group = Adw.PreferencesGroup()
        size_group.set_title("Window Size")
        size_group.set_description("Configure window dimensions and behavior")
        page.add(size_group)
        
        # Width setting
        self.width_row = Adw.ActionRow()
        self.width_row.set_title("Width")
        self.width_row.set_subtitle("Window width in pixels")
        
        self.width_spinbox = Gtk.SpinButton()
        self.width_spinbox.set_range(400, 1920)
        self.width_spinbox.set_increments(50, 100)
        self.width_spinbox.set_valign(Gtk.Align.CENTER)
        self.width_spinbox.connect("value-changed", self.on_setting_changed)
        self.width_row.add_suffix(self.width_spinbox)
        size_group.add(self.width_row)
        
        # Height setting
        self.height_row = Adw.ActionRow()
        self.height_row.set_title("Height")
        self.height_row.set_subtitle("Window height in pixels")
        
        self.height_spinbox = Gtk.SpinButton()
        self.height_spinbox.set_range(300, 1200)
        self.height_spinbox.set_increments(50, 100)
        self.height_spinbox.set_valign(Gtk.Align.CENTER)
        self.height_spinbox.connect("value-changed", self.on_setting_changed)
        self.height_row.add_suffix(self.height_spinbox)
        size_group.add(self.height_row)
        
        # Behavior settings group
        behavior_group = Adw.PreferencesGroup()
        behavior_group.set_title("Window Behavior")
        behavior_group.set_description("Configure window management behavior")
        page.add(behavior_group)
        
        # Fixed size toggle
        self.fixed_size_row = Adw.ActionRow()
        self.fixed_size_row.set_title("Fixed Size")
        self.fixed_size_row.set_subtitle("Prevent window from being resized")
        
        self.fixed_size_switch = Gtk.Switch()
        self.fixed_size_switch.set_valign(Gtk.Align.CENTER)
        self.fixed_size_switch.connect("notify::active", self.on_setting_changed)
        self.fixed_size_row.add_suffix(self.fixed_size_switch)
        behavior_group.add(self.fixed_size_row)
        
        # Floating window toggle
        self.floating_row = Adw.ActionRow()
        self.floating_row.set_title("Floating Window")
        self.floating_row.set_subtitle("Hint to window manager to keep window floating")
        
        self.floating_switch = Gtk.Switch()
        self.floating_switch.set_valign(Gtk.Align.CENTER)
        self.floating_switch.connect("notify::active", self.on_setting_changed)
        self.floating_row.add_suffix(self.floating_switch)
        behavior_group.add(self.floating_row)
        
        # Apply button
        apply_button = Gtk.Button()
        apply_button.set_label("Apply Settings")
        apply_button.add_css_class("suggested-action")
        apply_button.connect("clicked", self.on_apply_settings)
        
        apply_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        apply_box.set_halign(Gtk.Align.CENTER)
        apply_box.set_margin_top(12)
        apply_box.append(apply_button)
        behavior_group.add(apply_box)
    
    def load_settings(self):
        """Load current window settings"""
        settings = self.parent_window.window_settings
        
        self.width_spinbox.set_value(settings.get('width', 800))
        self.height_spinbox.set_value(settings.get('height', 900))
        self.fixed_size_switch.set_active(settings.get('fixed_size', True))
        self.floating_switch.set_active(settings.get('floating', True))
    
    def on_setting_changed(self, *args):
        """Handle setting changes"""
        pass  # Settings are applied when Apply button is clicked
    
    def on_apply_settings(self, button):
        """Apply the current settings"""
        settings = {
            'width': int(self.width_spinbox.get_value()),
            'height': int(self.height_spinbox.get_value()),
            'fixed_size': self.fixed_size_switch.get_active(),
            'floating': self.floating_switch.get_active()
        }
        
        # Apply to parent window
        self.parent_window.apply_window_settings(settings)
        
        # Show confirmation
        if hasattr(self.parent_window, 'show_toast'):
            self.parent_window.show_toast("Window settings applied!")
        
        # Close dialog
        self.close()


class WallpaperDownloadWindow(Adw.Window):
    def __init__(self, parent_window, **kwargs):
        super().__init__(**kwargs)
        self.set_transient_for(parent_window)
        self.set_modal(True)
        self.set_default_size(600, 500)
        self.set_title("Download Wallpapers")
        
        self.parent_window = parent_window
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the download window"""
        # Toast overlay
        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)
        
        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.toast_overlay.set_child(main_box)
        
        # Header bar
        header_bar = Adw.HeaderBar()
        main_box.append(header_bar)
        
        # Content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        main_box.append(content_box)
        
        # Repository selection group
        repo_group = Adw.PreferencesGroup()
        repo_group.set_title("Curated Collections")
        repo_group.set_description("Choose from high-quality wallpaper repositories")
        content_box.append(repo_group)
        
        # Repository list
        self.repo_listbox = Gtk.ListBox()
        self.repo_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.repo_listbox.add_css_class("boxed-list")
        repo_group.add(self.repo_listbox)
        
        # Populate repositories
        for repo_name, repo_url in WALLPAPER_REPOS.items():
            row = Adw.ActionRow()
            row.set_title(repo_name)
            row.set_subtitle(f"github.com/{repo_url}")
            
            # Repository icon
            repo_icon = Gtk.Image()
            repo_icon.set_from_icon_name("folder-download-symbolic")
            row.add_prefix(repo_icon)
            
            # Download button
            download_btn = Gtk.Button()
            download_btn.set_label("Download")
            download_btn.add_css_class("suggested-action")
            download_btn.set_valign(Gtk.Align.CENTER)
            download_btn.connect("clicked", self.on_download_repo, repo_url, repo_name)
            row.add_suffix(download_btn)
            
            self.repo_listbox.append(row)
    
    def on_download_repo(self, button, repo_url, repo_name):
        """Download from selected repository"""
        button.set_sensitive(False)
        button.set_label("Downloading...")
        
        wallpaper_dir = get_wallpaper_dir()
        threading.Thread(target=self.download_background, 
                        args=(repo_url, repo_name, wallpaper_dir, button), 
                        daemon=True).start()
    
    def download_background(self, repo_url, repo_name, wallpaper_dir, button):
        """Download repository in background"""
        try:
            success = download_wallpapers_from_repo(repo_url, wallpaper_dir)
            GLib.idle_add(self.on_download_complete, success, repo_name, button)
        except Exception as e:
            GLib.idle_add(self.on_download_error, str(e), button)
    
    def on_download_complete(self, success, repo_name, button):
        """Handle download completion"""
        button.set_sensitive(True)
        button.set_label("Download")
        
        if success:
            self.show_toast(f"Successfully downloaded from {repo_name}")
            # Refresh parent window
            if self.parent_window:
                self.parent_window.get_application().activate_action("refresh")
        else:
            self.show_toast(f"Failed to download from {repo_name}")
    
    def on_download_error(self, error, button):
        """Handle download error"""
        button.set_sensitive(True)
        button.set_label("Download")
        self.show_toast(f"Download failed: {error}")
    
    def show_toast(self, message):
        """Show a toast notification"""
        toast = Adw.Toast()
        toast.set_title(message)
        toast.set_timeout(4)
        self.toast_overlay.add_toast(toast)


class ThemeManagerApplication(Adw.Application):
    def __init__(self):
        super().__init__(application_id='com.thememanager.app', 
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        
        self.current_colors = None
        self.wallpapers_list = []
        self.selected_wallpaper = None
        self.preview_colors = None  # Colors from selected wallpaper
        self.theme_applied = False  # Track if user applied a new theme
        
        # Backup current theme on startup
        self.backup_current_theme()
        
        # Create actions
        self.create_action('quit', self.on_quit_action, ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('refresh', self.on_refresh_action)
        self.create_action('app_config', self.on_app_config_action)
        self.create_action('window_settings', self.on_window_settings_action)
        self.create_action('download_wallpapers', self.on_download_wallpapers_action)

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = ThemeManagerWindow(application=self)
        win.present()
        
        # Initialize UI in background thread
        threading.Thread(target=self.load_initial_data, daemon=True).start()

    def load_initial_data(self):
        """Load wallpapers and colors in background"""
        setup_wallpapers_dir()
        self.wallpapers_list = list_wallpapers()
        self.current_colors = read_pywal_colors()
        
        # Update UI on main thread
        GLib.idle_add(self.update_ui_data)

    def update_ui_data(self):
        """Update UI with loaded data"""
        win = self.props.active_window
        if win:
            win.refresh_wallpaper_list(self.wallpapers_list)
            win.refresh_color_display(self.current_colors)
            win.update_status()

    def on_refresh_action(self, *args):
        """Refresh all data"""
        threading.Thread(target=self.load_initial_data, daemon=True).start()

    def on_app_config_action(self, *args):
        """Open app configuration dialog"""
        win = self.props.active_window
        if win:
            dialog = AppConfigWindow(win)
            dialog.present_dialog()

    def on_window_settings_action(self, *args):
        """Open window settings dialog"""
        win = self.props.active_window
        if win:
            dialog = WindowSettingsDialog(win)
            dialog.present_dialog()

    def on_download_wallpapers_action(self, *args):
        """Open wallpaper download window"""
        win = self.props.active_window
        if win:
            download_window = WallpaperDownloadWindow(win)
            download_window.present()

    def on_about_action(self, *args):
        about = Adw.AboutDialog(
            application_name="Theme Manager",
            application_icon='preferences-desktop-theme',
            developer_name="Theme Manager Team", 
            version="3.0.0",
            website="https://github.com/user/theme-manager",
            copyright="© 2025 Theme Manager Team",
            license_type=Gtk.License.GPL_3_0_ONLY,
            comments="Modern theme management for Linux desktops using pywal\n\nBuilt with GTK4 and Libadwaita"
        )
        about.present(self.props.active_window)

    def backup_current_theme(self):
        """Backup current theme colors for restoration"""
        try:
            import shutil
            current_cache_dir = os.path.expanduser("~/.cache/wal")
            backup_dir = os.path.expanduser("~/.config/Theme-Manager/theme_backup")
            
            if os.path.exists(current_cache_dir):
                # Create backup directory
                os.makedirs(os.path.dirname(backup_dir), exist_ok=True)
                
                # Remove existing backup
                if os.path.exists(backup_dir):
                    shutil.rmtree(backup_dir)
                
                # Create new backup
                shutil.copytree(current_cache_dir, backup_dir)
                print("Theme backup created successfully")
        except Exception as e:
            print(f"Failed to backup current theme: {e}")
    
    def restore_original_theme(self):
        """Restore the original theme that was active when app started"""
        try:
            import shutil
            backup_dir = os.path.expanduser("~/.config/Theme-Manager/theme_backup")
            current_cache_dir = os.path.expanduser("~/.cache/wal")
            
            if os.path.exists(backup_dir):
                # Remove current cache
                if os.path.exists(current_cache_dir):
                    shutil.rmtree(current_cache_dir)
                
                # Restore backup
                shutil.copytree(backup_dir, current_cache_dir)
                
                # Reload applications that use pywal
                self.reload_themed_apps()
                
                print("Original theme restored successfully")
        except Exception as e:
            print(f"Failed to restore original theme: {e}")
    
    def reload_themed_apps(self):
        """Reload applications that might be using pywal colors"""
        try:
            # Reload applications based on what's enabled
            app_configs = load_config_locations()
            
            # Only reload apps that are enabled in our config
            if app_configs.get('waybar', {}).get('enabled', False):
                subprocess.run(['killall', '-SIGUSR2', 'waybar'], capture_output=True)
            
        except Exception as e:
            print(f"Failed to reload themed apps: {e}")
    
    def on_quit_action(self, *args):
        """Handle application quit - restore original theme if no new theme was applied"""
        if not self.theme_applied:
            self.restore_original_theme()
        self.quit()

    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


class ThemeManagerWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize plugin manager
        plugin_dir = os.path.join(os.path.dirname(__file__), 'plugins')
        self.plugin_manager = PluginManager(plugin_dir)
        
        # Load window settings
        self.window_settings = self.load_window_settings()
        
        # Apply window settings
        width = self.window_settings.get('width', 800)
        height = self.window_settings.get('height', 900)
        resizable = not self.window_settings.get('fixed_size', True)
        
        self.set_default_size(width, height)
        self.set_resizable(resizable)
        self.set_title("Theme Manager")
        
        self.setup_ui()
    
    def load_window_settings(self):
        """Load window settings from config"""
        try:
            config_dir = os.path.expanduser("~/.config/Theme-Manager")
            settings_file = os.path.join(config_dir, "window_settings.yaml")
            
            if os.path.exists(settings_file):
                import yaml
                with open(settings_file, 'r') as f:
                    return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Error loading window settings: {e}")
        
        # Default settings
        return {
            'width': 800,
            'height': 900,
            'fixed_size': True,
            'floating': True
        }
    
    def save_window_settings(self, settings):
        """Save window settings to config"""
        try:
            config_dir = os.path.expanduser("~/.config/Theme-Manager")
            os.makedirs(config_dir, exist_ok=True)
            settings_file = os.path.join(config_dir, "window_settings.yaml")
            
            import yaml
            with open(settings_file, 'w') as f:
                yaml.dump(settings, f)
        except Exception as e:
            print(f"Error saving window settings: {e}")
    
    def apply_window_settings(self, settings):
        """Apply new window settings"""
        self.window_settings = settings
        
        # Apply size
        width = settings.get('width', 800)
        height = settings.get('height', 900)
        self.set_default_size(width, height)
        
        # Apply resizable setting
        resizable = not settings.get('fixed_size', True)
        self.set_resizable(resizable)
        
        # Save settings
        self.save_window_settings(settings)

    def setup_ui(self):
        """Setup the main UI layout"""
        # Main container with header bar
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(main_box)
        
        # Header bar
        header_bar = Adw.HeaderBar()
        
        # Refresh button
        refresh_btn = Gtk.Button()
        refresh_btn.set_icon_name("view-refresh-symbolic")
        refresh_btn.set_tooltip_text("Refresh")
        refresh_btn.connect("clicked", lambda x: self.get_application().activate_action("refresh"))
        header_bar.pack_start(refresh_btn)
        
        # Download button
        download_btn = Gtk.Button()
        download_btn.set_icon_name("folder-download-symbolic")
        download_btn.set_tooltip_text("Download Wallpapers")
        download_btn.connect("clicked", lambda x: self.get_application().activate_action("download_wallpapers"))
        header_bar.pack_start(download_btn)
        
        # Menu button
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        
        menu = Gio.Menu()
        menu.append("Application Settings", "app.app_config")
        menu.append("Window Settings", "app.window_settings")
        menu.append("About", "app.about")
        menu.append("Quit", "app.quit")
        
        popover = Gtk.PopoverMenu()
        popover.set_menu_model(menu)
        menu_button.set_popover(popover)
        header_bar.pack_end(menu_button)
        
        main_box.append(header_bar)
        
        # Toast overlay for notifications
        self.toast_overlay = Adw.ToastOverlay()
        main_box.append(self.toast_overlay)
        
        # Scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        self.toast_overlay.set_child(scrolled)
        
        # Main content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24) 
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        scrolled.set_child(content_box)
        
        # Current Theme Status
        self.setup_status_section(content_box)
        
        # Wallpaper Selection
        self.setup_wallpaper_section(content_box)
        
        # Color Palette Display  
        self.setup_color_section(content_box)
        
        # Load preview setting
        self.live_preview_enabled = self.load_preview_setting()

    def load_preview_setting(self):
        """Load preview setting from config"""
        try:
            config_dir = os.path.expanduser("~/.config/Theme-Manager")
            settings_file = os.path.join(config_dir, "app_settings.yaml")
            
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = yaml.safe_load(f) or {}
                    return settings.get('live_preview_enabled', True)
        except Exception as e:
            print(f"Error loading preview setting: {e}")
        
        return True  # Default to enabled
    
    def set_preview_enabled(self, enabled):
        """Set whether live preview is enabled"""
        self.live_preview_enabled = enabled

    def setup_status_section(self, parent):
        """Setup current theme status section"""
        status_group = Adw.PreferencesGroup()
        status_group.set_title("Current Theme Status")
        status_group.set_description("Overview of active theme configuration")
        parent.append(status_group)
        
        # Theme status row
        self.theme_status_row = Adw.ActionRow()
        self.theme_status_row.set_title("Theme Status")
        self.theme_status_row.set_subtitle("No theme applied")
        self.status_icon = Gtk.Image()
        self.status_icon.set_from_icon_name("dialog-warning-symbolic")
        self.theme_status_row.add_prefix(self.status_icon)
        status_group.add(self.theme_status_row)
        
        # Wallpaper info row
        self.wallpaper_info_row = Adw.ActionRow()
        self.wallpaper_info_row.set_title("Current Wallpaper")
        self.wallpaper_info_row.set_subtitle("None selected")
        wp_icon = Gtk.Image()
        wp_icon.set_from_icon_name("image-x-generic-symbolic") 
        self.wallpaper_info_row.add_prefix(wp_icon)
        status_group.add(self.wallpaper_info_row)
        
        # Application count row
        self.app_count_row = Adw.ActionRow()
        self.app_count_row.set_title("Configured Applications")
        self.app_count_row.set_subtitle("0 applications configured")
        app_icon = Gtk.Image()
        app_icon.set_from_icon_name("applications-system-symbolic")
        self.app_count_row.add_prefix(app_icon)
        
        # Configure button
        config_btn = Gtk.Button()
        config_btn.set_label("Configure")
        config_btn.set_valign(Gtk.Align.CENTER)
        config_btn.connect("clicked", lambda x: self.get_application().activate_action("app_config"))
        self.app_count_row.add_suffix(config_btn)
        status_group.add(self.app_count_row)

    def setup_wallpaper_section(self, parent):
        """Setup wallpaper selection section"""
        wallpaper_group = Adw.PreferencesGroup()
        wallpaper_group.set_title("Wallpaper Selection")
        wallpaper_group.set_description("Choose a wallpaper to generate your theme")
        parent.append(wallpaper_group)
        
        # Wallpaper directory row
        self.wallpaper_dir_row = Adw.ActionRow()
        self.wallpaper_dir_row.set_title("Wallpaper Directory")
        self.update_wallpaper_dir_display()
        
        dir_btn = Gtk.Button()
        dir_btn.set_icon_name("folder-open-symbolic")
        dir_btn.set_valign(Gtk.Align.CENTER)
        dir_btn.connect("clicked", self.on_choose_wallpaper_dir)
        self.wallpaper_dir_row.add_suffix(dir_btn)
        wallpaper_group.add(self.wallpaper_dir_row)
        
        # Wallpaper list
        self.wallpaper_listbox = Gtk.ListBox()
        self.wallpaper_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.wallpaper_listbox.connect("row-selected", self.on_wallpaper_selected)
        self.wallpaper_listbox.add_css_class("boxed-list")
        wallpaper_group.add(self.wallpaper_listbox)
        
        # Apply wallpaper button
        self.apply_wallpaper_btn = Gtk.Button()
        self.apply_wallpaper_btn.set_label("Apply Wallpaper")
        self.apply_wallpaper_btn.add_css_class("suggested-action")
        self.apply_wallpaper_btn.add_css_class("pill")
        self.apply_wallpaper_btn.set_sensitive(False)
        self.apply_wallpaper_btn.connect("clicked", self.on_apply_wallpaper_only)
        
        apply_wallpaper_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        apply_wallpaper_box.set_halign(Gtk.Align.CENTER)
        apply_wallpaper_box.set_margin_top(12)
        apply_wallpaper_box.append(self.apply_wallpaper_btn)
        wallpaper_group.add(apply_wallpaper_box)

    def setup_color_section(self, parent):
        """Setup color palette display section"""
        # Preview colors section (shown when wallpaper selected)
        self.preview_color_group = Adw.PreferencesGroup()
        self.preview_color_group.set_title("Preview Colors")
        self.preview_color_group.set_description("Colors from selected wallpaper")
        self.preview_color_group.set_visible(False)  # Hidden until wallpaper selected
        parent.append(self.preview_color_group)
        
        # Preview color grid
        self.preview_color_flowbox = Gtk.FlowBox()
        self.preview_color_flowbox.set_max_children_per_line(8)
        self.preview_color_flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.preview_color_flowbox.set_margin_top(12)
        self.preview_color_group.add(self.preview_color_flowbox)
        
        # Apply preview colors button
        self.apply_colors_btn = Gtk.Button()
        self.apply_colors_btn.set_label("Apply Color Theme")
        self.apply_colors_btn.add_css_class("suggested-action")
        self.apply_colors_btn.set_sensitive(False)
        self.apply_colors_btn.connect("clicked", self.on_apply_colors_only)
        
        apply_colors_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        apply_colors_box.set_halign(Gtk.Align.CENTER)
        apply_colors_box.set_margin_top(12)
        apply_colors_box.append(self.apply_colors_btn)
        self.preview_color_group.add(apply_colors_box)
        
        # Current colors section
        self.current_color_group = Adw.PreferencesGroup()
        self.current_color_group.set_title("Current Theme Colors")
        self.current_color_group.set_description("Active theme colors from pywal")
        parent.append(self.current_color_group)
        
        # Current color grid
        self.current_color_flowbox = Gtk.FlowBox()
        self.current_color_flowbox.set_max_children_per_line(8)
        self.current_color_flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.current_color_flowbox.set_margin_top(12)
        self.current_color_group.add(self.current_color_flowbox)
        
        # Action buttons row for current colors
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        action_box.set_halign(Gtk.Align.CENTER)
        action_box.set_margin_top(12)
        
        # Copy colors button
        self.copy_colors_btn = Gtk.Button()
        self.copy_colors_btn.set_label("Copy Current Colors")
        self.copy_colors_btn.set_sensitive(False)
        self.copy_colors_btn.connect("clicked", self.on_copy_colors)
        action_box.append(self.copy_colors_btn)
        
        # Apply theme button (moved here)
        self.apply_theme_btn = Gtk.Button()
        self.apply_theme_btn.set_label("Apply Selected Theme")
        self.apply_theme_btn.add_css_class("suggested-action")
        self.apply_theme_btn.set_sensitive(False)
        self.apply_theme_btn.connect("clicked", self.on_apply_theme)
        action_box.append(self.apply_theme_btn)
        
        self.current_color_group.add(action_box)

    def update_wallpaper_dir_display(self):
        """Update wallpaper directory display"""
        dir_config = load_theme_manager_config()
        wallpaper_dir = dir_config.get('wallpapers_dir', '~/Pictures/wallpapers')
        self.wallpaper_dir_row.set_subtitle(wallpaper_dir)

    def update_status(self):
        """Update status displays"""
        # Update app count
        app_configs = load_config_locations()
        enabled_count = sum(1 for config in app_configs.values() if config.get('enabled', False))
        self.app_count_row.set_subtitle(f"{enabled_count} applications configured")

    def refresh_wallpaper_list(self, wallpapers):
        """Refresh the wallpaper list"""
        # Clear existing children
        child = self.wallpaper_listbox.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.wallpaper_listbox.remove(child)
            child = next_child
        
        if not wallpapers:
            # Empty state
            empty_row = Adw.ActionRow()
            empty_row.set_title("No wallpapers found")
            empty_row.set_subtitle("Download wallpapers or add them to your wallpaper directory")
            empty_icon = Gtk.Image()
            empty_icon.set_from_icon_name("image-missing-symbolic")
            empty_row.add_prefix(empty_icon)
            self.wallpaper_listbox.append(empty_row)
            return
        
        # Add wallpaper rows
        for wallpaper in wallpapers[:10]:  # Limit to 10 for demo
            row = Adw.ActionRow()
            row.set_title(wallpaper)
            
            # Try to get file size
            try:
                wallpaper_path = os.path.join(get_wallpaper_dir(), wallpaper)
                size = os.path.getsize(wallpaper_path)
                if size < 1024*1024:
                    size_str = f"{size//1024}KB"
                else:
                    size_str = f"{size//1024//1024}MB"
                row.set_subtitle(size_str)
            except:
                row.set_subtitle("Unknown size")
            
            # Wallpaper icon
            wp_icon = Gtk.Image()
            wp_icon.set_from_icon_name("image-x-generic-symbolic")
            row.add_prefix(wp_icon)
            
            # Preview button
            preview_btn = Gtk.Button()
            preview_btn.set_icon_name("view-reveal-symbolic")
            preview_btn.set_valign(Gtk.Align.CENTER)
            preview_btn.set_tooltip_text("Preview")
            preview_btn.connect("clicked", self.on_preview_wallpaper, wallpaper)
            row.add_suffix(preview_btn)
            
            self.wallpaper_listbox.append(row)

    def refresh_color_display(self, colors):
        """Refresh the current color palette display"""
        # Clear existing colors
        child = self.current_color_flowbox.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.current_color_flowbox.remove(child)
            child = next_child
        
        if not colors:
            self.current_color_group.set_description("No theme colors available - apply a theme first")
            self.copy_colors_btn.set_sensitive(False)
            return
        
        self.current_color_group.set_description("Active theme colors from pywal")
        self.copy_colors_btn.set_sensitive(True)
        
        # Add color swatches (limit to 8 colors)
        if 'colors' in colors:
            for i in range(min(8, len(colors['colors']))):
                color_key = f"color{i}"
                if color_key in colors['colors']:
                    color_value = colors['colors'][color_key]
                    color_box = self.create_color_swatch(color_value, color_key)
                    self.current_color_flowbox.append(color_box)
    
    def refresh_preview_colors(self, colors):
        """Refresh the preview color palette display"""
        # Clear existing colors
        child = self.preview_color_flowbox.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.preview_color_flowbox.remove(child)
            child = next_child
        
        if not colors:
            self.preview_color_group.set_visible(False)
            self.apply_colors_btn.set_sensitive(False)
            return
        
        self.preview_color_group.set_visible(True)
        self.preview_color_group.set_description("Colors from selected wallpaper")
        self.apply_colors_btn.set_sensitive(True)
        
        # Add color swatches (limit to 8 colors)
        if 'colors' in colors:
            for i in range(min(8, len(colors['colors']))):
                color_key = f"color{i}"
                if color_key in colors['colors']:
                    color_value = colors['colors'][color_key]
                    color_box = self.create_color_swatch(color_value, f"preview-{color_key}")
                    self.preview_color_flowbox.append(color_box)

    def create_color_swatch(self, color_value, label):
        """Create a color swatch widget"""
        # Create clickable button for color swatch
        color_btn = Gtk.Button()
        color_btn.add_css_class("flat")
        color_btn.set_tooltip_text(f"Click to copy {color_value}")
        color_btn.connect("clicked", self.on_color_clicked, color_value)
        
        color_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        color_box.set_margin_top(4)
        color_box.set_margin_bottom(4)
        color_box.set_margin_start(4)
        color_box.set_margin_end(4)
        
        # Color square - fixed size
        color_frame = Gtk.Frame()
        color_frame.set_size_request(50, 32)  # Smaller, consistent size
        
        color_area = Gtk.DrawingArea()
        color_area.set_size_request(50, 32)
        color_area.set_draw_func(self.draw_color_swatch, color_value)
        
        color_frame.set_child(color_area)
        color_box.append(color_frame)
        
        # Color label - shorter
        color_label = Gtk.Label()
        display_label = label.replace("preview-", "").replace("color", "")
        color_label.set_text(display_label)
        color_label.add_css_class("caption")
        color_label.set_max_width_chars(4)
        color_label.set_ellipsize(3)  # Ellipsize at end
        color_box.append(color_label)
        
        # Value label - shorter
        value_label = Gtk.Label()
        value_label.set_text(color_value[:7])  # Truncate long color values
        value_label.add_css_class("caption")
        value_label.add_css_class("dim-label")
        value_label.set_max_width_chars(7)
        color_box.append(value_label)
        
        color_btn.set_child(color_box)
        return color_btn

    def draw_color_swatch(self, area, cr, width, height, color_value):
        """Draw a color swatch"""
        try:
            # Parse color
            rgba = Gdk.RGBA()
            if rgba.parse(color_value):
                cr.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
                cr.rectangle(0, 0, width, height)
                cr.fill()
        except:
            # Fallback to gray
            cr.set_source_rgb(0.5, 0.5, 0.5)
            cr.rectangle(0, 0, width, height)
            cr.fill()

    def on_color_clicked(self, button, color_value):
        """Handle color swatch click - copy to clipboard"""
        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.set_text(color_value)
        self.show_toast(f"Copied {color_value} to clipboard")

    def on_wallpaper_selected(self, listbox, row):
        """Handle wallpaper selection"""
        if row and row.get_title() != "No wallpapers found":
            self.selected_wallpaper = row.get_title()
            self.apply_wallpaper_btn.set_sensitive(True)
            self.apply_colors_btn.set_sensitive(False)  # Disable until preview generated
            self.apply_theme_btn.set_sensitive(True)
            
            # Always generate preview colors for UI display
            wallpaper_path = os.path.join(get_wallpaper_dir(), self.selected_wallpaper)
            threading.Thread(target=self.generate_preview_colors, args=(wallpaper_path,), daemon=True).start()
        else:
            self.selected_wallpaper = None
            self.apply_wallpaper_btn.set_sensitive(False)
            self.apply_colors_btn.set_sensitive(False)
            self.apply_theme_btn.set_sensitive(False)
            # Hide preview colors
            GLib.idle_add(self.refresh_preview_colors, None)
    
    def generate_preview_colors(self, wallpaper_path):
        """Generate color preview for selected wallpaper without affecting current theme"""
        try:
            import tempfile
            import shutil
            import json
            
            # Create a temporary directory for preview generation
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_cache_dir = os.path.join(temp_dir, "wal")
                os.makedirs(temp_cache_dir, exist_ok=True)
                
                # Set environment to use temporary cache directory
                env = os.environ.copy()
                env['XDG_CACHE_HOME'] = temp_dir
                
                # Generate colors in isolated environment
                result = subprocess.run([
                    "wal", "-i", wallpaper_path, "-n", "-q"  # -n = don't set wallpaper, -q = quiet
                ], capture_output=True, text=True, env=env)
                
                if result.returncode == 0:
                    # Read colors from temporary cache
                    colors_file = os.path.join(temp_cache_dir, "colors.json")
                    if os.path.exists(colors_file):
                        with open(colors_file, 'r') as f:
                            preview_colors = json.load(f)
                        
                        self.get_application().preview_colors = preview_colors
                        GLib.idle_add(self.refresh_preview_colors, preview_colors)
                        
                        # If live preview is enabled, apply colors to system
                        if self.live_preview_enabled:
                            GLib.idle_add(self.apply_live_preview, wallpaper_path)
                        
                        return
                        
        except Exception as e:
            print(f"Preview generation failed: {e}")
        
        # If all else fails, hide preview
        GLib.idle_add(self.refresh_preview_colors, None)
    
    def apply_live_preview(self, wallpaper_path):
        """Apply preview colors to live system (non-permanent)"""
        try:
            # Generate colors with pywal (this will update the cache)
            result = subprocess.run(["wal", "-i", wallpaper_path, "-n"], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                # Apply to configured apps using plugin system
                try:
                    colors = read_pywal_colors()
                    if colors:
                        results = self.plugin_manager.apply_themes(colors)
                        # Log any failures
                        for plugin_name, success in results.items():
                            if not success:
                                print(f"Failed to apply theme to {plugin_name}")
                except Exception as e:
                    print(f"Plugin theme application failed: {e}")
                    
        except Exception as e:
            print(f"Live preview application failed: {e}")

    def on_preview_wallpaper(self, button, wallpaper):
        """Preview wallpaper"""
        wallpaper_path = os.path.join(get_wallpaper_dir(), wallpaper)
        try:
            subprocess.Popen([
                "feh", "--scale-down", "--auto-zoom",
                "--geometry", "800x600+100+100",
                "--title", f"Preview: {wallpaper}",
                wallpaper_path
            ])
            self.show_toast("Preview opened")
        except Exception as e:
            self.show_toast(f"Preview failed: {str(e)}")

    def on_apply_wallpaper_only(self, button):
        """Apply only the wallpaper without changing theme colors"""
        if not self.selected_wallpaper:
            return
        
        wallpaper_path = os.path.join(get_wallpaper_dir(), self.selected_wallpaper)
        button.set_sensitive(False)
        button.set_label("Applying Wallpaper...")
        
        # Apply wallpaper in background
        threading.Thread(target=self.apply_wallpaper_background, args=(wallpaper_path, button), daemon=True).start()
    
    def on_apply_colors_only(self, button):
        """Apply only the color theme from preview without changing wallpaper"""
        if not self.get_application().preview_colors:
            return
        
        button.set_sensitive(False)
        button.set_label("Applying Colors...")
        
        # Apply colors in background
        threading.Thread(target=self.apply_colors_background, args=(button,), daemon=True).start()
    
    def apply_wallpaper_background(self, wallpaper_path, button):
        """Apply wallpaper in background thread"""
        try:
            # Use wallpaper utility to set wallpaper
            success = apply_wallpaper(wallpaper_path)
            
            if success:
                GLib.idle_add(self.on_wallpaper_applied_success, wallpaper_path, button)
            else:
                GLib.idle_add(self.on_wallpaper_applied_error, "Failed to set wallpaper", button)
                
        except Exception as e:
            GLib.idle_add(self.on_wallpaper_applied_error, str(e), button)
    
    def apply_colors_background(self, button):
        """Apply preview colors in background thread"""
        try:
            if not self.selected_wallpaper:
                GLib.idle_add(self.on_colors_applied_error, "No wallpaper selected", button)
                return
                
            wallpaper_path = os.path.join(get_wallpaper_dir(), self.selected_wallpaper)
            
            # Generate colors with pywal (without setting wallpaper)
            result = subprocess.run(["wal", "-i", wallpaper_path, "-n"], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                # Apply themes using plugin system
                try:
                    colors = read_pywal_colors()
                    if colors:
                        results = self.plugin_manager.apply_themes(colors)
                        # Log any failures but don't stop execution
                        for plugin_name, success in results.items():
                            if not success:
                                print(f"Failed to apply theme to {plugin_name}")
                except Exception as e:
                    print(f"Plugin theme application failed: {e}")
                
                GLib.idle_add(self.on_colors_applied_success, button)
            else:
                GLib.idle_add(self.on_colors_applied_error, result.stderr, button)
                
        except Exception as e:
            GLib.idle_add(self.on_colors_applied_error, str(e), button)
    
    def on_wallpaper_applied_success(self, wallpaper_path, button):
        """Handle successful wallpaper application"""
        button.set_sensitive(True)
        button.set_label("Apply Wallpaper")
        
        # Update status
        self.wallpaper_info_row.set_subtitle(os.path.basename(wallpaper_path))
        
        self.show_toast("Wallpaper applied successfully!")
    
    def on_wallpaper_applied_error(self, error, button):
        """Handle wallpaper application error"""
        button.set_sensitive(True)
        button.set_label("Apply Wallpaper")
        self.show_toast(f"Wallpaper application failed: {error}")
    
    def on_colors_applied_success(self, button):
        """Handle successful color application"""
        button.set_sensitive(True)
        button.set_label("Apply Color Theme")
        
        # Mark that a theme was applied
        self.get_application().theme_applied = True
        
        # Update status
        self.theme_status_row.set_subtitle("Color theme active")
        self.status_icon.set_from_icon_name("emblem-ok-symbolic")
        
        self.show_toast("Color theme applied successfully!")
        
        # Refresh current colors
        threading.Thread(target=self.get_application().load_initial_data, daemon=True).start()
    
    def on_colors_applied_error(self, error, button):
        """Handle color application error"""
        button.set_sensitive(True)
        button.set_label("Apply Color Theme")
        self.show_toast(f"Color theme application failed: {error}")

    def on_apply_theme(self, button):
        """Apply the selected theme (wallpaper + colors)"""
        if not self.selected_wallpaper:
            return
        
        wallpaper_path = os.path.join(get_wallpaper_dir(), self.selected_wallpaper)
        button.set_sensitive(False)
        button.set_label("Applying Theme...")
        
        # Run in background thread
        threading.Thread(target=self.apply_theme_background, args=(wallpaper_path, button), daemon=True).start()

    def apply_theme_background(self, wallpaper_path, button):
        """Apply theme in background thread"""
        try:
            # Set wallpaper
            set_wallpaper_swww(wallpaper_path)
            
            # Generate colors with pywal
            result = subprocess.run(["wal", "-i", wallpaper_path], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                # Apply themes using plugin system
                try:
                    colors = read_pywal_colors()
                    if colors:
                        results = self.plugin_manager.apply_themes(colors)
                        # Log any failures but don't stop execution
                        for plugin_name, success in results.items():
                            if not success:
                                print(f"Failed to apply theme to {plugin_name}")
                    
                    # Also suggest GTK theme update to match colors
                    GLib.idle_add(self.suggest_gtk_theme_update)
                except Exception as e:
                    print(f"Plugin theme application failed: {e}")
                
                # Success
                GLib.idle_add(self.on_theme_applied_success, wallpaper_path, button)
            else:
                GLib.idle_add(self.on_theme_applied_error, result.stderr, button)
                
        except Exception as e:
            GLib.idle_add(self.on_theme_applied_error, str(e), button)

    def on_theme_applied_success(self, wallpaper_path, button):
        """Handle successful theme application"""
        button.set_sensitive(True)
        button.set_label("Apply Selected Theme")
        
        # Mark that a theme was applied
        self.get_application().theme_applied = True
        
        # Update status
        self.theme_status_row.set_subtitle("Theme active")
        self.wallpaper_info_row.set_subtitle(os.path.basename(wallpaper_path))
        
        # Update status icon
        self.status_icon.set_from_icon_name("emblem-ok-symbolic")
        
        self.show_toast("Theme applied successfully!")
        
        # Refresh colors
        threading.Thread(target=self.get_application().load_initial_data, daemon=True).start()

    def on_theme_applied_error(self, error, button):
        """Handle theme application error"""
        button.set_sensitive(True)
        button.set_label("Apply Selected Theme")
        self.show_toast(f"Theme application failed: {error}")

    def on_copy_colors(self, button):
        """Copy current theme colors to clipboard"""
        if not self.get_application().current_colors:
            return
        
        colors = self.get_application().current_colors
        color_text = "# Current Theme Colors\n"
        
        if 'colors' in colors:
            for i in range(min(8, len(colors['colors']))):
                color_key = f"color{i}"
                if color_key in colors['colors']:
                    color_text += f"{color_key}: {colors['colors'][color_key]}\n"
        
        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.set_text(color_text)
        self.show_toast("Current colors copied to clipboard!")

    def on_choose_wallpaper_dir(self, button):
        """Choose wallpaper directory"""
        self.show_toast("Directory chooser feature coming soon!")
    
    def suggest_gtk_theme_update(self):
        """Suggest updating GTK theme to match current colors"""
        try:
            # Read current pywal colors
            colors = read_pywal_colors()
            if not colors or 'special' not in colors:
                return
            
            # Check if current colors suggest a dark or light theme
            bg_color = colors['special'].get('background', '#000000')
            # Convert hex to RGB to determine brightness
            bg_hex = bg_color.lstrip('#')
            if len(bg_hex) == 6:
                r = int(bg_hex[0:2], 16)
                g = int(bg_hex[2:4], 16) 
                b = int(bg_hex[4:6], 16)
                brightness = (r * 0.299 + g * 0.587 + b * 0.114) / 255
                
                # Suggest appropriate theme
                current_theme = get_current_gtk3_theme()
                suggested_theme = None
                
                if brightness < 0.5:  # Dark theme needed
                    if 'light' in current_theme.lower() or current_theme == 'Adwaita':
                        # Look for a dark variant
                        available_themes = get_available_gtk_themes()
                        for theme in available_themes:
                            if 'dark' in theme['name'].lower() or 'mocha' in theme['name'].lower():
                                suggested_theme = theme['name']
                                break
                else:  # Light theme needed
                    if 'dark' in current_theme.lower() or 'mocha' in current_theme.lower():
                        # Look for a light variant
                        available_themes = get_available_gtk_themes()
                        for theme in available_themes:
                            if 'light' in theme['name'].lower() or theme['name'] == 'Adwaita':
                                suggested_theme = theme['name']
                                break
                
                if suggested_theme and suggested_theme != current_theme:
                    self.show_toast(f"💡 Consider switching to '{suggested_theme}' theme for better color matching")
                    
        except Exception as e:
            print(f"Theme suggestion failed: {e}")

    def show_toast(self, message):
        """Show a toast notification"""
        toast = Adw.Toast()
        toast.set_title(message)
        toast.set_timeout(3)
        self.toast_overlay.add_toast(toast)


def main():
    app = ThemeManagerApplication()
    return app.run(sys.argv)


if __name__ == "__main__":
    main()
