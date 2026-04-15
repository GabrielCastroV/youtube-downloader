"""History drawer panel."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import customtkinter as ctk  # type: ignore[import-untyped]

from yt_downloader import history
from yt_downloader.i18n import Translator
from yt_downloader.models import HistoryEntry
from yt_downloader.ui import theme
from yt_downloader.ui.icons import ICON_OPEN, ICON_TRASH


class HistoryPanel(ctk.CTkScrollableFrame):  # type: ignore[misc]
    """Scrollable download history."""

    def __init__(
        self,
        parent: ctk.CTkFrame | ctk.CTk,
        t: Translator,
        on_redownload: Callable[[str], None],
        on_cleared: Callable[[], None],
    ) -> None:
        super().__init__(
            parent,
            label_text="",
            fg_color=theme.ctk_color(theme._Dark.surface, theme._Light.surface),
            corner_radius=theme.Radius.CARD,
        )
        self._t = t
        self._on_redownload = on_redownload
        self._on_cleared = on_cleared
        self._build()

    def refresh(self) -> None:
        for w in self.winfo_children():
            w.destroy()
        entries = history.all_entries()
        if not entries:
            ctk.CTkLabel(
                self,
                text=self._t("ui.history_empty"),
                font=ctk.CTkFont(size=13),
                text_color=theme.ctk_color(theme._Dark.text_muted, theme._Light.text_muted),
            ).pack(pady=theme.Space.LG)
            return

        # Clear all button
        ctk.CTkButton(
            self,
            text=ICON_TRASH + " " + self._t("ui.clear_history"),
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color=theme.ctk_color(theme._Dark.surface2, theme._Light.surface2),
            text_color=theme.ctk_color(theme._Dark.error, theme._Light.error),
            command=self._clear_all,
        ).pack(anchor="e", padx=theme.Space.SM, pady=(theme.Space.SM, 0))

        for entry in entries:
            _HistoryRow(self, entry, self._t, self._on_redownload, self._delete).pack(
                fill="x", pady=(0, theme.Space.XS)
            )

    def update_lang(self) -> None:
        self.refresh()

    def _build(self) -> None:
        self.refresh()

    def _clear_all(self) -> None:
        history.clear()
        self._on_cleared()
        self.refresh()

    def _delete(self, entry_id: int) -> None:
        history.delete(entry_id)
        self.refresh()


class _HistoryRow(ctk.CTkFrame):  # type: ignore[misc]
    def __init__(
        self,
        parent: ctk.CTkScrollableFrame,
        entry: HistoryEntry,
        t: Translator,
        on_redownload: Callable[[str], None],
        on_delete: Callable[[int], None],
    ) -> None:
        super().__init__(
            parent,
            fg_color=theme.ctk_color(theme._Dark.surface2, theme._Light.surface2),
            corner_radius=8,
        )
        self._entry = entry
        self._t = t
        self._on_redownload = on_redownload
        self._on_delete = on_delete
        self._build()

    def _build(self) -> None:
        title_short = (self._entry.title or self._entry.url)[:48]
        ctk.CTkLabel(
            self,
            text=title_short,
            font=ctk.CTkFont(size=11),
            text_color=theme.ctk_color(theme._Dark.text, theme._Light.text),
            anchor="w",
        ).pack(side="left", padx=theme.Space.SM, pady=6, fill="x", expand=True)

        # Open file
        ctk.CTkButton(
            self,
            text=ICON_OPEN,
            width=28,
            height=24,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color=theme.ctk_color(theme._Dark.border, theme._Light.border),
            text_color=theme.ctk_color(theme._Dark.text_muted, theme._Light.text_muted),
            command=self._open_file,
        ).pack(side="right", padx=(0, 2))

        # Re-download
        ctk.CTkButton(
            self,
            text="↺",
            width=28,
            height=24,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color=theme.ctk_color(theme._Dark.border, theme._Light.border),
            text_color=theme.ctk_color(theme._Dark.text_muted, theme._Light.text_muted),
            command=lambda: self._on_redownload(self._entry.url),
        ).pack(side="right", padx=(0, 2))

        # Delete
        ctk.CTkButton(
            self,
            text=ICON_TRASH,
            width=28,
            height=24,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color=theme.ctk_color(theme._Dark.border, theme._Light.border),
            text_color=theme.ctk_color(theme._Dark.text_muted, theme._Light.text_muted),
            command=lambda: self._on_delete(self._entry.id),
        ).pack(side="right", padx=(0, 4))

    def _open_file(self) -> None:
        p = Path(self._entry.filepath)
        if p.exists():
            if sys.platform == "win32":
                import os

                os.startfile(p)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.run(["open", str(p)], check=False)
            else:
                subprocess.run(["xdg-open", str(p)], check=False)
        else:
            # Open containing folder
            folder = p.parent if p.parent.exists() else Path.home()
            if sys.platform == "win32":
                import os

                os.startfile(folder)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.run(["open", str(folder)], check=False)
            else:
                subprocess.run(["xdg-open", str(folder)], check=False)
