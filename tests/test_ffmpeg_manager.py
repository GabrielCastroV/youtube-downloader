"""Tests for ffmpeg_manager.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from yt_downloader import ffmpeg_manager


class TestDetect:
    def test_returns_none_when_nothing_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("yt_downloader.ffmpeg_manager.ffmpeg_bin_dir", lambda: tmp_path)
        monkeypatch.setattr("shutil.which", lambda _: None)
        result = ffmpeg_manager.detect()
        assert result is None

    def test_detects_from_explicit_path(self, tmp_path: Path) -> None:
        exe = tmp_path / "ffmpeg.exe"
        exe.write_bytes(b"fake")
        result = ffmpeg_manager.detect(explicit_path=str(exe))
        assert result == exe

    def test_detects_from_managed_location(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("yt_downloader.ffmpeg_manager.ffmpeg_bin_dir", lambda: tmp_path)
        monkeypatch.setattr("shutil.which", lambda _: None)
        exe_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
        exe = tmp_path / exe_name
        exe.write_bytes(b"fake")
        result = ffmpeg_manager.detect()
        assert result == exe

    def test_detects_from_system_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake_ffmpeg = tmp_path / "ffmpeg"
        fake_ffmpeg.write_bytes(b"fake")
        managed_dir = tmp_path / "managed"
        monkeypatch.setattr("yt_downloader.ffmpeg_manager.ffmpeg_bin_dir", lambda: managed_dir)
        monkeypatch.setattr("shutil.which", lambda _: str(fake_ffmpeg))
        result = ffmpeg_manager.detect()
        assert result == fake_ffmpeg
