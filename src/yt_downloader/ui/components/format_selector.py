"""Format and quality selection controls.

Contains:
- Mode chips: Video+Audio / Audio only / Video only
- Contextual quality/format dropdowns
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

import customtkinter as ctk  # type: ignore[import-untyped]

from yt_downloader.i18n import Translator
from yt_downloader.models import (
    AudioFormat,
    DownloadMode,
    VideoCodec,
    VideoContainer,
)
from yt_downloader.ui import theme

_AUDIO_FORMATS: list[AudioFormat] = ["m4a", "mp3", "opus", "wav", "flac"]
_VIDEO_CONTAINERS: list[VideoContainer] = ["mp4", "webm", "mkv"]
_VIDEO_CODECS: list[VideoCodec] = ["best", "h264", "av1", "vp9"]


class FormatSelector(ctk.CTkFrame):  # type: ignore[misc]
    """Mode chips + contextual quality dropdowns."""

    def __init__(
        self,
        parent: ctk.CTkFrame | ctk.CTk,
        t: Translator,
        on_change: Callable[[], None],
    ) -> None:
        super().__init__(parent, fg_color="transparent")
        self._t = t
        self._on_change = on_change
        self._mode: DownloadMode = "video+audio"
        self._chips: dict[DownloadMode, ctk.CTkButton] = {}
        self._build()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    @property
    def mode(self) -> DownloadMode:
        return self._mode

    @property
    def audio_format(self) -> str:
        return str(self._audio_fmt_var.get())

    @property
    def audio_quality(self) -> str:
        return str(self._audio_q_var.get())

    @property
    def video_resolution(self) -> str:
        v = str(self._video_res_var.get())
        return "best" if v == self._t("ui.best") else v

    @property
    def video_container(self) -> str:
        return str(self._video_cont_var.get())

    @property
    def video_codec(self) -> str:
        return str(self._video_codec_var.get())

    def set_mode(self, mode: DownloadMode) -> None:
        self._select_mode(mode)

    def update_lang(self) -> None:
        modes: list[tuple[DownloadMode, str]] = [
            ("video+audio", self._t("ui.mode.video_audio")),
            ("audio", self._t("ui.mode.audio")),
            ("video", self._t("ui.mode.video")),
        ]
        for mode, label in modes:
            self._chips[mode].configure(text=label)

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        # --- Chip row ---
        chip_row = ctk.CTkFrame(self, fg_color="transparent")
        chip_row.pack(fill="x", pady=(0, theme.Space.SM))

        modes: list[tuple[DownloadMode, str]] = [
            ("video+audio", self._t("ui.mode.video_audio")),
            ("audio", self._t("ui.mode.audio")),
            ("video", self._t("ui.mode.video")),
        ]
        for mode, label in modes:
            btn = ctk.CTkButton(
                chip_row,
                text=label,
                font=ctk.CTkFont(size=13),
                height=34,
                corner_radius=theme.Radius.CHIP,
                command=lambda m=mode: self._select_mode(m),
                fg_color=theme.ctk_color(theme._Dark.surface2, theme._Light.surface2),
                hover_color=theme.ctk_color(theme._Dark.border, theme._Light.border),
                text_color=theme.ctk_color(theme._Dark.text, theme._Light.text),
            )
            btn.pack(side="left", padx=(0, theme.Space.XS))
            self._chips[mode] = btn

        # --- Audio quality row ---
        self._audio_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._audio_q_var = ctk.StringVar(value="best")
        self._audio_fmt_var = ctk.StringVar(value="m4a")

        self._add_dropdown(
            self._audio_frame, self._t("ui.quality"), self._audio_q_var, self._quality_labels()
        )
        self._add_dropdown(
            self._audio_frame, self._t("ui.format"), self._audio_fmt_var, _AUDIO_FORMATS
        )

        # --- Video quality row ---
        self._video_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._video_res_var = ctk.StringVar(value="1080")
        self._video_cont_var = ctk.StringVar(value="mp4")
        self._video_codec_var = ctk.StringVar(value="best")

        self._add_dropdown(
            self._video_frame,
            self._t("ui.resolution"),
            self._video_res_var,
            self._resolution_labels(),
        )
        self._add_dropdown(
            self._video_frame, self._t("ui.container"), self._video_cont_var, _VIDEO_CONTAINERS
        )
        self._add_dropdown(
            self._video_frame, self._t("ui.codec"), self._video_codec_var, _VIDEO_CODECS
        )

        self._select_mode("video+audio")

    def _add_dropdown(
        self,
        parent: ctk.CTkFrame,
        label: str,
        var: ctk.StringVar,
        values: Sequence[str],
    ) -> ctk.CTkOptionMenu:
        col = ctk.CTkFrame(parent, fg_color="transparent")
        col.pack(side="left", padx=(0, theme.Space.SM))
        ctk.CTkLabel(
            col,
            text=label,
            font=ctk.CTkFont(size=11),
            text_color=theme.ctk_color(theme._Dark.text_muted, theme._Light.text_muted),
        ).pack(anchor="w")
        om = ctk.CTkOptionMenu(
            col,
            variable=var,
            values=values,
            font=ctk.CTkFont(size=13),
            width=110,
            height=32,
            corner_radius=theme.Radius.BUTTON,
            fg_color=theme.ctk_color(theme._Dark.surface2, theme._Light.surface2),
            button_color=theme.ctk_color(theme._Dark.border, theme._Light.border),
            button_hover_color=theme.ctk_color(theme._Dark.surface2, theme._Light.border),
            text_color=theme.ctk_color(theme._Dark.text, theme._Light.text),
            command=lambda _: self._on_change(),
        )
        om.pack()
        return om

    def _quality_labels(self) -> list[str]:
        return ["best", "320", "256", "192", "128", "96"]

    def _resolution_labels(self) -> list[str]:
        return ["best", "4320", "2160", "1440", "1080", "720", "480", "360"]

    def _select_mode(self, mode: DownloadMode) -> None:
        self._mode = mode
        accent = theme.colors.accent
        inactive_fg = theme.ctk_color(theme._Dark.surface2, theme._Light.surface2)
        inactive_text = theme.ctk_color(theme._Dark.text, theme._Light.text)

        for m, btn in self._chips.items():
            if m == mode:
                btn.configure(fg_color=accent, text_color="#FFFFFF", hover_color=accent)
            else:
                btn.configure(
                    fg_color=inactive_fg,
                    text_color=inactive_text,
                    hover_color=theme.ctk_color(theme._Dark.border, theme._Light.border),
                )

        # Show/hide contextual rows
        self._audio_frame.pack_forget()
        self._video_frame.pack_forget()

        if mode == "audio":
            self._audio_frame.pack(fill="x", pady=(theme.Space.SM, 0))
        elif mode == "video":
            self._video_frame.pack(fill="x", pady=(theme.Space.SM, 0))
        else:  # video+audio
            self._video_frame.pack(fill="x", pady=(theme.Space.SM, 0))
            self._audio_frame.pack(fill="x", pady=(theme.Space.XS, 0))

        self._on_change()
