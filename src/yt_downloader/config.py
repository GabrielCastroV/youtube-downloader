"""User configuration, persisted as JSON in the platform config directory.

Uses Pydantic v2 for validation and serialisation.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from yt_downloader.paths import config_path

log = logging.getLogger(__name__)

Language = Literal["es", "en"]
Theme = Literal["dark", "light"]
DownloadMode = Literal["video+audio", "audio", "video"]


class Config(BaseModel):
    """All persisted user preferences."""

    language: Language = "es"
    theme: Theme = "dark"
    default_output_dir: str = str(Path.home() / "Downloads")
    default_mode: DownloadMode = "video+audio"
    default_audio_format: str = "m4a"
    default_audio_quality: str = "best"
    default_video_resolution: str = "1080"
    default_video_container: str = "mp4"
    default_video_codec: str = "best"
    embed_thumbnail: bool = True
    embed_metadata: bool = True
    filename_template: str = "%(title)s.%(ext)s"
    window_width: int = Field(default=540, ge=400, le=1200)
    window_height: int = Field(default=680, ge=500, le=1200)
    ffmpeg_path: str = ""  # empty = auto-detect
    # Advanced preferences
    concurrent_downloads: int = Field(default=2, ge=1, le=5)
    auto_open_after_download: bool = False
    notify_on_complete: bool = True
    speed_limit_kbps: int = Field(default=0, ge=0)  # 0 = unlimited
    max_retries: int = Field(default=3, ge=0, le=10)

    model_config = {"validate_assignment": True}


def load() -> Config:
    """Load config from disk, returning defaults if the file doesn't exist."""
    path = config_path()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return Config(**data)
        except Exception:
            log.warning("Config file corrupt or incompatible; using defaults.", exc_info=True)
    return Config()


def save(cfg: Config) -> None:
    """Persist config to disk."""
    path = config_path()
    try:
        path.write_text(cfg.model_dump_json(indent=2), encoding="utf-8")
    except OSError:
        log.warning("Could not save config to %s", path, exc_info=True)
