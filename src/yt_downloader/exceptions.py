"""Typed exception hierarchy for yt-downloader.

All user-facing errors carry an i18n key (``user_key``) and an optional
technical detail string that is written to the log but never shown raw in the
UI.
"""

from __future__ import annotations


class DownloaderError(Exception):
    """Base class for all yt-downloader errors."""

    user_key: str = "error.unknown"

    def __init__(self, details: str = "") -> None:
        self.details = details
        super().__init__(details or self.__class__.__name__)


class InvalidURLError(DownloaderError):
    """The URL is not a recognisable YouTube URL."""

    user_key = "error.invalid_url"


class VideoUnavailableError(DownloaderError):
    """Video is private, removed, age-restricted, or geo-blocked."""

    user_key = "error.video_unavailable"


class NetworkError(DownloaderError):
    """DNS failure, timeout, or lost connection."""

    user_key = "error.network"


class FFmpegMissingError(DownloaderError):
    """FFmpeg not found; required for merging streams or converting formats."""

    user_key = "error.ffmpeg_missing"


class FFmpegInstallError(DownloaderError):
    """FFmpeg auto-install failed."""

    user_key = "error.ffmpeg_install"


class QualityUnavailableError(DownloaderError):
    """The requested quality/format is not available for this video."""

    user_key = "error.quality_unavailable"


class DiskSpaceError(DownloaderError):
    """Not enough disk space to complete the download."""

    user_key = "error.disk_space"


class OutputPermissionError(DownloaderError):
    """Cannot write to the selected output directory."""

    user_key = "error.permission"


class DownloadCancelled(DownloaderError):
    """User cancelled the download — not a real error, handled as normal flow."""

    user_key = "status.cancelled"


class UnexpectedError(DownloaderError):
    """Catch-all for unclassified errors; full traceback goes to log."""

    user_key = "error.unexpected"
