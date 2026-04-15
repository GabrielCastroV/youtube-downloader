# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-04-14

### Added

- Full-featured YouTube downloader powered by **yt-dlp**
- **Format selection**: Video+Audio, Audio only, Video only modes
- **Quality options**: resolution (360p → 4K), container (MP4/WebM/MKV), codec (H.264/AV1/VP9)
- **Audio options**: MP3, M4A, Opus, WAV, FLAC at 96–320 kbps
- **Download queue** with live progress, speed, and ETA per item
- **Persistent history** via local SQLite database with re-download and open-file actions
- **Subtitle support**: auto-generated + manual, embed or export `.srt`
- **Clip trimming** by start/end timestamps (`mm:ss`)
- **Playlist downloads** with configurable item range
- **Thumbnail + metadata embedding** (ID3/MP4 tags)
- **FFmpeg auto-detection** and one-click install from Settings
- **Dark / Light mode** toggle with instant switch, persisted across sessions
- **Bilingual UI** (Español / English) with full key coverage
- **Keyboard shortcuts**: `Ctrl+Enter` to download, `Esc` to cancel
- **Advanced panel**: output folder, filename template, subtitle/clip/playlist options
- **Settings panel**: theme, language, folder, FFmpeg, concurrent downloads, speed limit, retries
- **Toast notifications** with auto-dismiss
- **Auto-paste prompt** when a YouTube URL is detected in the clipboard
- Pinned progress bar at top of window — always visible regardless of page
- "Open folder" button after download completes — opens OS file explorer at output directory
- Footer with author credits and social links

### Technical

- Python 3.11+ · CustomTkinter 5 · yt-dlp · Pydantic v2 · SQLite stdlib
- `ThreadPoolExecutor`-backed download queue with configurable concurrency
- Rotating log files (5 × 1 MB) stored in platform-appropriate user directory
- Typed exception hierarchy with i18n user-facing messages
- 74 tests · pytest-cov · ruff · mypy strict · pre-commit hooks
- CI: matrix across Python 3.11/3.12/3.13 × Ubuntu/macOS/Windows
- Release builds via PyInstaller (Windows `.exe`, macOS `.app`, Linux binary)

[1.0.0]: https://github.com/GabrielCastroV/youtube-downloader/releases/tag/v1.0.0
