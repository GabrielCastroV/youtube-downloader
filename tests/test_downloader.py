"""Tests for downloader.py."""

from __future__ import annotations

import queue
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from yt_downloader.downloader import Downloader, _parse_timestamp
from yt_downloader.exceptions import (
    FFmpegMissingError,
    NetworkError,
    QualityUnavailableError,
    VideoUnavailableError,
)
from yt_downloader.models import DownloadOptions, ProgressEvent


@pytest.fixture
def options(tmp_path: Path) -> DownloadOptions:
    return DownloadOptions(
        url="https://www.youtube.com/watch?v=test",
        output_dir=tmp_path,
    )


@pytest.fixture
def event_queue() -> queue.Queue[ProgressEvent]:
    return queue.Queue()


class TestParseTimestamp:
    def test_mm_ss(self) -> None:
        assert _parse_timestamp("1:30") == pytest.approx(90.0)

    def test_hh_mm_ss(self) -> None:
        assert _parse_timestamp("1:01:00") == pytest.approx(3660.0)

    def test_zero(self) -> None:
        assert _parse_timestamp("0:00") == pytest.approx(0.0)


class TestDownloader:
    def _make_ydl_mock(self) -> MagicMock:
        m = MagicMock()
        m.__enter__ = MagicMock(return_value=m)
        m.__exit__ = MagicMock(return_value=False)
        m.download.return_value = None
        return m

    def test_successful_run(
        self, options: DownloadOptions, event_queue: queue.Queue[ProgressEvent]
    ) -> None:
        mock_ydl = self._make_ydl_mock()
        with patch("yt_dlp.YoutubeDL", return_value=mock_ydl):
            dl = Downloader(options, event_queue)
            dl.run()  # should not raise
        mock_ydl.download.assert_called_once()

    def test_cancel_raises(
        self, options: DownloadOptions, event_queue: queue.Queue[ProgressEvent]
    ) -> None:
        import yt_dlp

        mock_ydl = self._make_ydl_mock()

        def side_effect_cancel(urls: list[str]) -> None:
            raise yt_dlp.utils.DownloadError("cancelled")

        mock_ydl.download.side_effect = side_effect_cancel

        with patch("yt_dlp.YoutubeDL", return_value=mock_ydl):
            dl = Downloader(options, event_queue)
            dl.cancel()
            assert dl._cancel_event.is_set()

    def test_map_error_network(self) -> None:
        import yt_dlp

        exc = yt_dlp.utils.DownloadError("network timeout connection refused")
        mapped = Downloader._map_error(exc)
        assert isinstance(mapped, NetworkError)

    def test_map_error_unavailable(self) -> None:
        import yt_dlp

        exc = yt_dlp.utils.DownloadError("Video unavailable: private")
        mapped = Downloader._map_error(exc)
        assert isinstance(mapped, VideoUnavailableError)

    def test_map_error_ffmpeg(self) -> None:
        import yt_dlp

        exc = yt_dlp.utils.DownloadError("ffmpeg not found at path")
        mapped = Downloader._map_error(exc)
        assert isinstance(mapped, FFmpegMissingError)

    def test_map_error_quality(self) -> None:
        import yt_dlp

        exc = yt_dlp.utils.DownloadError("requested format is not available")
        mapped = Downloader._map_error(exc)
        assert isinstance(mapped, QualityUnavailableError)

    def test_build_format_audio_only(
        self, options: DownloadOptions, event_queue: queue.Queue[ProgressEvent]
    ) -> None:
        from dataclasses import replace

        opts = replace(options, mode="audio")
        dl = Downloader(opts, event_queue)
        assert dl._build_format_string() == "bestaudio/best"

    def test_build_format_video_only(
        self, options: DownloadOptions, event_queue: queue.Queue[ProgressEvent]
    ) -> None:
        from dataclasses import replace

        opts = replace(options, mode="video", video_resolution="720")
        dl = Downloader(opts, event_queue)
        fmt = dl._build_format_string()
        assert "height<=720" in fmt
        assert "bestaudio" not in fmt

    def test_build_format_video_audio(
        self, options: DownloadOptions, event_queue: queue.Queue[ProgressEvent]
    ) -> None:
        from dataclasses import replace

        opts = replace(options, mode="video+audio", video_resolution="1080")
        dl = Downloader(opts, event_queue)
        fmt = dl._build_format_string()
        assert "height<=1080" in fmt
        assert "bestaudio" in fmt
