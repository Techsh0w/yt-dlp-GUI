import sys
import os

os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QCoreApplication

from src.main_window import MainWindow


def main():
    QCoreApplication.setApplicationName("YT-DLP Studio")
    QCoreApplication.setApplicationVersion("1.0.0")
    QCoreApplication.setOrganizationName("YT-DLP-Studio")
    QCoreApplication.setOrganizationDomain("ytdlp-studio.local")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # High-DPI: crisp scaling on Fedora/GNOME, Ubuntu, Windows and macOS.
    try:
        app.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.RoundPreferFloor)
    except Exception:
        pass

    # Eye-catching modern dark theme.
    try:
        from src.styles import STYLESHEET
        app.setStyleSheet(STYLESHEET)
    except Exception as exc:
        print(f"Could not apply stylesheet: {exc}", file=sys.stderr)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()