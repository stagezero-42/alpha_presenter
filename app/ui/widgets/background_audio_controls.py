# app/ui/widgets/background_audio_controls.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider
from PyQt6.QtCore import Qt, pyqtSignal

class BackgroundAudioControls(QWidget):
    """Widget for background audio controls."""
    load_requested = pyqtSignal()
    play_pause_toggled = pyqtSignal()
    stop_clicked = pyqtSignal()
    loop_toggled = pyqtSignal(bool)
    volume_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Background Audio:"))

        self.load_button = QPushButton("Load BG Audio")
        self.load_button.clicked.connect(self.load_requested)
        self.play_pause_button = QPushButton("Play BG")
        self.play_pause_button.clicked.connect(self.play_pause_toggled)
        self.stop_button = QPushButton("Stop BG")
        self.stop_button.clicked.connect(self.stop_clicked)
        self.loop_button = QPushButton("Loop BG: OFF")
        self.loop_button.setCheckable(True)
        self.loop_button.toggled.connect(self.loop_toggled)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.load_button)
        buttons_layout.addWidget(self.play_pause_button)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.addWidget(self.loop_button)
        layout.addLayout(buttons_layout)

        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("BG Volume:"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50) # Default
        self.volume_slider.valueChanged.connect(self.volume_changed)
        volume_layout.addLayout(volume_layout)
        layout.addLayout(volume_layout)

    def set_playing_state(self, is_playing):
        self.play_pause_button.setText("Pause BG" if is_playing else "Play BG")

    def set_loop_state(self, is_looping):
        self.loop_button.setChecked(is_looping)
        self.loop_button.setText(f"Loop BG: {'ON' if is_looping else 'OFF'}")

    def set_volume(self, volume):
        self.volume_slider.setValue(volume)

