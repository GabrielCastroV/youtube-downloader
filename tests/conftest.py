"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from yt_downloader.config import Config
from yt_downloader.i18n import Translator
from yt_downloader.models import DownloadOptions, VideoInfo


@pytest.fixture
def tmp_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect all platform dirs to a temp directory."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    return tmp_path


@pytest.fixture
def default_config() -> Config:
    return Config()


@pytest.fixture
def translator_es() -> Translator:
    return Translator("es")


@pytest.fixture
def translator_en() -> Translator:
    return Translator("en")


@pytest.fixture
def sample_video_info() -> VideoInfo:
    return VideoInfo(
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        title="Rick Astley - Never Gonna Give You Up",
        channel="Rick Astley",
        duration_s=213,
        thumbnail_url="https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
        is_short=False,
        is_playlist=False,
        playlist_count=None,
        available_resolutions=["1080", "720", "480", "360"],
    )


@pytest.fixture
def sample_options(tmp_path: Path) -> DownloadOptions:
    return DownloadOptions(
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        mode="video+audio",
        output_dir=tmp_path,
    )


@pytest.fixture
def mock_yt_dlp(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Mock yt_dlp.YoutubeDL to avoid real network calls."""
    mock_ydl = MagicMock()
    mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
    mock_ydl.__exit__ = MagicMock(return_value=False)
    mock_ydl.extract_info.return_value = {
        "title": "Test Video",
        "uploader": "Test Channel",
        "duration": 120,
        "thumbnail": "https://example.com/thumb.jpg",
        "formats": [
            {"height": 1080, "vcodec": "avc1.4d401f", "acodec": "mp4a.40.2"},
            {"height": 720, "vcodec": "avc1.4d401f", "acodec": "mp4a.40.2"},
        ],
    }
    mock_ydl.download.return_value = None
    monkeypatch.setattr("yt_dlp.YoutubeDL", lambda opts: mock_ydl)
    return mock_ydl
