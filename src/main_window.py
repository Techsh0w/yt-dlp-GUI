"""Main window — wires the UI to QThread workers with zero UI blocking."""

from __future__ import annotations

import html
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QThread, QTimer, Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QTableWidgetItem,
)

from .options import (
    APP_VERSION,
    FORMAT_PRESETS,
    OUTTMPL_PRESETS,
    SPONSOR_CATEGORIES,
    build_ydl_opts,
    default_settings,
)
from .ui_main import Ui_MainWindow
from .utils import (
    ensure_dir,
    format_bytes,
    format_eta,
    format_percent,
    format_speed,
    is_valid_url,
    load_settings,
    save_settings,
)
from .workers import (
    FormatFetchWorker,
    UpdateCheckWorker,
    UpdateInstallWorker,
    YtDlpWorker,
    get_yt_dlp_version,
    parse_formats,
)

LEVEL_COLORS = {
    "info": "#58a6ff",
    "success": "#3fb950",
    "warning": "#d29922",
    "error": "#f85149",
    "debug": "#6e7681",
}


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)
        self.versionLabel.setText(f"v{APP_VERSION}")

        self.settings_data: Dict[str, Any] = load_settings(default_settings())
        self._threads: List[QThread] = []
        self._dl_worker: Optional[YtDlpWorker] = None
        self._console_collapsed = False
        self._pending_latest = ""

        self._connect_signals()
        self.apply_settings_to_ui()
        self.refresh_engine_label()
        self.append_log("YT-DLP Studio ready. All heavy work runs in background threads.", "info")

        if self.settings_data.get("auto_check_updates", True):
            QTimer.singleShot(1500, self.check_for_updates)

    # ==================================================================
    # wiring
    # ==================================================================
    def _connect_signals(self) -> None:
        self.downloadButton.clicked.connect(self.start_download)
        self.cancelButton.clicked.connect(self.cancel_download)
        self.fetchFormatsButton.clicked.connect(self.fetch_formats)
        self.addQueueButton.clicked.connect(self.add_to_queue)
        self.urlInput.returnPressed.connect(self.add_to_queue)
        self.removeQueueButton.clicked.connect(self.remove_selected_queue)
        self.clearQueueButton.clicked.connect(lambda: (self.queueList.clear(), self._sync_queue_label()))
        self.pasteButton.clicked.connect(self._paste_clipboard)
        self.clearButton.clicked.connect(self.urlInput.clear)

        self.outputDirBrowse.clicked.connect(self._browse_output_dir)
        self.cookieBrowse.clicked.connect(self._browse_cookie_file)
        self.ffmpegBrowse.clicked.connect(self._browse_ffmpeg)

        self.checkUpdateButton.clicked.connect(self.check_for_updates)
        self.updateEngineButton.clicked.connect(self.install_update)

        self.copyConsoleButton.clicked.connect(self._copy_console)
        self.clearConsoleButton.clicked.connect(self.consoleOutput.clear)
        self.expandConsoleButton.clicked.connect(self._toggle_console)

        self.formatPresetCombo.currentTextChanged.connect(self._on_format_preset_changed)
        self.outtmplPresetCombo.currentTextChanged.connect(self._on_outtmpl_preset_changed)
        self.sbSelectAll.clicked.connect(lambda: self._set_sponsor_all(True))
        self.sbSelectNone.clicked.connect(lambda: self._set_sponsor_all(False))
        self.resetDefaultsButton.clicked.connect(self._reset_defaults)

    # ==================================================================
    # settings <-> UI
    # ==================================================================
    def collect_settings(self) -> Dict[str, Any]:
        u = self  # shorthand
        sponsor = [c for c in SPONSOR_CATEGORIES if u.sponsorChecks[c].isChecked()]
        audio_q = u.audioQualityCombo.currentText().split(" ")[0]
        return {
            "format_preset": u.formatPresetCombo.currentText(),
            "format_custom": u.formatCustomEdit.text().strip(),
            "merge_format": u.mergeFormatCombo.currentText(),
            "output_dir": u.outputDirEdit.text().strip(),
            "outtmpl_preset": u.outtmplPresetCombo.currentText(),
            "outtmpl_custom": u.outtmplCustomEdit.text().strip(),
            "restrict_filenames": u.restrictFilenamesCheck.isChecked(),
            "windows_filenames": u.windowsFilenamesCheck.isChecked(),
            "embed_thumbnail": u.embedThumbnailCheck.isChecked(),
            "embed_metadata": u.embedMetadataCheck.isChecked(),
            "embed_chapters": u.embedChaptersCheck.isChecked(),
            "write_thumbnail": u.writeThumbnailCheck.isChecked(),
            "write_info_json": u.writeInfoJsonCheck.isChecked(),
            "write_description": u.writeDescriptionCheck.isChecked(),
            "no_overwrites": u.noOverwritesCheck.isChecked(),
            "continuedl": u.continueDlCheck.isChecked(),
            "noplaylist": u.noPlaylistCheck.isChecked(),
            "playlist_start": u.playlistStartSpin.value(),
            "playlist_end": u.playlistEndSpin.value(),
            "playlist_items": u.playlistItemsEdit.text().strip(),
            "max_downloads": u.maxDownloadsSpin.value(),
            "date_after": u.dateAfterEdit.text().strip(),
            "date_before": u.dateBeforeEdit.text().strip(),
            "match_filter": u.matchFilterEdit.text().strip(),
            "section_start": u.sectionStartEdit.text().strip(),
            "section_end": u.sectionEndEdit.text().strip(),
            "cookie_file": u.cookieFileEdit.text().strip(),
            "cookies_from_browser": u.cookiesBrowserCombo.currentText(),
            "proxy": u.proxyEdit.text().strip(),
            "socket_timeout": u.socketTimeoutSpin.value(),
            "retries": u.retriesSpin.value(),
            "rate_limit": u.rateLimitEdit.text().strip(),
            "user_agent": u.userAgentEdit.text().strip(),
            "referer": u.refererEdit.text().strip(),
            "no_check_certificate": u.noCheckCertCheck.isChecked(),
            "sponsor_categories": sponsor,
            "sponsor_action": u.sponsorActionCombo.currentText(),
            "write_subs": u.writeSubsCheck.isChecked(),
            "embed_subs": u.embedSubsCheck.isChecked(),
            "auto_subs": u.autoSubsCheck.isChecked(),
            "subs_langs": u.subsLangsEdit.text().strip() or "en",
            "subs_format": u.subsFormatCombo.currentText(),
            "extract_audio": u.extractAudioCheck.isChecked(),
            "audio_format": u.audioFormatCombo.currentText(),
            "audio_quality": audio_q,
            "concurrent_fragments": u.concurrentFragmentsSpin.value(),
            "hls_prefer_native": u.hlsNativeCheck.isChecked(),
            "ffmpeg_location": u.ffmpegLocationEdit.text().strip(),
            "postprocessor_args": u.postprocArgsEdit.text().strip(),
            "extractor_args": u.extractorArgsEdit.text().strip(),
            "exec_after": u.execAfterEdit.text().strip(),
            "verbose": u.verboseCheck.isChecked(),
            "custom_ydl_json": u.customJsonEdit.toPlainText().strip(),
            "auto_check_updates": u.autoCheckUpdatesCheck.isChecked(),
        }

    def apply_settings_to_ui(self) -> None:
        s = self.settings_data
        self._set_combo(self.formatPresetCombo, s.get("format_preset", ""), list(FORMAT_PRESETS))
        self.formatCustomEdit.setText(s.get("format_custom", ""))
        self._set_combo(self.mergeFormatCombo, s.get("merge_format", "mkv"), None)
        self.outputDirEdit.setText(s.get("output_dir", ""))
        self._set_combo(self.outtmplPresetCombo, s.get("outtmpl_preset", "Title + ID"), list(OUTTMPL_PRESETS))
        self.outtmplCustomEdit.setText(s.get("outtmpl_custom", ""))
        self.restrictFilenamesCheck.setChecked(bool(s.get("restrict_filenames")))
        self.windowsFilenamesCheck.setChecked(bool(s.get("windows_filenames")))
        self.embedThumbnailCheck.setChecked(bool(s.get("embed_thumbnail", True)))
        self.embedMetadataCheck.setChecked(bool(s.get("embed_metadata", True)))
        self.embedChaptersCheck.setChecked(bool(s.get("embed_chapters", True)))
        self.writeThumbnailCheck.setChecked(bool(s.get("write_thumbnail")))
        self.writeInfoJsonCheck.setChecked(bool(s.get("write_info_json")))
        self.writeDescriptionCheck.setChecked(bool(s.get("write_description")))
        self.noOverwritesCheck.setChecked(bool(s.get("no_overwrites")))
        self.continueDlCheck.setChecked(bool(s.get("continuedl", True)))
        self.noPlaylistCheck.setChecked(bool(s.get("noplaylist")))
        self.playlistStartSpin.setValue(int(s.get("playlist_start") or 1))
        self.playlistEndSpin.setValue(int(s.get("playlist_end") or 0))
        self.playlistItemsEdit.setText(s.get("playlist_items", ""))
        self.maxDownloadsSpin.setValue(int(s.get("max_downloads") or 0))
        self.dateAfterEdit.setText(s.get("date_after", ""))
        self.dateBeforeEdit.setText(s.get("date_before", ""))
        self.matchFilterEdit.setText(s.get("match_filter", ""))
        self.sectionStartEdit.setText(s.get("section_start", ""))
        self.sectionEndEdit.setText(s.get("section_end", ""))
        self.cookieFileEdit.setText(s.get("cookie_file", ""))
        self._set_combo(self.cookiesBrowserCombo, s.get("cookies_from_browser", "none"), None)
        self.proxyEdit.setText(s.get("proxy", ""))
        self.socketTimeoutSpin.setValue(int(s.get("socket_timeout") or 30))
        self.retriesSpin.setValue(int(s.get("retries") if s.get("retries") != "" else 10))
        self.rateLimitEdit.setText(s.get("rate_limit", ""))
        self.userAgentEdit.setText(s.get("user_agent", ""))
        self.refererEdit.setText(s.get("referer", ""))
        self.noCheckCertCheck.setChecked(bool(s.get("no_check_certificate")))
        for cat, cb in self.sponsorChecks.items():
            cb.setChecked(cat in (s.get("sponsor_categories") or []))
        self._set_combo(self.sponsorActionCombo, s.get("sponsor_action", "remove"), None)
        self.writeSubsCheck.setChecked(bool(s.get("write_subs")))
        self.embedSubsCheck.setChecked(bool(s.get("embed_subs")))
        self.autoSubsCheck.setChecked(bool(s.get("auto_subs")))
        self.subsLangsEdit.setText(s.get("subs_langs", "en"))
        self._set_combo(self.subsFormatCombo, s.get("subs_format", "srt"), None)
        self.extractAudioCheck.setChecked(bool(s.get("extract_audio")))
        self._set_combo(self.audioFormatCombo, s.get("audio_format", "mp3"), None)
        self._set_combo(self.audioQualityCombo, str(s.get("audio_quality", "192")), None, startswith=True)
        self.concurrentFragmentsSpin.setValue(int(s.get("concurrent_fragments") or 4))
        self.hlsNativeCheck.setChecked(bool(s.get("hls_prefer_native")))
        self.ffmpegLocationEdit.setText(s.get("ffmpeg_location", ""))
        self.postprocArgsEdit.setText(s.get("postprocessor_args", ""))
        self.extractorArgsEdit.setText(s.get("extractor_args", ""))
        self.execAfterEdit.setText(s.get("exec_after", ""))
        self.verboseCheck.setChecked(bool(s.get("verbose")))
        self.customJsonEdit.setPlainText(s.get("custom_ydl_json", ""))
        self.autoCheckUpdatesCheck.setChecked(bool(s.get("auto_check_updates", True)))
        self._on_format_preset_changed(self.formatPresetCombo.currentText())
        self._on_outtmpl_preset_changed(self.outtmplPresetCombo.currentText())

    @staticmethod
    def _set_combo(combo, value: str, items=None, startswith: bool = False) -> None:  # noqa: ANN001
        value = str(value or "")
        if items:
            for it in items:
                if combo.findText(it) < 0:
                    combo.addItem(it)
        idx = combo.findText(value)
        if idx < 0 and startswith:
            for i in range(combo.count()):
                if combo.itemText(i).startswith(value):
                    idx = i
                    break
        if idx >= 0:
            combo.setCurrentIndex(idx)

    # -- small UI slots --------------------------------------------------
    def _on_format_preset_changed(self, text: str) -> None:
        is_custom = text == "Custom…"
        self.formatCustomEdit.setEnabled(is_custom)
        if not is_custom and text in FORMAT_PRESETS and FORMAT_PRESETS[text] != "__custom__":
            self.formatCustomEdit.setText(FORMAT_PRESETS[text])

    def _on_outtmpl_preset_changed(self, text: str) -> None:
        if text in OUTTMPL_PRESETS:
            self.outtmplCustomEdit.setText(OUTTMPL_PRESETS[text])

    def _set_sponsor_all(self, checked: bool) -> None:
        for cb in self.sponsorChecks.values():
            cb.setChecked(checked)

    def _reset_defaults(self) -> None:
        self.settings_data = default_settings()
        self.apply_settings_to_ui()
        save_settings(self.settings_data)
        self.append_log("Settings reset to defaults.", "warning")

    def _paste_clipboard(self) -> None:
        self.urlInput.setText(QApplication.clipboard().text().strip())
        self.urlInput.setFocus()

    def _browse_output_dir(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Choose download folder", self.outputDirEdit.text() or ".")
        if d:
            self.outputDirEdit.setText(d)

    def _browse_cookie_file(self) -> None:
        f, _ = QFileDialog.getOpenFileName(self, "Select cookies.txt", "", "Text files (*.txt);;All files (*)")
        if f:
            self.cookieFileEdit.setText(f)

    def _browse_ffmpeg(self) -> None:
        f, _ = QFileDialog.getOpenFileName(self, "Select ffmpeg binary", "", "All files (*)")
        if f:
            self.ffmpegLocationEdit.setText(f)

    def _copy_console(self) -> None:
        QApplication.clipboard().setText(self.consoleOutput.toPlainText())

    def _toggle_console(self) -> None:
        self._console_collapsed = not self._console_collapsed
        self.consoleOutput.setVisible(not self._console_collapsed)
        self.expandConsoleButton.setText("Expand" if self._console_collapsed else "Collapse")

    # ==================================================================
    # queue
    # ==================================================================
    def queue_urls(self) -> List[str]:
        return [self.queueList.item(i).text() for i in range(self.queueList.count())]

    def add_to_queue(self) -> None:
        url = self.urlInput.text().strip()
        if not url:
            return
        if not is_valid_url(url):
            QMessageBox.warning(self, "Invalid URL", "That doesn't look like a supported URL.\nIt should start with http(s)://")
            return
        if url in self.queue_urls():
            self.statusLabel.setText("URL already in queue")
            return
        self.queueList.addItem(url)
        self.urlInput.clear()
        self._sync_queue_label()

    def remove_selected_queue(self) -> None:
        for item in self.queueList.selectedItems():
            self.queueList.takeItem(self.queueList.row(item))
        self._sync_queue_label()

    def _sync_queue_label(self) -> None:
        self.queueLabel.setText(f"Queue: {self.queueList.count()}")

    # ==================================================================
    # downloads (QThread + streaming signals — UI never blocks)
    # ==================================================================
    def _current_ydl_opts(self, *, for_probe: bool = False) -> Dict[str, Any]:
        self.settings_data = self.collect_settings()
        save_settings(self.settings_data)
        return build_ydl_opts(self.settings_data, for_probe=for_probe)

    def start_download(self) -> None:
        urls = self.queue_urls()
        single = self.urlInput.text().strip()
        if single and single not in urls:
            if not is_valid_url(single):
                QMessageBox.warning(self, "Invalid URL", "The URL in the input box is not valid.")
                return
            urls = [*urls, single]
        if not urls:
            QMessageBox.information(self, "Nothing to download", "Paste a URL or add items to the queue first.")
            return
        try:
            ydl_opts = self._current_ydl_opts()
        except ValueError as exc:
            QMessageBox.critical(self, "Invalid settings", str(exc))
            return
        ensure_dir(self.settings_data.get("output_dir", ""))

        self._set_busy(True, f"Downloading {len(urls)} item(s)…")
        self.append_log(f"Starting download of {len(urls)} URL(s) with format '{ydl_opts.get('format')}'.", "info")

        thread = QThread(self)
        worker = YtDlpWorker(ydl_opts, urls)
        worker.moveToThread(thread)
        thread.started.connect(worker.run_download)
        worker.progress.connect(self.on_download_progress)
        worker.log.connect(self.append_log)
        worker.error.connect(lambda m: self.append_log(m, "error"))
        worker.finished.connect(self.on_download_finished)
        # teardown (must run even on cancel)
        worker.finished.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._threads.append(thread)
        self._dl_worker = worker
        # drop dead threads
        self._threads = [t for t in self._threads if t.isRunning() or t is thread]
        thread.start()

    def cancel_download(self) -> None:
        if self._dl_worker is not None:
            self.append_log("Cancelling… waiting for worker to stop.", "warning")
            self._dl_worker.cancel()
            self.statusLabel.setText("Cancelling…")

    def on_download_progress(self, d: dict) -> None:
        if d.get("status") == "finished":
            self.progressBar.setValue(1000)
            self.progressInfoLabel.setText("Merging / post-processing…")
            return
        pct = format_percent(d.get("downloaded_bytes"), d.get("total_bytes"), d.get("percent_str", ""))
        self.progressBar.setValue(int(pct * 10))
        self.progressBar.setFormat(f"{pct:.1f}%")
        name = (d.get("filename") or "")[:70]
        down = format_bytes(d.get("downloaded_bytes"))
        total = format_bytes(d.get("total_bytes")) if d.get("total_bytes") else "?"
        self.progressInfoLabel.setText(f"{d.get('percent_str', f'{pct:.1f}%')} · {down} / {total} · {name}")
        self.speedLabel.setText(format_speed(d.get("speed")))
        self.etaLabel.setText(format_eta(d.get("eta")))

    def on_download_finished(self, ok: bool, message: str) -> None:
        self._set_busy(False, message)
        self._dl_worker = None
        if ok:
            self.progressBar.setValue(1000)
            self.progressBar.setFormat("Done")
            self.speedLabel.setText("—")
            self.etaLabel.setText("ETA —")
            self.append_log(message, "success")
            QMessageBox.information(self, "Download complete", message)
        else:
            self.append_log(f"Finished: {message}", "warning" if "ancell" in message else "error")
            if "ancell" not in message:
                QMessageBox.warning(self, "Download finished with issues", message)

    def _set_busy(self, busy: bool, status: str) -> None:
        self.downloadButton.setEnabled(not busy)
        self.fetchFormatsButton.setEnabled(not busy)
        self.cancelButton.setEnabled(busy)
        self.statusLabel.setText(status)
        if busy:
            self.progressBar.setValue(0)
            self.progressBar.setFormat("%p%")

    # ==================================================================
    # format probe (background)
    # ==================================================================
    def fetch_formats(self) -> None:
        url = self.urlInput.text().strip() or (self.queue_urls()[0] if self.queueList.count() else "")
        if not url or not is_valid_url(url):
            QMessageBox.information(self, "Fetch formats", "Paste a valid video URL first.")
            return
        try:
            opts = self._current_ydl_opts(for_probe=True)
        except ValueError as exc:
            QMessageBox.critical(self, "Invalid settings", str(exc))
            return
        self._set_busy(True, "Probing formats…")
        self.append_log(f"Probing: {url}", "info")

        thread = QThread(self)
        worker = FormatFetchWorker(url, opts)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.log.connect(self.append_log)
        worker.error.connect(lambda m: (self.append_log(m, "error"), QMessageBox.warning(self, "Probe failed", m)))
        worker.formats_ready.connect(self.on_formats_ready)
        worker.finished.connect(lambda _ok: self._set_busy(False, "Probe finished"))
        worker.finished.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._threads.append(thread)
        thread.start()

    def on_formats_ready(self, formats: list, info: dict) -> None:
        rows = parse_formats(formats, info)
        title = info.get("title", "?")
        dur = info.get("duration") or 0
        self.probeInfoLabel.setText(f"{title}  ·  {dur // 60}:{dur % 60:02d}  ·  {len(rows)} streams")
        tbl = self.formatTable
        tbl.setRowCount(0)
        tbl.setVisible(True)
        for r in rows[:60]:
            i = tbl.rowCount()
            tbl.insertRow(i)
            codecs = f"{r['vcodec']}/{r['acodec']}"
            vals = [r["format_id"], r["ext"], r["resolution"] or str(r["height"]) + "p",
                    codecs, format_bytes(r["filesize"]), r["format_note"]]
            for j, v in enumerate(vals):
                item = QTableWidgetItem(str(v))
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                tbl.setItem(i, j, item)
        tbl.resizeColumnsToContents()
        self.append_log(f"Found {len(rows)} usable formats for '{title}'.", "success")

    # ==================================================================
    # self-updating engine (background, no restart)
    # ==================================================================
    def refresh_engine_label(self) -> None:
        ver = get_yt_dlp_version()
        self.engineVersionLabel.setText(f"engine: yt-dlp {ver}")
        self.currentEngineLabel.setText(f"Installed: yt-dlp {ver}")

    def check_for_updates(self) -> None:
        self.checkUpdateButton.setEnabled(False)
        self.updateStatusLabel.setText("Checking GitHub for the latest yt-dlp release…")
        self.updateProgressBar.setRange(0, 0)  # spinner
        thread = QThread(self)
        worker = UpdateCheckWorker(get_yt_dlp_version())
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(lambda p, m: (self.updateProgressBar.setRange(0, 100),
                                              self.updateProgressBar.setValue(p),
                                              self.updateStatusLabel.setText(m)))
        worker.log.connect(self.append_log)
        worker.error.connect(lambda m: self.append_log(m, "error"))
        worker.finished.connect(self.on_update_checked)
        worker.finished.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._threads.append(thread)
        thread.start()

    def on_update_checked(self, available: bool, latest: str, message: str) -> None:
        self.checkUpdateButton.setEnabled(True)
        self.updateProgressBar.setRange(0, 100)
        self.updateProgressBar.setValue(100 if not available else 60)
        self._pending_latest = latest if available else ""
        if available:
            self.latestEngineLabel.setText(f"Latest release: {latest}  —  update available")
            self.updateStatusLabel.setText(f"Update available: {latest}. Hit 'Update yt-dlp engine'.")
            self.statusLabel.setText(f"Engine update available: {latest}")
        else:
            self.latestEngineLabel.setText(f"Latest release: {latest or 'same as installed'}")
            self.updateStatusLabel.setText(message)
            self.updateProgressBar.setValue(100)

    def install_update(self) -> None:
        self.updateEngineButton.setEnabled(False)
        self.updateProgressBar.setRange(0, 0)  # spinner
        self.updateStatusLabel.setText("Upgrading engine in the background… UI stays responsive.")
        thread = QThread(self)
        worker = UpdateInstallWorker()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(lambda p, m: (self.updateProgressBar.setRange(0, 100),
                                              self.updateProgressBar.setValue(p),
                                              self.updateStatusLabel.setText(m)))
        worker.log.connect(self.append_log)
        worker.error.connect(lambda m: self.append_log(m, "error"))
        worker.finished.connect(self.on_update_installed)
        worker.finished.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._threads.append(thread)
        thread.start()

    def on_update_installed(self, ok: bool, new_version: str, message: str) -> None:
        self.updateEngineButton.setEnabled(True)
        self.updateProgressBar.setRange(0, 100)
        self.updateProgressBar.setValue(100 if ok else 0)
        self.updateStatusLabel.setText(message)
        if ok:
            self.refresh_engine_label()  # no restart needed
            self.statusLabel.setText(f"Engine updated: {message}")
            QMessageBox.information(self, "Engine updated",
                                    f"{message}\nNo restart was needed — keep downloading.")
        else:
            QMessageBox.critical(self, "Engine update failed", message)

    # ==================================================================
    # console (chunk-by-chunk streaming sink)
    # ==================================================================
    def append_log(self, message: str, level: str = "info") -> None:
        if level == "debug" and not self.showDebugCheck.isChecked():
            return
        color = LEVEL_COLORS.get(level, "#c9d1d9")
        ts = datetime.now().strftime("%H:%M:%S")
        safe = html.escape(message)
        cursor = self.consoleOutput.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.consoleOutput.setTextCursor(cursor)
        self.consoleOutput.appendHtml(f'<span style="color:#6e7681;">[{ts}]</span> <span style="color:{color};">{safe}</span>')
        if self.autoscrollCheck.isChecked():
            self.consoleOutput.verticalScrollBar().setValue(
                self.consoleOutput.verticalScrollBar().maximum())

    # ==================================================================
    def closeEvent(self, event) -> None:  # noqa: D102
        try:
            self.settings_data = self.collect_settings()
            save_settings(self.settings_data)
        except Exception:
            pass
        for t in self._threads:
            try:
                if t.isRunning():
                    t.quit()
                    t.wait(1500)
            except Exception:
                pass
        super().closeEvent(event)
