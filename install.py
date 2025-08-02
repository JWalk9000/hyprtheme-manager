#!/usr/bin/env python3
"""
GTK Theme Manager Installer
Installs dependencies and sets up the desktop entry for the GTK Theme Manager
"""

import os
import sys
import subprocess
import shutil
import yaml
from pathlib import Path

class ThemeManagerInstaller:
    def __init__(self):
        self.script_dir = Path(__file__).parent.resolve()
        self.home_dir = Path.home()
        self.config_dir = self.home_dir / ".config" / "Theme-Manager"
        self.desktop_dir = self.home_dir / ".local" / "share" / "applications"
        
    def detect_distro(self):
        """Detect the Linux distribution"""
        try:
            with open('/etc/os-release', 'r') as f:
                content = f.read().lower()
                if 'arch' in content or 'manjaro' in content:
                    return 'arch'
                elif 'ubuntu' in content or 'debian' in content or 'mint' in content:
                    return 'ubuntu'
                elif 'fedora' in content or 'rhel' in content or 'centos' in content:
                    return 'fedora'
        except FileNotFoundError:
            pass
        
        # Fallback detection
        if shutil.which('pacman'):
            return 'arch'
        elif shutil.which('apt'):
            return 'ubuntu'
        elif shutil.which('dnf') or shutil.which('yum'):
            return 'fedora'
        
        return 'unknown'
    
    def load_dependencies(self):
        """Load dependencies from YAML file"""
        deps_file = self.script_dir / "dependencies.yaml"
        try:
            with open(deps_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"❌ Dependencies file not found: {deps_file}")
            return None
        except yaml.YAMLError as e:
            print(f"❌ Error parsing dependencies.yaml: {e}")
            return None
    
    def check_python_version(self):
        """Check if Python version is sufficient"""
        if sys.version_info < (3, 8):
            print("❌ Python 3.8+ is required")
            return False
        print(f"✅ Python {sys.version.split()[0]} is sufficient")
        return True
    
    def install_system_packages(self, distro, packages):
        """Install system packages based on distribution"""
        if distro == 'arch':
            cmd = ['sudo', 'pacman', '-S', '--needed', '--noconfirm'] + packages
        elif distro == 'ubuntu':
            # Update package list first
            subprocess.run(['sudo', 'apt', 'update'], check=False)
            cmd = ['sudo', 'apt', 'install', '-y'] + packages
        elif distro == 'fedora':
            cmd = ['sudo', 'dnf', 'install', '-y'] + packages
        else:
            print(f"❌ Unsupported distribution: {distro}")
            print("Please install GTK4, libadwaita, and Python dependencies manually")
            return False
        
        print(f"🔧 Installing system packages for {distro}...")
        print(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("✅ System packages installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install system packages: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
            return False
    
    def install_python_packages(self, packages):
        """Install Python packages using pip"""
        print("🔧 Installing Python packages...")
        
        for package in packages:
            try:
                cmd = [sys.executable, '-m', 'pip', 'install', '--user', package]
                print(f"Installing {package}...")
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                print(f"✅ {package} installed")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install {package}: {e}")
                return False
        
        return True
    
    def setup_directories(self):
        """Create necessary directories"""
        print("📁 Setting up directories...")
        
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Create desktop applications directory
        self.desktop_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"✅ Config directory: {self.config_dir}")
        print(f"✅ Desktop directory: {self.desktop_dir}")
        
        return True
    
    def copy_files(self):
        """Copy application files to config directory"""
        print("📋 Copying application files...")
        
        files_to_copy = [
            'main.py',
            'config_manager.py',
            'template_manager.py',
            'wallpaper_utils.py',
            'plugin_manager.py',
            'plugin_config_window.py',
            'plugins',
            'config',
            'theme-manager-gtk'
        ]
        
        for item in files_to_copy:
            src = self.script_dir / item
            dst = self.config_dir / item
            
            if src.exists():
                if src.is_dir():
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                    print(f"✅ Copied directory: {item}")
                else:
                    shutil.copy2(src, dst)
                    # Make executable if it's the launcher script
                    if item == 'theme-manager-gtk':
                        dst.chmod(0o755)
                    print(f"✅ Copied file: {item}")
            else:
                print(f"⚠️  File not found: {item}")
        
        return True
    
    def install_desktop_entry(self):
        """Install the desktop entry"""
        print("🖥️  Installing desktop entry...")
        
        desktop_content = f"""[Desktop Entry]
Name=Theme Manager GTK
Comment=Manage Hyprland themes and wallpapers
Exec={self.config_dir}/theme-manager-gtk
Icon=preferences-desktop-theme
Terminal=false
Type=Application
Categories=Settings;DesktopSettings;GTK;
Keywords=theme;wallpaper;hyprland;gtk;
StartupNotify=true
"""
        
        desktop_file = self.desktop_dir / "theme-manager-gtk.desktop"
        
        try:
            with open(desktop_file, 'w') as f:
                f.write(desktop_content)
            
            # Make desktop file executable
            desktop_file.chmod(0o755)
            
            print(f"✅ Desktop entry installed: {desktop_file}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to install desktop entry: {e}")
            return False
    
    def check_gtk_installation(self):
        """Verify GTK4 and Libadwaita are available"""
        print("🔍 Checking GTK4 and Libadwaita installation...")
        
        try:
            # Test GTK4 import
            import gi
            gi.require_version('Gtk', '4.0')
            gi.require_version('Adw', '1')
            from gi.repository import Gtk, Adw
            
            print("✅ GTK4 and Libadwaita are available")
            return True
            
        except Exception as e:
            print(f"❌ GTK4/Libadwaita not available: {e}")
            return False
    
    def run_installation(self):
        """Run the complete installation process"""
        print("🚀 GTK Theme Manager Installation")
        print("=" * 40)
        
        # Check Python version
        if not self.check_python_version():
            return False
        
        # Detect distribution
        distro = self.detect_distro()
        print(f"🐧 Detected distribution: {distro}")
        
        # Load dependencies
        deps = self.load_dependencies()
        if not deps:
            return False
        
        # Install system packages
        if distro in deps['system_packages']:
            packages = deps['system_packages'][distro]
            if not self.install_system_packages(distro, packages):
                print("⚠️  System package installation failed, continuing anyway...")
        else:
            print(f"⚠️  No package list for {distro}, please install GTK4 and dependencies manually")
        
        # Install Python packages
        if 'python_packages' in deps:
            if not self.install_python_packages(deps['python_packages']):
                print("⚠️  Python package installation failed, continuing anyway...")
        
        # Check GTK installation
        if not self.check_gtk_installation():
            print("❌ GTK4/Libadwaita verification failed")
            print("Please install GTK4 and Libadwaita manually and try again")
            return False
        
        # Setup directories
        if not self.setup_directories():
            return False
        
        # Copy files
        if not self.copy_files():
            return False
        
        # Install desktop entry
        if not self.install_desktop_entry():
            return False
        
        print("\n" + "=" * 40)
        print("🎉 Installation completed successfully!")
        print(f"📂 Application installed to: {self.config_dir}")
        print("🖥️  Desktop entry created - Theme Manager GTK should appear in your application menu")
        print(f"🚀 You can also run directly: {self.config_dir}/theme-manager-gtk")
        print("\n💡 Optional: Install Hyprland, Waybar, and Rofi for full functionality")
        
        return True

def main():
    installer = ThemeManagerInstaller()
    
    try:
        success = installer.run_installation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Installation failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
