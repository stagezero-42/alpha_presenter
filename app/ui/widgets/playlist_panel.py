# app/ui/widgets/playlist_panel.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal

class PlaylistPanel(QWidget):
    """Widget for displaying and managing the playlist."""
    add_media_requested = pyqtSignal()
    remove_media_requested = pyqtSignal(list) # list of selected QListWidgetItems
    item_double_clicked = pyqtSignal(QListWidgetItem)
    items_reordered = pyqtSignal() # Emitted after drag-drop

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Playlist:"))
        self.playlist_widget = QListWidget()
        self.playlist_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.playlist_widget.itemDoubleClicked.connect(self.item_double_clicked)
        # For drag and drop reordering, QListWidget handles it internally.
        # If you need to sync with PlaylistManager after a drop,
        # you might need to connect to model().rowsMoved or similar,
        # or handle it by rebuilding the playlist from the widget order.
        # For simplicity, we can emit a generic items_reordered signal.
        # A more robust way is to subclass QListWidget and override dropEvent.
        # self.playlist_widget.model().rowsMoved.connect(lambda: self.items_reordered.emit())


        layout.addWidget(self.playlist_widget)

        buttons_layout = QHBoxLayout()
        add_media_button = QPushButton("Add Files")
        add_media_button.clicked.connect(self.add_media_requested)
        buttons_layout.addWidget(add_media_button)

        remove_media_button = QPushButton("Remove Selected")
        remove_media_button.clicked.connect(self._on_remove_media_clicked)
        buttons_layout.addWidget(remove_media_button)
        layout.addLayout(buttons_layout)

    def _on_remove_media_clicked(self):
        selected_items = self.playlist_widget.selectedItems()
        if selected_items:
            self.remove_media_requested.emit(selected_items)

    def update_view(self, media_items):
        """Updates the QListWidget with items."""
        current_selection = self.playlist_widget.currentRow() # Preserve selection if possible
        self.playlist_widget.clear()
        for i, media_item in enumerate(media_items):
            # Assuming media_item has display_name and media_type attributes
            item_widget = QListWidgetItem(f"{i+1}. {media_item.display_name} ({media_item.media_type})")
            item_widget.setData(Qt.ItemDataRole.UserRole, media_item) # Store MediaItem object
            self.playlist_widget.addItem(item_widget)
        if 0 <= current_selection < self.playlist_widget.count():
            self.playlist_widget.setCurrentRow(current_selection)


    def get_all_list_widget_items(self):
        """Returns all QListWidgetItems in their current order."""
        return [self.playlist_widget.item(i) for i in range(self.playlist_widget.count())]

    def set_current_row(self, index):
        if 0 <= index < self.playlist_widget.count():
            self.playlist_widget.setCurrentRow(index)

    def get_selected_items_data(self):
        """Returns the MediaItem data from selected QListWidgetItems."""
        return [item.data(Qt.ItemDataRole.UserRole) for item in self.playlist_widget.selectedItems()]

    def get_item_data_at_row(self, row):
        item = self.playlist_widget.item(row)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def get_row(self, item_widget):
        return self.playlist_widget.row(item_widget)
