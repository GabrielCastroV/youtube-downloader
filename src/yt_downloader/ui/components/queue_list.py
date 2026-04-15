"""Queue panel — list of pending/active/done downloads with live progress."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk  # type: ignore[import-untyped]

from yt_downloader.i18n import Translator
from yt_downloader.queue import ItemStatus, QueueItem
from yt_downloader.ui import theme
from yt_downloader.ui.icons import ICON_CANCEL

_STATUS_COLORS: dict[ItemStatus, str] = {
    "queued": "#86868B",
    "active": "#FF9F0A",
    "done": "#30D158",
    "error": "#FF453A",
    "cancelled": "#86868B",
}

_TERMINAL_STATUSES: frozenset[ItemStatus] = frozenset({"done", "error", "cancelled"})


class QueuePanel(ctk.CTkScrollableFrame):  # type: ignore[misc]
    """Scrollable list of queue items with live progress for active downloads."""

    def __init__(
        self,
        parent: ctk.CTkFrame | ctk.CTk,
        t: Translator,
        on_cancel: Callable[[str], None],
    ) -> None:
        super().__init__(
            parent,
            label_text="",
            fg_color=theme.ctk_color(theme._Dark.surface, theme._Light.surface),
            corner_radius=theme.Radius.CARD,
        )
        self._t = t
        self._on_cancel = on_cancel
        self._rows: dict[str, _QueueRow] = {}
        self._items: list[QueueItem] = []
        self._polling = False
        self._build_empty()

    def refresh(self, items: list[QueueItem]) -> None:
        self._items = items
        self._empty_label.pack_forget()

        # Remove rows no longer in items
        active_ids = {it.id for it in items}
        for item_id in list(self._rows):
            if item_id not in active_ids:
                self._rows[item_id].destroy()
                del self._rows[item_id]

        for item in items:
            if item.id in self._rows:
                self._rows[item.id].update_status(item.status)
            else:
                row = _QueueRow(self, item, self._t, self._on_cancel)
                row.pack(fill="x", pady=(0, theme.Space.XS))
                self._rows[item.id] = row

        if not items:
            self._empty_label.pack(pady=theme.Space.LG)

        # Start polling if any active items
        if not self._polling and any(it.status == "active" for it in items):
            self._polling = True
            self._poll_active()

    def update_lang(self) -> None:
        pass

    def _build_empty(self) -> None:
        self._empty_label = ctk.CTkLabel(
            self,
            text=self._t("ui.queue_empty"),
            font=ctk.CTkFont(size=13),
            text_color=theme.ctk_color(theme._Dark.text_muted, theme._Light.text_muted),
        )
        self._empty_label.pack(pady=theme.Space.LG)

    def _poll_active(self) -> None:
        """Drain each active item's event queue and update its row."""
        has_active = False
        for item in self._items:
            if item.status != "active":
                continue
            has_active = True
            row = self._rows.get(item.id)
            if row is None:
                continue
            try:
                while True:
                    ev = item.event_queue.get_nowait()
                    if ev.percent is not None:
                        row.update_progress(ev.percent, ev.speed_bps)
            except Exception:
                pass

        if has_active:
            self.after(200, self._poll_active)
        else:
            self._polling = False


class _QueueRow(ctk.CTkFrame):  # type: ignore[misc]
    def __init__(
        self,
        parent: ctk.CTkScrollableFrame,
        item: QueueItem,
        t: Translator,
        on_cancel: Callable[[str], None],
    ) -> None:
        super().__init__(
            parent,
            fg_color=theme.ctk_color(theme._Dark.surface2, theme._Light.surface2),
            corner_radius=8,
        )
        self._item = item
        self._t = t
        self._on_cancel = on_cancel
        self._build()

    def _build(self) -> None:
        # Top row: URL + status badge + cancel button
        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.pack(fill="x")

        url_short = self._item.options.url[:50] + ("…" if len(self._item.options.url) > 50 else "")
        ctk.CTkLabel(
            top_row,
            text=url_short,
            font=ctk.CTkFont(size=11),
            text_color=theme.ctk_color(theme._Dark.text, theme._Light.text),
            anchor="w",
        ).pack(side="left", padx=theme.Space.SM, pady=6, fill="x", expand=True)

        self._pct_var = ctk.StringVar(value="")
        self._pct_label = ctk.CTkLabel(
            top_row,
            textvariable=self._pct_var,
            font=ctk.CTkFont(size=10),
            text_color=theme.ctk_color(theme._Dark.text_muted, theme._Light.text_muted),
            width=40,
        )
        self._pct_label.pack(side="right", padx=(0, theme.Space.XS))

        self._status_badge = ctk.CTkLabel(
            top_row,
            text=self._t(f"ui.status.{self._item.status}"),
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=_STATUS_COLORS.get(self._item.status, "#86868B"),
            width=70,
        )
        self._status_badge.pack(side="right", padx=theme.Space.SM)

        if self._item.status in ("queued", "active"):
            ctk.CTkButton(
                top_row,
                text=ICON_CANCEL,
                width=28,
                height=24,
                font=ctk.CTkFont(size=12),
                corner_radius=theme.Radius.BUTTON,
                fg_color="transparent",
                hover_color=theme.ctk_color(theme._Dark.border, theme._Light.border),
                text_color=theme.ctk_color(theme._Dark.text_muted, theme._Light.text_muted),
                command=lambda: self._on_cancel(self._item.id),
            ).pack(side="right")

        # Progress bar (hidden unless active)
        self._progress_bar = ctk.CTkProgressBar(
            self,
            mode="determinate",
            height=3,
            corner_radius=2,
            progress_color=theme.colors.accent,
            fg_color=theme.ctk_color(theme._Dark.border, theme._Light.border),
        )
        self._progress_bar.set(0)
        if self._item.status == "active":
            self._progress_bar.pack(fill="x", padx=theme.Space.SM, pady=(0, theme.Space.XS))

    def update_progress(self, pct: float, speed_bps: float | None) -> None:
        self._progress_bar.set(pct / 100)
        self._pct_var.set(f"{pct:.0f}%")
        if not self._progress_bar.winfo_ismapped():
            self._progress_bar.pack(fill="x", padx=theme.Space.SM, pady=(0, theme.Space.XS))

    def update_status(self, status: ItemStatus) -> None:
        self._status_badge.configure(
            text=self._t(f"ui.status.{status}"),
            text_color=_STATUS_COLORS.get(status, "#86868B"),
        )
        if status in _TERMINAL_STATUSES:
            self._progress_bar.pack_forget()
            if status == "done":
                self._progress_bar.set(1.0)
                self._pct_var.set("100%")
