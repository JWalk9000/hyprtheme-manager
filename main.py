# Main application logic goes here.

import sys
import argparse
from app_settings import AppSettings

def main():
    """
    Parses arguments, selects a UI backend, and launches the application.
    """
    parser = argparse.ArgumentParser(description="A simple theme and wallpaper manager.")
    parser.add_argument(
        '--ui', 
        choices=['gtk', 'qt'], 
        help='Specify the UI backend to use (overrides settings).'
    )
    args = parser.parse_args()

    settings = AppSettings()
    
    # Determine which backend to use
    backend = args.ui or settings.get('ui.backend', 'gtk')

    print(f"Using '{backend}' UI backend.")

    try:
        if backend == 'gtk':
            from gdk_ui import create_app
        elif backend == 'qt':
            from qt_ui import create_app
        else:
            # This case should ideally not be reached due to settings default
            print(f"Error: Unknown UI backend '{backend}' specified.", file=sys.stderr)
            sys.exit(1)
            
        # Create and run the application
        app = create_app(settings)
        sys.exit(app.run())

    except ImportError as e:
        print(f"Error: Could not import the '{backend}' UI backend.", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()