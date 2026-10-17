"""Background workers — all yt-dlp / network / subprocess work lives here.

Every worker is a QObject designed to be moved to a QThread. The GUI thread
must NEVER call yt-dlp, pip, or blocking network I/O directly. Communication
is chunk-by-chunk via Qt signals (thread-safe queued connections).
"""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QObject, Signal, Slot

try:
    import yt_dlp
    from yt_dlp.utils import DownloadError
except ImportError:  # pragma: no cover - handled gracefully at runtime
    yt_dlp = None  # type: ignore
    DownloadError = Exception  # type: ignore


class _Cancelled(Exception):
    """Raised inside progress hooks when the user hits Cancel."""


# ---------------------------------------------------------------------------
# Download worker (yt-dlp Python API, streaming progress_hooks + logger)
# ---------------------------------------------------------------------------
class YtDlpWorker(QObject):
    """Run yt-dlp downloads off the GUI thread with live streaming output."""

    progress = Signal(dict)          # chunk-by-chunk progress dicts
    log = Signal(str, str)           # (message, level): info/success/warning/error/debug
    finished = Signal(bool, str)     # (ok, message)
    error = Signal(str)

    def __init__(self, ydl_opts: Dict[str, Any], urls: List[str]):
        super().__init__()
        self.ydl_opts = dict(ydl_opts)
        self.urls = list(urls)
        self._is_cancelled = False

    def cancel(self) -> None:
        self._is_cancelled = True

    @Slot()
    def run_download(self) -> None:
        if yt_dlp is None:
            msg = "yt-dlp is not installed. Run: pip install -U yt-dlp"
            self.error.emit(msg)
            self.finished.emit(False, msg)
            return

        self._install_hooks()

        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                for url in self.urls:
                    if self._is_cancelled:
                        self.log.emit("Download cancelled by user.", "warning")
                        self.finished.emit(False, "Cancelled by user")
                        return
                    self.log.emit(f"Starting download: {url}", "info")
                    try:
                        ydl.download([url])
                    except _Cancelled:
                        self.log.emit("Download cancelled by user.", "warning")
                        self.finished.emit(False, "Cancelled by user")
                        return
                if self._is_cancelled:
                    self.finished.emit(False, "Cancelled by user")
                else:
                    self.finished.emit(True, "All downloads completed successfully.")
        except DownloadError as exc:
            self.error.emit(str(exc))
            self.finished.emit(False, str(exc))
        except Exception as exc:  # noqa: BLE001 - surface everything to the UI
            self.error.emit(f"Unexpected error: {exc}")
            self.finished.emit(False, str(exc))

    # -- hooks -------------------------------------------------------------
    def _install_hooks(self) -> None:
        worker = self

        def progress_hook(d: Dict[str, Any]) -> None:
            if worker._is_cancelled:
                raise _Cancelled("cancelled")
            status = d.get("status")
            if status == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                # _percent_str looks like " 12.3%"; keep raw + numeric fraction.
                self.progress.emit({
                    "status": "downloading",
                    "filename": d.get("filename", "") or d.get("info_dict", {}).get("title", ""),
                    "downloaded_bytes": d.get("downloaded_bytes", 0),
                    "total_bytes": total,
                    "total_bytes_estimate": d.get("total_bytes_estimate", 0),
                    "speed": d.get("speed") or 0,
                    "eta": d.get("eta"),
                    "percent_str": (d.get("_percent_str") or "").strip(),
                    "fragment_index": d.get("fragment_index"),
                    "fragment_count": d.get("fragment_count"),
                })
                # Also stream a terse stdout-style line for the console.
                try:
                    pct = (d.get("_percent_str") or "").strip()
                    spd = d.get("_speed_str", "")
                    eta = d.get("_eta_str", "")
                    total_s = d.get("_total_bytes_str", "")
                    if pct:
                        self.log.emit(f"[download] {pct} of {total_s} at {spd} ETA {eta}".strip(), "debug")
                except Exception:
                    pass
            elif status == "finished":
                self.progress.emit({"status": "finished", "filename": d.get("filename", "")})
                name = Path(d.get("filename", "")).name or "file"
                self.log.emit(f"Finished: {name} — merging/post-processing…", "success")
            elif status == "error":
                self.log.emit(f"Error: {d.get('error', 'unknown error')}", "error")

        class _Logger:
            def debug(self, msg: str) -> None:  # noqa: D102
                worker.log.emit(msg, "debug")

            def info(self, msg: str) -> None:  # noqa: D102
                worker.log.emit(msg, "info")

            def warning(self, msg: str) -> None:  # noqa: D102
                worker.log.emit(msg, "warning")

            def error(self, msg: str) -> None:  # noqa: D102
                worker.log.emit(msg, "error")

        # Chain with any caller-supplied hooks instead of clobbering them.
        existing = self.ydl_opts.get("progress_hooks", [])
        self.ydl_opts["progress_hooks"] = [*existing, progress_hook]
        # postprocessor hooks stream "started/finished" events too.
        existing_pp = self.ydl_opts.get("postprocessor_hooks", [])

        def _pp_hook(d: Dict[str, Any]) -> None:
            if worker._is_cancelled:
                raise _Cancelled("cancelled")
            self.log.emit(f"[postprocess] {d.get('status')}: {d.get('postprocessor')}", "info")

        self.ydl_opts["postprocessor_hooks"] = [*existing_pp, _pp_hook]
        self.ydl_opts["logger"] = _Logger()


# ---------------------------------------------------------------------------
# Format / info probe worker
# ---------------------------------------------------------------------------
class FormatFetchWorker(QObject):
    formats_ready = Signal(list, dict)  # (formats, full_info_dict)
    error = Signal(str)
    log = Signal(str, str)
    finished = Signal(bool)

    def __init__(self, url: str, ydl_opts: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.url = url
        self.ydl_opts = dict(ydl_opts or {})

    @Slot()
    def run(self) -> None:
        if yt_dlp is None:
            self.error.emit("yt-dlp is not installed.")
            self.finished.emit(False)
            return
        opts: Dict[str, Any] = {"quiet": True, "no_warnings": True, "skip_download": True}
        opts.update(self.ydl_opts)
        # Never let a probe write files.
        opts["skip_download"] = True
        opts.pop("progress_hooks", None)
        try:
            self.log.emit(f"Probing formats for: {self.url}", "info")
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
            if not info:
                self.error.emit("No metadata returned for this URL.")
                self.finished.emit(False)
                return
            # Flatten playlists: report the first N entries' formats via info itself.
            if info.get("_type") == "playlist":
                self.log.emit(
                    f"Playlist detected: {info.get('title', '?')} "
                    f"({len(info.get('entries', []))} entries)", "info")
            self.formats_ready.emit(info.get("formats", []) or [], info)
            self.finished.emit(True)
        except Exception as exc:  # noqa: BLE001
            self.error.emit(f"Failed to fetch formats: {exc}")
            self.finished.emit(False)


# ---------------------------------------------------------------------------
# Self-update workers (check + upgrade, both fully asynchronous)
# ---------------------------------------------------------------------------
class UpdateCheckWorker(QObject):
    progress = Signal(int, str)          # (percent, message)
    finished = Signal(bool, str, str)    # (update_available, latest_version, message)
    log = Signal(str, str)
    error = Signal(str)

    def __init__(self, current_version: str = ""):
        super().__init__()
        self.current_version = (current_version or "").strip()

    @Slot()
    def run(self) -> None:
        self.progress.emit(10, "Contacting GitHub releases API…")
        self.log.emit("Checking for yt-dlp engine updates…", "info")
        try:
            req = urllib.request.Request(
                "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest",
                headers={"User-Agent": "yt-dlp-gui", "Accept": "application/vnd.github+json"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310 - pinned host
                data = json.load(resp)
            latest = str(data.get("tag_name", "")).lstrip("v").strip()
            self.progress.emit(60, f"Latest release: {latest or 'unknown'}")
            if not latest:
                raise RuntimeError("Empty release tag from GitHub API")
            if self._is_newer(latest, self.current_version):
                self.progress.emit(100, "Update available")
                self.log.emit(f"Update available: {self.current_version} → {latest}", "success")
                self.finished.emit(True, latest, f"Update available: {latest}")
            else:
                self.progress.emit(100, "Already up to date")
                self.log.emit(f"Engine is up to date ({self.current_version}).", "info")
                self.finished.emit(False, self.current_version, "Already up to date")
        except Exception as exc:  # noqa: BLE001
            msg = f"Update check failed: {exc}"
            self.error.emit(msg)
            self.log.emit(msg, "error")
            self.finished.emit(False, "", msg)

    def _is_newer(self, latest: str, current: str) -> bool:
        try:
            from packaging.version import Version
            return Version(latest) > Version(current)
        except Exception:
            return bool(latest) and latest != current


class UpdateInstallWorker(QObject):
    """Upgrade the engine without freezing/restarting the host app.

    - Normal (source) installs: ``pip install --upgrade yt-dlp`` streamed
      line-by-line via Popen so the console shows live output.
    - Frozen (PyInstaller) builds: download the standalone yt-dlp binary for
      the current OS from the latest GitHub release with streaming progress.
    """

    progress = Signal(int, str)
    finished = Signal(bool, str, str)  # (ok, new_version, message)
    log = Signal(str, str)
    error = Signal(str)

    @Slot()
    def run(self) -> None:
        if getattr(sys, "frozen", False):
            self._update_frozen_binary()
        else:
            self._update_via_pip()

    # -- pip path -----------------------------------------------------------
    def _update_via_pip(self) -> None:
        self.progress.emit(5, "Starting pip upgrade…")
        self.log.emit("Upgrading yt-dlp via pip…", "info")
        try:
            proc = subprocess.Popen(
                [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
            assert proc.stdout is not None
            for line in proc.stdout:  # streams chunk-by-chunk → console
                line = line.rstrip()
                if line:
                    self.log.emit(line, "debug")
            rc = proc.wait(timeout=300)
            if rc != 0:
                msg = f"pip exited with code {rc}"
                self.error.emit(msg)
                self.log.emit(msg, "error")
                self.finished.emit(False, "", msg)
                return
            self.progress.emit(85, "Verifying new version…")
            ver = subprocess.run(
                [sys.executable, "-c", "import yt_dlp; print(yt_dlp.version.__version__)"],
                capture_output=True, text=True, timeout=30,
            )
            new_version = ver.stdout.strip() if ver.returncode == 0 else "unknown"
            self.progress.emit(100, "Update complete")
            self.log.emit(f"Engine updated to {new_version}. No restart needed.", "success")
            self.finished.emit(True, new_version, f"Updated to {new_version}")
        except subprocess.TimeoutExpired:
            msg = "Update timed out after 5 minutes."
            self.error.emit(msg)
            self.finished.emit(False, "", msg)
        except Exception as exc:  # noqa: BLE001
            msg = f"Update failed: {exc}"
            self.error.emit(msg)
            self.finished.emit(False, "", msg)

    # -- frozen path --------------------------------------------------------
    def _update_frozen_binary(self) -> None:
        import platform
        system = platform.system().lower()
        asset = {"windows": "yt-dlp.exe", "darwin": "yt-dlp_macos", "linux": "yt-dlp_linux"}.get(system, "yt-dlp_linux")
        url = f"https://github.com/yt-dlp/yt-dlp/releases/latest/download/{asset}"
        dest_dir = Path(sys.executable).parent
        dest = dest_dir / asset
        self.progress.emit(5, f"Downloading {asset}…")
        self.log.emit(f"Frozen build detected — downloading standalone binary: {url}", "info")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "yt-dlp-gui"})
            with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
                total = int(resp.headers.get("Content-Length", 0) or 0)
                downloaded = 0
                with open(dest, "wb") as fh:
                    while True:
                        chunk = resp.read(256 * 1024)
                        if not chunk:
                            break
                        fh.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            self.progress.emit(int(downloaded / total * 100), f"Downloading… {downloaded // 1024} KiB")
            if system != "windows":
                dest.chmod(0o755)
            self.progress.emit(100, "Binary replaced")
            self.log.emit(f"Engine binary updated at {dest}. No restart needed.", "success")
            self.finished.emit(True, "latest", f"Binary updated: {dest.name}")
        except Exception as exc:  # noqa: BLE001
            msg = f"Binary update failed: {exc}"
            self.error.emit(msg)
            self.finished.emit(False, "", msg)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_yt_dlp_version() -> str:
    try:
        import yt_dlp as _y  # local import: picks up freshly upgraded package
        return str(_y.version.__version__)
    except Exception:
        return "unknown"


def parse_formats(formats: List[Dict[str, Any]], info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Reduce raw yt-dlp format dicts to the columns the UI table needs."""
    parsed: List[Dict[str, Any]] = []
    for f in formats:
        if f.get("vcodec") == "none" and f.get("acodec") == "none":
            continue  # storyboard / images
        size = f.get("filesize") or f.get("filesize_approx") or 0
        parsed.append({
            "format_id": str(f.get("format_id", "")),
            "ext": str(f.get("ext", "")),
            "resolution": str(f.get("resolution") or ""),
            "height": int(f.get("height") or 0),
            "fps": f.get("fps") or 0,
            "vcodec": str(f.get("vcodec") or "none"),
            "acodec": str(f.get("acodec") or "none"),
            "filesize": int(size or 0),
            "tbr": f.get("tbr") or 0,
            "format_note": str(f.get("format_note") or ""),
            "protocol": str(f.get("protocol") or ""),
        })
    # Best-first ordering for display.
    parsed.sort(key=lambda r: (r["height"], float(r["tbr"] or 0)), reverse=True)
    return parsed
