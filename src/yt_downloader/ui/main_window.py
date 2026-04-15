"""Main application window.

Layout:
  ┌──────────────────────────────────┐
  │  Header: title + nav + toggles   │
  ├──────────────────────────────────┤
  │  Page content (switches via nav) │
  │                                  │
  │  [Home]   URL input              │
  │           Preview card           │
  │           Format selector        │
  │           Advanced panel         │
  │           Download button        │
  │           Progress card          │
  │                                  │
  │  [Queue]  Queue list             │
  │  [History] History list          │
  │  [Settings] Settings panel       │
  └──────────────────────────────────┘
"""

from __future__ import annotations

import logging
import queue
import sys
import threading
import webbrowser

import customtkinter as ctk  # type: ignore[import-untyped]

from yt_downloader import ffmpeg_manager, history
from yt_downloader.config import Config, save
from yt_downloader.downloader import Downloader
from yt_downloader.exceptions import (
    DownloadCancelled,
    DownloaderError,
)
from yt_downloader.i18n import Language, Translator
from yt_downloader.metadata import fetch, is_youtube_url
from yt_downloader.models import DownloadOptions, ProgressEvent, VideoInfo
from yt_downloader.queue import DownloadQueue, ItemStatus, QueueItem
from yt_downloader.ui import theme
from yt_downloader.ui.components.advanced_panel import AdvancedPanel
from yt_downloader.ui.components.format_selector import FormatSelector
from yt_downloader.ui.components.history_drawer import HistoryPanel
from yt_downloader.ui.components.preview_card import PreviewCard
from yt_downloader.ui.components.progress_card import ProgressCard
from yt_downloader.ui.components.queue_list import QueuePanel
from yt_downloader.ui.components.settings_panel import SettingsPanel
from yt_downloader.ui.components.toast import ToastManager
from yt_downloader.ui.components.url_input import URLInput
from yt_downloader.ui.icons import (
    ICON_DOWNLOAD,
    ICON_HISTORY,
    ICON_MOON,
    ICON_QUEUE,
    ICON_SETTINGS,
    ICON_SUN,
)

log = logging.getLogger(__name__)

_PAGE_HOME = "home"
_PAGE_QUEUE = "queue"
_PAGE_HISTORY = "history"
_PAGE_SETTINGS = "settings"


class MainWindow(ctk.CTk):  # type: ignore[misc]
    """Root application window."""

    def __init__(self, t: Translator, cfg: Config) -> None:
        super().__init__()
        self._t = t
        self._cfg = cfg
        self._current_page: str = _PAGE_HOME
        self._video_info: VideoInfo | None = None
        self._fetch_thread: threading.Thread | None = None
        self._active_downloader: Downloader | None = None
        self._progress_queue: queue.Queue[ProgressEvent] = queue.Queue()
        self._downloading = False
        from pathlib import Path

        self._last_output_dir: Path = Path.home() / "Downloads"

        # Download queue
        ffmpeg_path = str(ffmpeg_manager.detect(cfg.ffmpeg_path) or "")
        self._dl_queue = DownloadQueue(
            max_workers=2,
            on_status=self._on_queue_status,
            ffmpeg_path=ffmpeg_path,
        )

        self._setup_window()
        theme.apply(cfg.theme)  # type: ignore[arg-type]
        self._build()
        self._toasts = ToastManager(self)
        self._poll_progress()

        # Auto-paste check after window is ready
        self.after(500, self._check_autopaste)

        # Drag & drop support (optional dependency)
        self._setup_dnd()

    # ------------------------------------------------------------------
    # Window setup
    # ------------------------------------------------------------------

    def _setup_window(self) -> None:
        self.title(self._t("app.title"))
        w, h = self._cfg.window_width, self._cfg.window_height
        self.geometry(f"{w}x{h}")
        self.minsize(460, 580)
        self.resizable(True, True)
        self.configure(fg_color=theme.ctk_color(theme._Dark.bg, theme._Light.bg))

        # Save window size on close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_dnd(self) -> None:
        try:
            from tkinterdnd2 import DND_TEXT  # type: ignore[import-untyped]

            self.drop_target_register(DND_TEXT)  # type: ignore[attr-defined]
            self.dnd_bind("<<Drop>>", self._on_drop)  # type: ignore[attr-defined]
        except Exception:
            pass  # optional dependency not available

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build(self) -> None:
        self._build_header()
        self._build_footer()
        self._build_progress_bar()
        self._build_content()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(
            self,
            height=52,
            fg_color=theme.ctk_color(theme._Dark.surface, theme._Light.surface),
            corner_radius=0,
        )
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        # Logo / title — click to go home
        ctk.CTkButton(
            header,
            text="▶ " + self._t("app.title"),
            font=ctk.CTkFont(family=theme.Font.FAMILY, size=16, weight="bold"),
            text_color=theme.colors.accent,
            fg_color="transparent",
            hover_color=theme.ctk_color(theme._Dark.surface2, theme._Light.surface2),
            corner_radius=theme.Radius.BUTTON,
            command=lambda: self._nav_to(_PAGE_HOME),
        ).pack(side="left", padx=theme.Space.SM)

        # Right-side controls
        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right", padx=theme.Space.MD)

        # Language toggle
        self._lang_var = ctk.StringVar(value=self._cfg.language.upper())
        ctk.CTkSegmentedButton(
            right,
            values=["ES", "EN"],
            variable=self._lang_var,
            width=80,
            height=30,
            font=ctk.CTkFont(size=11),
            command=self._on_lang_toggle,
        ).pack(side="left", padx=(0, theme.Space.SM))

        # Theme toggle
        self._theme_icon_var = ctk.StringVar(
            value=ICON_MOON if self._cfg.theme == "dark" else ICON_SUN
        )
        ctk.CTkButton(
            right,
            textvariable=self._theme_icon_var,
            width=32,
            height=32,
            font=ctk.CTkFont(size=15),
            fg_color="transparent",
            hover_color=theme.ctk_color(theme._Dark.surface2, theme._Light.surface2),
            text_color=theme.ctk_color(theme._Dark.text, theme._Light.text),
            command=self._toggle_theme,
        ).pack(side="left", padx=(0, theme.Space.XS))

        # Nav icons
        nav_buttons = [
            (ICON_QUEUE, _PAGE_QUEUE, self._t("ui.queue")),
            (ICON_HISTORY, _PAGE_HISTORY, self._t("ui.history")),
            (ICON_SETTINGS, _PAGE_SETTINGS, self._t("ui.settings")),
        ]
        for icon, page, _tip in nav_buttons:
            btn = ctk.CTkButton(
                right,
                text=icon,
                width=32,
                height=32,
                font=ctk.CTkFont(size=15),
                fg_color="transparent",
                hover_color=theme.ctk_color(theme._Dark.surface2, theme._Light.surface2),
                text_color=theme.ctk_color(theme._Dark.text, theme._Light.text),
                command=lambda p=page: self._nav_to(p),
            )
            btn.pack(side="left", padx=2)

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(
            self,
            height=30,
            fg_color=theme.ctk_color(theme._Dark.surface, theme._Light.surface),
            corner_radius=0,
        )
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        ctk.CTkLabel(
            footer,
            text="© Gabriel Castro",
            font=ctk.CTkFont(size=10),
            text_color=theme.ctk_color(theme._Dark.text_muted, theme._Light.text_muted),
        ).pack(side="left", padx=theme.Space.MD)

        right = ctk.CTkFrame(footer, fg_color="transparent")
        right.pack(side="right", padx=theme.Space.SM)

        ctk.CTkButton(
            right,
            text="𝕏",
            width=28,
            height=22,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="transparent",
            hover_color=theme.ctk_color(theme._Dark.surface2, theme._Light.surface2),
            text_color=theme.ctk_color(theme._Dark.text_muted, theme._Light.text_muted),
            corner_radius=theme.Radius.BUTTON,
            command=lambda: webbrowser.open("https://x.com/avocadostoasted"),
        ).pack(side="right", padx=2)

        ctk.CTkButton(
            right,
            text="GitHub",
            width=52,
            height=22,
            font=ctk.CTkFont(size=10),
            fg_color="transparent",
            hover_color=theme.ctk_color(theme._Dark.surface2, theme._Light.surface2),
            text_color=theme.ctk_color(theme._Dark.text_muted, theme._Light.text_muted),
            corner_radius=theme.Radius.BUTTON,
            command=lambda: webbrowser.open("https://github.com/GabrielCastroV"),
        ).pack(side="right", padx=2)

    def _build_progress_bar(self) -> None:
        """Progress card pinned between header and content — always visible when downloading."""
        self._progress = ProgressCard(
            self,
            self._t,
            on_cancel=self._cancel_download,
            on_open_folder=self._open_download_folder,
        )
        # Not packed initially; show() packs it, hide() removes it

    def _build_content(self) -> None:
        self._content = ctk.CTkScrollableFrame(
            self,
            fg_color=theme.ctk_color(theme._Dark.bg, theme._Light.bg),
            corner_radius=0,
            scrollbar_button_color=theme.ctk_color(theme._Dark.surface2, theme._Light.surface2),
        )
        self._content.pack(fill="both", expand=True, padx=theme.Space.MD, pady=theme.Space.MD)
        self._content.columnconfigure(0, weight=1)

        self._build_home_page()

    def _build_home_page(self) -> None:
        self._home_frame = ctk.CTkFrame(self._content, fg_color="transparent")

        # URL input
        self._url_input = URLInput(self._home_frame, self._t, self._on_url_change)
        self._url_input.pack(fill="x", pady=(0, theme.Space.SM))

        # Preview card (hidden until URL valid)
        self._preview = PreviewCard(self._home_frame, self._t)

        # Format selector
        self._format_sel = FormatSelector(
            self._home_frame,
            self._t,
            on_change=lambda: None,
        )
        self._format_sel.pack(fill="x", pady=(0, theme.Space.SM))

        # Advanced panel
        self._advanced = AdvancedPanel(self._home_frame, self._t)
        self._advanced.set_defaults(
            folder=self._cfg.default_output_dir,
            template=self._cfg.filename_template,
            embed_thumb=self._cfg.embed_thumbnail,
            embed_meta=self._cfg.embed_metadata,
        )
        self._advanced.pack(fill="x", pady=(0, theme.Space.SM))

        # Thumbnail switch (always visible, above download button)
        thumb_row = ctk.CTkFrame(self._home_frame, fg_color="transparent")
        thumb_row.pack(fill="x", pady=(0, theme.Space.XS))
        self._thumb_var = ctk.IntVar(value=1 if self._cfg.embed_thumbnail else 0)
        ctk.CTkSwitch(
            thumb_row,
            text=self._t("ui.embed_thumbnail"),
            variable=self._thumb_var,
            onvalue=1,
            offvalue=0,
            font=ctk.CTkFont(size=13),
            text_color=theme.ctk_color(theme._Dark.text, theme._Light.text),
        ).pack(side="left", padx=theme.Space.XS)

        # Download button
        self._dl_btn = ctk.CTkButton(
            self._home_frame,
            text=ICON_DOWNLOAD + "  " + self._t("ui.download"),
            font=ctk.CTkFont(family=theme.Font.FAMILY, size=15, weight="bold"),
            height=50,
            corner_radius=theme.Radius.BUTTON,
            fg_color=theme.colors.accent,
            hover_color=theme.colors.accent_hover,
            text_color="#FFFFFF",
            command=self._start_download,
        )
        self._dl_btn.pack(fill="x", pady=(theme.Space.SM, theme.Space.MD))

        self._home_frame.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _nav_to(self, page: str) -> None:
        if self._current_page == page:
            if page == _PAGE_HOME:
                return  # already home, do nothing
            # Toggle back to home when pressing same nav icon again
            page = _PAGE_HOME

        self._current_page = page
        # Clear content area
        for w in self._content.winfo_children():
            w.pack_forget()

        if page == _PAGE_HOME:
            self._home_frame.pack(fill="both", expand=True)
        elif page == _PAGE_QUEUE:
            self._show_queue_page()
        elif page == _PAGE_HISTORY:
            self._show_history_page()
        elif page == _PAGE_SETTINGS:
            self._show_settings_page()

    def _show_queue_page(self) -> None:
        panel = QueuePanel(
            self._content,
            self._t,
            on_cancel=self._dl_queue.cancel,
        )
        panel.refresh(self._dl_queue.items)
        panel.pack(fill="both", expand=True)

    def _show_history_page(self) -> None:
        panel = HistoryPanel(
            self._content,
            self._t,
            on_redownload=self._redownload,
            on_cleared=lambda: self._toasts.success(self._t("toast.history_cleared")),
        )
        panel.pack(fill="both", expand=True)

    def _show_settings_page(self) -> None:
        panel = SettingsPanel(
            self._content,
            self._t,
            self._cfg,
            on_theme_change=self._on_theme_change,
            on_lang_change=self._on_lang_change,
            on_ffmpeg_installed=self._on_ffmpeg_installed,
        )
        panel.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # URL handling
    # ------------------------------------------------------------------

    def _on_url_change(self, url: str) -> None:
        if not is_youtube_url(url):
            self._preview.hide()
            return
        # Fetch metadata in background
        if self._fetch_thread and self._fetch_thread.is_alive():
            return  # debounce: ignore if already fetching
        self._fetch_thread = threading.Thread(target=self._fetch_metadata, args=(url,), daemon=True)
        self._fetch_thread.start()

    def _fetch_metadata(self, url: str) -> None:
        try:
            info = fetch(url)
            self.after(0, lambda: self._on_info_ready(info))
        except DownloaderError:
            self.after(0, lambda: self._preview.hide())
        except Exception:
            self.after(0, lambda: self._preview.hide())

    def _on_info_ready(self, info: VideoInfo) -> None:
        self._video_info = info
        self._preview.show(info)

    def _check_autopaste(self) -> None:
        self._url_input.check_clipboard()

    def _on_drop(self, event: object) -> None:
        try:
            url = str(getattr(event, "data", "")).strip()
            if is_youtube_url(url):
                self._url_input.set_url(url)
                self._nav_to(_PAGE_HOME)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Download flow
    # ------------------------------------------------------------------

    def _start_download(self) -> None:
        url = self._url_input.get_url()
        if not url:
            self._toasts.error(self._t("error.invalid_url"))
            return
        if not is_youtube_url(url):
            self._toasts.error(self._t("error.invalid_url"))
            return

        # Check ffmpeg when needed
        fmt = self._format_sel
        needs_ffmpeg = fmt.mode != "audio" or fmt.audio_format != "m4a"
        if needs_ffmpeg:
            ffp = ffmpeg_manager.detect(self._cfg.ffmpeg_path)
            if not ffp:
                self._toasts.warning(self._t("error.ffmpeg_missing"))
                self._nav_to(_PAGE_SETTINGS)
                return

        adv = self._advanced
        opts = DownloadOptions(
            url=url,
            mode=fmt.mode,
            audio_format=fmt.audio_format,  # type: ignore[arg-type]
            audio_quality=fmt.audio_quality,
            video_resolution=fmt.video_resolution,
            video_container=fmt.video_container,  # type: ignore[arg-type]
            video_codec=fmt.video_codec,  # type: ignore[arg-type]
            output_dir=adv.output_dir,
            filename_template=adv.filename_template,
            embed_thumbnail=bool(self._thumb_var.get()),
            embed_metadata=adv.embed_metadata,
            subtitles=adv.subtitles,
            clip_start=adv.clip_start,
            clip_end=adv.clip_end,
            playlist_start=adv.playlist_start,
            playlist_end=adv.playlist_end,
        )

        self._last_output_dir = opts.output_dir  # used by open-folder button
        self._downloading = True
        self._dl_btn.configure(state="disabled")
        self._progress.show()

        # Reset queue and run directly for single-item UX
        self._progress_queue = queue.Queue()
        ffmpeg_path = str(ffmpeg_manager.detect(self._cfg.ffmpeg_path) or "")
        self._active_downloader = Downloader(opts, self._progress_queue, ffmpeg_path)

        threading.Thread(
            target=self._run_download,
            args=(opts,),
            daemon=True,
        ).start()

    def _run_download(self, opts: DownloadOptions) -> None:
        assert self._active_downloader is not None
        try:
            self._active_downloader.run()
            title = self._video_info.title if self._video_info else opts.url
            history.add(
                url=opts.url,
                title=title,
                filepath=str(opts.output_dir / opts.filename_template),
                mode=opts.mode,
                success=True,
            )
            self.after(0, self._on_download_done)
        except DownloadCancelled:
            self.after(0, self._on_download_cancelled)
        except DownloaderError as exc:
            key = exc.user_key
            self.after(0, lambda k=key: self._on_download_error(k))
        except Exception:
            log.exception("Unexpected download error")
            self.after(0, lambda: self._on_download_error("error.unexpected"))

    def _on_download_done(self) -> None:
        self._downloading = False
        self._dl_btn.configure(state="normal")
        self._toasts.success(self._t("toast.download_done"))
        # Progress card stays visible so user can click "Open folder"

    def _open_download_folder(self, _filepath: str) -> None:
        import os
        import subprocess
        from pathlib import Path

        folder = self._last_output_dir
        if not folder.exists():
            folder = Path.home() / "Downloads"
        try:
            if sys.platform == "win32":
                os.startfile(folder)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.run(["open", str(folder)], check=False)
            else:
                subprocess.run(["xdg-open", str(folder)], check=False)
        except Exception:
            log.warning("Could not open folder: %s", folder)

    def _on_download_cancelled(self) -> None:
        self._downloading = False
        self._dl_btn.configure(state="normal")
        self._progress.hide()
        self._toasts.info(self._t("status.cancelled"))

    def _on_download_error(self, key: str) -> None:
        self._downloading = False
        self._dl_btn.configure(state="normal")
        self._toasts.error(self._t(key))
        self._progress.hide()

    def _cancel_download(self) -> None:
        if self._active_downloader:
            self._active_downloader.cancel()

    def _redownload(self, url: str) -> None:
        self._url_input.set_url(url)
        self._nav_to(_PAGE_HOME)

    # ------------------------------------------------------------------
    # Progress polling
    # ------------------------------------------------------------------

    def _poll_progress(self) -> None:
        try:
            while True:
                ev = self._progress_queue.get_nowait()
                self._progress.update_event(ev)
        except Exception:
            pass
        self.after(100, self._poll_progress)

    # ------------------------------------------------------------------
    # Queue status callback (from worker threads)
    # ------------------------------------------------------------------

    def _on_queue_status(
        self, item: QueueItem, status: ItemStatus, ev: ProgressEvent | None
    ) -> None:
        # Update queue page if currently shown
        pass  # QueuePanel.refresh() called when user opens the page

    # ------------------------------------------------------------------
    # Theme & language
    # ------------------------------------------------------------------

    def _toggle_theme(self) -> None:
        current = self._cfg.theme
        new_theme = "light" if current == "dark" else "dark"
        self._on_theme_change(new_theme)

    def _on_theme_change(self, new_theme: str) -> None:
        self._cfg.theme = new_theme  # type: ignore[assignment]
        save(self._cfg)
        theme.apply(new_theme)  # type: ignore[arg-type]
        self._theme_icon_var.set(ICON_MOON if new_theme == "dark" else ICON_SUN)
        self.configure(fg_color=theme.ctk_color(theme._Dark.bg, theme._Light.bg))

    def _on_lang_toggle(self, value: str) -> None:
        lang: Language = "en" if value == "EN" else "es"
        self._on_lang_change(lang)

    def _on_lang_change(self, lang: Language) -> None:
        self._t.set_language(lang)
        self._cfg.language = lang
        save(self._cfg)
        self._lang_var.set(lang.upper())
        self._update_all_lang()

    def _update_all_lang(self) -> None:
        self.title(self._t("app.title"))
        self._url_input.update_lang()
        self._preview.update_lang()
        self._format_sel.update_lang()
        self._advanced.update_lang()
        self._dl_btn.configure(text=ICON_DOWNLOAD + "  " + self._t("ui.download"))
        self._progress.update_lang()

    def _on_ffmpeg_installed(self, path: str) -> None:
        self._cfg.ffmpeg_path = path
        save(self._cfg)
        self._dl_queue._ffmpeg_path = path  # type: ignore[attr-defined]
        self._toasts.success(self._t("toast.ffmpeg_installed"))

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def _on_close(self) -> None:
        # Save window geometry
        try:
            self._cfg.window_width = self.winfo_width()
            self._cfg.window_height = self.winfo_height()
            save(self._cfg)
        except Exception:
            pass
        self._dl_queue.shutdown()
        self.destroy()
