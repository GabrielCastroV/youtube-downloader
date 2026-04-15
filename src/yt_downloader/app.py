"""Application entry point: wires Config → I18n → Theme → MainWindow."""

from __future__ import annotations

from yt_downloader import config as cfg_module
from yt_downloader import logging_setup
from yt_downloader.i18n import Translator
from yt_downloader.ui import theme
from yt_downloader.ui.main_window import MainWindow


def run() -> None:
    """Bootstrap and start the application."""
    logging_setup.setup()

    cfg = cfg_module.load()
    theme.apply(cfg.theme)  # type: ignore[arg-type]

    t = Translator(cfg.language)  # type: ignore[arg-type]

    window = MainWindow(t=t, cfg=cfg)
    window.mainloop()
