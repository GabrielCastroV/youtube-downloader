# Contributing to YT Downloader

Thank you for your interest in contributing!

## Getting started

```bash
git clone https://github.com/GabrielCastroV/youtube-downloader.git
cd youtube-downloader
uv sync --extra dev
uv run pre-commit install
```

## Commit style

We use **Conventional Commits**:

```
feat: add subtitle language selector
fix: handle private video error correctly
chore: update yt-dlp to 2026.x.x
docs: add ffmpeg manual install instructions
test: add queue cancellation test
```

Subject ≤ 50 chars. Body only when the *why* isn't obvious from the diff.

## Pull requests

1. Fork → branch → PR against `main`
2. All CI checks must pass (lint, types, tests)
3. Tests required for any non-trivial behaviour change
4. Keep PRs focused — one feature or fix per PR

## Code style

- **Formatter:** `ruff format` (line length 100)
- **Linter:** `ruff check` — fix warnings before opening PR
- **Types:** `mypy --strict` must pass with no new errors
- **No bare except:** always catch specific exceptions or map to typed hierarchy
- **Thread safety:** never call tkinter APIs from worker threads; use `widget.after(0, fn)`

## Running checks locally

```bash
uv run ruff format src tests
uv run ruff check src tests
uv run mypy src
uv run pytest
```

## Questions?

Open a [Discussion](https://github.com/GabrielCastroV/youtube-downloader/discussions)
or an [Issue](https://github.com/GabrielCastroV/youtube-downloader/issues).
