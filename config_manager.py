import os
import yaml

CONFIG_DIR = os.path.expanduser('~/.config/Theme-manager/config')
CONFIG_LOCATIONS_FILE = os.path.join(CONFIG_DIR, 'app-locations.yaml')
THEME_MANAGER_CONFIG = os.path.join(CONFIG_DIR, 'theme-manager.yaml')

def default_app_locations():
    return {
        'wofi': {'enabled': False, 'path': os.path.expanduser('~/.config/wofi/style.css')},
        'waybar': {'enabled': False, 'path': os.path.expanduser('~/.config/waybar/style.css')},
        'mako': {'enabled': False, 'path': os.path.expanduser('~/.config/mako/config')},
        'kitty': {'enabled': False, 'path': os.path.expanduser('~/.config/kitty/pywal.conf')},
        'gtk': {'enabled': False, 'path': os.path.expanduser('~/.config/gtk-3.0/settings.ini')},
        'qt': {'enabled': False, 'path': os.path.expanduser('~/.config/qt5ct/qt5ct.conf')},
    }

def load_config_locations():
    if not os.path.exists(CONFIG_LOCATIONS_FILE):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_LOCATIONS_FILE, 'w') as f:
            yaml.safe_dump(default_app_locations(), f)
        return default_app_locations()
    with open(CONFIG_LOCATIONS_FILE) as f:
        return yaml.safe_load(f)

def save_config_locations(data):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_LOCATIONS_FILE, 'w') as f:
        yaml.safe_dump(data, f)

def load_theme_manager_config():
    if not os.path.exists(THEME_MANAGER_CONFIG):
        return {'wallpapers_dir': os.path.expanduser('~/Pictures/wallpapers')}
    with open(THEME_MANAGER_CONFIG) as f:
        return yaml.safe_load(f)

def save_theme_manager_config(data):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(THEME_MANAGER_CONFIG, 'w') as f:
        yaml.safe_dump(data, f)
