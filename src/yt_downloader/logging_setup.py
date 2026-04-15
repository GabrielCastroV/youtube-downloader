"""Configure application-wide logging.

* Console: simple INFO-level messages during development.
* File: rotating log at the platform log directory, DEBUG level, with
  full tracebacks.  Max 5 × 1 MB files.
"""

from __future__ import annotations

import logging
import logging.handlers
import sys

from yt_downloader.paths import log_path

_configured = False


def setup(debug: bool = False) -> None:
    global _configured
    if _configured:
        return
    _configured = True

    root = logging.getLogger("yt_downloader")
    root.setLevel(logging.DEBUG)

    # --- rotating file handler ---
    fh = logging.handlers.RotatingFileHandler(
        log_path(),
        maxBytes=1 * 1024 * 1024,  # 1 MB
        backupCount=4,
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    root.addHandler(fh)

    # --- stream handler (stderr) ---
    sh = logging.StreamHandler(sys.stderr)
    sh.setLevel(logging.DEBUG if debug else logging.WARNING)
    sh.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    root.addHandler(sh)

    # Silence noisy third-party loggers
    logging.getLogger("yt_dlp").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
