"""
Plugin Configuration Window
Provides GUI for managing theme plugins
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gio
import os
from plugin_manager import PluginManager

class PluginConfigWindow(Adw.PreferencesWindow):
    def __init__(self, parent=None):
        super().__init__()
        self.set_title("Theme Plugin Configuration")
        self.set_default_size(600, 500)
        self.set_transient_for(parent)
        self.set_modal(True)
        
        # Initialize plugin manager
        plugin_dir = os.path.join(os.path.dirname(__file__), 'plugins')
        self.plugin_manager = PluginManager(plugin_dir)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the plugin configuration interface"""
        
        # Main page
        main_page = Adw.PreferencesPage()
        main_page.set_title("Plugins")
        main_page.set_icon_name("extension-symbolic")
        self.add(main_page)
        
        # Available plugins group
        available_group = Adw.PreferencesGroup()
        available_group.set_title("Available Plugins")
        available_group.set_description("Enable or disable theme plugins")
        main_page.add(available_group)
        
        # Add plugin rows
        for plugin in self.plugin_manager.get_all_plugins():
            plugin_row = self.create_plugin_row(plugin)
            available_group.add(plugin_row)
        
        # Plugin info group
        info_group = Adw.PreferencesGroup()
        info_group.set_title("Plugin Information")
        info_group.set_description("Details about loaded plugins")
        main_page.add(info_group)
        
        # Plugin count info
        total_plugins = len(self.plugin_manager.get_all_plugins())
        enabled_plugins = len(self.plugin_manager.get_enabled_plugins())
        available_plugins = len(self.plugin_manager.get_available_plugins())
        
        count_row = Adw.ActionRow()
        count_row.set_title("Plugin Statistics")
        count_row.set_subtitle(f"Total: {total_plugins} | Enabled: {enabled_plugins} | Available: {available_plugins}")
        count_row.set_icon_name("folder-symbolic")
        info_group.add(count_row)
        
        # Refresh button
        refresh_row = Adw.ActionRow()
        refresh_row.set_title("Refresh Plugins")
        refresh_row.set_subtitle("Reload plugins from disk")
        refresh_row.set_icon_name("view-refresh-symbolic")
        
        refresh_button = Gtk.Button()
        refresh_button.set_icon_name("view-refresh-symbolic")
        refresh_button.set_valign(Gtk.Align.CENTER)
        refresh_button.add_css_class("flat")
        refresh_button.connect("clicked", self.on_refresh_clicked)
        refresh_row.add_suffix(refresh_button)
        
        info_group.add(refresh_row)
    
    def create_plugin_row(self, plugin):
        """Create a row for a plugin"""
        row = Adw.ActionRow()
        row.set_title(plugin.display_name)
        row.set_subtitle(plugin.description)
        
        # Set icon based on availability
        if plugin.is_available():
            row.set_icon_name("emblem-ok-symbolic")
        else:
            row.set_icon_name("dialog-warning-symbolic")
        
        # Enable/disable switch
        switch = Gtk.Switch()
        switch.set_valign(Gtk.Align.CENTER)
        switch.set_active(plugin.name in self.plugin_manager.enabled_plugins)
        switch.connect("notify::active", self.on_plugin_toggled, plugin.name)
        row.add_suffix(switch)
        
        # Info button
        info_button = Gtk.Button()
        info_button.set_icon_name("help-about-symbolic")
        info_button.set_valign(Gtk.Align.CENTER)
        info_button.add_css_class("flat")
        info_button.connect("clicked", self.on_plugin_info_clicked, plugin)
        row.add_suffix(info_button)
        
        return row
    
    def on_plugin_toggled(self, switch, param, plugin_name):
        """Handle plugin enable/disable toggle"""
        if switch.get_active():
            if self.plugin_manager.enable_plugin(plugin_name):
                self.show_toast(f"Enabled {plugin_name}")
            else:
                self.show_toast(f"Failed to enable {plugin_name}")
                switch.set_active(False)
        else:
            if self.plugin_manager.disable_plugin(plugin_name):
                self.show_toast(f"Disabled {plugin_name}")
            else:
                self.show_toast(f"Failed to disable {plugin_name}")
                switch.set_active(True)
    
    def on_plugin_info_clicked(self, button, plugin):
        """Show detailed plugin information"""
        dialog = PluginInfoDialog(plugin, self)
        dialog.show()
    
    def on_refresh_clicked(self, button):
        """Refresh plugin list"""
        # Reload plugins
        self.plugin_manager.load_plugins()
        
        # Refresh the UI
        self.remove_all_pages()
        self.setup_ui()
        
        self.show_toast("Plugins refreshed")
    
    def show_toast(self, message):
        """Show a toast notification"""
        toast = Adw.Toast()
        toast.set_title(message)
        toast.set_timeout(3)
        
        # Get the toast overlay from parent if available
        if hasattr(self.get_transient_for(), 'toast_overlay'):
            self.get_transient_for().toast_overlay.add_toast(toast)
    
    def remove_all_pages(self):
        """Remove all preference pages"""
        while True:
            page = self.get_visible_page()
            if page:
                self.remove(page)
            else:
                break

class PluginInfoDialog(Adw.MessageDialog):
    def __init__(self, plugin, parent=None):
        super().__init__()
        self.set_transient_for(parent)
        self.set_modal(True)
        
        self.set_heading(f"{plugin.display_name} Information")
        
        # Build info text
        info_lines = [
            f"Name: {plugin.name}",
            f"Description: {plugin.description}",
            f"Config Path: {plugin.config_path}",
            f"Template: {plugin.template_name}.template",
            f"Available: {'Yes' if plugin.is_available() else 'No'}",
        ]
        
        if plugin.dependencies:
            info_lines.append(f"Dependencies: {', '.join(plugin.dependencies)}")
        
        if plugin.optional_dependencies:
            info_lines.append(f"Optional: {', '.join(plugin.optional_dependencies)}")
        
        self.set_body("\n".join(info_lines))
        
        self.add_response("close", "Close")
        self.set_default_response("close")
