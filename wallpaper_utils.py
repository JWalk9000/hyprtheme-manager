#!/usr/bin/env python3
"""
Wallpaper utilities for Theme Manager
All functions and classes for managing wallpapers, including caching colors and generating themes.
Clean implementation that is UI agnostic. Includes Hyprland wallpaper setting.
"""

import os
import json
import yaml
import hashlib
import tempfile
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from PIL import Image, ImageOps
from app_settings import AppSettings


class WallpaperManager:
    """
    Manages wallpaper operations including directory scanning, thumbnail generation,
    and color caching. UI-agnostic implementation.
    """
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    THUMBNAIL_SIZE = (150, 150)
    
    def __init__(self, wallpaper_dir: Optional[str] = None, settings: Optional[AppSettings] = None):
        """
        Initialize the wallpaper manager.
        
        Args:
            wallpaper_dir: Path to wallpaper directory. If None, uses settings or default.
            settings: AppSettings instance. If None, creates new instance.
        """
        self.settings = settings or AppSettings()
        
        # Get wallpaper directory from settings or parameter
        if wallpaper_dir:
            self.wallpaper_dir = Path(wallpaper_dir)
        else:
            settings_dir = self.settings.get('wallpaper.directory')
            self.wallpaper_dir = Path(settings_dir) if settings_dir else Path.home() / "Pictures" / "Wallpapers"
        
        self.thumbnail_dir = self.wallpaper_dir / "thumbnails"
        self.cache_file = self.wallpaper_dir / "wallpaper_colors.yaml"
        self.color_cache = {}
        
        # Check if directory exists - if not, this will need UI intervention
        self.directory_exists = self.wallpaper_dir.exists()
        
        if self.directory_exists:
            # Ensure directories exist
            self.wallpaper_dir.mkdir(parents=True, exist_ok=True)
            self.thumbnail_dir.mkdir(exist_ok=True)
            
            # Load existing color cache
            self._load_color_cache()
    
    def ensure_wallpaper_directory(self, fallback_dir: Optional[str] = None) -> bool:
        """
        Ensure wallpaper directory exists. If not, create it or use fallback.
        
        Args:
            fallback_dir: Directory to use if default doesn't exist
            
        Returns:
            True if directory is ready, False if needs user intervention
        """
        if self.directory_exists:
            return True
            
        if fallback_dir:
            # User selected a directory
            self.wallpaper_dir = Path(fallback_dir)
            self.settings.set('wallpaper.directory', str(self.wallpaper_dir))
            
            # Update derived paths
            self.thumbnail_dir = self.wallpaper_dir / "thumbnails"
            self.cache_file = self.wallpaper_dir / "wallpaper_colors.yaml"
            
            # Create directories
            self.wallpaper_dir.mkdir(parents=True, exist_ok=True)
            self.thumbnail_dir.mkdir(exist_ok=True)
            
            # Load cache
            self._load_color_cache()
            self.directory_exists = True
            return True
        else:
            # Try to create default directory
            try:
                self.wallpaper_dir.mkdir(parents=True, exist_ok=True)
                self.thumbnail_dir.mkdir(exist_ok=True)
                self._load_color_cache()
                self.directory_exists = True
                return True
            except (OSError, PermissionError):
                return False

    def set_wallpaper_directory(self, new_dir: str) -> bool:
        """
        Change the wallpaper directory and update paths. Updates settings.
        
        Args:
            new_dir: Path to new wallpaper directory
            
        Returns:
            True if successful, False otherwise
        """
        try:
            new_path = Path(new_dir)
            if not new_path.exists():
                return False
                
            self.wallpaper_dir = new_path
            self.thumbnail_dir = self.wallpaper_dir / "thumbnails"
            self.cache_file = self.wallpaper_dir / "wallpaper_colors.yaml"
            
            # Update settings
            self.settings.set('wallpaper.directory', str(self.wallpaper_dir))
            
            # Ensure thumbnail directory exists
            self.thumbnail_dir.mkdir(exist_ok=True)
            
            # Load cache for new directory
            self._load_color_cache()
            self.directory_exists = True
            
            return True
        except Exception as e:
            print(f"Error setting wallpaper directory: {e}")
            return False
    
    def get_wallpaper_files(self) -> List[Path]:
        """
        Get all wallpaper files in the current directory.
        
        Returns:
            List of Path objects for valid wallpaper files
        """
        wallpapers = []
        
        # Return empty list if directory doesn't exist
        if not self.directory_exists or not self.wallpaper_dir.exists():
            return wallpapers
        
        try:
            for file_path in self.wallpaper_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_FORMATS:
                    wallpapers.append(file_path)
        except Exception as e:
            print(f"Error scanning wallpaper directory: {e}")
        
        return sorted(wallpapers)
    
    def get_wallpaper_thumbnail(self, wallpaper_path: Path) -> Optional[Path]:
        """
        Get or create a thumbnail for the given wallpaper.
        
        Args:
            wallpaper_path: Path to the wallpaper file
            
        Returns:
            Path to thumbnail file, or None if failed
        """
        # Create thumbnail filename based on original file hash
        file_hash = self._get_file_hash(wallpaper_path)
        thumbnail_path = self.thumbnail_dir / f"{file_hash}.jpg"
        
        # Return existing thumbnail if it exists and is newer than original
        if (thumbnail_path.exists() and 
            thumbnail_path.stat().st_mtime > wallpaper_path.stat().st_mtime):
            return thumbnail_path
        
        # Generate new thumbnail
        try:
            with Image.open(wallpaper_path) as img:
                # Convert to RGB if necessary (for formats like PNG with transparency)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Create thumbnail maintaining aspect ratio
                img.thumbnail(self.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                
                # Center crop to exact thumbnail size
                img = ImageOps.fit(img, self.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                
                # Save thumbnail
                img.save(thumbnail_path, "JPEG", quality=85)
                
            return thumbnail_path
            
        except Exception as e:
            print(f"Error creating thumbnail for {wallpaper_path}: {e}")
            return None
    
    def generate_all_thumbnails(self, progress_callback=None) -> int:
        """
        Generate thumbnails for all wallpapers in the directory.
        
        Args:
            progress_callback: Optional callback function(current, total, filename)
            
        Returns:
            Number of thumbnails generated
        """
        wallpapers = self.get_wallpaper_files()
        generated = 0
        
        for i, wallpaper in enumerate(wallpapers):
            if progress_callback:
                progress_callback(i + 1, len(wallpapers), wallpaper.name)
            
            if self.get_wallpaper_thumbnail(wallpaper):
                generated += 1
        
        return generated
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Generate a hash for the file based on path and modification time."""
        content = f"{file_path.absolute()}_{file_path.stat().st_mtime}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _load_color_cache(self):
        """Load color cache from YAML file."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    data = yaml.safe_load(f)
                    self.color_cache = data.get('wallpaper_colors', {}) if data else {}
            else:
                self.color_cache = {}
        except Exception as e:
            print(f"Error loading color cache: {e}")
            self.color_cache = {}
    
    def _save_color_cache(self):
        """Save color cache to YAML file."""
        try:
            cache_data = {
                'wallpaper_colors': self.color_cache,
                'cache_info': {
                    'folder': str(self.wallpaper_dir),
                    'last_updated': __import__('datetime').datetime.now().isoformat(),
                    'total_cached': len(self.color_cache)
                }
            }
            with open(self.cache_file, 'w') as f:
                yaml.safe_dump(cache_data, f, default_flow_style=False, indent=2)
        except Exception as e:
            print(f"Error saving color cache: {e}")
    
    def get_wallpaper_colors(self, wallpaper_path: Path) -> Optional[Dict[str, str]]:
        """
        Get colors for a wallpaper, using cache if available.
        
        Args:
            wallpaper_path: Path to the wallpaper file
            
        Returns:
            Dictionary of colors (color0-color15) or None if failed
        """
        # Generate cache key
        file_hash = self._get_file_hash(wallpaper_path)
        
        # Check cache first
        if file_hash in self.color_cache:
            return self.color_cache[file_hash]
        
        # Generate colors using pywal
        colors = self._generate_colors_with_pywal(wallpaper_path)
        
        # Cache the result
        if colors:
            self.color_cache[file_hash] = colors
            self._save_color_cache()
        
        return colors
    
    def _generate_colors_with_pywal(self, wallpaper_path: Path) -> Optional[Dict[str, str]]:
        """
        Generate colors from wallpaper using pywal.
        
        Args:
            wallpaper_path: Path to the wallpaper file
            
        Returns:
            Dictionary of colors or None if failed
        """
        try:
            # Run pywal to generate colors
            result = subprocess.run([
                'wal', '-i', str(wallpaper_path), '-n'  # -n = don't set wallpaper
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Pywal failed: {result.stderr}")
                return None
            
            # Read generated colors from default cache location
            colors_file = Path.home() / '.cache' / 'wal' / 'colors.json'
            if colors_file.exists():
                with open(colors_file, 'r') as f:
                    data = json.load(f)
                    colors = data.get('colors', {})
                    
                    # Apply standard colors for positions 9-15
                    standard_colors = {
                        'color9':  '#ff4444',  # Bright Red - errors, danger
                        'color10': '#44ff44',  # Bright Green - success, safe
                        'color11': '#ffff44',  # Bright Yellow - warnings, caution  
                        'color12': '#4444ff',  # Bright Blue - info, links
                        'color13': '#ff44ff',  # Bright Magenta - highlights
                        'color14': '#44ffff',  # Bright Cyan - accents
                        'color15': '#ffffff'   # Pure White - text, backgrounds
                    }
                    
                    # Override positions 9-15 with our standard colors
                    for color_key, color_value in standard_colors.items():
                        colors[color_key] = color_value
                    
                    return colors
            else:
                print("Colors file not found after pywal execution")
                return None
                
        except FileNotFoundError:
            print("Pywal not found. Please install pywal for color generation.")
        except Exception as e:
            print(f"Error generating colors with pywal: {e}")
        
        return None
    
    def clear_cache(self):
        """Clear the color cache."""
        self.color_cache = {}
        if self.cache_file.exists():
            self.cache_file.unlink()
        print(f"Cleared color cache for {self.wallpaper_dir}")
    
    def clear_thumbnails(self):
        """Clear all generated thumbnails."""
        try:
            for thumbnail in self.thumbnail_dir.glob("*.jpg"):
                thumbnail.unlink()
        except Exception as e:
            print(f"Error clearing thumbnails: {e}")
    
    def get_directory_info(self) -> Dict:
        """
        Get information about the current wallpaper directory.
        
        Returns:
            Dictionary with directory statistics
        """
        wallpapers = self.get_wallpaper_files()
        thumbnails = list(self.thumbnail_dir.glob("*.jpg"))
        
        return {
            'directory': str(self.wallpaper_dir),
            'wallpaper_count': len(wallpapers),
            'thumbnail_count': len(thumbnails),
            'cached_colors': len(self.color_cache),
            'supported_formats': list(self.SUPPORTED_FORMATS)
        }


# Convenience functions for UI backends

def create_wallpaper_manager(wallpaper_dir: Optional[str] = None) -> WallpaperManager:
    """Create a new WallpaperManager instance."""
    return WallpaperManager(wallpaper_dir)

def get_wallpaper_list_with_thumbnails(manager: WallpaperManager) -> List[Tuple[Path, Optional[Path]]]:
    """
    Get a list of wallpapers with their thumbnail paths.
    
    Args:
        manager: WallpaperManager instance
        
    Returns:
        List of tuples (wallpaper_path, thumbnail_path)
    """
    wallpapers = manager.get_wallpaper_files()
    result = []
    
    for wallpaper in wallpapers:
        thumbnail = manager.get_wallpaper_thumbnail(wallpaper)
        result.append((wallpaper, thumbnail))
    
    return result


def set_wallpaper(wallpaper_path: str) -> bool:
    """
    Set wallpaper using SWWW for Hyprland.
    Simple function that just sets the wallpaper and persists it to Hyprland config.
    
    Args:
        wallpaper_path: Path to the wallpaper image
        
    Returns:
        True if successful, False otherwise
    """
    try:
        wallpaper_path = Path(wallpaper_path).expanduser().absolute()
        
        if not wallpaper_path.exists():
            print(f"Wallpaper not found: {wallpaper_path}")
            return False
        
        # Set wallpaper with SWWW
        cmd = ["swww", "img", str(wallpaper_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"SWWW failed: {result.stderr}")
            return False
        
        # Persist to Hyprland config for startup
        hyprland_config = Path("~/.config/hypr/hyprland.conf").expanduser()
        if hyprland_config.exists():
            _update_hyprland_wallpaper_config(hyprland_config, wallpaper_path)
        
        print(f"✅ Wallpaper set: {wallpaper_path.name}")
        return True
        
    except Exception as e:
        print(f"Error setting wallpaper: {e}")
        return False


def get_current_wallpaper() -> Optional[Path]:
    """
    Get the currently set wallpaper by querying SWWW.
    
    Returns:
        Path to current wallpaper file, or None if not found
    """
    try:
        # Query SWWW for current wallpaper
        result = subprocess.run(
            ["swww", "query"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            # Parse SWWW output - format is usually: "eDP-1: /path/to/wallpaper.jpg"
            for line in result.stdout.strip().split('\n'):
                if ':' in line and '/' in line:
                    # Extract the path part after the colon
                    wallpaper_path = line.split(':', 1)[1].strip()
                    path_obj = Path(wallpaper_path)
                    if path_obj.exists():
                        return path_obj
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        print(f"Could not query current wallpaper via SWWW: {e}")
    
    # Fallback: Try to read from Hyprland config
    try:
        hyprland_config = Path("~/.config/hypr/hyprland.conf").expanduser()
        if hyprland_config.exists():
            with open(hyprland_config, 'r') as f:
                content = f.read()
            
            # Look for swww img command in exec-once
            for line in content.split('\n'):
                if 'swww' in line and 'img' in line and 'exec-once' in line:
                    # Extract the wallpaper path from the command
                    if '"' in line:
                        # Handle quoted paths
                        parts = line.split('"')
                        for i, part in enumerate(parts):
                            if 'swww' in part and i + 1 < len(parts):
                                potential_path = parts[i + 1]
                                if potential_path and potential_path != 'swww img ':
                                    path_obj = Path(potential_path)
                                    if path_obj.exists():
                                        return path_obj
                    else:
                        # Handle unquoted paths
                        if 'swww img ' in line:
                            path_start = line.find('swww img ') + len('swww img ')
                            potential_path = line[path_start:].strip()
                            if potential_path:
                                path_obj = Path(potential_path)
                                if path_obj.exists():
                                    return path_obj
    except Exception as e:
        print(f"Could not read Hyprland config for wallpaper: {e}")
    
    return None


def _update_hyprland_wallpaper_config(config_path: Path, wallpaper_path: Path):
    """Update Hyprland config to include wallpaper startup command."""
    try:
        # Read current config
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Remove existing swww exec lines
        lines = content.split('\n')
        filtered_lines = [line for line in lines if not (line.strip().startswith('exec-once') and 'swww' in line)]
        
        # Add new wallpaper command
        swww_cmd = f'exec-once = swww img {wallpaper_path}'
        
        # Find a good place to insert (after other exec-once commands or at the end)
        insert_index = len(filtered_lines)
        for i, line in enumerate(filtered_lines):
            if line.strip().startswith('exec-once'):
                insert_index = i + 1
        
        filtered_lines.insert(insert_index, swww_cmd)
        
        # Write back to config
        with open(config_path, 'w') as f:
            f.write('\n'.join(filtered_lines))
        
        print(f"Updated Hyprland config with wallpaper startup")
        
    except Exception as e:
        print(f"Failed to update Hyprland config: {e}")



