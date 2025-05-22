from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPalette, QColor, QScreen


class PresentationWindow(QWidget):
    """Window for displaying media on the secondary screen."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Presentation Output")
        self.setMinimumSize(QSize(640, 480))  # Minimum size

        # Set background to black
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("black"))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # Layout to hold the video frame or image
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # No margins

        # This QWidget will be used by VLC to draw video.
        # For images, you might use a QLabel, or also use VLC.
        # Using a generic QWidget for VLC is common.
        self.video_frame = QWidget(self)
        # Ensure video_frame also has a black background if it's not filled by video
        frame_palette = self.video_frame.palette()
        frame_palette.setColor(QPalette.ColorRole.Window, QColor("black"))
        self.video_frame.setPalette(frame_palette)
        self.video_frame.setAutoFillBackground(True)

        layout.addWidget(self.video_frame)
        self.setLayout(layout)

        self.target_screen_index = -1  # -1 means auto or primary if only one

    def set_target_screen_index(self, index):
        """Set the preferred screen index for this window."""
        screens = QApplication.screens()
        if 0 <= index < len(screens):
            self.target_screen_index = index
        elif len(screens) > 1:  # Auto-select non-primary if index is invalid
            primary_screen = QApplication.primaryScreen()
            for i, screen in enumerate(screens):
                if screen != primary_screen:
                    self.target_screen_index = i
                    break
            if self.target_screen_index == -1:  # Fallback if only primary or error
                self.target_screen_index = 0 if len(screens) > 0 else -1
        elif len(screens) == 1:
            self.target_screen_index = 0  # Only one screen
        else:
            self.target_screen_index = -1  # No screens? Should not happen with GUI

    def show_on_target_screen(self):
        """Moves and shows the window on the target screen, fullscreen."""
        screens = QApplication.screens()
        target_screen = None

        if 0 <= self.target_screen_index < len(screens):
            target_screen = screens[self.target_screen_index]
        elif len(screens) > 1:  # Default to first non-primary if not set or invalid
            primary = QApplication.primaryScreen()
            for screen in screens:
                if screen != primary:
                    target_screen = screen
                    break
            if not target_screen:  # If all are primary (e.g. cloned) or only one screen
                target_screen = QApplication.primaryScreen() if QApplication.primaryScreen() else screens[
                    0] if screens else None
        elif screens:  # Only one screen
            target_screen = screens[0]

        if target_screen:
            self.setGeometry(target_screen.geometry())
            self.showFullScreen()
        else:
            # Fallback: show normally if no specific screen found (e.g. headless)
            self.show()
            print("Warning: Target screen not found or not specified. Showing on default screen.")

    def winId(self):
        """Returns the window ID of the video_frame for VLC."""
        # Ensure the video_frame is created and has a valid window ID
        # This might require the widget to be shown or at least created.
        return self.video_frame.winId()

    def display_image(self, qimage_or_path):
        """
        Displays an image. For simplicity, this might be handled by VLC too.
        If using QLabel for images:
        """
        # If self.video_frame is a QLabel:
        # if isinstance(qimage_or_path, str):
        #     pixmap = QPixmap(qimage_or_path)
        # else: # Assume QImage
        #     pixmap = QPixmap.fromImage(qimage_or_path)
        # self.video_frame.setPixmap(pixmap.scaled(
        #     self.video_frame.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        # ))
        pass  # Placeholder - VLC will handle images via PlaybackController

    def clear_display(self):
        """Clears the display (e.g., show black background)."""
        # If using QLabel: self.video_frame.clear()
        # If VLC is used, stopping playback or playing a blank media will clear it.
        # The black background of video_frame should show.
        pass

    def closeEvent(self, event):
        # Potentially notify main window or playback controller
        print("PresentationWindow closing.")
        super().closeEvent(event)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    # Test presentation window
    # To test dual screen, you need to have a secondary monitor configured
    pres_win = PresentationWindow()

    # Try to auto-detect secondary screen for testing
    screens = QApplication.screens()
    if len(screens) > 1:
        for i, screen in enumerate(screens):
            if screen != QApplication.primaryScreen():
                pres_win.set_target_screen_index(i)
                break
    elif screens:
        pres_win.set_target_screen_index(0)

    pres_win.show_on_target_screen()
    sys.exit(app.exec())
