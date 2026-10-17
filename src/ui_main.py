"""Complete PySide6 layout — pure widgets, no worker logic.

``Ui_MainWindow.setupUi`` builds every widget the app needs with stable
``objectName`` values that match the QSS theme in ``styles.py``. All runtime
wiring (threads, signals, settings I/O) lives in ``main_window.py``.
"""

from __future__ import annotations

from typing import Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from .options import (
    AUDIO_FORMATS,
    BROWSERS,
    FORMAT_PRESETS,
    MERGE_FORMATS,
    OUTTMPL_PRESETS,
    SPONSOR_CATEGORIES,
    SUB_FORMATS,
)


def _group(title: str) -> tuple[QGroupBox, QVBoxLayout]:
    box = QGroupBox(title)
    box.setProperty("class", "settingsGroup")
    lay = QVBoxLayout(box)
    lay.setSpacing(8)
    lay.setContentsMargins(14, 14, 14, 14)
    return box, lay


def _form_row(label_text: str, widget: QWidget, tooltip: str = "") -> QHBoxLayout:
    row = QHBoxLayout()
    lab = QLabel(label_text)
    lab.setObjectName("settingLabel")
    lab.setMinimumWidth(170)
    if tooltip:
        lab.setToolTip(tooltip)
        widget.setToolTip(tooltip)
    row.addWidget(lab)
    row.addWidget(widget, 1)
    return row


def _scroll_tab() -> tuple[QWidget, QVBoxLayout]:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setObjectName("settingsScrollArea")
    inner = QWidget()
    inner.setObjectName("settingsContent")
    lay = QVBoxLayout(inner)
    lay.setSpacing(10)
    lay.setContentsMargins(10, 10, 10, 10)
    lay.addStretch(1)
    scroll.setWidget(inner)
    holder = QWidget()
    hl = QVBoxLayout(holder)
    hl.setContentsMargins(0, 0, 0, 0)
    hl.addWidget(scroll)
    # insert content above the stretch: return inner layout; caller inserts at 0
    return holder, lay


class Ui_MainWindow:
    """Builds the main window UI. Access widgets as attributes on this object."""

    def setupUi(self, win: QMainWindow) -> None:
        win.setObjectName("MainWindow")
        win.setWindowTitle("YT-DLP Studio — fast yt-dlp desktop client")
        win.resize(1180, 840)
        win.setMinimumSize(920, 680)

        self.centralWidget = QWidget(win)
        self.centralWidget.setObjectName("centralWidget")
        win.setCentralWidget(self.centralWidget)
        main = QVBoxLayout(self.centralWidget)
        main.setSpacing(10)
        main.setContentsMargins(14, 12, 14, 12)

        # -- header ------------------------------------------------------
        self.headerFrame = QFrame()
        self.headerFrame.setObjectName("headerFrame")
        self.headerFrame.setFixedHeight(58)
        hl = QHBoxLayout(self.headerFrame)
        hl.setContentsMargins(14, 8, 14, 8)
        self.appTitleLabel = QLabel("YT-DLP Studio")
        self.appTitleLabel.setObjectName("appTitleLabel")
        self.versionLabel = QLabel("v1.0.0")
        self.versionLabel.setObjectName("versionLabel")
        self.engineVersionLabel = QLabel("engine: …")
        self.engineVersionLabel.setToolTip("Installed yt-dlp library version")
        self.engineVersionLabel.setStyleSheet("color:#8b8e94; font-size:11px;")
        hl.addWidget(self.appTitleLabel)
        hl.addWidget(self.versionLabel)
        hl.addSpacing(8)
        hl.addWidget(self.engineVersionLabel)
        hl.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.headerHint = QLabel("Linux • Windows • macOS  —  threaded, zero-freeze downloads")
        self.headerHint.setStyleSheet("color:#6b6e74; font-size:11px;")
        hl.addWidget(self.headerHint)
        main.addWidget(self.headerFrame)

        # -- URL / queue input -------------------------------------------
        self.inputFrame = QFrame()
        self.inputFrame.setObjectName("inputFrame")
        il = QVBoxLayout(self.inputFrame)
        il.setSpacing(8)
        il.setContentsMargins(14, 12, 14, 12)

        row1 = QHBoxLayout()
        self.urlInput = QLineEdit()
        self.urlInput.setObjectName("urlInput")
        self.urlInput.setPlaceholderText("Paste a video, playlist or channel URL…  (Enter = add to queue)")
        self.urlInput.setClearButtonEnabled(False)
        row1.addWidget(self.urlInput, 1)
        self.pasteButton = QPushButton("Paste")
        self.pasteButton.setObjectName("pasteButton")
        self.clearButton = QPushButton("Clear")
        self.clearButton.setObjectName("clearButton")
        row1.addWidget(self.pasteButton)
        row1.addWidget(self.clearButton)
        il.addLayout(row1)

        row2 = QHBoxLayout()
        self.addQueueButton = QPushButton("Add to queue")
        self.addQueueButton.setObjectName("settingsButton")
        self.addQueueButton.setToolTip("Add the URL above to the download queue")
        self.fetchFormatsButton = QPushButton("Fetch formats")
        self.fetchFormatsButton.setObjectName("settingsButton")
        self.fetchFormatsButton.setToolTip("Probe available streams without downloading (runs in background)")
        self.downloadButton = QPushButton("Download")
        self.downloadButton.setObjectName("downloadButton")
        self.downloadButton.setToolTip("Start downloading the whole queue with current settings")
        self.cancelButton = QPushButton("Cancel")
        self.cancelButton.setObjectName("settingsButton")
        self.cancelButton.setEnabled(False)
        row2.addWidget(self.addQueueButton)
        row2.addWidget(self.fetchFormatsButton)
        row2.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        row2.addWidget(self.cancelButton)
        row2.addWidget(self.downloadButton)
        il.addLayout(row2)

        row3 = QHBoxLayout()
        self.queueList = QListWidget()
        self.queueList.setMaximumHeight(86)
        self.queueList.setToolTip("Download queue — every entry is processed in order")
        row3.addWidget(self.queueList, 1)
        qbtns = QVBoxLayout()
        self.removeQueueButton = QPushButton("Remove")
        self.removeQueueButton.setObjectName("pasteButton")
        self.clearQueueButton = QPushButton("Clear all")
        self.clearQueueButton.setObjectName("clearButton")
        qbtns.addWidget(self.removeQueueButton)
        qbtns.addWidget(self.clearQueueButton)
        qbtns.addStretch(1)
        row3.addLayout(qbtns)
        il.addLayout(row3)
        main.addWidget(self.inputFrame)

        # -- progress ------------------------------------------------------
        self.progressFrame = QFrame()
        self.progressFrame.setObjectName("progressFrame")
        pl = QVBoxLayout(self.progressFrame)
        pl.setSpacing(6)
        pl.setContentsMargins(14, 10, 14, 10)
        top = QHBoxLayout()
        self.progressInfoLabel = QLabel("Ready — paste a URL to begin.")
        self.progressInfoLabel.setObjectName("progressInfoLabel")
        self.progressInfoLabel.setStyleSheet("color:#c9d1d9;")
        top.addWidget(self.progressInfoLabel, 1)
        self.speedLabel = QLabel("—")
        self.speedLabel.setObjectName("speedLabel")
        self.etaLabel = QLabel("ETA —")
        self.etaLabel.setObjectName("etaLabel")
        top.addWidget(self.speedLabel)
        top.addWidget(self.etaLabel)
        pl.addLayout(top)
        self.progressBar = QProgressBar()
        self.progressBar.setObjectName("progressBar")
        self.progressBar.setRange(0, 1000)
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(True)
        pl.addWidget(self.progressBar)
        self.probeInfoLabel = QLabel("")
        self.probeInfoLabel.setStyleSheet("color:#8b8e94; font-size:11px;")
        self.probeInfoLabel.setWordWrap(True)
        pl.addWidget(self.probeInfoLabel)
        self.formatTable = QTableWidget(0, 6)
        self.formatTable.setHorizontalHeaderLabels(["ID", "Ext", "Res", "Codecs", "Size", "Note"])
        self.formatTable.horizontalHeader().setStretchLastSection(True)
        self.formatTable.setMaximumHeight(130)
        self.formatTable.setVisible(False)
        pl.addWidget(self.formatTable)
        main.addWidget(self.progressFrame)

        # -- splitter: tabs + console --------------------------------------
        splitter = QSplitter(Qt.Vertical)

        self.tabWidget = QTabWidget()
        self.tabWidget.setTabPosition(QTabWidget.North)
        self._build_general_tab()
        self._build_playlist_tab()
        self._build_network_tab()
        self._build_subs_tab()
        self._build_postproc_tab()
        self._build_engine_tab()
        splitter.addWidget(self.tabWidget)

        self.consoleFrame = QFrame()
        self.consoleFrame.setObjectName("consoleFrame")
        cl = QVBoxLayout(self.consoleFrame)
        cl.setSpacing(0)
        cl.setContentsMargins(0, 0, 0, 0)
        self.consoleToolbar = QFrame()
        self.consoleToolbar.setObjectName("consoleToolbar")
        ctl = QHBoxLayout(self.consoleToolbar)
        ctl.setContentsMargins(10, 4, 10, 4)
        title = QLabel("Terminal console  (live yt-dlp output)")
        title.setStyleSheet("color:#c9d1d9; font-weight:600; font-size:12px;")
        ctl.addWidget(title)
        ctl.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.autoscrollCheck = QCheckBox("Autoscroll")
        self.autoscrollCheck.setChecked(True)
        self.showDebugCheck = QCheckBox("Debug")
        self.showDebugCheck.setChecked(False)
        self.showDebugCheck.setToolTip("Show verbose [debug] lines in the console")
        self.copyConsoleButton = QPushButton("Copy")
        self.clearConsoleButton = QPushButton("Clear")
        self.expandConsoleButton = QPushButton("Collapse")
        for b in (self.copyConsoleButton, self.clearConsoleButton, self.expandConsoleButton):
            b.setCursor(Qt.PointingHandCursor)
        ctl.addWidget(self.autoscrollCheck)
        ctl.addWidget(self.showDebugCheck)
        ctl.addWidget(self.copyConsoleButton)
        ctl.addWidget(self.clearConsoleButton)
        ctl.addWidget(self.expandConsoleButton)
        cl.addWidget(self.consoleToolbar)
        self.consoleOutput = QPlainTextEdit()
        self.consoleOutput.setObjectName("consoleOutput")
        self.consoleOutput.setReadOnly(True)
        self.consoleOutput.setMinimumHeight(120)
        self.consoleOutput.setPlaceholderText("yt-dlp output streams here in real time…")
        cl.addWidget(self.consoleOutput, 1)
        splitter.addWidget(self.consoleFrame)
        splitter.setSizes([520, 220])
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        main.addWidget(splitter, 1)

        # -- status bar ------------------------------------------------------
        self.statusBar = QStatusBar()
        self.statusBar.setObjectName("statusBar")
        self.statusLabel = QLabel("Ready")
        self.queueLabel = QLabel("Queue: 0")
        self.statusBar.addWidget(self.statusLabel, 1)
        self.statusBar.addPermanentWidget(self.queueLabel)
        win.setStatusBar(self.statusBar)

    # =====================================================================
    # tabs
    # =====================================================================
    def _finish_tab(self, holder: QWidget, inner_lay: QVBoxLayout, title: str) -> None:
        inner_lay.insertWidget(0, QLabel(""))  # spacer guard
        self.tabWidget.addTab(holder, title)

    # -- General ------------------------------------------------------------
    def _build_general_tab(self) -> None:
        holder, lay = _scroll_tab()

        g1, l1 = _group("Format & quality  (maps to -f)")
        self.formatPresetCombo = QComboBox()
        self.formatPresetCombo.addItems(list(FORMAT_PRESETS.keys()))
        l1.addLayout(_form_row("Format preset", self.formatPresetCombo,
                               "yt-dlp -f format selection string"))
        self.formatCustomEdit = QLineEdit("bestvideo+bestaudio/best")
        self.formatCustomEdit.setPlaceholderText("e.g. bestvideo[height<=1080]+bestaudio/best")
        l1.addLayout(_form_row("Custom format", self.formatCustomEdit))
        self.mergeFormatCombo = QComboBox()
        self.mergeFormatCombo.addItems(MERGE_FORMATS)
        self.mergeFormatCombo.setCurrentText("mkv")
        l1.addLayout(_form_row("Merge container", self.mergeFormatCombo,
                               "merge-output-format for video+audio muxing"))
        lay.insertWidget(0, g1)

        g2, l2 = _group("Output paths  (maps to -o / -P)")
        self.outputDirEdit = QLineEdit()
        self.outputDirBrowse = QPushButton("Browse…")
        self.outputDirBrowse.setObjectName("pasteButton")
        r = QHBoxLayout()
        r.addWidget(self.outputDirEdit, 1)
        r.addWidget(self.outputDirBrowse)
        l2.addLayout(_form_row("Download folder", self._wrap(r)))
        self.outtmplPresetCombo = QComboBox()
        self.outtmplPresetCombo.addItems(list(OUTTMPL_PRESETS.keys()))
        l2.addLayout(_form_row("Name template", self.outtmplPresetCombo, "Output filename template"))
        self.outtmplCustomEdit = QLineEdit(OUTTMPL_PRESETS["Title + ID"])
        l2.addLayout(_form_row("Custom template", self.outtmplCustomEdit,
                               "Supports %(title)s, %(id)s, %(ext)s, …"))
        self.restrictFilenamesCheck = QCheckBox("Restrict filenames to ASCII (portable)")
        self.windowsFilenamesCheck = QCheckBox("Windows-safe filenames")
        l2.addWidget(self.restrictFilenamesCheck)
        l2.addWidget(self.windowsFilenamesCheck)
        self.noOverwritesCheck = QCheckBox("Never overwrite existing files")
        self.continueDlCheck = QCheckBox("Resume partial downloads")
        self.continueDlCheck.setChecked(True)
        l2.addWidget(self.noOverwritesCheck)
        l2.addWidget(self.continueDlCheck)
        lay.insertWidget(1, g2)

        g3, l3 = _group("Embedding  (post-processors)")
        self.embedThumbnailCheck = QCheckBox("Embed thumbnail in file")
        self.embedThumbnailCheck.setChecked(True)
        self.embedMetadataCheck = QCheckBox("Embed metadata / chapters")
        self.embedMetadataCheck.setChecked(True)
        self.embedChaptersCheck = QCheckBox("Add chapters (when available)")
        self.embedChaptersCheck.setChecked(True)
        self.writeThumbnailCheck = QCheckBox("Also save thumbnail as separate file")
        self.writeInfoJsonCheck = QCheckBox("Save .info.json metadata")
        self.writeDescriptionCheck = QCheckBox("Save description as .description file")
        for c in (self.embedThumbnailCheck, self.embedMetadataCheck, self.embedChaptersCheck,
                  self.writeThumbnailCheck, self.writeInfoJsonCheck, self.writeDescriptionCheck):
            l3.addWidget(c)
        lay.insertWidget(2, g3)

        self._finish_tab(holder, lay, "General & Output")

    # -- Playlist ------------------------------------------------------------
    def _build_playlist_tab(self) -> None:
        holder, lay = _scroll_tab()

        g1, l1 = _group("Playlist selection  (--no-playlist, --playlist-start/end/items)")
        self.noPlaylistCheck = QCheckBox("Download single video even if URL is a playlist")
        l1.addWidget(self.noPlaylistCheck)
        self.playlistStartSpin = QSpinBox()
        self.playlistStartSpin.setRange(1, 100000)
        self.playlistStartSpin.setValue(1)
        l1.addLayout(_form_row("Playlist start index", self.playlistStartSpin))
        self.playlistEndSpin = QSpinBox()
        self.playlistEndSpin.setRange(0, 100000)
        self.playlistEndSpin.setValue(0)
        self.playlistEndSpin.setSpecialValueText("all")
        l1.addLayout(_form_row("Playlist end index (0 = all)", self.playlistEndSpin))
        self.playlistItemsEdit = QLineEdit()
        self.playlistItemsEdit.setPlaceholderText("e.g. 1-5,7,9  (overrides start/end)")
        l1.addLayout(_form_row("Playlist items slice", self.playlistItemsEdit))
        self.maxDownloadsSpin = QSpinBox()
        self.maxDownloadsSpin.setRange(0, 100000)
        self.maxDownloadsSpin.setSpecialValueText("unlimited")
        l1.addLayout(_form_row("Max downloads", self.maxDownloadsSpin))
        lay.insertWidget(0, g1)

        g2, l2 = _group("Filters & chapter slicing")
        self.dateAfterEdit = QLineEdit()
        self.dateAfterEdit.setPlaceholderText("YYYYMMDD  (e.g. 20240101)")
        l2.addLayout(_form_row("Only after date", self.dateAfterEdit, "--dateafter"))
        self.dateBeforeEdit = QLineEdit()
        self.dateBeforeEdit.setPlaceholderText("YYYYMMDD")
        l2.addLayout(_form_row("Only before date", self.dateBeforeEdit, "--datebefore"))
        self.matchFilterEdit = QLineEdit()
        self.matchFilterEdit.setPlaceholderText('e.g. duration > 120 & view_count > 1000')
        l2.addLayout(_form_row("Match filter", self.matchFilterEdit, "--match-filter"))
        self.sectionStartEdit = QLineEdit()
        self.sectionStartEdit.setPlaceholderText("10:00  (leave empty for full video)")
        l2.addLayout(_form_row("Section start", self.sectionStartEdit, "--download-sections"))
        self.sectionEndEdit = QLineEdit()
        self.sectionEndEdit.setPlaceholderText("12:00")
        l2.addLayout(_form_row("Section end", self.sectionEndEdit))
        lay.insertWidget(1, g2)

        self._finish_tab(holder, lay, "Playlist & Range")

    # -- Network ------------------------------------------------------------
    def _build_network_tab(self) -> None:
        holder, lay = _scroll_tab()

        g1, l1 = _group("Authentication  (--cookies, --cookies-from-browser)")
        self.cookieFileEdit = QLineEdit()
        self.cookieFileEdit.setPlaceholderText("Path to cookies.txt (Netscape format)…")
        self.cookieBrowse = QPushButton("Browse…")
        self.cookieBrowse.setObjectName("pasteButton")
        l1.addLayout(_form_row("Cookie file", self._wrap2(self.cookieFileEdit, self.cookieBrowse)))
        self.cookiesBrowserCombo = QComboBox()
        self.cookiesBrowserCombo.addItems(BROWSERS)
        l1.addLayout(_form_row("Or read from browser", self.cookiesBrowserCombo))
        lay.insertWidget(0, g1)

        g2, l2 = _group("Network  (--proxy, --limit-rate, --user-agent …)")
        self.proxyEdit = QLineEdit()
        self.proxyEdit.setPlaceholderText("e.g. http://127.0.0.1:8080  or  socks5://127.0.0.1:1080")
        l2.addLayout(_form_row("Proxy URL", self.proxyEdit))
        self.rateLimitEdit = QLineEdit()
        self.rateLimitEdit.setPlaceholderText("e.g. 2M, 500K  (empty = unlimited)")
        l2.addLayout(_form_row("Rate limit", self.rateLimitEdit, "--limit-rate"))
        self.socketTimeoutSpin = QSpinBox()
        self.socketTimeoutSpin.setRange(5, 300)
        self.socketTimeoutSpin.setValue(30)
        self.socketTimeoutSpin.setSuffix(" s")
        l2.addLayout(_form_row("Socket timeout", self.socketTimeoutSpin))
        self.retriesSpin = QSpinBox()
        self.retriesSpin.setRange(0, 100)
        self.retriesSpin.setValue(10)
        l2.addLayout(_form_row("Retries", self.retriesSpin, "-R"))
        self.userAgentEdit = QLineEdit()
        self.userAgentEdit.setPlaceholderText("Custom User-Agent (empty = yt-dlp default)")
        l2.addLayout(_form_row("User-Agent", self.userAgentEdit, "--user-agent"))
        self.refererEdit = QLineEdit()
        self.refererEdit.setPlaceholderText("Custom Referer header")
        l2.addLayout(_form_row("Referer", self.refererEdit, "--referer"))
        self.noCheckCertCheck = QCheckBox("Skip HTTPS certificate validation (insecure)")
        l2.addWidget(self.noCheckCertCheck)
        self.ffmpegLocationEdit = QLineEdit()
        self.ffmpegLocationEdit.setPlaceholderText("Auto-detect if empty")
        self.ffmpegBrowse = QPushButton("Browse…")
        self.ffmpegBrowse.setObjectName("pasteButton")
        l2.addLayout(_form_row("ffmpeg binary", self._wrap2(self.ffmpegLocationEdit, self.ffmpegBrowse),
                               "--ffmpeg-location"))
        lay.insertWidget(1, g2)

        self._finish_tab(holder, lay, "Auth & Network")

    # -- Subs & Sponsor ------------------------------------------------------
    def _build_subs_tab(self) -> None:
        holder, lay = _scroll_tab()

        g1, l1 = _group("SponsorBlock  (categories + action)")
        self.sponsorChecks: Dict[str, QCheckBox] = {}
        grid = QGridLayout()
        grid.setSpacing(6)
        defaults = {"sponsor", "selfpromo", "interaction"}
        for i, cat in enumerate(SPONSOR_CATEGORIES):
            cb = QCheckBox(cat)
            cb.setChecked(cat in defaults)
            self.sponsorChecks[cat] = cb
            grid.addWidget(cb, i // 2, i % 2)
        l1.addLayout(grid)
        self.sponsorActionCombo = QComboBox()
        self.sponsorActionCombo.addItems(["remove", "mark_chapters"])
        l1.addLayout(_form_row("Sponsor action", self.sponsorActionCombo,
                               "remove segments or keep them as chapters"))
        sb_row = QHBoxLayout()
        self.sbSelectAll = QPushButton("Select all")
        self.sbSelectAll.setObjectName("pasteButton")
        self.sbSelectNone = QPushButton("None")
        self.sbSelectNone.setObjectName("clearButton")
        sb_row.addWidget(self.sbSelectAll)
        sb_row.addWidget(self.sbSelectNone)
        sb_row.addStretch(1)
        l1.addLayout(sb_row)
        lay.insertWidget(0, g1)

        g2, l2 = _group("Subtitles  (--write-subs, --embed-subs …)")
        self.writeSubsCheck = QCheckBox("Download subtitle files")
        self.embedSubsCheck = QCheckBox("Embed subtitles into video")
        self.autoSubsCheck = QCheckBox("Include auto-generated subtitles")
        for c in (self.writeSubsCheck, self.embedSubsCheck, self.autoSubsCheck):
            l2.addWidget(c)
        self.subsLangsEdit = QLineEdit("en")
        self.subsLangsEdit.setPlaceholderText("e.g. en,es,de  or  all")
        l2.addLayout(_form_row("Subtitle languages", self.subsLangsEdit, "--sub-langs"))
        self.subsFormatCombo = QComboBox()
        self.subsFormatCombo.addItems(SUB_FORMATS)
        l2.addLayout(_form_row("Subtitle format", self.subsFormatCombo))
        lay.insertWidget(1, g2)

        self._finish_tab(holder, lay, "Subs & Sponsor")

    # -- Post-processing ------------------------------------------------------
    def _build_postproc_tab(self) -> None:
        holder, lay = _scroll_tab()

        g1, l1 = _group("Audio extraction  (--extract-audio)")
        self.extractAudioCheck = QCheckBox("Extract audio only (skip video)")
        l1.addWidget(self.extractAudioCheck)
        self.audioFormatCombo = QComboBox()
        self.audioFormatCombo.addItems(AUDIO_FORMATS)
        l1.addLayout(_form_row("Audio codec", self.audioFormatCombo, "--audio-format"))
        self.audioQualityCombo = QComboBox()
        self.audioQualityCombo.addItems(["0 (best)", "64", "128", "192", "256", "320"])
        self.audioQualityCombo.setCurrentText("192")
        l1.addLayout(_form_row("Audio quality (kbps)", self.audioQualityCombo, "--audio-quality"))
        lay.insertWidget(0, g1)

        g2, l2 = _group("Performance & hooks")
        self.concurrentFragmentsSpin = QSpinBox()
        self.concurrentFragmentsSpin.setRange(1, 32)
        self.concurrentFragmentsSpin.setValue(4)
        l2.addLayout(_form_row("Parallel fragments", self.concurrentFragmentsSpin, "-N"))
        self.hlsNativeCheck = QCheckBox("Prefer native HLS downloader")
        l2.addWidget(self.hlsNativeCheck)
        self.postprocArgsEdit = QLineEdit()
        self.postprocArgsEdit.setPlaceholderText("e.g. -c:v libx264 -crf 23  (ffmpeg postprocessor args)")
        l2.addLayout(_form_row("Postprocessor args", self.postprocArgsEdit, "--postprocessor-args"))
        self.extractorArgsEdit = QLineEdit()
        self.extractorArgsEdit.setPlaceholderText("e.g. youtube=player_client=android;skip=dash")
        l2.addLayout(_form_row("Extractor args", self.extractorArgsEdit, "--extractor-args"))
        self.execAfterEdit = QLineEdit()
        self.execAfterEdit.setPlaceholderText("Shell command run after each file, e.g. notify-send done")
        l2.addLayout(_form_row("Run after download", self.execAfterEdit, "--exec"))
        self.verboseCheck = QCheckBox("Verbose yt-dlp logging (debug mode)")
        l2.addWidget(self.verboseCheck)
        lay.insertWidget(1, g2)

        g3, l3 = _group("Custom ydl_opts overlay (advanced, JSON object)")
        self.customJsonEdit = QPlainTextEdit()
        self.customJsonEdit.setPlaceholderText('e.g. {"updatetime": false, "sleep_interval": 2}')
        self.customJsonEdit.setMaximumHeight(90)
        l3.addWidget(self.customJsonEdit)
        self.resetDefaultsButton = QPushButton("Reset all settings to defaults")
        self.resetDefaultsButton.setObjectName("settingsButton")
        l3.addWidget(self.resetDefaultsButton)
        lay.insertWidget(2, g3)

        self._finish_tab(holder, lay, "Post-processing")

    # -- Engine ---------------------------------------------------------------
    def _build_engine_tab(self) -> None:
        holder, lay = _scroll_tab()

        g1, l1 = _group("yt-dlp engine  (self-updating core)")
        self.currentEngineLabel = QLabel("Installed: …")
        self.latestEngineLabel = QLabel("Latest release: unknown")
        l1.addWidget(self.currentEngineLabel)
        l1.addWidget(self.latestEngineLabel)
        self.updateStatusLabel = QLabel("Tip: updates install in the background — no restart needed.")
        self.updateStatusLabel.setWordWrap(True)
        self.updateStatusLabel.setStyleSheet("color:#8b8e94;")
        l1.addWidget(self.updateStatusLabel)
        self.updateProgressBar = QProgressBar()
        self.updateProgressBar.setRange(0, 100)
        self.updateProgressBar.setValue(0)
        l1.addWidget(self.updateProgressBar)
        btns = QHBoxLayout()
        self.checkUpdateButton = QPushButton("Check for updates")
        self.checkUpdateButton.setObjectName("settingsButton")
        self.updateEngineButton = QPushButton("Update yt-dlp engine")
        self.updateEngineButton.setObjectName("updateButton")
        btns.addWidget(self.checkUpdateButton)
        btns.addWidget(self.updateEngineButton)
        btns.addStretch(1)
        l1.addLayout(btns)
        self.autoCheckUpdatesCheck = QCheckBox("Check for engine updates on startup")
        self.autoCheckUpdatesCheck.setChecked(True)
        l1.addWidget(self.autoCheckUpdatesCheck)
        lay.insertWidget(0, g1)

        g2, l2 = _group("About")
        about = QLabel(
            "YT-DLP Studio · PySide6 (Qt) frontend for yt-dlp.\n"
            "All downloads, probes and upgrades run in QThread workers — "
            "the UI never blocks. Output streams live into the console below."
        )
        about.setWordWrap(True)
        about.setStyleSheet("color:#8b8e94;")
        l2.addWidget(about)
        lay.insertWidget(1, g2)

        self._finish_tab(holder, lay, "Engine & Updates")

    # -- tiny helpers -----------------------------------------------------------
    @staticmethod
    def _wrap(layout: QHBoxLayout) -> QWidget:
        w = QWidget()
        w.setLayout(layout)
        w.setContentsMargins(0, 0, 0, 0)
        return w

    @staticmethod
    def _wrap2(a: QWidget, b: QWidget) -> QWidget:
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(6)
        l.addWidget(a, 1)
        l.addWidget(b)
        return w
