STYLESHEET = """
/* ===== Global ===== */
* {
    font-family: "Segoe UI", "Inter", "Ubuntu", "Cantarell", "Noto Sans", sans-serif;
    font-size: 13px;
    color: #e4e6eb;
}

QWidget {
    background-color: #181a1b;
    color: #e4e6eb;
}

/* ===== Scrollbars ===== */
QScrollBar:vertical {
    background: #1e2022;
    width: 8px;
    margin: 0px;
    border: none;
}
QScrollBar::handle:vertical {
    background: #3a3d41;
    min-height: 30px;
    border-radius: 4px;
    margin: 2px;
}
QScrollBar::handle:vertical:hover {
    background: #4a4e54;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    background: #1e2022;
    height: 8px;
    margin: 0px;
    border: none;
}
QScrollBar::handle:horizontal {
    background: #3a3d41;
    min-width: 30px;
    border-radius: 4px;
    margin: 2px;
}
QScrollBar::handle:horizontal:hover {
    background: #4a4e54;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ===== Main Window ===== */
QMainWindow {
    background-color: #181a1b;
}

#centralWidget {
    background-color: #181a1b;
}

/* ===== Header / Title Bar Area ===== */
#headerFrame {
    background-color: #1e2022;
    border-bottom: 1px solid #2a2d30;
    border-radius: 0px;
}

#appTitleLabel {
    font-size: 20px;
    font-weight: 600;
    color: #ffffff;
    letter-spacing: -0.5px;
}

#versionLabel {
    font-size: 11px;
    color: #8b8e94;
    background-color: #2a2d30;
    padding: 2px 8px;
    border-radius: 10px;
}

/* ===== Input Area ===== */
#inputFrame {
    background-color: #1e2022;
    border: 1px solid #2a2d30;
    border-radius: 10px;
}

#urlInput {
    background-color: #252729;
    border: 1px solid #3a3d41;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 14px;
    color: #e4e6eb;
    selection-background-color: #3b82f6;
}
#urlInput:focus {
    border: 1px solid #3b82f6;
    background-color: #2a2d30;
}
#urlInput::placeholder {
    color: #6b6e74;
}

#pasteButton, #clearButton {
    background-color: #2a2d30;
    border: 1px solid #3a3d41;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 500;
    color: #e4e6eb;
}
#pasteButton:hover, #clearButton:hover {
    background-color: #3a3d41;
    border-color: #4a4e54;
}
#pasteButton:pressed, #clearButton:pressed {
    background-color: #252729;
}

/* ===== Action Buttons ===== */
#downloadButton {
    background-color: #3b82f6;
    border: none;
    border-radius: 10px;
    padding: 14px 32px;
    font-size: 15px;
    font-weight: 600;
    color: #ffffff;
}
#downloadButton:hover {
    background-color: #2563eb;
}
#downloadButton:pressed {
    background-color: #1d4ed8;
}
#downloadButton:disabled {
    background-color: #2a2d30;
    color: #6b6e74;
}

#settingsButton {
    background-color: #2a2d30;
    border: 1px solid #3a3d41;
    border-radius: 10px;
    padding: 14px 24px;
    font-size: 14px;
    font-weight: 500;
    color: #e4e6eb;
}
#settingsButton:hover {
    background-color: #3a3d41;
    border-color: #4a4e54;
}

/* ===== Progress Area ===== */
#progressFrame {
    background-color: #1e2022;
    border: 1px solid #2a2d30;
    border-radius: 10px;
}

#progressBar {
    background-color: #252729;
    border: none;
    border-radius: 6px;
    height: 12px;
    text-align: center;
    font-size: 11px;
    font-weight: 600;
    color: #ffffff;
}
#progressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #3b82f6, stop:1 #06b6d4);
    border-radius: 6px;
}

#progressInfoLabel {
    font-size: 12px;
    color: #9a9da3;
}

#speedLabel, #etaLabel {
    font-size: 12px;
    font-variant-numeric: tabular-nums;
    color: #9a9da3;
    background-color: #252729;
    padding: 4px 10px;
    border-radius: 6px;
    border: 1px solid #2a2d30;
}

/* ===== Console / Log Area ===== */
#consoleFrame {
    background-color: #0d1117;
    border: 1px solid #2a2d30;
    border-radius: 10px;
}

#consoleOutput {
    background-color: #0d1117;
    border: none;
    font-family: "JetBrains Mono", "Fira Code", "Consolas", monospace;
    font-size: 11px;
    line-height: 1.5;
    color: #c9d1d9;
    padding: 12px;
}

#consoleOutput .info { color: #58a6ff; }
#consoleOutput .warning { color: #d29922; }
#consoleOutput .error { color: #f85149; }
#consoleOutput .success { color: #3fb950; }
#consoleOutput .debug { color: #8b949e; }

#consoleToolbar {
    background-color: #161b22;
    border-bottom: 1px solid #2a2d30;
    border-radius: 10px 10px 0 0;
}

#consoleToolbar QPushButton {
    background-color: transparent;
    border: none;
    padding: 6px 12px;
    color: #8b949e;
    font-size: 12px;
    border-radius: 4px;
}
#consoleToolbar QPushButton:hover {
    background-color: #21262d;
    color: #c9d1d9;
}

/* ===== Tab Widget (Settings) ===== */
QTabWidget::pane {
    border: 1px solid #2a2d30;
    border-radius: 10px;
    background-color: #1e2022;
    margin-top: -1px;
}

QTabBar::tab {
    background-color: #1e2022;
    border: 1px solid #2a2d30;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 10px 20px;
    margin-right: 2px;
    color: #8b8e94;
    font-weight: 500;
}
QTabBar::tab:selected {
    background-color: #1e2022;
    border-color: #3b82f6;
    border-bottom: 1px solid #1e2022;
    color: #3b82f6;
}
QTabBar::tab:hover:!selected {
    background-color: #252729;
    color: #e4e6eb;
}

/* ===== Settings Panels ===== */
#settingsScrollArea {
    background-color: transparent;
    border: none;
}

#settingsContent {
    background-color: transparent;
}

.settingsGroup {
    background-color: #252729;
    border: 1px solid #2a2d30;
    border-radius: 10px;
    margin: 8px;
    padding: 16px;
}

.settingsGroupTitle {
    font-size: 13px;
    font-weight: 600;
    color: #3b82f6;
    padding-bottom: 8px;
    border-bottom: 1px solid #2a2d30;
    margin-bottom: 12px;
}

/* ===== Form Elements ===== */
QLabel {
    color: #c9d1d9;
}

#settingLabel {
    font-weight: 500;
    color: #e4e6eb;
    min-width: 180px;
}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #252729;
    border: 1px solid #3a3d41;
    border-radius: 6px;
    padding: 8px 12px;
    color: #e4e6eb;
    selection-background-color: #3b82f6;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #3b82f6;
    background-color: #2a2d30;
}
QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {
    border-color: #4a4e54;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    width: 12px;
    height: 12px;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #8b8e94;
}
QComboBox QAbstractItemView {
    background-color: #1e2022;
    border: 1px solid #2a2d30;
    border-radius: 6px;
    selection-background-color: #3b82f6;
    color: #e4e6eb;
    padding: 4px;
}

QCheckBox {
    color: #e4e6eb;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #3a3d41;
    background-color: #252729;
}
QCheckBox::indicator:checked {
    background-color: #3b82f6;
    border-color: #3b82f6;
}
QCheckBox::indicator:hover {
    border-color: #4a4e54;
}

QRadioButton {
    color: #e4e6eb;
    spacing: 8px;
}
QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 1px solid #3a3d41;
    background-color: #252729;
}
QRadioButton::indicator:checked {
    background-color: #3b82f6;
    border-color: #3b82f6;
}
QRadioButton::indicator:hover {
    border-color: #4a4e54;
}

QSlider::groove:horizontal {
    background: #2a2d30;
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #3b82f6;
    border: none;
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}
QSlider::handle:horizontal:hover {
    background: #60a5fa;
}

QTextEdit {
    background-color: #252729;
    border: 1px solid #3a3d41;
    border-radius: 6px;
    padding: 8px;
    color: #e4e6eb;
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 11px;
}
QTextEdit:focus {
    border-color: #3b82f6;
}

/* ===== Dialogs ===== */
QDialog {
    background-color: #1e2022;
    border: 1px solid #2a2d30;
    border-radius: 12px;
}

QMessageBox {
    background-color: #1e2022;
}
QMessageBox QLabel {
    color: #e4e6eb;
}
QMessageBox QPushButton {
    background-color: #2a2d30;
    border: 1px solid #3a3d41;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: 500;
    color: #e4e6eb;
    min-width: 80px;
}
QMessageBox QPushButton:hover {
    background-color: #3a3d41;
}
QMessageBox QPushButton:default {
    background-color: #3b82f6;
    border-color: #3b82f6;
    color: #ffffff;
}

/* ===== Tooltips ===== */
QToolTip {
    background-color: #1e2022;
    border: 1px solid #3a3d41;
    border-radius: 6px;
    padding: 8px 12px;
    color: #e4e6eb;
    font-size: 12px;
}

/* ===== Splitter ===== */
QSplitter::handle {
    background-color: #2a2d30;
}
QSplitter::handle:horizontal {
    width: 1px;
}
QSplitter::handle:vertical {
    height: 1px;
}

/* ===== List/Tree Views ===== */
QListView, QTreeView, QTableView {
    background-color: #1e2022;
    border: 1px solid #2a2d30;
    border-radius: 6px;
    outline: none;
    color: #e4e6eb;
}
QListView::item, QTreeView::item {
    padding: 6px 10px;
    border-radius: 4px;
}
QListView::item:selected, QTreeView::item:selected {
    background-color: #3b82f6;
    color: #ffffff;
}
QListView::item:hover, QTreeView::item:hover {
    background-color: #2a2d30;
}

/* ===== Progress Dialog ===== */
QProgressDialog {
    background-color: #1e2022;
    border: 1px solid #2a2d30;
    border-radius: 10px;
}
QProgressDialog QLabel {
    color: #e4e6eb;
}
QProgressDialog QProgressBar {
    background-color: #252729;
    border: none;
    border-radius: 6px;
    height: 10px;
}
QProgressDialog QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #3b82f6, stop:1 #06b6d4);
    border-radius: 6px;
}

/* ===== Custom Widgets ===== */
#dropArea {
    background-color: #1e2022;
    border: 2px dashed #3a3d41;
    border-radius: 12px;
}
#dropArea:hover {
    border-color: #3b82f6;
    background-color: #252729;
}
#dropArea.active {
    border-color: #3b82f6;
    background-color: #1e293b;
}

#statusBar {
    background-color: #1e2022;
    border-top: 1px solid #2a2d30;
    color: #8b8e94;
    font-size: 12px;
    padding: 4px 12px;
}

#updateButton {
    background-color: #10b981;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
    color: #ffffff;
}
#updateButton:hover {
    background-color: #059669;
}
#updateButton:disabled {
    background-color: #2a2d30;
    color: #6b6e74;
}
"""

APP_ID = "ytdlp-studio"