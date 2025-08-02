import os
import json
import subprocess

def read_pywal_colors():
    PYWAL_COLORS = os.path.expanduser('~/.cache/wal/colors.json')
    if not os.path.exists(PYWAL_COLORS):
        print(f"pywal colors not found: {PYWAL_COLORS}")
        return {}
    with open(PYWAL_COLORS) as f:
        return json.load(f)

def read_template(app, template_dir):
    template_path = os.path.join(template_dir, f"{app}.template")
    if not os.path.exists(template_path):
        print(f"No template for {app} at {template_path}")
        return None
    with open(template_path) as f:
        return f.read()

def render_template(template, colors):
    if not template or not colors:
        return template
    for i in range(16):
        key = f"color{i}"
        val = colors['colors'].get(key, '')
        template = template.replace(f"{{{{{key}}}}}", val)
    for key in ['background', 'foreground', 'cursor']:
        val = colors['special'].get(key, '')
        template = template.replace(f"{{{{{key}}}}}", val)
    return template

def write_config(path, content):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)
    except Exception as e:
        print(f"[ERROR] Could not write config {path}: {e}")

def set_wallpaper_swww(wallpaper_path):
    """Set wallpaper using swww"""
    try:
        subprocess.run(["swww", "img", wallpaper_path], check=True)
        return True
    except Exception as e:
        print(f"[ERROR] swww failed: {e}")
        return False
