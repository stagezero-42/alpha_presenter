# Media Presenter Application

## 1. High-Level Overview

Media Presenter is a Python-based application designed for managing and displaying a single playlist of images, videos, and audio files on a secondary screen, while potentially playing an independent background audio track. The application is controlled from the primary screen and is intended to be packaged as a standalone Windows executable.

**Core Inspirations:**
This project draws inspiration from applications like OpenLP, aiming for a simplified feature set focused on a single playlist and straightforward media playback. The OpenLP project on GitLab (https://gitlab.com/openlp/openlp) can be a valuable resource for tackling specific challenges, especially regarding VLC integration and dual-screen management in a Qt environment.

## 2. Modular Architecture

The application will be built with a modular design to separate concerns and improve maintainability.

* **`main.py`**: Entry point of the application. Initializes the QApplication and the main window.
* **`app/ui_module.py`**: Handles the main control interface on the primary screen. This includes the main window, playlist view, media controls (play, pause, stop, next, previous, seek, volume for main playlist), and background audio controls (load, play/pause, stop, loop, volume). It interacts with other modules to reflect state and handle user actions.
* **`app/presentation_window.py`**: Manages the window displayed on the secondary screen. This window will show the visual media (images, videos) in fullscreen.
* **`app/playlist_module.py`**: Responsible for creating, modifying, saving (to JSON), and loading playlists. It defines the `MediaItem` class (attributes: file path, type, display name, duration, loop, start/end points) and the `PlaylistManager` class.
* **`app/playback_module.py`**: Manages media playback using `python-vlc`.
    * **`PlaybackController`**: Handles the main playlist media. It creates a VLC instance and a media player for images, videos, or standalone audio from the playlist. It directs visual output to the `PresentationWindow`.
    * **`BackgroundAudioManager`**: Manages the independent background audio track. It uses a separate VLC instance and media player.
* **`app/config_module.py`**: Manages application settings (e.g., secondary screen preference, default durations, keyboard bindings, last opened playlist, background audio settings) using `QSettings`.
    * **`SettingsManager`**: Provides an interface to load and save these settings.

## 3. Module Interaction Example: Playing a Playlist Item with Background Audio

1.  **User Action (UI Module)**: User selects a video in the playlist view (part of `ui_module.py`) and clicks "Play".
2.  **UI to Playlist Module**: The `ui_module.py` might query the `playlist_module.py` for the selected `MediaItem`'s details (e.g., path, type).
3.  **UI to Playback Module**: The `ui_module.py` instructs the `PlaybackController` (in `playback_module.py`) to play the selected `MediaItem`.
4.  **Playback Module (Main Media)**:
    * The `PlaybackController` gets the `MediaItem`.
    * It initializes its `vlc.MediaPlayer` instance.
    * It loads the media from the file path.
    * It tells the VLC player to render its video output onto the `PresentationWindow` (which is on the secondary screen).
    * It starts playback.
    * It emits signals for playback events (e.g., end of media, position changed) which the `ui_module.py` can connect to for updating controls.
5.  **Playback Module (Background Audio)**:
    * Concurrently, if the `BackgroundAudioManager` (in `playback_module.py`) has an audio file loaded and is in a playing state, its dedicated `vlc.MediaPlayer` instance continues playing the background audio. Its volume and playback state are controlled independently via the UI elements connected to the `BackgroundAudioManager`.
6.  **UI Update (UI Module)**: The `ui_module.py` updates playback controls (e.g., progress bar, pause button state) based on signals from the `PlaybackController`.

## 4. Key Technical Challenges & Considerations

* **Dual-Screen Management**:
    * Reliably detecting all connected screens (`QApplication.screens()`).
    * Allowing the user to select the presentation screen or auto-detecting a non-primary screen.
    * Moving the `PresentationWindow` to the correct screen and making it fullscreen.
    * Handling screen connection/disconnection events (more advanced).
* **`python-vlc` Integration**:
    * Managing multiple `vlc.Instance()` and `vlc.MediaPlayer()` objects (one for main playlist, one for background audio) to ensure they don't interfere.
    * Embedding video output into a Qt widget (`MediaPlayer.set_hwnd()` with `PresentationWindow.winId()`). This requires the widget to be created and visible.
    * Handling different media types (images might be displayed directly by Qt for simplicity, or also via VLC). For consistency and to leverage VLC's format support, using VLC for images is a good approach.
    * Event handling from VLC (e.g., `MediaPlayerEndReached`, `MediaPlayerPositionChanged`) to update the UI and control playlist flow.
* **Playlist Serialization**: Storing playlist data (list of `MediaItem` objects and settings) in a structured JSON format.
* **Configuration Persistence**: Using `QSettings` for platform-appropriate storage of application settings.
* **Keyboard Bindings**: Implementing a system where users can customize shortcuts. This involves capturing key events and mapping them to actions. `QShortcut` can be used, or a more central event filter.
* **Packaging**: Using PyInstaller will require careful configuration to include all necessary files, `python-vlc` binaries, and Qt libraries. Testing the packaged executable thoroughly is crucial.
* **Error Handling and Logging**: Robust error handling (e.g., file not found, unsupported format) and logging will be important for debugging and user experience.
* **Resource Management**: Properly releasing VLC instances and media players when they are no longer needed or when the application closes to avoid resource leaks.

## 5. Suggested Project Directory Structure


    media_presenter/
    ├── main.py                    # Application entry point
    ├── app/
    │   ├── init.py
    │   ├── ui_module.py           # Main window, controls, UI logic
    │   ├── presentation_window.py # Window for secondary screen display
    │   ├── playlist_module.py     # Playlist and MediaItem classes
    │   ├── playback_module.py     # PlaybackController and BackgroundAudioManager
    │   ├── config_module.py       # SettingsManager
    │   └── utils.py               # Optional: Utility functions, constants
    ├── resources/
    │   └── icons/
    │       └── placeholder_icon.png # Placeholder for app icons
    ├── requirements.txt             # Python dependencies
    └── README.md                    # This file


This structure provides a good starting point. As the application grows, sub-packages within `app/` (e.g., `app/ui/widgets/`) might become necessary.
