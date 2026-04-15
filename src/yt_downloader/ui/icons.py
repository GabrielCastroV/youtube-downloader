"""Icon loading helpers.

We use simple Unicode glyphs for most icons so no image files are required.
For thumbnail loading we use Pillow.
"""

from __future__ import annotations

import io
import logging
import urllib.request
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL.ImageTk import PhotoImage as PILPhotoImage

log = logging.getLogger(__name__)

# Unicode glyphs used throughout the UI
ICON_PASTE = "⎘"
ICON_FOLDER = "📁"
ICON_SETTINGS = "⚙"
ICON_MOON = "🌙"
ICON_SUN = "☀"
ICON_QUEUE = "☰"
ICON_HISTORY = "🕒"
ICON_DOWNLOAD = "↓"
ICON_CANCEL = "✕"
ICON_RETRY = "↺"
ICON_CHECK = "✓"
ICON_WARN = "⚠"
ICON_ERROR = "✕"
ICON_CLOSE = "✕"
ICON_CHEVRON = "›"
ICON_LANGUAGE = "🌐"
ICON_OPEN = "↗"
ICON_TRASH = "🗑"


def load_thumbnail(url: str, width: int = 200, height: int = 112) -> PILPhotoImage | None:
    """Download a thumbnail image and return a Pillow PhotoImage, or None on failure."""
    try:
        from PIL import Image, ImageTk  # type: ignore[import-untyped]

        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()

        img = Image.open(io.BytesIO(data)).convert("RGB")
        img = img.resize((width, height), Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        log.debug("Thumbnail load failed for %s", url, exc_info=True)
        return None
