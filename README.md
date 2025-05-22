# Media Presenter Application

## 1. High-Level Overview

Media Presenter is a Python-based application designed for managing and displaying a single playlist of images, videos, and audio files on a secondary screen, while potentially playing an independent background audio track. The application is controlled from the primary screen and is intended to be packaged as a standalone Windows executable.

**Core Inspirations:**
This project draws inspiration from applications like OpenLP, aiming for a simplified feature set focused on a single playlist and straightforward media playback. The OpenLP project on GitLab (https://gitlab.com/openlp/openlp) can be a valuable resource for tackling specific challenges, especially regarding VLC integration and dual-screen management in a Qt environment.

## 2. Modular Architecture

The application is built with a modular design to separate concerns and improve maintainability.

* **`main.py`**: Entry point of the application. Initializes the QApplication and the main window.
* **`app/ui_module.py`**: Contains the `MainWindow` class, which acts as the main orchestrator for the user interface on the primary screen. It initializes and manages various UI panels.
    * **`app/ui/widgets/` (New Sub-package):** Contains dedicated QWidget subclasses for different UI panels:
        * `playlist_panel.py` (`PlaylistPanel`): Manages the visual list of media items, allowing users to add, remove, and reorder items. Emits signals for user interactions.
        * `main_playback_controls.py` (`MainPlaybackControls`): Provides UI elements (buttons, sliders) for controlling the main playlist media (play, pause, stop, next, previous, seek, volume). Emits signals for control actions.
        * `background_audio_controls.py` (`BackgroundAudioControls`): Offers UI elements for managing the independent background audio track (load, play/pause, stop, loop, volume). Emits signals for control actions.
* **`app/presentation_window.py`**: Manages the `PresentationWindow` displayed on the secondary screen. This window will show the visual media (images, videos) in fullscreen.
* **`app/playlist_module.py`**: Responsible for creating, modifying, saving (to JSON), and loading playlists. It defines the `MediaItem` class (attributes: file path, type, display name, duration, loop, start/end points) and the `PlaylistManager` class.
* **`app/playback_module.py`**: Manages media playback using `python-vlc`.
    * `PlaybackController`: Handles the main playlist media. It creates a VLC instance and a media player for images, videos, or standalone audio from the playlist. It directs visual output to the `PresentationWindow`.
    * `BackgroundAudioManager`: Manages the independent background audio track. It uses a separate VLC instance and media player.
* **`app/config_module.py`**: Manages application settings (e.g., secondary screen preference, default durations, keyboard bindings, last opened playlist, background audio settings) using `QSettings`.
    * `SettingsManager`: Provides an interface to load and save these settings.
* **`app/utils.py`**: Optional module for utility functions and constants.

## 3. Module Interaction Example: Playing a Playlist Item with Background Audio

1.  **User Action (UI Module - PlaylistPanel)**: User selects a video in the `PlaylistPanel` (managed by `app/ui/widgets/playlist_panel.py`) and double-clicks it.
2.  **PlaylistPanel to MainWindow**: The `PlaylistPanel` emits a signal (e.g., `item_double_clicked`). The `MainWindow` (in `app/ui_module.py`) has a slot connected to this signal.
3.  **MainWindow to Playlist Module**: The `MainWindow`'s slot queries the `PlaylistManager` (in `app/playlist_module.py`) to set the current item and get its details (e.g., path, type).
4.  **MainWindow to Playback Module**: The `MainWindow` instructs the `PlaybackController` (in `app/playback_module.py`) to play the selected `MediaItem`.
5.  **Playback Module (Main Media)**:
    * The `PlaybackController` gets the `MediaItem`.
    * It initializes its `vlc.MediaPlayer` instance.
    * It loads the media from the file path.
    * It tells the VLC player to render its video output onto the `PresentationWindow` (which is on the secondary screen).
    * It starts playback.
    * It emits signals for playback events (e.g., end of media, position changed, duration changed).
6.  **Playback Module (Background Audio)**:
    * Concurrently, if the `BackgroundAudioManager` (in `app/playback_module.py`) has an audio file loaded and is in a playing state, its dedicated `vlc.MediaPlayer` instance continues playing the background audio. Its volume and playback state are controlled independently via the `BackgroundAudioControls` widget, with signals handled by `MainWindow`.
7.  **Playback Module to MainWindow to UI Widgets**:
    * Signals from `PlaybackController` (e.g., `media_duration_changed`, `media_ended`) are connected to slots in `MainWindow`.
    * These slots in `MainWindow` then call methods on the appropriate UI widgets (e.g., `MainPlaybackControls.update_time_display()`, `MainPlaybackControls.set_playing_state()`) to update the control interface.

## 4. Key Technical Challenges & Considerations

* **Dual-Screen Management**:
    * Reliably detecting all connected screens (`QApplication.screens()`).
    * Allowing the user to select the presentation screen or auto-detecting a non-primary screen.
    * Moving the `PresentationWindow` to the correct screen and making it fullscreen.
* **`python-vlc` Integration**:
    * Managing multiple `vlc.Instance()` and `vlc.MediaPlayer()` objects.
    * Embedding video output into a Qt widget (`MediaPlayer.set_hwnd()` with `PresentationWindow.video_frame.winId()`).
    * Handling different media types and VLC events.
* **Playlist Serialization**: Storing playlist data in a structured JSON format.
* **Configuration Persistence**: Using `QSettings` for platform-appropriate storage.
* **Keyboard Bindings**: Implementing a system for customizable shortcuts.
* **Packaging**: Using PyInstaller for Windows executables.
* **Error Handling and Logging**: Implementing robust error handling and logging.
* **Resource Management**: Properly releasing VLC instances and media players.

## 5. Suggested Project Directory Structure

    
    media_presenter/
    ├── main.py                 # Application entry point
    ├── app/
    │   ├── init.py
    │   ├── ui_module.py          # MainWindow class, orchestrates UI panels
    │   ├── presentation_window.py # Window for secondary screen display
    │   ├── playlist_module.py    # PlaylistManager and MediaItem classes
    │   ├── playback_module.py    # PlaybackController and BackgroundAudioManager
    │   ├── config_module.py      # SettingsManager
    │   ├── ui/                   # Sub-package for UI components
    │   │   ├── init.py
    │   │   └── widgets/          # Dedicated QWidget subclasses
    │   │       ├── init.py
    │   │       ├── playlist_panel.py
    │   │       ├── main_playback_controls.py
    │   │       └── background_audio_controls.py
    │   └── utils.py              # Optional: Utility functions, constants
    ├── resources/
    │   └── icons/
    │       └── placeholder_icon.png
    ├── requirements.txt          # Python dependencies
    └── README.md                 # This file


This structure provides a good starting point. As the application grows, further sub-packages or modules might become necessary.
