from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QMessageBox  # For error display

try:
    import vlc
except ImportError:
    vlc = None
    print("ERROR: python-vlc or VLC library not found. Playback will be disabled.")
    # Consider raising an exception or having a more robust fallback if VLC is critical


class BasePlaybackManager(QObject):
    """Base class for managing a VLC MediaPlayer instance."""
    # Signals for UI updates
    media_ended = pyqtSignal()
    media_position_changed = pyqtSignal(float)  # position as ratio 0.0-1.0
    media_duration_changed = pyqtSignal(int)  # duration in ms
    error_occurred = pyqtSignal(str)  # For reporting errors

    def __init__(self, hwnd=None):  # hwnd for video output if applicable
        super().__init__()
        if not vlc:
            self.instance = None
            self.player = None
            self.error_occurred.emit("VLC is not available.")
            return

        # Forcing some options for stability or features if needed
        # Example: vlc_args = ['--no-xlib'] # if on Linux and facing issues
        # self.instance = vlc.Instance(vlc_args)
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.current_media_path = None
        self.is_video_output_set = False

        if hwnd:
            self.set_video_output(hwnd)

        # VLC event manager
        self.event_manager = self.player.event_manager()
        self.event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_media_end_reached)
        self.event_manager.event_attach(vlc.EventType.MediaPlayerPositionChanged, self._on_media_position_changed)
        self.event_manager.event_attach(vlc.EventType.MediaPlayerEncounteredError, self._on_media_error)
        # MediaPlayerMediaChanged can be useful too
        self.event_manager.event_attach(vlc.EventType.MediaPlayerMediaChanged, self._on_media_changed)

    def _on_media_changed(self, event):
        """Called when the media in the player changes."""
        # This is a good place to fetch initial duration
        # Use a short QTimer to allow media to fully load before getting duration
        QTimer.singleShot(100, self._fetch_and_emit_duration)

    def _fetch_and_emit_duration(self):
        if self.player:
            duration = self.player.get_length()  # in ms
            self.media_duration_changed.emit(duration if duration > 0 else 0)

    def _on_media_end_reached(self, event):
        self.media_ended.emit()

    def _on_media_position_changed(self, event):
        if self.player and self.player.is_playing():  # Only emit if actually playing
            position = self.player.get_position()  # float 0.0 to 1.0
            self.media_position_changed.emit(position)

    def _on_media_error(self, event):
        # VLC errors are often not very descriptive by default.
        # For more details, you might need to check VLC logs or use more advanced error handling.
        error_msg = "An error occurred in VLC media player."
        # Try to get more info if possible (VLC API for errors is limited here)
        # For example, if media couldn't be opened.
        if self.current_media_path:
            error_msg = f"Error playing media: {self.current_media_path}"
        print(f"VLC Error Event: {event.type}")  # Log the event type
        self.error_occurred.emit(error_msg)

    def load_media(self, file_path, media_type="unknown"):
        if not self.player:
            self.error_occurred.emit("Player not initialized.")
            return False
        try:
            # For images, VLC might need specific options or might not be the best player
            # but it generally handles them.
            media = self.instance.media_new(file_path)
            # Add options if needed, e.g., for image duration if VLC handles it directly
            # if media_type == 'image' and hasattr(self, 'default_image_duration'):
            #    media.add_option(f':image-duration={self.default_image_duration // 1000}')

            self.player.set_media(media)
            self.current_media_path = file_path
            # Duration will be emitted by _on_media_changed -> _fetch_and_emit_duration
            return True
        except Exception as e:
            err_msg = f"Failed to load media '{file_path}': {e}"
            print(err_msg)
            self.error_occurred.emit(err_msg)
            self.current_media_path = None
            return False

    def play(self):
        if self.player and self.current_media_path:
            if self.player.play() == -1:  # Play returns -1 on error
                self.error_occurred.emit(f"Could not start playback for {self.current_media_path}.")
                return False
            return True
        elif not self.current_media_path:
            self.error_occurred.emit("No media loaded to play.")
        return False

    def pause(self):
        if self.player:
            self.player.pause()  # This is a toggle: pause/resume

    def resume(self):
        if self.player and not self.player.is_playing():
            # Ensure it's actually paused and not stopped/ended
            if self.player.get_state() == vlc.State.Paused:
                self.player.pause()  # Toggles back to play

    def stop(self):
        if self.player:
            self.player.stop()
            # self.current_media_path = None # Or keep it to allow replay

    def set_volume(self, volume):  # Volume 0-100
        if self.player:
            self.player.audio_set_volume(volume)

    def get_volume(self):
        if self.player:
            return self.player.audio_get_volume()
        return 0

    def set_position(self, position):  # Position 0.0 to 1.0
        if self.player and self.player.is_seekable():
            self.player.set_position(position)

    def get_position(self):
        if self.player:
            return self.player.get_position()
        return 0.0

    def get_duration(self):  # in ms
        if self.player:
            return self.player.get_length()
        return 0

    def is_playing(self):
        if self.player:
            return self.player.is_playing()
        return False

    def get_player_state(self):
        if self.player:
            return self.player.get_state()
        return None  # Or a default state like vlc.State.NothingSpecial

    def can_seek(self):
        if self.player:
            return self.player.is_seekable()
        return False

    def get_current_media_path(self):
        return self.current_media_path

    def set_video_output(self, hwnd):
        """Sets the window handle for video output."""
        if self.player and hwnd:
            try:
                self.player.set_hwnd(hwnd)
                self.is_video_output_set = True
            except Exception as e:
                # This can fail if hwnd is invalid or on some platforms with specific VLC builds
                err_msg = f"Failed to set video output (HWND): {e}"
                print(err_msg)
                self.error_occurred.emit(err_msg)
                self.is_video_output_set = False

    def release_player(self):
        if self.player:
            self.player.stop()
            self.player.release()
            self.player = None
        if self.instance:
            self.instance.release()
            self.instance = None
        print(f"{self.__class__.__name__} resources released.")


class PlaybackController(BasePlaybackManager):
    """Manages playback for the main playlist (images, videos, audio)."""

    def __init__(self, presentation_hwnd):
        super().__init__(hwnd=presentation_hwnd)
        self.current_media_type = None
        # self.default_image_duration = 5000 # ms, can be loaded from settings

    def play_media(self, file_path, media_type="unknown"):
        self.current_media_type = media_type
        if super().load_media(file_path, media_type):
            # Ensure video output is set if it's a visual media type
            if media_type in ['video', 'image'] and not self.is_video_output_set and self.player:
                # This assumes presentation_hwnd was passed and is valid.
                # The HWND might need to be re-applied if the presentation window was hidden/re-shown.
                # For simplicity, we assume it's set during init.
                # If issues, re-call self.player.set_hwnd(presentation_hwnd) here.
                print("Video output HWND should be set for visual media.")

            # For images, VLC might play them for a default short duration
            # or requires specific options. If an image is meant to be static
            # until the next item, custom handling or specific VLC options are needed.
            # Example: media.add_option(':image-duration=-1') for indefinite display (VLC specific)
            # For now, we assume VLC handles it or it plays for a default/set duration.

            return self.play()
        return False

    # Override release if specific cleanup needed
    # def release_player(self):
    #     super().release_player()


class BackgroundAudioManager(BasePlaybackManager):
    """Manages playback for the independent background audio track."""

    def __init__(self):
        super().__init__(hwnd=None)  # No video output for background audio
        self._loop = False

    def load_media(self, file_path):
        # Background audio is always 'audio' type
        return super().load_media(file_path, media_type="audio")

    def set_loop(self, loop_on):
        self._loop = loop_on
        if self.player:
            # For looping, one way is to re-play on 'MediaPlayerEndReached' if self._loop is True.
            # Some VLC versions/bindings might have direct loop options on media or player.
            # vlc.PlaybackMode.loop, vlc.PlaybackMode.repeat
            # self.player.set_playback_mode(vlc.PlaybackMode.loop if loop_on else vlc.PlaybackMode.default)
            # The above might not be available or work as expected in all python-vlc versions.
            # A common robust way is to handle it via the EndReached event.
            pass  # Looping handled in _on_media_end_reached_bg

    def _on_media_end_reached(self, event):
        """Override to handle looping for background audio."""
        if self._loop and self.current_media_path:
            print("Background audio looping...")
            # Re-load and play the same media.
            # Need to be careful to avoid deep recursion or rapid events if media is very short.
            # A small delay might be good.
            # self.play() # This might just replay from end. Better to seek to start or reload.
            self.player.set_media(self.instance.media_new(self.current_media_path))  # Re-set media
            self.play()
        else:
            super()._on_media_end_reached(event)  # Emit signal if not looping

    # Override release if specific cleanup needed
    # def release_player(self):
    #     super().release_player()

