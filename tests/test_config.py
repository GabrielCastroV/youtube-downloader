"""Tests for config.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from yt_downloader.config import Config, load, save


def test_default_config() -> None:
    cfg = Config()
    assert cfg.language == "es"
    assert cfg.theme == "dark"
    assert cfg.embed_thumbnail is True
    assert cfg.window_width == 540
    assert cfg.concurrent_downloads == 2
    assert cfg.auto_open_after_download is False
    assert cfg.notify_on_complete is True
    assert cfg.speed_limit_kbps == 0
    assert cfg.max_retries == 3


def test_config_validation() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Config(window_width=100)  # below minimum


def test_new_field_validation_concurrent() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Config(concurrent_downloads=0)  # below minimum (1)
    with pytest.raises(ValidationError):
        Config(concurrent_downloads=6)  # above maximum (5)


def test_new_field_validation_speed_limit() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Config(speed_limit_kbps=-1)  # negative not allowed


def test_new_field_validation_retries() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Config(max_retries=-1)  # below minimum (0)
    with pytest.raises(ValidationError):
        Config(max_retries=11)  # above maximum (10)


def test_new_fields_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from yt_downloader.config import load, save

    cfg_file = tmp_path / "config.json"
    monkeypatch.setattr("yt_downloader.config.config_path", lambda: cfg_file)

    cfg = Config(
        concurrent_downloads=4,
        auto_open_after_download=True,
        notify_on_complete=False,
        speed_limit_kbps=1000,
        max_retries=5,
    )
    save(cfg)
    loaded = load()

    assert loaded.concurrent_downloads == 4
    assert loaded.auto_open_after_download is True
    assert loaded.notify_on_complete is False
    assert loaded.speed_limit_kbps == 1000
    assert loaded.max_retries == 5


def test_save_and_load(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg_file = tmp_path / "config.json"
    monkeypatch.setattr("yt_downloader.config.config_path", lambda: cfg_file)

    cfg = Config(language="en", theme="light", window_width=600)
    save(cfg)

    assert cfg_file.exists()
    data = json.loads(cfg_file.read_text())
    assert data["language"] == "en"
    assert data["theme"] == "light"
    assert data["window_width"] == 600


def test_load_nonexistent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    missing = tmp_path / "nonexistent.json"
    monkeypatch.setattr("yt_downloader.config.config_path", lambda: missing)
    cfg = load()
    assert cfg.language == "es"  # defaults


def test_load_corrupt_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bad_file = tmp_path / "config.json"
    bad_file.write_text("not json at all!!!", encoding="utf-8")
    monkeypatch.setattr("yt_downloader.config.config_path", lambda: bad_file)
    cfg = load()
    assert cfg.language == "es"  # falls back to defaults


def test_load_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg_file = tmp_path / "config.json"
    monkeypatch.setattr("yt_downloader.config.config_path", lambda: cfg_file)

    original = Config(language="en", theme="light", embed_thumbnail=False)
    save(original)
    loaded = load()

    assert loaded.language == original.language
    assert loaded.theme == original.theme
    assert loaded.embed_thumbnail == original.embed_thumbnail
