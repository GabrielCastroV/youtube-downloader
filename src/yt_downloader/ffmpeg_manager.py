"""FFmpeg auto-detection and installation manager.

Detection order:
  1. Explicit path from user config.
  2. System PATH.
  3. App-managed binary at ``<user_data_dir>/bin/ffmpeg[.exe]``.

Installation downloads the official static build for the current OS and
extracts the ``ffmpeg`` executable into the app-managed directory.
"""

from __future__ import annotations

import logging
import platform
import shutil
import stat
import tempfile
import urllib.request
import zipfile
from collections.abc import Callable
from pathlib import Path

from yt_downloader.exceptions import FFmpegInstallError
from yt_downloader.paths import ffmpeg_bin_dir

log = logging.getLogger(__name__)

_OS = platform.system()

# Official static build URLs (no auth, no tracking)
_DOWNLOAD_URLS: dict[str, str] = {
    "Windows": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
    "Darwin": "https://evermeet.cx/ffmpeg/getrelease/ffmpeg/zip",
    "Linux": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz",
}


def _ffmpeg_exe_name() -> str:
    return "ffmpeg.exe" if _OS == "Windows" else "ffmpeg"


def detect(explicit_path: str = "") -> Path | None:
    """Return the path to an existing ffmpeg binary, or *None*."""
    # 1. Explicit config path
    if explicit_path:
        p = Path(explicit_path)
        if p.is_file():
            log.debug("FFmpeg from config: %s", p)
            return p

    # 2. System PATH
    found = shutil.which("ffmpeg")
    if found:
        log.debug("FFmpeg in PATH: %s", found)
        return Path(found)

    # 3. App-managed location
    managed = ffmpeg_bin_dir() / _ffmpeg_exe_name()
    if managed.is_file():
        log.debug("FFmpeg managed: %s", managed)
        return managed

    return None


def install(progress_cb: Callable[[int, int], None] | None = None) -> Path:
    """Download and install the official ffmpeg binary.

    *progress_cb(bytes_done, bytes_total)* is called periodically if provided.

    Returns the installed :class:`~pathlib.Path`.
    Raises :class:`~yt_downloader.exceptions.FFmpegInstallError` on failure.
    """
    url = _DOWNLOAD_URLS.get(_OS)
    if not url:
        raise FFmpegInstallError(f"Unsupported OS for auto-install: {_OS}")

    log.info("Downloading FFmpeg from %s", url)
    dest_dir = ffmpeg_bin_dir()

    try:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            archive = tmp_path / ("ffmpeg.zip" if "zip" in url else "ffmpeg.tar.xz")

            _download(url, archive, progress_cb)

            if archive.suffix == ".zip":
                exe = _extract_zip(archive, tmp_path)
            else:
                exe = _extract_tarxz(archive, tmp_path)

            dest = dest_dir / _ffmpeg_exe_name()
            shutil.copy2(exe, dest)

            if _OS != "Windows":
                dest.chmod(dest.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

            log.info("FFmpeg installed at %s", dest)
            return dest

    except FFmpegInstallError:
        raise
    except Exception as exc:
        log.exception("FFmpeg install failed")
        raise FFmpegInstallError(str(exc)) from exc


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _download(url: str, dest: Path, cb: Callable[[int, int], None] | None) -> None:
    with urllib.request.urlopen(url, timeout=60) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        done = 0
        chunk = 64 * 1024
        with dest.open("wb") as fh:
            while True:
                data = resp.read(chunk)
                if not data:
                    break
                fh.write(data)
                done += len(data)
                if cb:
                    cb(done, total)


def _extract_zip(archive: Path, tmp: Path) -> Path:
    """Extract and return the ffmpeg executable path."""
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(tmp)
    # gyan.dev layout: ffmpeg-*-essentials_build/bin/ffmpeg.exe
    matches = list(tmp.rglob("ffmpeg.exe"))
    if not matches:
        matches = list(tmp.rglob("ffmpeg"))
    if not matches:
        raise FFmpegInstallError("ffmpeg binary not found in archive")
    return matches[0]


def _extract_tarxz(archive: Path, tmp: Path) -> Path:
    import tarfile

    with tarfile.open(archive, "r:xz") as tf:
        tf.extractall(tmp)
    matches = list(tmp.rglob("ffmpeg"))
    if not matches:
        raise FFmpegInstallError("ffmpeg binary not found in archive")
    # pick the actual executable (not a directory)
    return next(p for p in matches if p.is_file())
