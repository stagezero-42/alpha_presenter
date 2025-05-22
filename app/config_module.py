from PyQt6.QtCore import QSettings, QVariant


class SettingsManager:
    """Manages application settings using QSettings."""

    def __init__(self, organization_name="MyCompany", application_name="MediaPresenter"):
        # QSettings will store settings in a platform-specific location
        # Windows: Registry
        # macOS: .plist file
        # Linux: .ini file
        self.settings = QSettings(QSettings.Format.IniFormat,  # Or NativeFormat
                                  QSettings.Scope.UserScope,
                                  organization_name,
                                  application_name)
        self._init_defaults()

    def _init_defaults(self):
        """Initialize default settings if they don't exist."""
        defaults = {
            "mainWindowGeometry": None,  # Will be QByteArray
            "presentationScreenIndex": -1,  # -1 for auto/prompt, 0 for primary, 1+ for others
            "defaultImageDuration": 5000,  # milliseconds
            "mainVolume": 80,  # 0-100
            "backgroundVolume": 50,  # 0-100
            "backgroundLoop": False,
            "autoPlayNext": True,
            "lastPlaylistPath": "",
            "lastMediaBrowsePath": "",
            "lastBgAudioPath": "",
            # Keyboard bindings could be stored as a dictionary string or multiple keys
            # "keyboardBindings/playPause": "Space",
            # "keyboardBindings/nextItem": "Right",
        }
        for key, value in defaults.items():
            if not self.settings.contains(key):
                if value is not None:  # QSettings doesn't like storing None directly for some types
                    self.settings.setValue(key, value)
                # else: self.settings.remove(key) # Ensure it's not there

    def set_setting(self, key, value):
        """Saves a setting."""
        if value is None:
            self.settings.remove(key)  # Remove if value is None
        else:
            self.settings.setValue(key, value)
        self.settings.sync()  # Ensure changes are written

    def get_setting(self, key, default_value=None):
        """Retrieves a setting."""
        if not self.settings.contains(key) and default_value is not None:
            # If key does not exist, and a default is provided,
            # optionally store this default for next time.
            # self.settings.setValue(key, default_value)
            return default_value

        value = self.settings.value(key, defaultValue=default_value)

        # QSettings might return strings for numbers/bools with IniFormat on some platforms
        # or if the stored type is ambiguous. Try to convert common types.
        if isinstance(default_value, bool):
            if isinstance(value, str):
                return value.lower() == 'true'
            return bool(value)
        if isinstance(default_value, int):
            try:
                return int(value)
            except (ValueError, TypeError):
                return default_value
        if isinstance(default_value, float):
            try:
                return float(value)
            except (ValueError, TypeError):
                return default_value

        return value

    def get_keyboard_bindings(self):
        """Retrieves all keyboard bindings as a dictionary."""
        bindings = {}
        self.settings.beginGroup("keyboardBindings")
        for key in self.settings.childKeys():
            bindings[key] = self.settings.value(key)
        self.settings.endGroup()
        return bindings

    def set_keyboard_binding(self, action_name, key_sequence):
        """Sets a specific keyboard binding."""
        self.settings.beginGroup("keyboardBindings")
        self.settings.setValue(action_name, key_sequence)
        self.settings.endGroup()
        self.settings.sync()


if __name__ == '__main__':
    # Example usage (requires QApplication instance for QSettings)
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)  # Needed for QSettings

    sm = SettingsManager("TestOrg", "TestAppConfig")
    sm.set_setting("testInt", 123)
    sm.set_setting("testBool", True)
    sm.set_setting("testString", "hello world")
    sm.set_setting("testNone", None)

    print(f"TestInt: {sm.get_setting('testInt', 0)} (type: {type(sm.get_setting('testInt', 0))})")
    print(f"TestBool: {sm.get_setting('testBool', False)} (type: {type(sm.get_setting('testBool', False))})")
    print(f"TestString: {sm.get_setting('testString', '')} (type: {type(sm.get_setting('testString', ''))})")
    print(f"TestNone: {sm.get_setting('testNone', 'default for none')}")  # Should be 'default for none'
    print(f"NonExistent: {sm.get_setting('nonExistentKey', 'default val')}")

    sm.set_keyboard_binding("playPause", "Ctrl+P")
    print(f"Bindings: {sm.get_keyboard_bindings()}")

    # Clean up test settings (optional)
    # sm.settings.clear()
    # print("Test settings cleared.")
