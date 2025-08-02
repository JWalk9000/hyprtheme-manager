import os
import yaml

CONFIG_DIR = os.path.expanduser('~/.config/Theme-manager/config')
THEME_MANAGER_CONFIG = os.path.join(CONFIG_DIR, 'theme-manager.yaml')

def load_theme_manager_config():
    if not os.path.exists(THEME_MANAGER_CONFIG):
        return {'wallpapers_dir': os.path.expanduser('~/Pictures/wallpapers')}
    with open(THEME_MANAGER_CONFIG) as f:
        return yaml.safe_load(f)

def save_theme_manager_config(data):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(THEME_MANAGER_CONFIG, 'w') as f:
        yaml.safe_dump(data, f)
