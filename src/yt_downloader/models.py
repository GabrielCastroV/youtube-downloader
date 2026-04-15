"""Domain model dataclasses.

All models are frozen (immutable after construction) and use ``__slots__``
for minimal memory overhead.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

# ---------------------------------------------------------------------------
# Download options
# ---------------------------------------------------------------------------

DownloadMode = Literal["video+audio", "audio", "video"]
AudioFormat = Literal["m4a", "mp3", "opus", "wav", "flac"]
VideoContainer = Literal["mp4", "webm", "mkv"]
VideoCodec = Literal["h264", "av1", "vp9", "best"]

AUDIO_QUALITIES = ["best", "320", "256", "192", "128", "96"]
VIDEO_RESOLUTIONS = ["best", "4320", "2160", "1440", "1080", "720", "480", "360"]


@dataclass(slots=True, frozen=True)
class SubtitleOptions:
    enabled: bool = False
    languages: tuple[str, ...] = ("en",)
    embed: bool = False  # True → embed in container; False → separate .srt files
    auto_generated: bool = True


@dataclass(slots=True, frozen=True)
class DownloadOptions:
    url: str
    mode: DownloadMode = "video+audio"
    # Audio options
    audio_format: AudioFormat = "m4a"
    audio_quality: str = "best"  # one of AUDIO_QUALITIES
    # Video options
    video_resolution: str = "1080"  # one of VIDEO_RESOLUTIONS
    video_container: VideoContainer = "mp4"
    video_codec: VideoCodec = "best"
    # Shared
    output_dir: Path = field(default_factory=lambda: Path.home() / "Downloads")
    filename_template: str = "%(title)s.%(ext)s"
    embed_thumbnail: bool = True
    embed_metadata: bool = True
    subtitles: SubtitleOptions = field(default_factory=SubtitleOptions)
    # Clip (None = full video)
    clip_start: str | None = None  # "mm:ss" or "hh:mm:ss"
    clip_end: str | None = None
    # Playlist
    playlist_start: int | None = None
    playlist_end: int | None = None


# ---------------------------------------------------------------------------
# Video info (from metadata fetch)
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class VideoInfo:
    url: str
    title: str
    channel: str
    duration_s: int  # seconds
    thumbnail_url: str | None
    is_short: bool
    is_playlist: bool
    playlist_count: int | None
    # Available qualities detected from yt-dlp
    available_resolutions: list[str] = field(default_factory=list)

    @property
    def duration_str(self) -> str:
        h, rem = divmod(self.duration_s, 3600)
        m, s = divmod(rem, 60)
        if h:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"


# ---------------------------------------------------------------------------
# Progress events (thread-safe, passed via queue.Queue)
# ---------------------------------------------------------------------------

ProgressStage = Literal["downloading", "processing", "merging", "done", "error"]


@dataclass(slots=True, frozen=True)
class ProgressEvent:
    stage: ProgressStage
    bytes_done: int = 0
    bytes_total: int | None = None
    speed_bps: float | None = None  # bytes per second
    eta_s: int | None = None
    filename: str = ""
    error_key: str | None = None  # i18n key when stage == "error"

    @property
    def percent(self) -> float | None:
        if self.bytes_total:
            return min(self.bytes_done / self.bytes_total * 100, 100.0)
        return None


# ---------------------------------------------------------------------------
# History entry
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class HistoryEntry:
    id: int
    url: str
    title: str
    filepath: str
    mode: DownloadMode
    timestamp: str  # ISO-8601
    success: bool
