#!/bin/bash
#
# GTK Theme Manager Installation Script
# Simple bash installer for the GTK Theme Manager
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$HOME/.config/Theme-Manager"
DESKTOP_DIR="$HOME/.local/share/applications"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}🔧 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

detect_distro() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        case $ID in
            arch|manjaro|garuda|endeavouros)
                echo "arch"
                ;;
            ubuntu|debian|linuxmint|pop|elementary)
                echo "ubuntu"
                ;;
            fedora|rhel|centos|rocky|alma)
                echo "fedora"
                ;;
            *)
                echo "unknown"
                ;;
        esac
    else
        echo "unknown"
    fi
}

install_arch_packages() {
    print_status "Installing packages for Arch Linux..."
    
    local packages=(
        "gtk4"
        "libadwaita" 
        "python"
        "python-gobject"
        "python-yaml"
        "python-requests"
        "python-pillow"
        "glib2"
    )
    
    sudo pacman -S --needed --noconfirm "${packages[@]}"
}

install_ubuntu_packages() {
    print_status "Installing packages for Ubuntu/Debian..."
    
    local packages=(
        "libgtk-4-1"
        "libadwaita-1-0"
        "python3"
        "python3-gi"
        "python3-yaml"
        "python3-requests"
        "python3-pil"
        "glib2.0-bin"
    )
    
    sudo apt update
    sudo apt install -y "${packages[@]}"
}

install_fedora_packages() {
    print_status "Installing packages for Fedora..."
    
    local packages=(
        "gtk4"
        "libadwaita"
        "python3"
        "python3-gobject"
        "python3-PyYAML"
        "python3-requests"
        "python3-pillow"
        "glib2"
    )
    
    sudo dnf install -y "${packages[@]}"
}

check_python() {
    print_status "Checking Python installation..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        return 1
    fi
    
    local python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    print_success "Python $python_version found"
    
    return 0
}

install_python_deps() {
    local distro=$(detect_distro)
    
    # Skip pip installation on Arch since packages are available via pacman
    if [[ "$distro" == "arch" ]]; then
        print_status "On Arch Linux, Python packages installed via pacman, skipping pip..."
        return 0
    fi
    
    print_status "Installing Python dependencies..."
    
    local packages=(
        "PyYAML>=6.0"
        "requests>=2.25.0"
        "Pillow>=8.0.0"
    )
    
    for package in "${packages[@]}"; do
        print_status "Installing $package..."
        python3 -m pip install --user "$package" || {
            print_warning "Failed to install $package, continuing..."
        }
    done
}

setup_directories() {
    print_status "Setting up directories..."
    
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$DESKTOP_DIR"
    
    print_success "Directories created"
}

copy_files() {
    print_status "Copying application files..."
    
    # Copy essential files
    local files_to_copy=(
        "main.py"
        "config_manager.py"
        "template_manager.py"
        "wallpaper_utils.py"
        "app-locations.yaml"
        "theme-manager-gtk"
    )
    
    for item in "${files_to_copy[@]}"; do
        if [[ -e "$SCRIPT_DIR/$item" ]]; then
            cp -r "$SCRIPT_DIR/$item" "$CONFIG_DIR/"
            print_success "Copied: $item"
        else
            print_warning "File not found: $item"
        fi
    done
    
    # Make launcher executable
    chmod +x "$CONFIG_DIR/theme-manager-gtk"
}

create_desktop_entry() {
    print_status "Creating desktop entry..."
    
    cat > "$DESKTOP_DIR/theme-manager-gtk.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Theme Manager GTK
Comment=Manage Hyprland themes and wallpapers with GTK4/Libadwaita
Exec=$CONFIG_DIR/theme-manager-gtk
Icon=preferences-desktop-theme
Terminal=false
Categories=Settings;DesktopSettings;GTK;
Keywords=theme;wallpaper;hyprland;gtk;pywal;colors;
StartupNotify=true
StartupWMClass=com.thememanager.gtk
EOF
    
    chmod +x "$DESKTOP_DIR/theme-manager-gtk.desktop"
    print_success "Desktop entry created at: $DESKTOP_DIR/theme-manager-gtk.desktop"
}

verify_installation() {
    print_status "Verifying GTK installation..."
    
    python3 -c "
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
print('GTK4 and Libadwaita are working!')
" 2>/dev/null && {
        print_success "GTK4 and Libadwaita verification passed"
        return 0
    } || {
        print_error "GTK4 or Libadwaita verification failed"
        return 1
    }
}

main() {
    echo "🚀 GTK Theme Manager Installation"
    echo "=================================="
    
    # Detect distribution
    local distro=$(detect_distro)
    print_status "Detected distribution: $distro"
    
    # Check Python
    if ! check_python; then
        print_error "Python check failed"
        exit 1
    fi
    
    # Install system packages based on distribution
    case $distro in
        arch)
            install_arch_packages
            ;;
        ubuntu)
            install_ubuntu_packages
            ;;
        fedora)
            install_fedora_packages
            ;;
        *)
            print_warning "Unknown distribution. Please install GTK4, Libadwaita, and Python dependencies manually"
            ;;
    esac
    
    # Install Python dependencies
    install_python_deps
    
    # Verify GTK installation
    if ! verify_installation; then
        print_error "GTK verification failed. Please install GTK4 and Libadwaita manually"
        exit 1
    fi
    
    # Setup application
    setup_directories
    copy_files
    create_desktop_entry
    
    echo ""
    echo "=================================="
    print_success "Installation completed successfully!"
    echo ""
    print_success "Application installed to: $CONFIG_DIR"
    print_success "Desktop entry created - Check your application menu for 'Theme Manager GTK'"
    print_success "You can also run directly: $CONFIG_DIR/theme-manager-gtk"
    echo ""
    print_warning "Optional: Install Hyprland, Waybar, and Rofi for full functionality"
}

# Run main function
main "$@"
