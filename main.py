import sys
from PyQt6.QtWidgets import QApplication
# It's good practice to place imports of your own modules after standard/third-party library imports.
# However, to ensure PyCharm recognizes the app structure immediately,
# you might create __init__.py files in subdirectories first.

# Assuming your app structure is media_presenter/app/
# You might need to adjust sys.path if running main.py directly from the root
# and PyCharm hasn't auto-configured the content roots yet.
# For a proper package, you'd typically run it as a module: python -m media_presenter.main
try:
    from app.ui_module import MainWindow
    from app.config_module import SettingsManager
except ImportError:
    # This is a fallback for direct script execution before PYTHONPATH is fully configured
    # Or if the 'app' directory is not correctly recognized as a package source root in the IDE
    print("Error: Could not import application modules. \n"
          "Ensure 'app' directory is in Python path or configure your IDE's source roots.\n"
          "Try creating __init__.py in the 'app' directory and its subdirectories if they don't exist.")
    sys.exit(1)


def main():
    """Main function to initialize and run the application."""
    app = QApplication(sys.argv)

    # Initialize settings manager (QSettings needs QApplication instance)
    settings_manager = SettingsManager() # Initialize early if needed by MainWindow

    # Initialize and show the main window
    main_window = MainWindow(settings_manager)
    main_window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    # Create __init__.py files if they don't exist to help with module recognition
    import os
    app_dir = os.path.join(os.path.dirname(__file__), "app")
    if not os.path.exists(os.path.join(app_dir, "__init__.py")):
        os.makedirs(app_dir, exist_ok=True)
        with open(os.path.join(app_dir, "__init__.py"), "w") as f:
            f.write("# This file makes 'app' a Python package\n")
        print(f"Created {os.path.join(app_dir, '__init__.py')}")

    # Create a dummy resources directory
    resources_dir = os.path.join(os.path.dirname(__file__), "resources", "icons")
    if not os.path.exists(resources_dir):
        os.makedirs(resources_dir, exist_ok=True)
        # Create a placeholder icon file
        placeholder_icon_path = os.path.join(resources_dir, "placeholder_icon.png")
        if not os.path.exists(placeholder_icon_path):
            try:
                # Simple way to create a tiny png (not a real one, but a file)
                with open(placeholder_icon_path, "wb") as f: # write bytes
                    f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')
                print(f"Created placeholder icon: {placeholder_icon_path}")
            except Exception as e:
                print(f"Could not create placeholder icon: {e}")
        print(f"Created directory: {resources_dir}")


    main()
