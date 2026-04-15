"""Fetch video metadata without downloading the media.

Uses yt-dlp in ``extract_info`` mode with ``download=False``.  The call is
intentionally synchronous so it can be wrapped in a thread by the caller.
"""

from __future__ import annotations

import logging
import re

import yt_dlp  # type: ignore[import-untyped]

from yt_downloader.exceptions import (
    InvalidURLError,
    NetworkError,
    UnexpectedError,
    VideoUnavailableError,
)
from yt_downloader.models import VideoInfo

log = logging.getLogger(__name__)

_YT_URL_PATTERN = re.compile(
    r"(https?://)?(www\.)?"
    r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
    r"[\w\-_&=?%+]+"
)


def is_youtube_url(url: str) -> bool:
    return bool(_YT_URL_PATTERN.search(url.strip()))


def fetch(url: str) -> VideoInfo:
    """Extract metadata for *url* and return a :class:`VideoInfo`.

    Raises one of the typed exceptions from :mod:`yt_downloader.exceptions`.
    """
    url = url.strip()
    if not is_youtube_url(url):
        raise InvalidURLError(f"Not a YouTube URL: {url!r}")

    ydl_opts: dict[str, object] = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": "discard_in_playlist",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as exc:
        msg = str(exc).lower()
        if any(k in msg for k in ("private", "unavailable", "removed", "geo", "age")):
            raise VideoUnavailableError(str(exc)) from exc
        if any(k in msg for k in ("network", "timeout", "connection", "resolve")):
            raise NetworkError(str(exc)) from exc
        raise UnexpectedError(str(exc)) from exc
    except Exception as exc:
        log.debug("Unexpected metadata error", exc_info=True)
        raise UnexpectedError(str(exc)) from exc

    if info is None:
        raise VideoUnavailableError("yt-dlp returned no info")

    # Playlist vs single video
    is_playlist = info.get("_type") == "playlist"
    playlist_count: int | None = info.get("playlist_count") if is_playlist else None

    if is_playlist:
        # Use first entry for thumbnail/title preview
        entries = info.get("entries") or []
        first = entries[0] if entries else {}
        title = info.get("title") or first.get("title") or "Playlist"
        channel = info.get("uploader") or first.get("uploader") or ""
        duration_s = int(first.get("duration") or 0)
        thumbnail_url = info.get("thumbnail") or first.get("thumbnail")
    else:
        title = info.get("title") or ""
        channel = info.get("uploader") or info.get("channel") or ""
        duration_s = int(info.get("duration") or 0)
        thumbnail_url = info.get("thumbnail")

    # Detect shorts: URL pattern or duration ≤ 60 s
    is_short = "/shorts/" in url or (not is_playlist and 0 < duration_s <= 60)

    # Collect available resolutions
    formats = info.get("formats") or []
    resolutions: list[str] = sorted(
        {str(f["height"]) for f in formats if f.get("height") and f.get("vcodec") != "none"},
        key=lambda h: int(h),
        reverse=True,
    )

    return VideoInfo(
        url=url,
        title=title,
        channel=channel,
        duration_s=duration_s,
        thumbnail_url=thumbnail_url,
        is_short=is_short,
        is_playlist=is_playlist,
        playlist_count=playlist_count,
        available_resolutions=resolutions,
    )
