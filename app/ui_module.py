import sys
from PyQt6.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QListWidget, QListWidgetItem, QFileDialog,
                             QSlider, QSplitter, QMenuBar, QMessageBox, QDockWidget)
from PyQt6.QtGui import QAction, QScreen
from PyQt6.QtCore import Qt, QSize, QTimer, QFileInfo

from .presentation_window import PresentationWindow
from .playlist_module import PlaylistManager, MediaItem
from .playback_module import PlaybackController, BackgroundAudioManager
from .config_module import SettingsManager

# Import the new widget panels
try:
    from .ui.widgets.playlist_panel import PlaylistPanel
    from .ui.widgets.main_playback_controls import MainPlaybackControls
    from .ui.widgets.background_audio_controls import BackgroundAudioControls
except ImportError as e:
    # Fallback for direct execution or if 'ui.widgets' is not found initially
    # This might happen if you run ui_module.py directly without the project structure fully recognized
    # Or if __init__.py is missing in app/ui/
    print(f"ImportError for widgets: {e}. Attempting relative import for development.")
    try:
        # Assuming ui_module.py is in app/ and widgets are in app/ui/widgets/
        # This relative path might be tricky depending on how the script is run.
        # For a proper package structure, the first try block should work.
        from ui.widgets.playlist_panel import PlaylistPanel
        from ui.widgets.main_playback_controls import MainPlaybackControls
        from ui.widgets.background_audio_controls import BackgroundAudioControls
    except ImportError:
        # Final fallback for the case where ui_module.py is run from within app/
        # and ui/widgets is a sibling directory to ui_module.py's location.
        # This is less standard for package structures.
        # from ..ui.widgets.playlist_panel import PlaylistPanel
        # from ..ui.widgets.main_playback_controls import MainPlaybackControls
        # from ..ui.widgets.background_audio_controls import BackgroundAudioControls
        # For now, let's assume the first try works with a proper project setup.
        # If errors persist, ensure app/ui/__init__.py and app/ui/widgets/__init__.py exist
        # and that PyCharm recognizes app as a sources root.
        print("Could not import widget panels. Ensure app/ui/widgets path is correct and __init__.py files exist.")
        # As a last resort for the code to run without widgets if imports fail:
        PlaylistPanel = MainPlaybackControls = BackgroundAudioControls = None

# Placeholder for vlc
try:
    import vlc
except ImportError:
    vlc = None


class MainWindow(QMainWindow):
    """Main control window for the application."""

    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.playlist_manager = PlaylistManager(self.settings_manager)
        self.presentation_window = None
        self.playback_controller = None
        self.background_audio_manager = None

        self.setWindowTitle("Media Presenter Control")
        self.setGeometry(100, 100, 1200, 700)

        self._init_ui_structure()  # Create main UI structure and widgets
        self._init_vlc_components()
        self._connect_widget_signals()  # Connect signals from new widgets
        self._load_settings()
        self._connect_manager_signals()  # Connect signals from backend managers

        self.playback_update_timer = QTimer(self)
        self.playback_update_timer.setInterval(500)
        self.playback_update_timer.timeout.connect(self._update_main_playback_progress)

    def _init_ui_structure(self):
        """Initialize the main UI structure and instantiate custom widgets."""
        # --- Menu Bar ---
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        open_playlist_action = QAction("&Open Playlist", self)
        open_playlist_action.triggered.connect(self.load_playlist_dialog)
        file_menu.addAction(open_playlist_action)
        save_playlist_action = QAction("&Save Playlist", self)
        save_playlist_action.triggered.connect(self.save_playlist_dialog)
        file_menu.addAction(save_playlist_action)
        file_menu.addSeparator()
        settings_action = QAction("&Settings", self)
        settings_action.triggered.connect(self._open_settings_dialog)
        file_menu.addAction(settings_action)
        file_menu.addSeparator()
        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menubar.addMenu("&View")
        self.toggle_presentation_action = QAction("Show/Hide Presentation Screen", self)
        self.toggle_presentation_action.setCheckable(True)
        self.toggle_presentation_action.triggered.connect(self._toggle_presentation_window_visibility)
        view_menu.addAction(self.toggle_presentation_action)

        # --- Main Layout (Splitter) ---
        main_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.setCentralWidget(main_splitter)

        # --- Instantiate Custom Widgets ---
        if PlaylistPanel:
            self.playlist_panel = PlaylistPanel()
            main_splitter.addWidget(self.playlist_panel)
        else:
            # Create a placeholder if the import failed, to prevent crashes
            self.playlist_panel = None
            main_splitter.addWidget(QLabel("PlaylistPanel failed to load"))

        # --- Right Panel for Controls ---
        controls_container = QWidget()
        controls_layout = QVBoxLayout(controls_container)

        if MainPlaybackControls:
            self.main_playback_controls = MainPlaybackControls()
            controls_layout.addWidget(self.main_playback_controls)
        else:
            # Create a placeholder if the import failed
            self.main_playback_controls = None
            controls_layout.addWidget(QLabel("MainPlaybackControls failed to load"))

        if BackgroundAudioControls:
            self.bg_audio_controls = BackgroundAudioControls()
            controls_layout.addWidget(self.bg_audio_controls)
        else:
            # Create a placeholder if the import failed
            self.bg_audio_controls = None
            controls_layout.addWidget(QLabel("BackgroundAudioControls failed to load"))

        controls_layout.addStretch(1)
        main_splitter.addWidget(controls_container)
        main_splitter.setSizes([300, 700])

        self.statusBar().showMessage("Ready")

    def _init_vlc_components(self):
        if not vlc:
            QMessageBox.critical(self, "VLC Error", "python-vlc or VLC library not found.")
            return

        self._setup_presentation_window()

        if self.presentation_window and self.presentation_window.video_frame:
            self.playback_controller = PlaybackController(self.presentation_window.video_frame.winId())
            self.playback_controller.media_ended.connect(self._handle_main_media_ended)
            self.playback_controller.media_duration_changed.connect(self._update_main_media_duration_display)
            self.playback_controller.error_occurred.connect(self._show_playback_error)
            # Position changed is handled by timer for main playback
        else:
            # Only show warning if presentation_window itself exists but its frame doesn't
            if self.presentation_window:
                QMessageBox.warning(self, "UI Error", "Presentation window video frame not available for VLC.")
            # If presentation_window is None, _setup_presentation_window likely failed silently or was skipped.

        self.background_audio_manager = BackgroundAudioManager()
        if self.background_audio_manager.player is None and vlc:  # Check if VLC was available during BackgroundAudioManager init
            QMessageBox.warning(self, "VLC Error", "BG Audio Manager: VLC player init failed.")
        self.background_audio_manager.error_occurred.connect(self._show_playback_error)

    def _connect_widget_signals(self):
        """Connect signals from the new UI widgets to MainWindow methods."""
        if self.playlist_panel:  # Check if widget was successfully created
            self.playlist_panel.add_media_requested.connect(self.add_media_to_playlist_dialog)
            self.playlist_panel.remove_media_requested.connect(self.remove_selected_media_from_playlist)
            self.playlist_panel.item_double_clicked.connect(self._on_playlist_listwidget_item_double_clicked)
            # self.playlist_panel.items_reordered.connect(self._handle_playlist_reorder) # Implement if needed

        if self.main_playback_controls:  # Check if widget was successfully created
            self.main_playback_controls.play_pause_toggled.connect(self._toggle_main_play_pause)
            self.main_playback_controls.stop_clicked.connect(self._stop_main_playback)
            self.main_playback_controls.next_clicked.connect(self._play_next_item)
            self.main_playback_controls.previous_clicked.connect(self._play_previous_item)
            self.main_playback_controls.seek_requested.connect(self._seek_main_media)
            self.main_playback_controls.volume_changed.connect(self._set_main_playback_volume)
            self.main_playback_controls.slider_pressed.connect(self._pause_timer_on_seek)
            self.main_playback_controls.slider_released.connect(self._resume_timer_after_seek)

        if self.bg_audio_controls:  # Check if widget was successfully created
            self.bg_audio_controls.load_requested.connect(self._load_background_audio_dialog)
            self.bg_audio_controls.play_pause_toggled.connect(self._toggle_background_audio_play_pause)
            self.bg_audio_controls.stop_clicked.connect(self._stop_background_audio)
            self.bg_audio_controls.loop_toggled.connect(self._toggle_background_audio_loop)
            self.bg_audio_controls.volume_changed.connect(self._set_background_audio_volume)

    def _connect_manager_signals(self):
        """Connect signals from backend managers to UI update slots."""
        self.playlist_manager.playlist_changed.connect(self._update_playlist_panel_view)

    def _load_settings(self):
        geometry = self.settings_manager.get_setting("mainWindowGeometry")
        if geometry:
            self.restoreGeometry(geometry)

        if self.main_playback_controls:
            self.main_playback_controls.set_volume(self.settings_manager.get_setting("mainVolume", 80))
        if self.bg_audio_controls:
            self.bg_audio_controls.set_volume(self.settings_manager.get_setting("backgroundVolume", 50))
            loop_bg = self.settings_manager.get_setting("backgroundLoop", False)
            self.bg_audio_controls.set_loop_state(loop_bg)
            if self.background_audio_manager:  # Ensure manager exists
                self.background_audio_manager.set_loop(loop_bg)

        last_playlist = self.settings_manager.get_setting("lastPlaylistPath")
        if last_playlist:
            self.playlist_manager.load_playlist(last_playlist)  # This should trigger playlist_changed signal

        screen_index = self.settings_manager.get_setting("presentationScreenIndex", -1)
        if self.presentation_window:  # Check if presentation_window exists
            self.presentation_window.set_target_screen_index(screen_index)
            self.presentation_window.show_on_target_screen()
            if hasattr(self, 'toggle_presentation_action'):  # Ensure action exists
                self.toggle_presentation_action.setChecked(self.presentation_window.isVisible())

    def _save_settings(self):
        self.settings_manager.set_setting("mainWindowGeometry", self.saveGeometry())
        if self.main_playback_controls:
            self.settings_manager.set_setting("mainVolume", self.main_playback_controls.volume_slider.value())
        if self.bg_audio_controls:
            self.settings_manager.set_setting("backgroundVolume", self.bg_audio_controls.volume_slider.value())
            self.settings_manager.set_setting("backgroundLoop", self.bg_audio_controls.loop_button.isChecked())

        if self.playlist_manager.current_playlist_path:
            self.settings_manager.set_setting("lastPlaylistPath", self.playlist_manager.current_playlist_path)
        if self.presentation_window:
            self.settings_manager.set_setting("presentationScreenIndex", self.presentation_window.target_screen_index)

    def _setup_presentation_window(self):
        if not self.presentation_window:
            self.presentation_window = PresentationWindow()
            screen_idx = self.settings_manager.get_setting("presentationScreenIndex", -1)
            self.presentation_window.set_target_screen_index(screen_idx)
            self.presentation_window.show_on_target_screen()
            if hasattr(self, 'toggle_presentation_action'):  # Ensure action exists
                self.toggle_presentation_action.setChecked(self.presentation_window.isVisible())

    def _toggle_presentation_window_visibility(self, checked):
        if not self.presentation_window:
            self._setup_presentation_window()
        if self.presentation_window:  # Ensure it was created
            if checked:
                self.presentation_window.show_on_target_screen()
            else:
                self.presentation_window.hide()
        if hasattr(self, 'toggle_presentation_action'):  # Ensure action exists
            self.toggle_presentation_action.setChecked(
                self.presentation_window.isVisible() if self.presentation_window else False)

    def _open_settings_dialog(self):
        screens = QApplication.screens()
        if len(screens) > 1 and self.presentation_window:
            screen_names = [f"Screen {i + 1}: {s.name()} ({s.geometry().width()}x{s.geometry().height()})" for i, s in
                            enumerate(screens)]
            current_idx = self.presentation_window.target_screen_index
            # Simplified auto-selection for dialog default
            if not (0 <= current_idx < len(screens)): current_idx = 0

            from PyQt6.QtWidgets import QInputDialog  # Keep import local
            item, ok = QInputDialog.getItem(self, "Select Presentation Screen", "Screen:", screen_names, current_idx,
                                            False)
            if ok and item:
                selected_idx = screen_names.index(item)
                self.presentation_window.set_target_screen_index(selected_idx)
                self.presentation_window.show_on_target_screen()
                self.settings_manager.set_setting("presentationScreenIndex", selected_idx)
        else:
            QMessageBox.information(self, "Screen Settings",
                                    "Multiple screens not detected or presentation window unavailable.")
        self.statusBar().showMessage("Settings dialog accessed.")

    # --- Playlist Management Methods ---
    def add_media_to_playlist_dialog(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Add Media",
                                                     self.settings_manager.get_setting("lastMediaBrowsePath", ""),
                                                     "Media (*.mp4 *.avi *.mkv *.jpg *.jpeg *.png *.bmp *.gif *.mp3 *.wav *.aac *.ogg *.flac);;Video (*.mp4 *.avi *.mkv);;Images (*.jpg *.jpeg *.png *.bmp *.gif);;Audio (*.mp3 *.wav *.aac *.ogg *.flac);;All (*)")
        if file_paths:
            self.settings_manager.set_setting("lastMediaBrowsePath", QFileInfo(file_paths[0]).absolutePath())
            for path in file_paths:
                self.playlist_manager.add_item(path)
            # PlaylistManager's playlist_changed signal will call _update_playlist_panel_view

    def remove_selected_media_from_playlist(self, selected_list_widget_items):
        # The PlaylistPanel gives us QListWidgetItems. We need to find their rows to remove from PlaylistManager.
        if not self.playlist_panel: return

        rows_to_remove = sorted([self.playlist_panel.get_row(item) for item in selected_list_widget_items],
                                reverse=True)
        for row in rows_to_remove:
            if row >= 0:  # Ensure row index is valid
                self.playlist_manager.remove_item(row)

    def _update_playlist_panel_view(self):
        if self.playlist_panel:
            self.playlist_panel.update_view(self.playlist_manager.get_items())
            current_pl_index = self.playlist_manager.current_index
            if current_pl_index != -1:
                self.playlist_panel.set_current_row(current_pl_index)

    def load_playlist_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Playlist",
                                              self.settings_manager.get_setting("lastPlaylistPath", ""),
                                              "JSON Playlist (*.json);;All Files (*)")
        if path:
            try:
                self.playlist_manager.load_playlist(path)
                self.settings_manager.set_setting("lastPlaylistPath", path)
                self.statusBar().showMessage(f"Playlist loaded: {path}")
            except Exception as e:
                QMessageBox.critical(self, "Load Error", f"Failed to load playlist: {e}")

    def save_playlist_dialog(self):
        default_path = self.playlist_manager.current_playlist_path or self.settings_manager.get_setting(
            "lastPlaylistPath", "")
        path, _ = QFileDialog.getSaveFileName(self, "Save Playlist", default_path,
                                              "JSON Playlist (*.json);;All Files (*)")
        if path:
            try:
                self.playlist_manager.save_playlist(path)
                self.settings_manager.set_setting("lastPlaylistPath", path)
                self.statusBar().showMessage(f"Playlist saved: {path}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save playlist: {e}")

    def _on_playlist_listwidget_item_double_clicked(self, item_widget: QListWidgetItem):
        if self.playlist_panel:
            row = self.playlist_panel.get_row(item_widget)
            if self.playlist_manager.set_current_index(row):
                self._play_current_main_playlist_item()

    # --- Main Playback Control Methods ---
    def _play_current_main_playlist_item(self):
        if not self.playback_controller or not self.playback_controller.player:
            self._show_playback_error("Main playback controller not ready.")
            return
        current_item = self.playlist_manager.get_current_item()
        if current_item:
            self.statusBar().showMessage(f"Playing: {current_item.display_name}")
            if self.playback_controller.play_media(current_item.path, current_item.media_type):
                if self.main_playback_controls:
                    self.main_playback_controls.set_playing_state(True)
                self.playback_update_timer.start()
                if self.playlist_panel:  # Update selection in panel
                    self.playlist_panel.set_current_row(self.playlist_manager.current_index)
            # else: error is handled by playback_controller's signal
        else:
            self.statusBar().showMessage("No item to play.")
            self.playback_controller.stop()  # Ensure player is stopped
            if self.main_playback_controls:
                self.main_playback_controls.set_playing_state(False)
                self.main_playback_controls.reset_time_display()
            self.playback_update_timer.stop()

    def _toggle_main_play_pause(self):
        if not self.playback_controller or not self.playback_controller.player: return
        if self.playback_controller.is_playing():
            self.playback_controller.pause()
            if self.main_playback_controls: self.main_playback_controls.set_playing_state(False)
            self.playback_update_timer.stop()
            self.statusBar().showMessage("Paused.")
        else:
            # Check if media is loaded or if player is in a state that requires starting from current/first item
            if not self.playback_controller.get_current_media_path() or \
                    self.playback_controller.get_player_state() in [vlc.State.Ended, vlc.State.Stopped, vlc.State.Error,
                                                                    None, vlc.State.NothingSpecial]:
                self._play_current_main_playlist_item()
            else:  # Resume from paused state
                self.playback_controller.resume()
                if self.main_playback_controls: self.main_playback_controls.set_playing_state(True)
                self.playback_update_timer.start()
                self.statusBar().showMessage("Resumed.")

    def _stop_main_playback(self):
        if not self.playback_controller or not self.playback_controller.player: return
        self.playback_controller.stop()
        if self.main_playback_controls:
            self.main_playback_controls.set_playing_state(False)
            self.main_playback_controls.reset_time_display()
        self.playback_update_timer.stop()
        self.statusBar().showMessage("Stopped.")

    def _play_next_item(self):
        if self.playlist_manager.select_next():
            self._play_current_main_playlist_item()
        else:
            self.statusBar().showMessage("End of playlist.")

    def _play_previous_item(self):
        if self.playlist_manager.select_previous():
            self._play_current_main_playlist_item()
        else:
            self.statusBar().showMessage("Start of playlist.")

    def _handle_main_media_ended(self):
        self.statusBar().showMessage("Media finished.")
        if self.settings_manager.get_setting("autoPlayNext", True):
            self._play_next_item()
        else:
            if self.main_playback_controls:
                self.main_playback_controls.set_playing_state(False)
                # Current time should be at the end, total duration remains.
                # self.main_playback_controls.update_time_display(self.playback_controller.get_duration(), self.playback_controller.get_duration())
            self.playback_update_timer.stop()

    def _update_main_playback_progress(self):
        if not self.playback_controller or not self.playback_controller.player or \
                not self.playback_controller.is_playing() or not self.main_playback_controls:
            return

        current_ms = int(self.playback_controller.get_position() * self.playback_controller.get_duration())
        total_ms = self.playback_controller.get_duration()
        self.main_playback_controls.update_time_display(current_ms, total_ms)

    def _update_main_media_duration_display(self, duration_ms):
        if self.main_playback_controls:
            # When duration changes (new media loaded), reset current time display part
            self.main_playback_controls.update_time_display(0, duration_ms if duration_ms >= 0 else -1)

    def _seek_main_media(self, slider_value):  # slider_value is 0-1000
        if not self.playback_controller or not self.playback_controller.player or not self.playback_controller.can_seek():
            return

        slider_max = self.main_playback_controls.get_seek_slider_max() if self.main_playback_controls else 1000
        target_pos = float(slider_value) / slider_max if slider_max > 0 else 0.0  # Convert to 0.0-1.0
        self.playback_controller.set_position(target_pos)

        # Update time label immediately
        if self.main_playback_controls:
            duration_ms = self.playback_controller.get_duration()
            current_time_ms = int(target_pos * duration_ms)
            self.main_playback_controls.update_time_display(current_time_ms, duration_ms)

    def _pause_timer_on_seek(self):
        if self.playback_update_timer.isActive():
            self.playback_update_timer.stop()

    def _resume_timer_after_seek(self):
        if self.playback_controller and self.playback_controller.player and self.playback_controller.is_playing():
            self.playback_update_timer.start()
            # After user releases slider, ensure the display updates to actual player position
            self._update_main_playback_progress()

    def _set_main_playback_volume(self, volume):
        if not self.playback_controller or not self.playback_controller.player: return
        self.playback_controller.set_volume(volume)
        self.statusBar().showMessage(f"Main Volume: {volume}%")

    # --- Background Audio Control Methods ---
    def _load_background_audio_dialog(self):
        if not self.background_audio_manager or not self.background_audio_manager.player:
            self._show_playback_error("Background audio player not ready.")
            return
        path, _ = QFileDialog.getOpenFileName(self, "Load BG Audio",
                                              self.settings_manager.get_setting("lastBgAudioPath", ""),
                                              "Audio Files (*.mp3 *.wav *.aac *.ogg *.flac);;All Files (*)")
        if path:
            self.settings_manager.set_setting("lastBgAudioPath", QFileInfo(path).absolutePath())
            if self.background_audio_manager.load_media(path):
                if self.bg_audio_controls: self.bg_audio_controls.set_playing_state(False)
                self.statusBar().showMessage(f"BG audio loaded: {QFileInfo(path).fileName()}")

    def _toggle_background_audio_play_pause(self):
        if not self.background_audio_manager or not self.background_audio_manager.player: return
        if self.background_audio_manager.is_playing():
            self.background_audio_manager.pause()
            if self.bg_audio_controls: self.bg_audio_controls.set_playing_state(False)
            self.statusBar().showMessage("BG audio paused.")
        else:
            if self.background_audio_manager.get_current_media_path():
                if self.background_audio_manager.play():
                    if self.bg_audio_controls: self.bg_audio_controls.set_playing_state(True)
                    self.statusBar().showMessage("BG audio playing.")
            else:
                self.statusBar().showMessage("No BG audio loaded.")

    def _stop_background_audio(self):
        if not self.background_audio_manager or not self.background_audio_manager.player: return
        self.background_audio_manager.stop()
        if self.bg_audio_controls: self.bg_audio_controls.set_playing_state(False)
        self.statusBar().showMessage("BG audio stopped.")

    def _toggle_background_audio_loop(self, checked):
        if not self.background_audio_manager or not self.background_audio_manager.player: return
        self.background_audio_manager.set_loop(checked)
        if self.bg_audio_controls: self.bg_audio_controls.set_loop_state(checked)
        self.statusBar().showMessage(f"BG audio loop: {'ON' if checked else 'OFF'}")

    def _set_background_audio_volume(self, volume):
        if not self.background_audio_manager or not self.background_audio_manager.player: return
        self.background_audio_manager.set_volume(volume)
        self.statusBar().showMessage(f"BG Volume: {volume}%")

    # --- General ---
    def _show_playback_error(self, error_message):
        QMessageBox.warning(self, "Playback Error", error_message)
        self.statusBar().showMessage(f"Error: {error_message}")

    def closeEvent(self, event):
        self._save_settings()
        if self.playback_controller: self.playback_controller.release_player()
        if self.background_audio_manager: self.background_audio_manager.release_player()
        if self.presentation_window: self.presentation_window.close()
        super().closeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)


    # Create a dummy settings manager for testing
    class DummySettingsManager:
        def get_setting(self, key, default=None): return default

        def set_setting(self, key, value): pass


    settings_mgr = DummySettingsManager()
    main_win = MainWindow(settings_mgr)
    main_win.show()
    sys.exit(app.exec())
