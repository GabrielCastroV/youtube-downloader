"""Application directory resolution (XDG / platform-dirs aware)."""

from __future__ import annotations

from pathlib import Path

from platformdirs import user_config_dir, user_data_dir, user_log_dir

APP_NAME = "yt-downloader"
APP_AUTHOR = "GabrielCastroV"


def config_dir() -> Path:
    p = Path(user_config_dir(APP_NAME, APP_AUTHOR))
    p.mkdir(parents=True, exist_ok=True)
    return p


def data_dir() -> Path:
    p = Path(user_data_dir(APP_NAME, APP_AUTHOR))
    p.mkdir(parents=True, exist_ok=True)
    return p


def log_dir() -> Path:
    p = Path(user_log_dir(APP_NAME, APP_AUTHOR))
    p.mkdir(parents=True, exist_ok=True)
    return p


def ffmpeg_bin_dir() -> Path:
    p = data_dir() / "bin"
    p.mkdir(parents=True, exist_ok=True)
    return p


def db_path() -> Path:
    return data_dir() / "history.db"


def config_path() -> Path:
    return config_dir() / "config.json"


def log_path() -> Path:
    return log_dir() / "app.log"
