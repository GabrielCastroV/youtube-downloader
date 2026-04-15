"""Allow running as ``python -m yt_downloader`` or via the ``yt-downloader`` script."""

from __future__ import annotations


def main() -> None:
    from yt_downloader.app import run

    run()


if __name__ == "__main__":
    main()
