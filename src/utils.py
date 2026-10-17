"""Small helpers: formatting, validation, settings persistence."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict

from PySide6.QtCore import QSettings

ORG = "YT-DLP-Studio"
APP = "ytdlp-studio"


def format_bytes(n: Any) -> str:
    try:
        n = float(n or 0)
    except (TypeError, ValueError):
        return "—"
    if n <= 0:
        return "—"
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if n < 1024 or unit == "TiB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024
    return f"{n:.1f} TiB"


def format_speed(bps: Any) -> str:
    try:
        bps = float(bps or 0)
    except (TypeError, ValueError):
        return "—"
    if bps <= 0:
        return "—"
    return f"{format_bytes(bps)}/s"


def format_eta(secs: Any) -> str:
    try:
        secs = int(secs) if secs is not None else -1
    except (TypeError, ValueError):
        return "ETA —"
    if secs is None or secs < 0:
        return "ETA —"
    if secs < 60:
        return f"ETA {secs}s"
    m, s = divmod(secs, 60)
    if m < 60:
        return f"ETA {m}m {s:02d}s"
    h, m = divmod(m, 60)
    return f"ETA {h}h {m:02d}m"


def format_percent(downloaded: Any, total: Any, fallback: str = "") -> float:
    """Return 0..100 float; fall back to parsing '12.3%' strings."""
    try:
        d, t = float(downloaded or 0), float(total or 0)
        if t > 0:
            return max(0.0, min(100.0, d / t * 100.0))
    except (TypeError, ValueError):
        pass
    m = re.search(r"([\d.]+)\s*%", fallback or "")
    if m:
        try:
            return max(0.0, min(100.0, float(m.group(1))))
        except ValueError:
            pass
    return 0.0


def is_valid_url(text: str) -> bool:
    t = (text or "").strip()
    return t.startswith(("http://", "https://", "ytsearch", "ytsearchdate", "geo:")) and len(t) > 10


def load_settings(defaults: Dict[str, Any]) -> Dict[str, Any]:
    store = QSettings(ORG, APP)
    data: Dict[str, Any] = dict(defaults)
    try:
        raw = store.value("settings_json", "")
        if raw:
            saved = json.loads(str(raw))
            if isinstance(saved, dict):
                data.update(saved)
    except Exception:
        pass
    return data


def save_settings(settings: Dict[str, Any]) -> None:
    try:
        store = QSettings(ORG, APP)
        store.setValue("settings_json", json.dumps(settings, default=str))
    except Exception:
        pass


def ensure_dir(path: str) -> str:
    p = Path(path).expanduser()
    try:
        p.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return str(p)
