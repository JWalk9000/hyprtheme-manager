#!/usr/bin/env python3
"""
Simple installation script for Theme Manager (Arch Linux).

Features:
- Checks for and installs missing dependencies on Arch
- Creates .desktop files for the application
- Prompts user to choose GTK, Qt, or both UI backends
- Sets up launch scripts
"""

import os
import sys
import subprocess
from pathlib import Path

class ThemeManagerInstaller:
    def __init__(self):
        self.script_dir = Path(__file__).parent.absolute()
        
    def is_arch_linux(self):
        """Check if running on Arch Linux."""
        return Path("/etc/arch-release").exists()
    
    
    def check_python_deps(self):
        """Check if Python dependencies are available."""
        required_modules = ["PyQt6", "gi", "yaml", "requests", "PIL"]
        missing = []
        
        for module in required_modules:
            try:
                if module == "PIL":
                    import PIL
                elif module == "gi":
                    import gi
                    gi.require_version('Gtk', '4.0')
                    gi.require_version('Adw', '1')
                else:
                    __import__(module)
            except ImportError:
                missing.append(module)
        
        return missing
    
    def install_arch_deps(self):
        """Install Arch Linux dependencies."""
        packages = [
            "gtk4", "libadwaita", "python", "python-pyqt6", 
            "python-gobject", "python-yaml", "python-requests", 
            "python-pillow", "python-pywal"
        ]
        
        print("📦 Installing dependencies with pacman...")
        try:
            cmd = ["sudo", "pacman", "-S", "--needed"] + packages
            subprocess.run(cmd, check=True)
            print("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            return False
    
    
    def choose_ui_backends(self):
        """Let user choose default UI backend."""
        print("\nChoose UI backend (this can be changed later from within the app):")
        print("1. GTK (default)")
        print("2. Qt6")
        
        while True:
            choice = input("\nEnter choice (1-2): ").strip()
            if choice in ["1", ""]:
                return "gtk"
            elif choice == "2":
                return "qt"
            else:
                print("Invalid choice. Please enter 1 or 2.")
    
    def set_default_ui(self, backend):
        """Set the default UI backend in settings.yaml."""
        settings_file = self.script_dir / "config" / "settings.yaml"
        
        # Read existing settings or create new ones
        settings = {}
        if settings_file.exists():
            try:
                import yaml
                with open(settings_file, 'r') as f:
                    settings = yaml.safe_load(f) or {}
            except Exception:
                pass
        
        # Set the default UI backend
        if 'ui' not in settings:
            settings['ui'] = {}
        settings['ui']['backend'] = backend
        
        # Write back to file
        try:
            import yaml
            settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(settings_file, 'w') as f:
                yaml.dump(settings, f, default_flow_style=False)
            print(f"✅ Set default UI backend to: {backend}")
        except Exception as e:
            print(f"⚠️  Could not save default UI setting: {e}")
    
    def create_desktop_files(self):
        """Create a single .desktop file."""
        desktop_dir = Path.home() / ".local/share/applications"
        desktop_dir.mkdir(parents=True, exist_ok=True)
        
        desktop_content = f"""[Desktop Entry]
Name=Theme Manager
Comment=Modern theme manager for Linux
Exec=python3 {self.script_dir}/main.py
Icon=applications-graphics
Terminal=false
Type=Application
Categories=Graphics;
"""
        
        desktop_file = desktop_dir / "theme-manager.desktop"
        with open(desktop_file, 'w') as f:
            f.write(desktop_content)
        os.chmod(desktop_file, 0o755)
        print(f"✅ Created: {desktop_file}")
    
    def create_launch_script(self):
        """Create a single launch script."""
        script_path = self.script_dir / "theme-manager"
        script_content = f"""#!/bin/bash
cd "{self.script_dir}"
python3 main.py "$@"
"""
        with open(script_path, 'w') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        print(f"✅ Created: {script_path}")
    
    def run_installation(self):
        """Run installation."""
        print("🚀 Theme Manager Installation (Arch Linux)")
        print("=" * 45)
        
        if not self.is_arch_linux():
            print("⚠️  This installer is designed for Arch Linux")
            print("For other distributions, install dependencies manually:")
            print("- Python 3.8+, PyQt6, GTK4, libadwaita, python-yaml, python-requests, python-pillow")
            if input("Continue anyway? (y/N): ").lower() != 'y':
                return False
        
        # Check dependencies
        missing = self.check_python_deps()
        if missing:
            print(f"⚠️  Missing: {', '.join(missing)}")
            if input("Install dependencies? (Y/n): ").lower() not in ['n', 'no']:
                if not self.install_arch_deps():
                    return False
        else:
            print("✅ All dependencies available")
        
        # Choose UI backend and set as default
        default_backend = self.choose_ui_backends()
        self.set_default_ui(default_backend)
        
        # Create files
        self.create_desktop_files()
        self.create_launch_script()
        
        # Make main script executable
        os.chmod(self.script_dir / "main.py", 0o755)
        
        print("\n🎉 Installation complete!")
        print("\nUsage:")
        print("  ./theme-manager")
        print("  python3 main.py")
        print("  Or launch from application menu")
        
        return True

def main():
    """Main installation function."""
    installer = ThemeManagerInstaller()
    
    try:
        success = installer.run_installation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Installation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
