"""URL input component with paste button, live validation, and auto-paste prompt."""

from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk  # type: ignore[import-untyped]

from yt_downloader.i18n import Translator
from yt_downloader.metadata import is_youtube_url
from yt_downloader.ui import theme
from yt_downloader.ui.icons import ICON_PASTE
from yt_downloader.ui.theme import _Dark, _Light

_DEBOUNCE_MS = 350


class URLInput(ctk.CTkFrame):  # type: ignore[misc]
    """Large URL input with paste button and debounced validation callback."""

    def __init__(
        self,
        parent: ctk.CTkFrame | ctk.CTk,
        t: Translator,
        on_url_change: Callable[[str], None],
    ) -> None:
        super().__init__(parent, fg_color="transparent")
        self._t = t
        self._on_url_change = on_url_change
        self._debounce_id: str | None = None
        self._autopaste_shown = False
        self._build()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def set_url(self, url: str) -> None:
        self._var.set(url)
        self._on_change()

    def get_url(self) -> str:
        return str(self._var.get()).strip()

    def check_clipboard(self) -> None:
        """Check clipboard for a YouTube URL and offer to paste it."""
        if self._autopaste_shown:
            return
        try:
            clip = self.clipboard_get()
        except Exception:
            return
        if is_youtube_url(clip) and not self.get_url():
            self._show_autopaste_prompt(clip)

    def update_lang(self) -> None:
        self._entry.configure(placeholder_text=self._t("ui.url_placeholder"))
        self._paste_btn.configure(text=self._t("ui.paste"))

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        # Outer row: entry + paste button
        row = ctk.CTkFrame(
            self,
            fg_color=theme.ctk_color(theme._Dark.surface, theme._Light.surface),
            corner_radius=theme.Radius.INPUT,
        )

        self._var = ctk.StringVar()
        self._var.trace_add("write", lambda *_: self._schedule_debounce())

        self._entry = ctk.CTkEntry(
            row,
            textvariable=self._var,
            placeholder_text=self._t("ui.url_placeholder"),
            font=ctk.CTkFont(family=theme.Font.FAMILY, size=theme.Font.SIZE_BODY),
            border_width=0,
            fg_color="transparent",
            text_color=theme.ctk_color(theme._Dark.text, theme._Light.text),
            placeholder_text_color=theme.ctk_color(theme._Dark.text_muted, theme._Light.text_muted),
            height=48,
        )
        self._entry.pack(side="left", fill="x", expand=True, padx=(theme.Space.MD, 0))

        self._paste_btn = ctk.CTkButton(
            row,
            text=ICON_PASTE + " " + self._t("ui.paste"),
            font=ctk.CTkFont(size=12),
            width=80,
            height=34,
            corner_radius=theme.Radius.BUTTON,
            fg_color=theme.ctk_color(_Dark.surface2, _Light.surface2),
            hover_color=theme.ctk_color(_Dark.border, _Light.border),
            text_color=theme.ctk_color(_Dark.text, _Light.text),
            command=self._paste,
        )
        self._paste_btn.pack(side="right", padx=theme.Space.SM, pady=theme.Space.SM)

        row.pack(fill="x")

        # Auto-paste banner (hidden initially)
        self._autopaste_frame = ctk.CTkFrame(
            self,
            fg_color=theme.ctk_color(_Dark.surface2, _Light.surface2),
            corner_radius=theme.Radius.BUTTON,
        )

    def _paste(self) -> None:
        try:
            clip = self.clipboard_get()
            self._var.set(clip.strip())
        except Exception:
            pass

    def _schedule_debounce(self) -> None:
        if self._debounce_id:
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(_DEBOUNCE_MS, self._on_change)

    def _on_change(self) -> None:
        url = self.get_url()
        self._update_border(url)
        self._on_url_change(url)

    def _update_border(self, url: str) -> None:
        # CustomTkinter entry doesn't expose border_color easily; visual feedback skipped
        _ = is_youtube_url(url)  # reserved for future accent-border implementation

    def _show_autopaste_prompt(self, url: str) -> None:
        self._autopaste_shown = True
        frame = self._autopaste_frame

        # Clear previous children
        for w in frame.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            frame,
            text=self._t("ui.autopaste_prompt"),
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=(theme.Space.MD, theme.Space.SM), pady=8)

        ctk.CTkButton(
            frame,
            text=self._t("ui.autopaste_yes"),
            width=80,
            height=28,
            font=ctk.CTkFont(size=12),
            fg_color=theme.colors.accent,
            hover_color=theme.colors.accent_hover,
            corner_radius=theme.Radius.BUTTON,
            command=lambda: (self.set_url(url), frame.pack_forget()),  # type: ignore[func-returns-value]
        ).pack(side="left", padx=4, pady=8)

        ctk.CTkButton(
            frame,
            text=self._t("ui.autopaste_no"),
            width=60,
            height=28,
            font=ctk.CTkFont(size=12),
            fg_color=theme.ctk_color(_Dark.border, _Light.border),
            hover_color=theme.ctk_color(_Dark.surface2, _Light.surface2),
            text_color=theme.ctk_color(_Dark.text, _Light.text),
            corner_radius=theme.Radius.BUTTON,
            command=frame.pack_forget,
        ).pack(side="left", padx=4, pady=8)

        frame.pack(fill="x", pady=(theme.Space.XS, 0))
