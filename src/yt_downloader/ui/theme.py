"""Design tokens for YT Downloader UI.

All colour, spacing, typography, and radius values live here.  Components
import from this module rather than hard-coding values.
"""

from __future__ import annotations

from typing import Literal

import customtkinter as ctk  # type: ignore[import-untyped]

ThemeMode = Literal["dark", "light"]


# ---------------------------------------------------------------------------
# Colour palettes
# ---------------------------------------------------------------------------


class _Palette:
    bg: str
    surface: str
    surface2: str
    border: str
    accent: str
    accent_hover: str
    accent_fg: str
    text: str
    text_muted: str
    success: str
    warning: str
    error: str


class _Dark(_Palette):
    bg = "#0D0D0F"
    surface = "#161618"
    surface2 = "#1F1F23"
    border = "#2C2C2E"
    accent = "#FF2D55"
    accent_hover = "#FF4568"
    accent_fg = "#FFFFFF"
    text = "#F5F5F7"
    text_muted = "#86868B"
    success = "#30D158"
    warning = "#FF9F0A"
    error = "#FF453A"


class _Light(_Palette):
    bg = "#FAFAFA"
    surface = "#FFFFFF"
    surface2 = "#F0F0F2"
    border = "#D1D1D6"
    accent = "#FF2D55"
    accent_hover = "#E0294D"
    accent_fg = "#FFFFFF"
    text = "#1D1D1F"
    text_muted = "#6E6E73"
    success = "#28CD41"
    warning = "#FF9500"
    error = "#FF3B30"


_PALETTES: dict[ThemeMode, type[_Palette]] = {
    "dark": _Dark,
    "light": _Light,
}


# ---------------------------------------------------------------------------
# Active palette (updated by apply())
# ---------------------------------------------------------------------------

colors: type[_Palette] = _Dark  # default; replaced on apply()


# ---------------------------------------------------------------------------
# Typography (size in px)
# ---------------------------------------------------------------------------


class Font:
    FAMILY = "Inter"
    SIZE_TITLE = 26
    SIZE_HEADING = 16
    SIZE_BODY = 13
    SIZE_SMALL = 11

    WEIGHT_REGULAR = "normal"
    WEIGHT_SEMIBOLD = "bold"


# ---------------------------------------------------------------------------
# Spacing (8 pt grid)
# ---------------------------------------------------------------------------


class Space:
    XS = 4
    SM = 8
    MD = 16
    LG = 24
    XL = 32
    XXL = 48


# ---------------------------------------------------------------------------
# Radii
# ---------------------------------------------------------------------------


class Radius:
    CARD = 10
    BUTTON = 6
    INPUT = 8
    CHIP = 8
    BADGE = 4
    TOAST = 8
    PILL = 999  # for segmented buttons / language toggles that should stay pill-shaped


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def apply(mode: ThemeMode) -> None:
    """Set CustomTkinter appearance and update the active colour palette."""
    global colors
    ctk.set_appearance_mode(mode)
    colors = _PALETTES[mode]


def ctk_color(dark: str, light: str) -> tuple[str, str]:
    """Helper to create a CTk two-mode colour tuple."""
    return (dark, light)
