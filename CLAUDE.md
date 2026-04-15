# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
# Install uv first (if not present)
pip install uv

# Install all dependencies
uv sync --extra dev

# Run the app
uv run yt-downloader
```

## Architecture

**Stack:** Python 3.12+ · CustomTkinter 5 (GUI) · yt-dlp (download backend) · Pydantic v2 (config) · SQLite stdlib (history) · ThreadPoolExecutor (queue)

**Package layout:**

```
src/yt_downloader/
├── __main__.py          # Entry: python -m yt_downloader
├── app.py               # Wires Config → I18n → MainWindow
├── config.py            # Pydantic settings, saved to user dir as JSON
├── i18n.py              # Translator class, ES/EN dicts
├── exceptions.py        # Typed error hierarchy (DownloaderError → subclasses)
├── models.py            # Frozen dataclasses: VideoInfo, DownloadOptions, ProgressEvent
├── paths.py             # XDG/platform-dirs paths for config/data/logs
├── logging_setup.py     # Rotating file log + stderr handler
├── downloader.py        # yt-dlp wrapper: translates DownloadOptions → ydl_opts, progress_hooks
├── metadata.py          # Fetch video info without downloading (extract_info + download=False)
├── ffmpeg_manager.py    # Detect ffmpeg in PATH/managed dir; download+install official binary
├── history.py           # SQLite CRUD via stdlib sqlite3
├── queue.py             # DownloadQueue backed by ThreadPoolExecutor; ItemStatus lifecycle
└── ui/
    ├── theme.py         # Design tokens: colors, spacing, radii, fonts; apply(mode) sets CTk theme
    ├── icons.py         # Unicode glyphs + Pillow thumbnail loader
    ├── main_window.py   # CTk root: header nav, page switching (home/queue/history/settings)
    └── components/
        ├── url_input.py         # Debounced entry + paste button + auto-paste prompt
        ├── preview_card.py      # Thumbnail + title + channel + duration + badges
        ├── format_selector.py   # Mode chips (Video+Audio/Audio/Video) + contextual dropdowns
        ├── advanced_panel.py    # Collapsible: output folder, template, subs, clip, playlist
        ├── progress_card.py     # Progress bar + % + speed + ETA + cancel
        ├── queue_list.py        # Scrollable queue with per-item status + cancel
        ├── history_drawer.py    # Scrollable history with open/re-download/delete actions
        ├── settings_panel.py    # Theme, language, default folder, FFmpeg, open logs
        └── toast.py             # Auto-dismiss bottom-right notifications
```

**Download flow:**
1. `url_input.py` debounces (350ms) → calls `metadata.fetch()` in background thread
2. Preview card populates; shorts/playlist detected from URL or duration
3. User selects format/quality → constructs `DownloadOptions` dataclass
4. Click Download → `Downloader(opts, queue).run()` in thread
5. `progress_hooks` emit `ProgressEvent` to `queue.Queue`
6. `main_window._poll_progress()` drains queue via `after(100, ...)` — 10 FPS UI update
7. On complete → write to history SQLite; toast success

**Error handling:**
- All exceptions inherit `DownloaderError`; each has `.user_key` (i18n key) and `.details`
- `downloader.py` maps `yt_dlp.utils.DownloadError` → typed exceptions via `_map_error()`
- UI shows translated message via `t(exc.user_key)` in a toast
- Full traceback goes to rotating log file (5 × 1MB) in user log dir
- Never use bare `except:` or swallow exceptions silently

**Thread safety:**
- All `after(ms, fn)` calls from worker threads → safe UI update
- Progress events via `queue.Queue` — never touch tkinter widgets from worker threads directly

## Run tests

```bash
uv run pytest
uv run pytest --no-cov -v   # verbose, no coverage
```

## Lint / Format / Types

```bash
uv run ruff format src tests   # format
uv run ruff check src tests    # lint
uv run mypy src                # types
```

## Key conventions

- `pathlib.Path` everywhere; no `os.path`
- `logging` module; no `print` in production code
- Type hints on all functions (mypy strict)
- Frozen dataclasses with `slots=True` for domain models
- `Pydantic v2` only for `Config` (validation + JSON serialization)
- Ruff line length: 100
