# app/ui/widgets/main_playback_controls.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider
from PyQt6.QtCore import Qt, pyqtSignal

class MainPlaybackControls(QWidget):
    """Widget for main media playback controls."""
    play_pause_toggled = pyqtSignal()
    stop_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    previous_clicked = pyqtSignal()
    seek_requested = pyqtSignal(int) # position value from slider
    volume_changed = pyqtSignal(int) # volume 0-100
    slider_pressed = pyqtSignal()
    slider_released = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Main Playback:"))

        self.play_pause_button = QPushButton("Play")
        self.play_pause_button.clicked.connect(self.play_pause_toggled)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_clicked)
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.previous_clicked)
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next_clicked)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.prev_button)
        buttons_layout.addWidget(self.play_pause_button)
        buttons_layout.addWidget(self.next_button)
        buttons_layout.addWidget(self.stop_button)
        layout.addLayout(buttons_layout)

        seek_layout = QHBoxLayout()
        self.current_time_label = QLabel("00:00")
        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.sliderMoved.connect(self.seek_requested)
        self.seek_slider.sliderPressed.connect(self.slider_pressed)
        self.seek_slider.sliderReleased.connect(self.slider_released)
        self.total_time_label = QLabel("00:00")
        seek_layout.addWidget(self.current_time_label)
        seek_layout.addWidget(self.seek_slider, 1)
        seek_layout.addWidget(self.total_time_label)
        layout.addLayout(seek_layout)

        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80) # Default
        self.volume_slider.valueChanged.connect(self.volume_changed)
        volume_layout.addWidget(self.volume_slider)
        layout.addLayout(volume_layout)

    def set_playing_state(self, is_playing):
        self.play_pause_button.setText("Pause" if is_playing else "Play")

    def update_time_display(self, current_ms, total_ms):
        self.current_time_label.setText(self._format_time(current_ms))
        if total_ms >= 0 : # total_ms can be 0 if duration is unknown initially
            self.total_time_label.setText(self._format_time(total_ms))
            self.seek_slider.setEnabled(total_ms > 0)
            if total_ms > 0:
                self.seek_slider.setMaximum(1000) # Standard range for position 0.0-1.0
                # Update slider position only if user is not dragging it
                if not self.seek_slider.isSliderDown():
                    position_ratio = current_ms / total_ms if total_ms > 0 else 0
                    self.seek_slider.setValue(int(position_ratio * 1000))
            else: # Unknown duration
                self.seek_slider.setValue(0)
        else: # Explicitly handle negative total_ms as unknown
            self.total_time_label.setText("--:--")
            self.current_time_label.setText("--:--")
            self.seek_slider.setEnabled(False)
            self.seek_slider.setValue(0)


    def reset_time_display(self):
        self.current_time_label.setText("00:00")
        self.total_time_label.setText("00:00")
        self.seek_slider.setValue(0)
        self.seek_slider.setEnabled(False) # Usually disabled until media with duration loads

    def set_volume(self, volume):
        self.volume_slider.setValue(volume)

    def _format_time(self, milliseconds):
        if milliseconds < 0: milliseconds = 0
        seconds = (milliseconds // 1000) % 60
        minutes = (milliseconds // (1000 * 60)) % 60
        return f"{minutes:02d}:{seconds:02d}"

    def get_seek_slider_value(self):
        return self.seek_slider.value()

    def get_seek_slider_max(self):
        return self.seek_slider.maximum()
