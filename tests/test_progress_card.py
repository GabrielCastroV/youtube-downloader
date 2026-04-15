"""Tests for progress_card.py formatting helpers."""

from __future__ import annotations

import pytest

from yt_downloader.ui.components.progress_card import _fmt_eta, _fmt_size, _fmt_speed


class TestFmtSize:
    def test_none_returns_question_mark(self) -> None:
        assert _fmt_size(None) == "?"

    def test_bytes(self) -> None:
        assert _fmt_size(512) == "512 B"

    def test_kilobytes(self) -> None:
        assert _fmt_size(5_000) == "5 KB"

    def test_megabytes(self) -> None:
        assert _fmt_size(1_500_000) == "1.5 MB"

    def test_gigabytes(self) -> None:
        assert _fmt_size(2_000_000_000) == "2.0 GB"

    def test_zero(self) -> None:
        assert _fmt_size(0) == "0 B"


class TestFmtSpeed:
    def test_none_returns_placeholder(self) -> None:
        result = _fmt_speed(None)
        assert result != ""  # must always be non-empty
        assert "B/s" in result  # must include unit

    def test_bytes_per_second(self) -> None:
        assert _fmt_speed(512) == "512 B/s"

    def test_kilobytes_per_second(self) -> None:
        assert _fmt_speed(500_000) == "500 KB/s"

    def test_megabytes_per_second(self) -> None:
        assert _fmt_speed(1_500_000) == "1.5 MB/s"

    def test_gigabytes_per_second(self) -> None:
        assert _fmt_speed(2_000_000_000) == "2.0 GB/s"


class TestFmtEta:
    def test_none_returns_empty(self) -> None:
        assert _fmt_eta(None) == ""

    def test_seconds_only(self) -> None:
        assert _fmt_eta(45) == "ETA 45s"

    def test_minutes_and_seconds(self) -> None:
        assert _fmt_eta(90) == "ETA 1m 30s"

    def test_hours_minutes(self) -> None:
        assert _fmt_eta(3661) == "ETA 1h 1m"

    def test_zero_seconds(self) -> None:
        assert _fmt_eta(0) == "ETA 0s"

    @pytest.mark.parametrize(
        ("seconds", "expected"),
        [
            (59, "ETA 59s"),
            (60, "ETA 1m 0s"),
            (3600, "ETA 1h 0m"),
        ],
    )
    def test_boundary_values(self, seconds: int, expected: str) -> None:
        assert _fmt_eta(seconds) == expected
