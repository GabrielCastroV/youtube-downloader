"""Toast notification system.

Toasts appear in the bottom-right of the window, auto-dismiss after 4 s,
and queue if multiple arrive simultaneously.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

import customtkinter as ctk  # type: ignore[import-untyped]

from yt_downloader.ui import theme

ToastKind = Literal["success", "error", "info", "warning"]

_DURATION_MS = 4000
_SLIDE_MS = 20
_SLIDE_STEP = 2


class _Toast(ctk.CTkFrame):  # type: ignore[misc]
    def __init__(
        self,
        parent: ctk.CTk | ctk.CTkFrame,
        message: str,
        kind: ToastKind,
        on_done: Callable[[], None],
    ) -> None:

        bg = {
            "success": theme.colors.success,
            "error": theme.colors.error,
            "info": theme.colors.accent,
            "warning": theme.colors.warning,
        }[kind]

        super().__init__(
            parent,
            fg_color=bg,
            corner_radius=theme.Radius.TOAST,
        )
        self._on_done = on_done

        icon_map = {"success": "✓", "error": "✕", "info": "ℹ", "warning": "⚠"}
        ctk.CTkLabel(
            self,
            text=icon_map[kind],
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#FFFFFF",
            width=24,
        ).pack(side="left", padx=(12, 4), pady=10)

        ctk.CTkLabel(
            self,
            text=message,
            font=ctk.CTkFont(size=13),
            text_color="#FFFFFF",
            wraplength=260,
        ).pack(side="left", padx=(0, 12), pady=10)

        self.after(_DURATION_MS, self._dismiss)

    def _dismiss(self) -> None:
        self.destroy()
        self._on_done()


class ToastManager:
    """Manages a queue of toast notifications anchored to a parent widget."""

    def __init__(self, parent: ctk.CTk) -> None:
        self._parent = parent
        self._active: list[_Toast] = []

    def show(self, message: str, kind: ToastKind = "info") -> None:
        toast = _Toast(self._parent, message, kind, on_done=lambda: self._remove())
        self._place(toast)
        self._active.append(toast)

    def success(self, message: str) -> None:
        self.show(message, "success")

    def error(self, message: str) -> None:
        self.show(message, "error")

    def warning(self, message: str) -> None:
        self.show(message, "warning")

    def info(self, message: str) -> None:
        self.show(message, "info")

    def _place(self, toast: _Toast) -> None:
        toast.place(relx=1.0, rely=1.0, anchor="se", x=-16, y=-(16 + 56 * len(self._active)))

    def _remove(self) -> None:
        self._active = [t for t in self._active if t.winfo_exists()]
        # Re-stack remaining
        for i, t in enumerate(self._active):
            t.place(relx=1.0, rely=1.0, anchor="se", x=-16, y=-(16 + 56 * i))
