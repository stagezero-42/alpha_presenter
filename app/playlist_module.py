import json
import os
from PyQt6.QtCore import QObject, pyqtSignal, QFileInfo


class MediaItem:
    """Represents a single item in the playlist."""

    def __init__(self, file_path, media_type=None, display_name=None, duration=None,
                 loop=False, start_point=None, end_point=None):
        self.file_path = file_path
        self.file_info = QFileInfo(file_path)

        if not self.file_info.exists():
            # Consider raising an error or handling this more gracefully
            print(f"Warning: File does not exist: {file_path}")
            # self.file_path = None # Or mark as invalid

        self.media_type = media_type if media_type else self._guess_media_type()
        self.display_name = display_name if display_name else self.file_info.fileName()

        # Duration: for images, this is display duration. For video/audio, it's actual length.
        # Actual length for video/audio will be fetched by VLC.
        self.duration = duration  # User-settable, especially for images

        self.loop = loop  # Specific to this item, e.g., for a short looping video/GIF
        self.start_point = start_point  # Playback start offset (in ms or seconds)
        self.end_point = end_point  # Playback end offset

    def _guess_media_type(self):
        """Guesses media type based on file extension."""
        if not self.file_path: return "unknown"
        ext = self.file_info.suffix().lower()
        if ext in ['jpg', 'jpeg', 'png', 'bmp', 'gif']:
            return 'image'
        elif ext in ['mp4', 'avi', 'wmv', 'mkv', 'mov', 'flv']:
            return 'video'
        elif ext in ['mp3', 'wav', 'aac', 'ogg', 'flac', 'm4a']:
            return 'audio'
        return 'unknown'

    def to_dict(self):
        """Serializes MediaItem to a dictionary for JSON storage."""
        return {
            'file_path': self.file_path,
            'media_type': self.media_type,
            'display_name': self.display_name,
            'duration': self.duration,
            'loop': self.loop,
            'start_point': self.start_point,
            'end_point': self.end_point,
        }

    @classmethod
    def from_dict(cls, data):
        """Deserializes MediaItem from a dictionary."""
        return cls(
            file_path=data.get('file_path'),
            media_type=data.get('media_type'),
            display_name=data.get('display_name'),
            duration=data.get('duration'),
            loop=data.get('loop', False),
            start_point=data.get('start_point'),
            end_point=data.get('end_point')
        )


class PlaylistManager(QObject):
    """Manages the playlist of media items."""
    playlist_changed = pyqtSignal()  # Emitted when the playlist is modified
    current_item_changed = pyqtSignal(MediaItem, int)  # Emitted when current item changes

    def __init__(self, settings_manager=None):  # settings_manager for default durations etc.
        super().__init__()
        self._items = []
        self.current_index = -1  # Index of the currently playing/selected item
        self.current_playlist_path = None
        self.settings_manager = settings_manager

    def add_item(self, file_path, media_type=None, position=-1):
        """Adds a new media item to the playlist."""
        try:
            # Default duration for images from settings
            default_image_duration = 5000  # ms, or get from settings_manager
            if self.settings_manager:
                default_image_duration = self.settings_manager.get_setting("defaultImageDuration", 5000)

            item = MediaItem(file_path, media_type)
            if item.media_type == 'image' and item.duration is None:
                item.duration = default_image_duration

            if not item.file_path or not QFileInfo(item.file_path).exists():
                print(f"Skipping invalid file: {file_path}")
                return

            if position == -1 or position >= len(self._items):
                self._items.append(item)
            else:
                self._items.insert(position, item)
            self.playlist_changed.emit()
        except Exception as e:
            print(f"Error adding item {file_path}: {e}")

    def remove_item(self, index):
        """Removes an item from the playlist by index."""
        if 0 <= index < len(self._items):
            del self._items[index]
            if self.current_index >= index:
                # Adjust current_index if an item before or at current_index is removed
                if self.current_index == index and self.current_index == len(self._items):  # last item removed
                    self.current_index -= 1
                elif self.current_index > index:
                    self.current_index -= 1

            self.playlist_changed.emit()

    def move_item(self, old_index, new_index):
        """Moves an item within the playlist."""
        if 0 <= old_index < len(self._items) and 0 <= new_index < len(self._items):
            item = self._items.pop(old_index)
            self._items.insert(new_index, item)
            # Adjust current_index if affected
            if self.current_index == old_index:
                self.current_index = new_index
            elif old_index < self.current_index <= new_index:
                self.current_index -= 1
            elif new_index <= self.current_index < old_index:
                self.current_index += 1
            self.playlist_changed.emit()

    def get_items(self):
        """Returns the list of all media items."""
        return self._items

    def get_item(self, index):
        """Returns a media item at a specific index."""
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def get_current_item(self):
        """Returns the currently selected media item."""
        return self.get_item(self.current_index)

    def set_current_index(self, index):
        """Sets the current item index."""
        if 0 <= index < len(self._items):
            self.current_index = index
            self.current_item_changed.emit(self._items[index], index)
            return True
        elif not self._items and index == -1:  # Allow setting to -1 if empty
            self.current_index = -1
            # self.current_item_changed.emit(None, -1) # Or handle None emission carefully
            return True
        return False

    def select_next(self):
        """Selects the next item in the playlist. Returns True if successful."""
        if not self._items: return False
        if self.current_index < len(self._items) - 1:
            self.current_index += 1
            self.current_item_changed.emit(self._items[self.current_index], self.current_index)
            return True
        return False  # At the end of the playlist

    def select_previous(self):
        """Selects the previous item in the playlist. Returns True if successful."""
        if not self._items: return False
        if self.current_index > 0:
            self.current_index -= 1
            self.current_item_changed.emit(self._items[self.current_index], self.current_index)
            return True
        return False  # At the beginning of the playlist

    def clear_playlist(self):
        """Clears all items from the playlist."""
        self._items.clear()
        self.current_index = -1
        self.current_playlist_path = None
        self.playlist_changed.emit()

    def save_playlist(self, file_path):
        """Saves the current playlist to a JSON file."""
        playlist_data = {
            'settings': {
                'default_image_duration': self.settings_manager.get_setting("defaultImageDuration",
                                                                            5000) if self.settings_manager else 5000
            },
            'items': [item.to_dict() for item in self._items]
        }
        try:
            with open(file_path, 'w') as f:
                json.dump(playlist_data, f, indent=4)
            self.current_playlist_path = file_path
        except IOError as e:
            print(f"Error saving playlist to {file_path}: {e}")
            raise

    def load_playlist(self, file_path):
        """Loads a playlist from a JSON file."""
        try:
            with open(file_path, 'r') as f:
                playlist_data = json.load(f)

            self.clear_playlist()  # Clear existing before loading

            # Load global settings from playlist if any
            # Example: self.settings_manager.set_setting("defaultImageDuration", playlist_data.get('settings', {}).get('default_image_duration', 5000))

            loaded_items = []
            for item_data in playlist_data.get('items', []):
                item = MediaItem.from_dict(item_data)
                if item.file_path and QFileInfo(item.file_path).exists():
                    loaded_items.append(item)
                else:
                    print(f"Warning: File '{item_data.get('file_path')}' not found, skipped from playlist.")

            self._items = loaded_items
            if self._items:
                self.current_index = 0  # Select first item by default
            else:
                self.current_index = -1

            self.current_playlist_path = file_path
            self.playlist_changed.emit()
            if self.get_current_item():  # Emit if an item is now current
                self.current_item_changed.emit(self.get_current_item(), self.current_index)

        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading playlist from {file_path}: {e}")
            raise
