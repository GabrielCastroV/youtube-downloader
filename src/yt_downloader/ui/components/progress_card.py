"""Download progress card with progress bar, stats, and cancel button."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk  # type: ignore[import-untyped]

from yt_downloader.i18n import Translator
from yt_downloader.models import ProgressEvent
from yt_downloader.ui import theme
from yt_downloader.ui.icons import ICON_CANCEL, ICON_FOLDER


def _fmt_size(b: int | None) -> str:
    if b is None:
        return "?"
    if b >= 1_000_000_000:
        return f"{b / 1_000_000_000:.1f} GB"
    if b >= 1_000_000:
        return f"{b / 1_000_000:.1f} MB"
    if b >= 1_000:
        return f"{b / 1_000:.0f} KB"
    return f"{b} B"


def _fmt_speed(bps: float | None) -> str:
    if bps is None:
        return "-- B/s"
    return _fmt_size(int(bps)) + "/s"


def _fmt_eta(s: int | None) -> str:
    if s is None:
        return ""
    if s >= 3600:
        return f"ETA {s // 3600}h {(s % 3600) // 60}m"
    if s >= 60:
        return f"ETA {s // 60}m {s % 60}s"
    return f"ETA {s}s"


class ProgressCard(ctk.CTkFrame):  # type: ignore[misc]
    """Shows download progress. Shown while downloading, hidden otherwise."""

    def __init__(
        self,
        parent: ctk.CTkFrame | ctk.CTk,
        t: Translator,
        on_cancel: Callable[[], None],
        on_open_folder: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(
            parent,
            fg_color=theme.ctk_color(theme._Dark.surface, theme._Light.surface),
            corner_radius=theme.Radius.CARD,
        )
        self._t = t
        self._on_cancel = on_cancel
        self._on_open_folder = on_open_folder
        self._last_filename: str = ""
        self._build()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def show(self) -> None:
        # Pack into parent (root window) right after the header, before content area
        self.pack(fill="x", side="top", pady=0)

    def hide(self) -> None:
        self.pack_forget()
        self._reset()

    def update_event(self, ev: ProgressEvent) -> None:
        stage = ev.stage

        if stage == "downloading":
            pct = ev.percent
            if pct is not None:
                self._bar.set(pct / 100)
                self._bar.configure(mode="determinate")
                self._pct_var.set(f"{pct:.1f}%")
            else:
                self._bar.configure(mode="indeterminate")
                self._pct_var.set("…")

            parts = [
                f"{_fmt_size(ev.bytes_done)}/{_fmt_size(ev.bytes_total)}",
                _fmt_speed(ev.speed_bps),
                _fmt_eta(ev.eta_s),
            ]
            self._stats_var.set("  ·  ".join(p for p in parts if p != ""))
            self._status_var.set(self._t("ui.downloading"))
            self._status_label.configure(
                text_color=theme.ctk_color(theme._Dark.text, theme._Light.text)
            )
            self._show_cancel_state()

        elif stage in ("processing", "merging"):
            self._bar.configure(mode="indeterminate")
            self._bar.start()
            self._status_var.set(
                self._t("ui.merging") if stage == "merging" else self._t("ui.processing")
            )
            self._status_label.configure(
                text_color=theme.ctk_color(theme._Dark.text, theme._Light.text)
            )
            self._pct_var.set("")
            self._stats_var.set("")
            self._show_cancel_state()

        elif stage == "done":
            self._bar.stop()
            self._bar.configure(
                mode="determinate",
                progress_color=theme.ctk_color(theme._Dark.success, theme._Light.success),
            )
            self._bar.set(1.0)
            self._status_var.set(self._t("ui.done"))
            self._status_label.configure(
                text_color=theme.ctk_color(theme._Dark.success, theme._Light.success)
            )
            self._pct_var.set("100%")
            self._last_filename = ev.filename
            self._stats_var.set(ev.filename)
            self._show_done_state()

    def update_lang(self) -> None:
        self._cancel_btn.configure(text=ICON_CANCEL + " " + self._t("ui.cancel"))
        self._folder_btn.configure(text=ICON_FOLDER + " " + self._t("ui.open_folder"))

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        pad = theme.Space.MD

        # Status row
        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.pack(fill="x", padx=pad, pady=(pad, theme.Space.XS))

        self._status_var = ctk.StringVar(value=self._t("ui.preparing"))
        self._status_label = ctk.CTkLabel(
            top_row,
            textvariable=self._status_var,
            font=ctk.CTkFont(family=theme.Font.FAMILY, size=13, weight="bold"),
            anchor="w",
        )
        self._status_label.pack(side="left", fill="x", expand=True)

        self._pct_var = ctk.StringVar()
        ctk.CTkLabel(
            top_row,
            textvariable=self._pct_var,
            font=ctk.CTkFont(family=theme.Font.FAMILY, size=13),
            text_color=theme.ctk_color(theme._Dark.text_muted, theme._Light.text_muted),
        ).pack(side="right")

        # Progress bar
        self._bar = ctk.CTkProgressBar(
            self,
            mode="determinate",
            height=10,
            corner_radius=5,
            progress_color=theme.colors.accent,
            fg_color=theme.ctk_color(theme._Dark.surface2, theme._Light.surface2),
        )
        self._bar.set(0)
        self._bar.pack(fill="x", padx=pad, pady=theme.Space.XS)

        # Stats / action row
        bottom_row = ctk.CTkFrame(self, fg_color="transparent")
        bottom_row.pack(fill="x", padx=pad, pady=(theme.Space.XS, pad))

        self._stats_var = ctk.StringVar()
        ctk.CTkLabel(
            bottom_row,
            textvariable=self._stats_var,
            font=ctk.CTkFont(size=11),
            text_color=theme.ctk_color(theme._Dark.text_muted, theme._Light.text_muted),
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        # Cancel button (shown while downloading)
        self._cancel_btn = ctk.CTkButton(
            bottom_row,
            text=ICON_CANCEL + " " + self._t("ui.cancel"),
            width=90,
            height=28,
            font=ctk.CTkFont(size=12),
            corner_radius=theme.Radius.BUTTON,
            fg_color=theme.ctk_color(theme._Dark.surface2, theme._Light.surface2),
            hover_color=theme.ctk_color(theme._Dark.error, theme._Dark.error),
            text_color=theme.ctk_color(theme._Dark.text, theme._Light.text),
            command=self._on_cancel,
        )
        self._cancel_btn.pack(side="right")

        # Open folder button (shown when done, hidden initially)
        self._folder_btn = ctk.CTkButton(
            bottom_row,
            text=ICON_FOLDER + " " + self._t("ui.open_folder"),
            width=120,
            height=28,
            font=ctk.CTkFont(size=12),
            corner_radius=theme.Radius.BUTTON,
            fg_color=theme.ctk_color(theme._Dark.success, theme._Light.success),
            hover_color=theme.ctk_color("#28B84A", "#20A040"),
            text_color="#FFFFFF",
            command=self._open_folder,
        )

    def _show_cancel_state(self) -> None:
        self._folder_btn.pack_forget()
        if not self._cancel_btn.winfo_ismapped():
            self._cancel_btn.pack(side="right")

    def _show_done_state(self) -> None:
        self._cancel_btn.pack_forget()
        if not self._folder_btn.winfo_ismapped():
            self._folder_btn.pack(side="right")

    def _open_folder(self) -> None:
        if self._on_open_folder:
            self._on_open_folder(self._last_filename)

    def _reset(self) -> None:
        self._bar.stop()
        self._bar.set(0)
        self._bar.configure(progress_color=theme.colors.accent)
        self._status_var.set(self._t("ui.preparing"))
        self._status_label.configure(
            text_color=theme.ctk_color(theme._Dark.text, theme._Light.text)
        )
        self._pct_var.set("")
        self._stats_var.set("")
        self._last_filename = ""
        self._folder_btn.pack_forget()
        if not self._cancel_btn.winfo_ismapped():
            self._cancel_btn.pack(side="right")
