"""Tests for the exception hierarchy."""

from __future__ import annotations

from yt_downloader.exceptions import (
    DownloadCancelled,
    DownloaderError,
    FFmpegMissingError,
    InvalidURLError,
    NetworkError,
    QualityUnavailableError,
    UnexpectedError,
    VideoUnavailableError,
)


def test_all_inherit_from_base() -> None:
    errors = [
        InvalidURLError,
        VideoUnavailableError,
        NetworkError,
        FFmpegMissingError,
        QualityUnavailableError,
        UnexpectedError,
        DownloadCancelled,
    ]
    for cls in errors:
        assert issubclass(cls, DownloaderError)
        assert issubclass(cls, Exception)


def test_each_has_user_key() -> None:
    errors = [
        InvalidURLError("test"),
        VideoUnavailableError("test"),
        NetworkError("test"),
        FFmpegMissingError("test"),
        QualityUnavailableError("test"),
        UnexpectedError("test"),
        DownloadCancelled("test"),
    ]
    for exc in errors:
        assert exc.user_key
        assert exc.user_key.startswith(("error.", "status."))


def test_details_stored() -> None:
    exc = InvalidURLError("some detail")
    assert exc.details == "some detail"
    assert "some detail" in str(exc)


def test_default_no_details() -> None:
    exc = NetworkError()
    assert exc.details == ""
