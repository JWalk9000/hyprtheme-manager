#!/usr/bin/env python3
"""
Wallpaper utilities for GTK Theme Manager
Clean implementation without rofi dependencies
"""

import os
import sys
import subprocess
from config_manager import load_theme_manager_config, save_theme_manager_config

def get_wallpaper_dir():
    """Get the configured wallpaper directory"""
    config = load_theme_manager_config()
    return config.get('wallpapers_dir', os.path.expanduser('~/Pictures/wallpapers'))

def list_wallpapers():
    """List all wallpaper files in the wallpaper directory"""
    wallpapers_dir = get_wallpaper_dir()
    exts = ('.jpg', '.jpeg', '.png', '.webp')
    if not os.path.exists(wallpapers_dir):
        return []
    return [f for f in os.listdir(wallpapers_dir) if f.lower().endswith(exts)]

def setup_wallpapers_dir():
    """Ensure wallpaper directory exists, create if needed"""
    config = load_theme_manager_config()
    wallpapers_dir = config.get('wallpapers_dir', os.path.expanduser('~/Pictures/wallpapers'))
    
    if not os.path.exists(wallpapers_dir):
        try:
            os.makedirs(wallpapers_dir, exist_ok=True)
            print(f"Created wallpapers directory: {wallpapers_dir}")
        except Exception as e:
            print(f"[ERROR] Could not create wallpapers directory: {e}")
            # Fallback to default location
            fallback_dir = os.path.expanduser('~/.config/Theme-Manager/wallpapers')
            try:
                os.makedirs(fallback_dir, exist_ok=True)
                wallpapers_dir = fallback_dir
                config['wallpapers_dir'] = wallpapers_dir
                save_theme_manager_config(config)
                print(f"Using fallback directory: {wallpapers_dir}")
            except Exception as e2:
                print(f"[ERROR] Could not create fallback directory: {e2}")
    
    return wallpapers_dir

def apply_wallpaper(wallpaper_path):
    """Apply a wallpaper using available tools"""
    if not os.path.exists(wallpaper_path):
        print(f"[ERROR] Wallpaper file not found: {wallpaper_path}")
        return False
    
    # Try different wallpaper setting tools in order of preference
    tools = [
        ['swww', 'img', wallpaper_path],
        ['hyprpaper', '--set', wallpaper_path],
        ['feh', '--bg-scale', wallpaper_path],
        ['nitrogen', '--set-scaled', wallpaper_path]
    ]
    
    for tool in tools:
        if subprocess.run(['which', tool[0]], capture_output=True).returncode == 0:
            try:
                subprocess.run(tool, check=True, capture_output=True)
                print(f"Applied wallpaper using {tool[0]}: {wallpaper_path}")
                return True
            except subprocess.CalledProcessError as e:
                print(f"[WARNING] {tool[0]} failed: {e}")
                continue
    
    print("[ERROR] No wallpaper setting tool found (tried: swww, hyprpaper, feh, nitrogen)")
    return False

def get_wallpaper_preview_path(wallpaper_name):
    """Get the full path to a wallpaper file"""
    wallpapers_dir = get_wallpaper_dir()
    return os.path.join(wallpapers_dir, wallpaper_name)
