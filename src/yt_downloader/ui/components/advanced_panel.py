"""Collapsible advanced options panel."""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk  # type: ignore[import-untyped]

from yt_downloader.i18n import Translator
from yt_downloader.models import SubtitleOptions
from yt_downloader.ui import theme
from yt_downloader.ui.icons import ICON_FOLDER


class AdvancedPanel(ctk.CTkFrame):  # type: ignore[misc]
    """Collapsible panel exposing subtitle, clip, playlist, and output options."""

    def __init__(self, parent: ctk.CTkFrame | ctk.CTk, t: Translator) -> None:
        super().__init__(parent, fg_color="transparent")
        self._t = t
        self._expanded = False
        self._build()

    # ------------------------------------------------------------------
    # Public getters
    # ------------------------------------------------------------------

    @property
    def output_dir(self) -> Path:
        return Path(self._folder_var.get() or str(Path.home() / "Downloads"))

    @property
    def filename_template(self) -> str:
        return self._template_var.get() or "%(title)s.%(ext)s"

    @property
    def subtitles(self) -> SubtitleOptions:
        langs = [lang.strip() for lang in self._sub_lang_var.get().split(",") if lang.strip()]
        return SubtitleOptions(
            enabled=bool(self._sub_var.get()),
            languages=tuple(langs) if langs else ("en",),
            embed=bool(self._sub_embed_var.get()),
            auto_generated=bool(self._sub_auto_var.get()),
        )

    @property
    def embed_thumbnail(self) -> bool:
        return bool(self._thumb_var.get())

    @property
    def embed_metadata(self) -> bool:
        return bool(self._meta_var.get())

    @property
    def clip_start(self) -> str | None:
        v = self._clip_start_var.get().strip()
        return v if v else None

    @property
    def clip_end(self) -> str | None:
        v = self._clip_end_var.get().strip()
        return v if v else None

    @property
    def playlist_start(self) -> int | None:
        try:
            return int(self._pls_start_var.get()) or None
        except ValueError:
            return None

    @property
    def playlist_end(self) -> int | None:
        try:
            return int(self._pls_end_var.get()) or None
        except ValueError:
            return None

    def set_defaults(
        self,
        folder: str,
        template: str,
        embed_thumb: bool,
        embed_meta: bool,
    ) -> None:
        self._folder_var.set(folder)
        self._template_var.set(template)
        self._thumb_var.set(int(embed_thumb))
        self._meta_var.set(int(embed_meta))

    def update_lang(self) -> None:
        self._toggle_btn.configure(text=self._chevron() + " " + self._t("ui.advanced"))

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        # Toggle header
        self._toggle_btn = ctk.CTkButton(
            self,
            text="› " + self._t("ui.advanced"),
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color=theme.ctk_color(theme._Dark.surface2, theme._Light.surface2),
            text_color=theme.ctk_color(theme._Dark.text_muted, theme._Light.text_muted),
            anchor="w",
            command=self._toggle,
        )
        self._toggle_btn.pack(fill="x")

        # Collapsible body
        self._body = ctk.CTkFrame(
            self,
            fg_color=theme.ctk_color(theme._Dark.surface, theme._Light.surface),
            corner_radius=theme.Radius.CARD,
        )

        self._build_body()

    def _build_body(self) -> None:
        pad = theme.Space.MD

        # Output folder
        self._section(self._t("ui.output_folder"))
        folder_row = ctk.CTkFrame(self._body, fg_color="transparent")
        folder_row.pack(fill="x", padx=pad, pady=(0, theme.Space.SM))
        _tc = theme.ctk_color(theme._Dark.text, theme._Light.text)
        _tc_muted = theme.ctk_color(theme._Dark.text_muted, theme._Light.text_muted)
        _entry_kw: dict[str, object] = {
            "text_color": _tc,
            "placeholder_text_color": _tc_muted,
        }

        self._folder_var = ctk.StringVar(value=str(Path.home() / "Downloads"))
        ctk.CTkEntry(
            folder_row,
            textvariable=self._folder_var,
            font=ctk.CTkFont(size=12),
            height=32,
            **_entry_kw,
        ).pack(  # type: ignore[arg-type]
            side="left", fill="x", expand=True
        )
        ctk.CTkButton(
            folder_row,
            text=ICON_FOLDER,
            width=36,
            height=32,
            corner_radius=theme.Radius.BUTTON,
            text_color=_tc,
            command=self._browse_folder,
        ).pack(side="left", padx=(4, 0))

        # Filename template
        self._section(self._t("ui.filename_template"))
        self._template_var = ctk.StringVar(value="%(title)s.%(ext)s")
        ctk.CTkEntry(
            self._body,
            textvariable=self._template_var,
            font=ctk.CTkFont(size=12),
            height=32,
            **_entry_kw,
        ).pack(  # type: ignore[arg-type]
            fill="x", padx=pad, pady=(0, theme.Space.SM)
        )

        # Embed options
        embed_row = ctk.CTkFrame(self._body, fg_color="transparent")
        embed_row.pack(fill="x", padx=pad, pady=(0, theme.Space.SM))
        self._thumb_var = ctk.IntVar(value=1)
        self._meta_var = ctk.IntVar(value=1)
        ctk.CTkCheckBox(
            embed_row,
            text=self._t("ui.embed_thumbnail"),
            variable=self._thumb_var,
            font=ctk.CTkFont(size=12),
            text_color=_tc,
        ).pack(side="left")
        ctk.CTkCheckBox(
            embed_row,
            text=self._t("ui.embed_metadata"),
            variable=self._meta_var,
            font=ctk.CTkFont(size=12),
            text_color=_tc,
        ).pack(side="left", padx=(16, 0))

        # Subtitles
        self._section(self._t("ui.subtitles"))
        self._sub_var = ctk.IntVar(value=0)
        sub_row = ctk.CTkFrame(self._body, fg_color="transparent")
        sub_row.pack(fill="x", padx=pad, pady=(0, 4))
        ctk.CTkSwitch(
            sub_row,
            text=self._t("ui.subtitles"),
            variable=self._sub_var,
            font=ctk.CTkFont(size=12),
            text_color=_tc,
            command=self._toggle_sub_opts,
        ).pack(side="left")

        self._sub_opts = ctk.CTkFrame(self._body, fg_color="transparent")
        self._sub_lang_var = ctk.StringVar(value="en, es")
        self._sub_embed_var = ctk.IntVar(value=0)
        self._sub_auto_var = ctk.IntVar(value=1)
        ctk.CTkLabel(
            self._sub_opts,
            text=self._t("ui.subtitle_languages"),
            font=ctk.CTkFont(size=11),
            text_color=_tc_muted,
        ).pack(anchor="w", padx=pad)
        ctk.CTkEntry(
            self._sub_opts,
            textvariable=self._sub_lang_var,
            font=ctk.CTkFont(size=12),
            height=30,
            **_entry_kw,
        ).pack(  # type: ignore[arg-type]
            fill="x", padx=pad, pady=(2, 4)
        )
        opt_row = ctk.CTkFrame(self._sub_opts, fg_color="transparent")
        opt_row.pack(fill="x", padx=pad, pady=(0, theme.Space.SM))
        ctk.CTkCheckBox(
            opt_row,
            text=self._t("ui.subtitle_embed"),
            variable=self._sub_embed_var,
            font=ctk.CTkFont(size=12),
            text_color=_tc,
        ).pack(side="left")
        ctk.CTkCheckBox(
            opt_row,
            text=self._t("ui.auto_generated"),
            variable=self._sub_auto_var,
            font=ctk.CTkFont(size=12),
            text_color=_tc,
        ).pack(side="left", padx=(16, 0))

        # Clip range
        self._section(self._t("ui.clip_range"))
        clip_row = ctk.CTkFrame(self._body, fg_color="transparent")
        clip_row.pack(fill="x", padx=pad, pady=(0, theme.Space.SM))
        self._clip_start_var = ctk.StringVar()
        self._clip_end_var = ctk.StringVar()
        ctk.CTkLabel(
            clip_row, text=self._t("ui.clip_from"), font=ctk.CTkFont(size=11), text_color=_tc
        ).pack(side="left")
        ctk.CTkEntry(
            clip_row,
            textvariable=self._clip_start_var,
            placeholder_text="0:00",
            width=70,
            height=30,
            font=ctk.CTkFont(size=12),
            **_entry_kw,
        ).pack(  # type: ignore[arg-type]
            side="left", padx=4
        )
        ctk.CTkLabel(
            clip_row, text=self._t("ui.clip_to"), font=ctk.CTkFont(size=11), text_color=_tc
        ).pack(side="left", padx=(8, 0))
        ctk.CTkEntry(
            clip_row,
            textvariable=self._clip_end_var,
            placeholder_text="5:00",
            width=70,
            height=30,
            font=ctk.CTkFont(size=12),
            **_entry_kw,
        ).pack(  # type: ignore[arg-type]
            side="left", padx=4
        )

        # Playlist range
        self._section(self._t("ui.playlist_range"))
        pl_row = ctk.CTkFrame(self._body, fg_color="transparent")
        pl_row.pack(fill="x", padx=pad, pady=(0, pad))
        self._pls_start_var = ctk.StringVar()
        self._pls_end_var = ctk.StringVar()
        ctk.CTkLabel(
            pl_row, text=self._t("ui.playlist_from"), font=ctk.CTkFont(size=11), text_color=_tc
        ).pack(side="left")
        ctk.CTkEntry(
            pl_row,
            textvariable=self._pls_start_var,
            placeholder_text="1",
            width=60,
            height=30,
            font=ctk.CTkFont(size=12),
            **_entry_kw,
        ).pack(  # type: ignore[arg-type]
            side="left", padx=4
        )
        ctk.CTkLabel(
            pl_row, text=self._t("ui.playlist_to"), font=ctk.CTkFont(size=11), text_color=_tc
        ).pack(side="left", padx=(8, 0))
        ctk.CTkEntry(
            pl_row,
            textvariable=self._pls_end_var,
            placeholder_text="10",
            width=60,
            height=30,
            font=ctk.CTkFont(size=12),
            **_entry_kw,
        ).pack(  # type: ignore[arg-type]
            side="left", padx=4
        )

        self._toggle_sub_opts()

    def _section(self, label: str) -> ctk.CTkLabel:
        lbl = ctk.CTkLabel(
            self._body,
            text=label,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=theme.ctk_color(theme._Dark.text_muted, theme._Light.text_muted),
            anchor="w",
        )
        lbl.pack(fill="x", padx=theme.Space.MD, pady=(theme.Space.SM, 2))
        return lbl

    def _toggle(self) -> None:
        self._expanded = not self._expanded
        if self._expanded:
            self._body.pack(fill="x", pady=(theme.Space.XS, 0))
        else:
            self._body.pack_forget()
        self._toggle_btn.configure(text=self._chevron() + " " + self._t("ui.advanced"))

    def _chevron(self) -> str:
        return "▾" if self._expanded else "›"

    def _browse_folder(self) -> None:
        from tkinter import filedialog

        path = filedialog.askdirectory(initialdir=self._folder_var.get() or str(Path.home()))
        if path:
            self._folder_var.set(path)

    def _toggle_sub_opts(self) -> None:
        if self._sub_var.get():
            self._sub_opts.pack(fill="x")
        else:
            self._sub_opts.pack_forget()
