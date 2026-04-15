"""Tests for metadata.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from yt_downloader.exceptions import InvalidURLError, VideoUnavailableError
from yt_downloader.metadata import fetch, is_youtube_url


class TestIsYoutubeUrl:
    def test_watch_url(self) -> None:
        assert is_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_short_url(self) -> None:
        assert is_youtube_url("https://youtu.be/dQw4w9WgXcQ")

    def test_shorts_url(self) -> None:
        assert is_youtube_url("https://www.youtube.com/shorts/abc123")

    def test_playlist_url(self) -> None:
        assert is_youtube_url("https://www.youtube.com/playlist?list=PLtest")

    def test_invalid_url(self) -> None:
        assert not is_youtube_url("https://example.com/video")

    def test_empty_string(self) -> None:
        assert not is_youtube_url("")

    def test_random_text(self) -> None:
        assert not is_youtube_url("just some text without a url")


class TestFetch:
    def test_raises_invalid_url_for_non_youtube(self) -> None:
        with pytest.raises(InvalidURLError):
            fetch("https://vimeo.com/123456789")

    def test_raises_invalid_url_for_empty(self) -> None:
        with pytest.raises(InvalidURLError):
            fetch("")

    def test_successful_fetch(self) -> None:
        mock_info = {
            "title": "Test Video",
            "uploader": "Test Channel",
            "duration": 120,
            "thumbnail": "https://example.com/thumb.jpg",
            "formats": [
                {"height": 1080, "vcodec": "avc1", "acodec": "mp4a"},
                {"height": 720, "vcodec": "avc1", "acodec": "mp4a"},
            ],
        }
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = mock_info

        with patch("yt_dlp.YoutubeDL", return_value=mock_ydl):
            info = fetch("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        assert info.title == "Test Video"
        assert info.channel == "Test Channel"
        assert info.duration_s == 120
        assert "1080" in info.available_resolutions
        assert not info.is_short
        assert not info.is_playlist

    def test_short_detection_by_url(self) -> None:
        mock_info = {
            "title": "A Short",
            "uploader": "Creator",
            "duration": 45,
            "thumbnail": None,
            "formats": [],
        }
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = mock_info

        with patch("yt_dlp.YoutubeDL", return_value=mock_ydl):
            info = fetch("https://www.youtube.com/shorts/abc123")

        assert info.is_short

    def test_unavailable_video_raises(self) -> None:
        import yt_dlp

        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.side_effect = yt_dlp.utils.DownloadError(
            "Video unavailable: private video"
        )

        with patch("yt_dlp.YoutubeDL", return_value=mock_ydl), pytest.raises(VideoUnavailableError):
            fetch("https://www.youtube.com/watch?v=private123")
