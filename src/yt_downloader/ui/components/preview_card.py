"""Video preview card shown after a URL is validated."""

from __future__ import annotations

import threading

import customtkinter as ctk  # type: ignore[import-untyped]

from yt_downloader.i18n import Translator
from yt_downloader.models import VideoInfo
from yt_downloader.ui import theme
from yt_downloader.ui.icons import load_thumbnail


class PreviewCard(ctk.CTkFrame):  # type: ignore[misc]
    """Displays thumbnail, title, channel, and duration for a video."""

    def __init__(self, parent: ctk.CTkFrame | ctk.CTk, t: Translator) -> None:
        super().__init__(
            parent,
            fg_color=theme.ctk_color(theme._Dark.surface, theme._Light.surface),
            corner_radius=theme.Radius.CARD,
        )
        self._t = t
        self._thumb_label: ctk.CTkLabel | None = None
        self._build()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def show(self, info: VideoInfo) -> None:
        self._title_var.set(info.title or "")
        self._channel_var.set(info.channel or "")
        self._duration_var.set(info.duration_str)

        # Badges
        for w in self._badge_row.winfo_children():
            w.destroy()
        if info.is_short:
            self._make_badge(self._t("ui.short_badge"), theme.colors.accent)
        if info.is_playlist:
            self._make_badge(self._t("ui.playlist_badge"), theme.colors.warning)
            if info.playlist_count:
                self._make_badge(
                    self._t("ui.video_count", n=str(info.playlist_count)),
                    theme.ctk_color(theme._Dark.surface2, theme._Light.surface2),
                )

        # Load thumbnail in background
        if info.thumbnail_url:
            threading.Thread(
                target=self._load_thumb,
                args=(info.thumbnail_url,),
                daemon=True,
            ).start()
        else:
            self._clear_thumb()

        self.pack(fill="x", pady=(0, theme.Space.MD))

    def hide(self) -> None:
        self.pack_forget()
        self._clear_thumb()

    def update_lang(self) -> None:
        pass  # dynamic labels only

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        self.columnconfigure(1, weight=1)

        # Thumbnail placeholder
        self._thumb_label = ctk.CTkLabel(
            self,
            text="",
            width=160,
            height=90,
            fg_color=theme.ctk_color(theme._Dark.surface2, theme._Light.surface2),
            corner_radius=8,
        )
        self._thumb_label.grid(
            row=0, column=0, rowspan=4, padx=theme.Space.MD, pady=theme.Space.MD, sticky="nw"
        )

        self._title_var = ctk.StringVar()
        ctk.CTkLabel(
            self,
            textvariable=self._title_var,
            font=ctk.CTkFont(family=theme.Font.FAMILY, size=13, weight="bold"),
            text_color=theme.ctk_color(theme._Dark.text, theme._Light.text),
            anchor="w",
            wraplength=280,
        ).grid(row=0, column=1, sticky="ew", padx=(0, theme.Space.MD), pady=(theme.Space.MD, 2))

        self._channel_var = ctk.StringVar()
        ctk.CTkLabel(
            self,
            textvariable=self._channel_var,
            font=ctk.CTkFont(family=theme.Font.FAMILY, size=12),
            text_color=theme.ctk_color(theme._Dark.text_muted, theme._Light.text_muted),
            anchor="w",
        ).grid(row=1, column=1, sticky="ew", padx=(0, theme.Space.MD))

        self._duration_var = ctk.StringVar()
        ctk.CTkLabel(
            self,
            textvariable=self._duration_var,
            font=ctk.CTkFont(family=theme.Font.FAMILY, size=11),
            text_color=theme.ctk_color(theme._Dark.text_muted, theme._Light.text_muted),
            anchor="w",
        ).grid(row=2, column=1, sticky="ew", padx=(0, theme.Space.MD))

        self._badge_row = ctk.CTkFrame(self, fg_color="transparent")
        self._badge_row.grid(
            row=3, column=1, sticky="w", padx=(0, theme.Space.MD), pady=(4, theme.Space.MD)
        )

    def _make_badge(self, text: str, color: str | tuple[str, str]) -> ctk.CTkLabel:
        lbl = ctk.CTkLabel(
            self._badge_row,
            text=text,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=color,
            text_color="#FFFFFF",
            corner_radius=theme.Radius.BADGE,
            padx=8,
            pady=2,
        )
        lbl.pack(side="left", padx=(0, 4))
        return lbl

    def _load_thumb(self, url: str) -> None:
        photo = load_thumbnail(url, 160, 90)
        if photo and self._thumb_label and self._thumb_label.winfo_exists():
            self._thumb_label.after(0, lambda: self._set_thumb(photo))

    def _set_thumb(self, photo: object) -> None:
        if self._thumb_label and self._thumb_label.winfo_exists():
            self._thumb_label.configure(image=photo, text="")
            self._thumb_label.image = photo  # type: ignore[attr-defined]  # keep ref

    def _clear_thumb(self) -> None:
        if self._thumb_label and self._thumb_label.winfo_exists():
            self._thumb_label.configure(image="", text="")
