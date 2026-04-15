"""yt-dlp download wrapper.

The :class:`Downloader` translates a :class:`~yt_downloader.models.DownloadOptions`
into a yt-dlp options dict, runs the download in the **caller's thread**, and
reports progress via a :class:`queue.Queue` of :class:`~yt_downloader.models.ProgressEvent`.

Callers are responsible for running :meth:`Downloader.run` in a background
thread and draining the event queue to update the UI.
"""

from __future__ import annotations

import logging
import queue
import threading
from pathlib import Path
from typing import Any

import yt_dlp  # type: ignore[import-untyped]

from yt_downloader.exceptions import (
    DiskSpaceError,
    DownloadCancelled,
    DownloaderError,
    FFmpegMissingError,
    NetworkError,
    OutputPermissionError,
    QualityUnavailableError,
    UnexpectedError,
    VideoUnavailableError,
)
from yt_downloader.models import DownloadOptions, ProgressEvent

log = logging.getLogger(__name__)

# Sentinel placed on the queue when the download finishes (success or error).
_DONE = object()


class Downloader:
    """Runs a single download job and emits :class:`ProgressEvent` objects."""

    def __init__(
        self,
        options: DownloadOptions,
        event_queue: queue.Queue[ProgressEvent],
        ffmpeg_path: str = "",
    ) -> None:
        self._opts = options
        self._queue = event_queue
        self._ffmpeg_path = ffmpeg_path
        self._cancel_event = threading.Event()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def cancel(self) -> None:
        """Signal the download to abort."""
        self._cancel_event.set()

    def run(self) -> None:
        """Execute the download.  Raises a typed exception on failure."""
        ydl_opts = self._build_ydl_opts()
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self._opts.url])
        except DownloadCancelled:
            self._emit(ProgressEvent(stage="error", error_key="status.cancelled"))
            raise
        except yt_dlp.utils.DownloadError as exc:
            typed = self._map_error(exc)
            self._emit(ProgressEvent(stage="error", error_key=typed.user_key))
            raise typed from exc
        except OSError as exc:
            err_msg = str(exc).lower()
            if "no space" in err_msg or "enospc" in err_msg:
                typed_os: DiskSpaceError | OutputPermissionError = DiskSpaceError(str(exc))
            else:
                typed_os = OutputPermissionError(str(exc))
            self._emit(ProgressEvent(stage="error", error_key=typed_os.user_key))
            raise typed_os from exc
        except Exception as exc:
            log.debug("Unexpected download error", exc_info=True)
            ue = UnexpectedError(str(exc))
            self._emit(ProgressEvent(stage="error", error_key=ue.user_key))
            raise ue from exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _emit(self, event: ProgressEvent) -> None:
        self._queue.put(event)

    def _progress_hook(self, d: dict[str, Any]) -> None:
        if self._cancel_event.is_set():
            raise DownloadCancelled("Cancelled by user")

        status = d.get("status", "")

        if status == "downloading":
            self._emit(
                ProgressEvent(
                    stage="downloading",
                    bytes_done=d.get("downloaded_bytes") or 0,
                    bytes_total=d.get("total_bytes") or d.get("total_bytes_estimate"),
                    speed_bps=d.get("speed"),
                    eta_s=d.get("eta"),
                    filename=Path(d.get("filename", "")).name,
                )
            )
        elif status == "finished":
            # Post-processing follows; switch to indeterminate mode
            self._emit(
                ProgressEvent(
                    stage="processing",
                    bytes_done=d.get("total_bytes") or d.get("downloaded_bytes") or 0,
                    bytes_total=d.get("total_bytes") or d.get("downloaded_bytes"),
                    filename=Path(d.get("filename", "")).name,
                )
            )

    def _postprocessor_hook(self, d: dict[str, Any]) -> None:
        pp = d.get("postprocessor", "")
        stage = "merging" if "Merger" in pp or "FFmpeg" in pp else "processing"
        if d.get("status") == "started":
            self._emit(ProgressEvent(stage=stage))  # type: ignore[arg-type]
        elif d.get("status") == "finished":
            self._emit(
                ProgressEvent(
                    stage="done",
                    filename=Path(d.get("info_dict", {}).get("filepath", "")).name,
                )
            )

    def _build_ydl_opts(self) -> dict[str, Any]:
        opts = self._opts
        ydl: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [self._progress_hook],
            "postprocessor_hooks": [self._postprocessor_hook],
            "outtmpl": str(opts.output_dir / opts.filename_template),
            "windowsfilenames": True,
        }

        if self._ffmpeg_path:
            ydl["ffmpeg_location"] = self._ffmpeg_path

        # --- format string ---
        ydl["format"] = self._build_format_string()

        # --- post-processors ---
        postprocessors: list[dict[str, Any]] = []

        if opts.mode == "video+audio" and opts.video_container in ("mp4", "mkv", "webm"):
            postprocessors.append(
                {
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": opts.video_container,
                }
            )

        if opts.mode == "audio":
            postprocessors.append(
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": opts.audio_format,
                    "preferredquality": (
                        "0" if opts.audio_quality == "best" else opts.audio_quality
                    ),
                }
            )

        if opts.embed_metadata:
            postprocessors.append({"key": "FFmpegMetadata", "add_metadata": True})

        if opts.embed_thumbnail:
            postprocessors.append({"key": "EmbedThumbnail"})
            ydl["writethumbnail"] = True

        # Subtitles
        if opts.subtitles.enabled:
            ydl["writesubtitles"] = not opts.subtitles.embed
            ydl["embedsubtitles"] = opts.subtitles.embed
            ydl["writeautomaticsub"] = opts.subtitles.auto_generated
            ydl["subtitleslangs"] = list(opts.subtitles.languages)
            if opts.subtitles.embed:
                postprocessors.append({"key": "FFmpegEmbedSubtitle"})

        # Clip range
        if opts.clip_start or opts.clip_end:
            download_ranges: list[dict[str, Any]] = []
            if opts.clip_start or opts.clip_end:
                download_ranges.append(
                    {
                        "start_time": _parse_timestamp(opts.clip_start or "0:00"),
                        "end_time": _parse_timestamp(opts.clip_end) if opts.clip_end else None,
                    }
                )
            ydl["download_ranges"] = yt_dlp.utils.download_range_func(
                None, [(r.get("start_time", 0), r.get("end_time")) for r in download_ranges]
            )
            ydl["force_keyframes_at_cuts"] = True

        # Playlist range
        if opts.playlist_start:
            ydl["playliststart"] = opts.playlist_start
        if opts.playlist_end:
            ydl["playlistend"] = opts.playlist_end

        if postprocessors:
            ydl["postprocessors"] = postprocessors

        return ydl

    def _build_format_string(self) -> str:
        opts = self._opts

        if opts.mode == "audio":
            return "bestaudio/best"

        if opts.mode == "video":
            # Video-only stream, no audio
            if opts.video_resolution == "best":
                codec_filter = _codec_filter(opts.video_codec)
                return f"bestvideo{codec_filter}/bestvideo"
            h = opts.video_resolution
            codec_filter = _codec_filter(opts.video_codec)
            return (
                f"bestvideo[height<={h}]{codec_filter}"
                f"/bestvideo[height<={h}]"
                f"/bestvideo{codec_filter}"
                "/bestvideo"
            )

        # video+audio (default)
        if opts.video_resolution == "best":
            codec_filter = _codec_filter(opts.video_codec)
            return f"bestvideo{codec_filter}+bestaudio/best"
        h = opts.video_resolution
        codec_filter = _codec_filter(opts.video_codec)
        return (
            f"bestvideo[height<={h}]{codec_filter}+bestaudio"
            f"/bestvideo[height<={h}]+bestaudio"
            f"/best[height<={h}]"
            "/best"
        )

    @staticmethod
    def _map_error(exc: yt_dlp.utils.DownloadError) -> DownloaderError:
        msg = str(exc).lower()
        if any(k in msg for k in ("private", "unavailable", "removed", "geo", "age-restricted")):
            return VideoUnavailableError(str(exc))
        if any(k in msg for k in ("network", "timeout", "connection", "resolve", "dns")):
            return NetworkError(str(exc))
        if "ffmpeg" in msg or "ffprobe" in msg:
            return FFmpegMissingError(str(exc))
        if "requested format is not available" in msg or "no video formats" in msg:
            return QualityUnavailableError(str(exc))
        return UnexpectedError(str(exc))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _codec_filter(codec: str) -> str:
    if codec == "h264":
        return "[vcodec^=avc1]"
    if codec == "av1":
        return "[vcodec^=av01]"
    if codec == "vp9":
        return "[vcodec^=vp09]"
    return ""  # "best" → no filter


def _parse_timestamp(ts: str) -> float:
    """Convert 'mm:ss' or 'hh:mm:ss' to seconds."""
    parts = [float(p) for p in ts.split(":")]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return float(ts)
