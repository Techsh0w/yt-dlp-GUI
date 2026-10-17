"""Centralised yt-dlp option catalogue + builder.

The settings UI edits a plain ``dict`` (see DEFAULT_SETTINGS). This module
translates that dict into a valid ``ydl_opts`` dict for yt-dlp. Keeping the
mapping in one place makes the UI "dynamic": adding a key here + a widget
in ui_main.py is all it takes to expose a new yt-dlp parameter.
"""

from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List

APP_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Presets shown in comboboxes
# ---------------------------------------------------------------------------
FORMAT_PRESETS: Dict[str, str] = {
    "Best quality (auto merge)": "bestvideo+bestaudio/best",
    "Best ≤ 1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
    "Best ≤ 720p": "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
    "Best ≤ 480p": "bestvideo[height<=480]+bestaudio/best[height<=480]/best",
    "Audio only (best)": "bestaudio/best",
    "Video only (best)": "bestvideo/best",
    "Smallest file": "worstvideo+worstaudio/worst",
    "MP4 preferred": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    "Custom…": "__custom__",
}

OUTTMPL_PRESETS: Dict[str, str] = {
    "Title + ID": "%(title)s [%(id)s].%(ext)s",
    "Title only": "%(title)s.%(ext)s",
    "Channel / Title": "%(uploader)s/%(title)s [%(id)s].%(ext)s",
    "Playlist indexed": "%(playlist_index)03d - %(title)s [%(id)s].%(ext)s",
    "Date + Title": "%(upload_date)s - %(title)s [%(id)s].%(ext)s",
}

MERGE_FORMATS = ["mkv", "mp4", "webm", "mov", "m4a", "mp3", "opus", "flac", "wav"]
AUDIO_FORMATS = ["mp3", "m4a", "opus", "flac", "wav", "vorbis", "aac"]
SUB_FORMATS = ["srt", "vtt", "ass", "lrc", "best"]
BROWSERS = ["none", "chrome", "chromium", "firefox", "edge", "brave", "opera", "safari", "vivaldi"]
SPONSOR_CATEGORIES = ["sponsor", "intro", "outro", "selfpromo", "interaction", "preview", "music_offtopic"]

DEFAULT_DOWNLOAD_DIR = str(Path.home() / "Downloads")


def default_settings() -> Dict[str, Any]:
    """Fresh settings dict with sane cross-platform defaults."""
    return {
        # General & output
        "format_preset": "Best quality (auto merge)",
        "format_custom": "bestvideo+bestaudio/best",
        "merge_format": "mkv",
        "output_dir": DEFAULT_DOWNLOAD_DIR,
        "outtmpl_preset": "Title + ID",
        "outtmpl_custom": OUTTMPL_PRESETS["Title + ID"],
        "restrict_filenames": False,
        "windows_filenames": False,
        "embed_thumbnail": True,
        "embed_metadata": True,
        "embed_chapters": True,
        "write_thumbnail": False,
        "write_info_json": False,
        "write_description": False,
        "no_overwrites": False,
        "continuedl": True,
        # Playlist & range
        "noplaylist": False,
        "playlist_start": 1,
        "playlist_end": 0,  # 0 == unset
        "playlist_items": "",
        "max_downloads": 0,
        "date_after": "",
        "date_before": "",
        "match_filter": "",
        "section_start": "",
        "section_end": "",
        # Auth & network
        "cookie_file": "",
        "cookies_from_browser": "none",
        "proxy": "",
        "socket_timeout": 30,
        "retries": 10,
        "rate_limit": "",
        "user_agent": "",
        "referer": "",
        "no_check_certificate": False,
        # Subtitles & SponsorBlock
        "sponsor_categories": ["sponsor", "selfpromo", "interaction"],
        "sponsor_action": "remove",  # remove | mark_chapters
        "write_subs": False,
        "embed_subs": False,
        "auto_subs": False,
        "subs_langs": "en",
        "subs_format": "srt",
        # Post-processing & advanced
        "extract_audio": False,
        "audio_format": "mp3",
        "audio_quality": "192",
        "concurrent_fragments": 4,
        "hls_prefer_native": False,
        "ffmpeg_location": "",
        "postprocessor_args": "",
        "extractor_args": "",
        "exec_after": "",
        "verbose": False,
        "custom_ydl_json": "",
        # Engine
        "auto_check_updates": True,
    }


def build_ydl_opts(settings: Dict[str, Any], *, for_probe: bool = False) -> Dict[str, Any]:
    """Map the settings dict to a yt-dlp ``ydl_opts`` dict.

    Raises ValueError with a human message on invalid user input (bad JSON,
    bad ints, …) so the UI can show it instead of crashing.
    """
    s = settings
    ydl: Dict[str, Any] = {
        "quiet": not bool(s.get("verbose")),
        "no_warnings": not bool(s.get("verbose")),
        "verbose": bool(s.get("verbose")),
        "continuedl": bool(s.get("continuedl", True)),
        "nooverwrites": bool(s.get("no_overwrites", False)),
        "restrictfilenames": bool(s.get("restrict_filenames", False)),
        "windowsfilenames": bool(s.get("windows_filenames", False)),
        "socket_timeout": int(s.get("socket_timeout") or 30),
        "retries": int(s.get("retries") if s.get("retries") != "" else 10),
        "concurrent_fragment_downloads": int(s.get("concurrent_fragments") or 4),
        "hls_prefer_native": bool(s.get("hls_prefer_native", False)),
        "nocheckcertificate": bool(s.get("no_check_certificate", False)),
    }

    # -- format ----------------------------------------------------------
    preset = s.get("format_preset", "")
    if preset == "Custom…":
        fmt = (s.get("format_custom") or "").strip()
    else:
        fmt = FORMAT_PRESETS.get(preset, "bestvideo+bestaudio/best")
    if s.get("extract_audio"):
        ydl["format"] = "bestaudio/best"
    elif fmt and fmt != "__custom__":
        ydl["format"] = fmt

    merge = (s.get("merge_format") or "").strip()
    if merge and not s.get("extract_audio"):
        ydl["merge_output_format"] = merge

    # -- output template ---------------------------------------------------
    out_dir = (s.get("output_dir") or DEFAULT_DOWNLOAD_DIR).strip() or DEFAULT_DOWNLOAD_DIR
    tmpl_name = s.get("outtmpl_preset", "Title + ID")
    tmpl = OUTTMPL_PRESETS.get(tmpl_name, s.get("outtmpl_custom", ""))
    if tmpl_name not in OUTTMPL_PRESETS:
        tmpl = s.get("outtmpl_custom", tmpl)
    # Absolute template: <dir>/<tmpl>
    ydl["outtmpl"] = str(Path(out_dir) / tmpl)
    os.makedirs(out_dir, exist_ok=True)

    # -- playlist / range ----------------------------------------------------
    ydl["noplaylist"] = bool(s.get("noplaylist", False))
    if int(s.get("playlist_start") or 1) > 1:
        ydl["playliststart"] = int(s["playlist_start"])
    if int(s.get("playlist_end") or 0) > 0:
        ydl["playlistend"] = int(s["playlist_end"])
    items = (s.get("playlist_items") or "").strip()
    if items:
        ydl["playlist_items"] = items  # e.g. "1-5,7,9"
    if int(s.get("max_downloads") or 0) > 0:
        ydl["max_downloads"] = int(s["max_downloads"])
    if (s.get("date_after") or "").strip():
        ydl["dateafter"] = s["date_after"].strip()
    if (s.get("date_before") or "").strip():
        ydl["datebefore"] = s["date_before"].strip()
    if (s.get("match_filter") or "").strip():
        ydl["match_filter"] = s["match_filter"].strip()

    # -- download sections (chapter slicing, e.g. *10:00-12:00) --------------
    sec_start = (s.get("section_start") or "").strip()
    sec_end = (s.get("section_end") or "").strip()
    if sec_start or sec_end:
        start = sec_start or "00:00"
        end = sec_end or "99:99:99"
        ydl["download_ranges"] = _make_section_range(start, end)
        ydl["force_keyframes_at_cuts"] = True

    # -- auth & network --------------------------------------------------------
    if (s.get("cookie_file") or "").strip():
        ydl["cookiefile"] = s["cookie_file"].strip()
    browser = s.get("cookies_from_browser", "none")
    if browser and browser != "none":
        ydl["cookiesfrombrowser"] = (browser,)
    if (s.get("proxy") or "").strip():
        ydl["proxy"] = s["proxy"].strip()
    if (s.get("rate_limit") or "").strip():
        ydl["ratelimit"] = _parse_rate_limit(s["rate_limit"].strip())
    headers: Dict[str, str] = {}
    if (s.get("user_agent") or "").strip():
        headers["User-Agent"] = s["user_agent"].strip()
    if (s.get("referer") or "").strip():
        headers["Referer"] = s["referer"].strip()
    if headers:
        ydl["http_headers"] = headers
    if (s.get("ffmpeg_location") or "").strip():
        ydl["ffmpeg_location"] = s["ffmpeg_location"].strip()

    # -- subtitles ---------------------------------------------------------------
    if s.get("write_subs") or s.get("embed_subs") or s.get("auto_subs"):
        ydl["writesubtitles"] = True
        ydl["writeautomaticsub"] = bool(s.get("auto_subs"))
        langs = [l.strip() for l in (s.get("subs_langs") or "en").split(",") if l.strip()]
        ydl["subtitleslangs"] = langs or ["en"]
        ydl["subtitlesformat"] = s.get("subs_format", "srt")
        ydl["embedsubtitles"] = bool(s.get("embed_subs"))

    # -- SponsorBlock --------------------------------------------------------------
    cats = [c for c in (s.get("sponsor_categories") or []) if c in SPONSOR_CATEGORIES]
    if cats:
        action = s.get("sponsor_action", "remove")
        if action == "mark_chapters":
            ydl["postprocessors"] = ydl.get("postprocessors", []) + [
                {"key": "SponsorBlock", "categories": cats, "api": "https://sponsor.ajay.app"},
                {"key": "ModifyChapters", "remove_sponsor_segments": set(), "force": False},
            ]
            # Marking is done via chapters; keep segments as chapters.
            ydl["postprocessors"][-2]["when"] = "pre_process"
        else:
            ydl["postprocessors"] = ydl.get("postprocessors", []) + [
                {"key": "SponsorBlock", "categories": cats, "api": "https://sponsor.ajay.app"}
            ]

    # -- embedding -------------------------------------------------------------------
    pp = list(ydl.get("postprocessors", []))
    if s.get("embed_metadata") and not for_probe:
    pp.append({"key": "FFmpegMetadata", "add_chapters": bool(s.get("embed_chapters")),
               "add_infojson": "if_exists"})
    if s.get("embed_thumbnail") and not for_probe:
        pp.append({"key": "EmbedThumbnail", "already_have_thumbnail": False})
    if s.get("extract_audio") and not for_probe:
        pp.append({"key": "FFmpegExtractAudio",
                   "preferredcodec": s.get("audio_format", "mp3"),
                   "preferredquality": str(s.get("audio_quality", "192"))})
    if s.get("embed_chapters") and not for_probe:
        # FFmpegMetadata already adds chapters; standalone embed for remux safety.
        pass
    if pp:
        ydl["postprocessors"] = pp
    if s.get("write_thumbnail"):
        ydl["writethumbnail"] = True
    if s.get("write_info_json"):
        ydl["writeinfojson"] = True
    if s.get("write_description"):
        ydl["writedescription"] = True

    # -- power-user freeform -------------------------------------------------------------
    if (s.get("postprocessor_args") or "").strip():
        ydl["postprocessor_args"] = _split_shell_like(s["postprocessor_args"])
    if (s.get("extractor_args") or "").strip():
        # yt-dlp expects extractor_args as dict; accept "key=value;key2=v2" shorthand.
        ydl["extractor_args"] = _parse_extractor_args(s["extractor_args"])
    if (s.get("exec_after") or "").strip() and not for_probe:
        cmd = s["exec_after"].strip()
        ydl["postprocessors"] = ydl.get("postprocessors", []) + [
            {"key": "Exec", "exec_cmd": cmd, "when": "after_move"}
        ]

    # -- custom JSON overlay (deep-merge, validated) ---------------------------------------
    custom_raw = (s.get("custom_ydl_json") or "").strip()
    if custom_raw:
        try:
            import json as _json
            overlay = _json.loads(custom_raw)
            if not isinstance(overlay, dict):
                raise ValueError("Custom JSON must be an object.")
            ydl.update(overlay)
        except Exception as exc:
            raise ValueError(f"Invalid custom ydl_opts JSON: {exc}") from exc

    if for_probe:
        ydl["skip_download"] = True

    return ydl


# ---------------------------------------------------------------------------
# parsers
# ---------------------------------------------------------------------------
def _parse_rate_limit(text: str) -> int:
    """Accept '1M', '500K', '2.5M', or raw bytes int → bytes/sec int."""
    t = text.strip().upper().replace(" ", "")
    mult = 1
    if t.endswith("K"):
        mult, t = 1024, t[:-1]
    elif t.endswith("M"):
        mult, t = 1024 * 1024, t[:-1]
    elif t.endswith("G"):
        mult, t = 1024 * 1024 * 1024, t[:-1]
    try:
        return int(float(t) * mult)
    except ValueError as exc:
        raise ValueError(f"Invalid rate limit '{text}'. Use e.g. 1M, 500K.") from exc


def _split_shell_like(text: str) -> List[str]:
    import shlex
    try:
        return shlex.split(text, posix=True)
    except ValueError as exc:
        raise ValueError(f"Could not parse args: {exc}") from exc


def _parse_extractor_args(text: str) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for chunk in text.replace(",", ";").split(";"):
        chunk = chunk.strip()
        if not chunk or "=" not in chunk:
            continue
        k, v = chunk.split("=", 1)
        out.setdefault(k.strip(), []).append(v.strip())
    return out


def _make_section_range(start: str, end: str):
    """Return a download_ranges callback-compatible spec for yt-dlp."""
    from yt_dlp.utils import parse_duration  # type: ignore

    def _cb(info_dict: Dict[str, Any], ydl):  # noqa: ANN001, ANN202
        dur = info_dict.get("duration") or 0
        s = parse_duration(start) or 0
        e = parse_duration(end) or dur or 0
        return [{"start_time": s, "end_time": e, "title": "custom section"}]

    return _cb


def settings_snapshot(settings: Dict[str, Any]) -> Dict[str, Any]:
    return deepcopy(settings)
