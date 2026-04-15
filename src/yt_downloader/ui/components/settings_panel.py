"""Settings panel — theme, language, default folder, FFmpeg."""

from __future__ import annotations

import subprocess
import sys
import threading
import webbrowser
from collections.abc import Callable
from pathlib import Path

import customtkinter as ctk  # type: ignore[import-untyped]

from yt_downloader import ffmpeg_manager
from yt_downloader.config import Config, save
from yt_downloader.i18n import Language, Translator
from yt_downloader.paths import log_dir
from yt_downloader.ui import theme
from yt_downloader.ui.icons import ICON_FOLDER


class SettingsPanel(ctk.CTkFrame):  # type: ignore[misc]
    """Full settings UI embedded in a frame."""

    def __init__(
        self,
        parent: ctk.CTkFrame | ctk.CTk,
        t: Translator,
        cfg: Config,
        on_theme_change: Callable[[str], None],
        on_lang_change: Callable[[Language], None],
        on_ffmpeg_installed: Callable[[str], None],
    ) -> None:
        super().__init__(
            parent,
            fg_color=theme.ctk_color(theme._Dark.surface, theme._Light.surface),
            corner_radius=theme.Radius.CARD,
        )
        self._t = t
        self._cfg = cfg
        self._on_theme = on_theme_change
        self._on_lang = on_lang_change
        self._on_ffmpeg = on_ffmpeg_installed
        self._ffmpeg_path = ffmpeg_manager.detect(cfg.ffmpeg_path)
        self._build()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def update_lang(self) -> None:
        self._rebuild()

    def refresh_ffmpeg(self) -> None:
        self._ffmpeg_path = ffmpeg_manager.detect(self._cfg.ffmpeg_path)
        self._update_ffmpeg_ui()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        self._rebuild()

    def _rebuild(self) -> None:
        for w in self.winfo_children():
            w.destroy()

        pad = theme.Space.MD

        # --- Theme ---
        self._section(self._t("ui.theme"))
        theme_row = ctk.CTkFrame(self, fg_color="transparent")
        theme_row.pack(fill="x", padx=pad, pady=(0, theme.Space.SM))
        self._theme_var = ctk.StringVar(value=self._cfg.theme)
        ctk.CTkSegmentedButton(
            theme_row,
            values=[self._t("ui.theme.dark"), self._t("ui.theme.light")],
            variable=self._theme_var,
            font=ctk.CTkFont(size=12),
            command=self._apply_theme,
        ).pack(side="left")

        # --- Language ---
        self._section(self._t("ui.language"))
        lang_row = ctk.CTkFrame(self, fg_color="transparent")
        lang_row.pack(fill="x", padx=pad, pady=(0, theme.Space.SM))
        self._lang_var = ctk.StringVar(value=self._cfg.language)
        ctk.CTkSegmentedButton(
            lang_row,
            values=["ES", "EN"],
            variable=self._lang_var,
            font=ctk.CTkFont(size=12),
            command=self._apply_lang,
        ).pack(side="left")

        # --- Default folder ---
        self._section(self._t("ui.default_folder"))
        folder_row = ctk.CTkFrame(self, fg_color="transparent")
        folder_row.pack(fill="x", padx=pad, pady=(0, theme.Space.SM))
        self._folder_var = ctk.StringVar(value=self._cfg.default_output_dir)
        ctk.CTkEntry(
            folder_row,
            textvariable=self._folder_var,
            font=ctk.CTkFont(size=12),
            height=30,
            text_color=theme.ctk_color(theme._Dark.text, theme._Light.text),
            placeholder_text_color=theme.ctk_color(theme._Dark.text_muted, theme._Light.text_muted),
        ).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            folder_row,
            text=ICON_FOLDER,
            width=32,
            height=30,
            corner_radius=theme.Radius.BUTTON,
            command=self._browse_folder,
        ).pack(side="left", padx=(4, 0))

        # --- FFmpeg ---
        self._section(self._t("ui.ffmpeg_section"))
        self._ffmpeg_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._ffmpeg_frame.pack(fill="x", padx=pad, pady=(0, theme.Space.SM))
        self._update_ffmpeg_ui()

        # --- Concurrent downloads ---
        self._section(self._t("ui.concurrent_downloads"))
        conc_row = ctk.CTkFrame(self, fg_color="transparent")
        conc_row.pack(fill="x", padx=pad, pady=(0, theme.Space.SM))
        self._conc_val_var = ctk.StringVar(value=str(self._cfg.concurrent_downloads))
        ctk.CTkLabel(
            conc_row,
            textvariable=self._conc_val_var,
            font=ctk.CTkFont(size=12, weight="bold"),
            width=20,
        ).pack(side="right")
        ctk.CTkSlider(
            conc_row,
            from_=1,
            to=5,
            number_of_steps=4,
            command=self._apply_concurrent,
        ).pack(side="left", fill="x", expand=True, padx=(0, theme.Space.SM))

        # --- Auto-open after download ---
        self._section(self._t("ui.auto_open"))
        auto_val = "on" if self._cfg.auto_open_after_download else "off"
        self._auto_open_var = ctk.StringVar(value=auto_val)
        ctk.CTkSwitch(
            self,
            text="",
            variable=self._auto_open_var,
            onvalue="on",
            offvalue="off",
            text_color=theme.ctk_color(theme._Dark.text, theme._Light.text),
            command=self._apply_auto_open,
        ).pack(anchor="w", padx=pad, pady=(0, theme.Space.SM))

        # --- Notify on complete ---
        self._section(self._t("ui.notify_complete"))
        self._notify_var = ctk.StringVar(value="on" if self._cfg.notify_on_complete else "off")
        ctk.CTkSwitch(
            self,
            text="",
            variable=self._notify_var,
            onvalue="on",
            offvalue="off",
            text_color=theme.ctk_color(theme._Dark.text, theme._Light.text),
            command=self._apply_notify,
        ).pack(anchor="w", padx=pad, pady=(0, theme.Space.SM))

        # --- Speed limit ---
        self._section(self._t("ui.speed_limit"))
        self._speed_var = ctk.StringVar(value=str(self._cfg.speed_limit_kbps))
        ctk.CTkEntry(
            self,
            textvariable=self._speed_var,
            font=ctk.CTkFont(size=12),
            height=30,
            width=120,
            corner_radius=theme.Radius.INPUT,
            text_color=theme.ctk_color(theme._Dark.text, theme._Light.text),
            placeholder_text_color=theme.ctk_color(theme._Dark.text_muted, theme._Light.text_muted),
        ).pack(anchor="w", padx=pad, pady=(0, theme.Space.SM))

        # --- Max retries ---
        self._section(self._t("ui.max_retries"))
        retry_row = ctk.CTkFrame(self, fg_color="transparent")
        retry_row.pack(fill="x", padx=pad, pady=(0, theme.Space.SM))
        self._retry_val_var = ctk.StringVar(value=str(self._cfg.max_retries))
        ctk.CTkLabel(
            retry_row,
            textvariable=self._retry_val_var,
            font=ctk.CTkFont(size=12, weight="bold"),
            width=20,
        ).pack(side="right")
        ctk.CTkSlider(
            retry_row,
            from_=0,
            to=10,
            number_of_steps=10,
            command=self._apply_retries,
        ).pack(side="left", fill="x", expand=True, padx=(0, theme.Space.SM))

        # --- Logs ---
        self._section(self._t("ui.open_logs"))
        ctk.CTkButton(
            self,
            text=self._t("ui.open_logs"),
            font=ctk.CTkFont(size=12),
            height=32,
            corner_radius=theme.Radius.BUTTON,
            command=self._open_logs,
        ).pack(anchor="w", padx=pad, pady=(0, theme.Space.SM))

        # --- About ---
        self._section(self._t("ui.about"))
        about_row = ctk.CTkFrame(self, fg_color="transparent")
        about_row.pack(fill="x", padx=pad, pady=(0, pad))
        ctk.CTkLabel(
            about_row,
            text=self._t("ui.made_by") + " Gabriel Castro",
            font=ctk.CTkFont(size=11),
            text_color=theme.ctk_color(theme._Dark.text_muted, theme._Light.text_muted),
        ).pack(side="left")
        ctk.CTkButton(
            about_row,
            text="GitHub",
            width=60,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color=theme.ctk_color(theme._Dark.surface2, theme._Light.surface2),
            text_color=theme.ctk_color(theme._Dark.text_muted, theme._Light.text_muted),
            corner_radius=theme.Radius.BUTTON,
            command=lambda: webbrowser.open("https://github.com/GabrielCastroV"),
        ).pack(side="left", padx=(theme.Space.SM, 2))
        ctk.CTkButton(
            about_row,
            text="𝕏",
            width=30,
            height=24,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="transparent",
            hover_color=theme.ctk_color(theme._Dark.surface2, theme._Light.surface2),
            text_color=theme.ctk_color(theme._Dark.text_muted, theme._Light.text_muted),
            corner_radius=theme.Radius.BUTTON,
            command=lambda: webbrowser.open("https://x.com/avocadostoasted"),
        ).pack(side="left", padx=2)

        # Save on any change
        self._folder_var.trace_add("write", lambda *_: self._save_folder())
        self._speed_var.trace_add("write", lambda *_: self._apply_speed_limit())

    def _section(self, label: str) -> ctk.CTkLabel:
        lbl = ctk.CTkLabel(
            self,
            text=label,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=theme.ctk_color(theme._Dark.text_muted, theme._Light.text_muted),
            anchor="w",
        )
        lbl.pack(fill="x", padx=theme.Space.MD, pady=(theme.Space.SM, 2))
        return lbl

    def _update_ffmpeg_ui(self) -> None:
        for w in self._ffmpeg_frame.winfo_children():
            w.destroy()

        if self._ffmpeg_path:
            ctk.CTkLabel(
                self._ffmpeg_frame,
                text=self._t("ui.ffmpeg_found"),
                font=ctk.CTkFont(size=12),
                text_color=theme.ctk_color(theme._Dark.success, theme._Light.success),
            ).pack(side="left")
            ctk.CTkLabel(
                self._ffmpeg_frame,
                text=str(self._ffmpeg_path),
                font=ctk.CTkFont(size=10),
                text_color=theme.ctk_color(theme._Dark.text_muted, theme._Light.text_muted),
            ).pack(side="left", padx=(8, 0))
        else:
            ctk.CTkLabel(
                self._ffmpeg_frame,
                text=self._t("ui.ffmpeg_missing_label"),
                font=ctk.CTkFont(size=12),
                text_color=theme.ctk_color(theme._Dark.error, theme._Light.error),
            ).pack(side="left")
            self._install_btn = ctk.CTkButton(
                self._ffmpeg_frame,
                text=self._t("ui.ffmpeg_install_btn"),
                font=ctk.CTkFont(size=12),
                width=150,
                height=30,
                corner_radius=theme.Radius.BUTTON,
                fg_color=theme.colors.accent,
                command=self._install_ffmpeg,
            )
            self._install_btn.pack(side="left", padx=(12, 0))

    def _install_ffmpeg(self) -> None:
        self._install_btn.configure(text=self._t("ui.ffmpeg_installing"), state="disabled")

        def _do() -> None:
            try:
                path = ffmpeg_manager.install()
                self._ffmpeg_path = path
                self.after(0, lambda: self._on_ffmpeg(str(path)))
                self.after(0, self._update_ffmpeg_ui)
            except Exception:
                self.after(0, self._update_ffmpeg_ui)

        threading.Thread(target=_do, daemon=True).start()

    def _apply_concurrent(self, value: float) -> None:
        v = max(1, min(5, round(value)))
        self._conc_val_var.set(str(v))
        self._cfg.concurrent_downloads = v
        save(self._cfg)

    def _apply_auto_open(self) -> None:
        self._cfg.auto_open_after_download = self._auto_open_var.get() == "on"
        save(self._cfg)

    def _apply_notify(self) -> None:
        self._cfg.notify_on_complete = self._notify_var.get() == "on"
        save(self._cfg)

    def _apply_speed_limit(self) -> None:
        try:
            v = max(0, int(self._speed_var.get()))
            self._cfg.speed_limit_kbps = v
            save(self._cfg)
        except ValueError:
            pass

    def _apply_retries(self, value: float) -> None:
        v = max(0, min(10, round(value)))
        self._retry_val_var.set(str(v))
        self._cfg.max_retries = v
        save(self._cfg)

    def _apply_theme(self, value: str) -> None:
        raw = "dark" if value == self._t("ui.theme.dark") else "light"
        self._cfg.theme = raw  # type: ignore[assignment]
        save(self._cfg)
        self._on_theme(raw)

    def _apply_lang(self, value: str) -> None:
        lang: Language = "en" if value == "EN" else "es"
        self._cfg.language = lang
        save(self._cfg)
        self._on_lang(lang)

    def _browse_folder(self) -> None:
        from tkinter import filedialog

        path = filedialog.askdirectory(initialdir=self._folder_var.get() or str(Path.home()))
        if path:
            self._folder_var.set(path)

    def _save_folder(self) -> None:
        self._cfg.default_output_dir = self._folder_var.get()
        save(self._cfg)

    def _open_logs(self) -> None:
        folder = log_dir()
        if sys.platform == "win32":
            import os

            os.startfile(folder)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", str(folder)], check=False)
        else:
            subprocess.run(["xdg-open", str(folder)], check=False)
