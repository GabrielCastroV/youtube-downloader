"""Tests for history.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from yt_downloader import history


@pytest.fixture(autouse=True)
def _tmp_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db = tmp_path / "history.db"
    monkeypatch.setattr("yt_downloader.history.db_path", lambda: db)


def test_add_and_retrieve() -> None:
    history.add(
        url="https://youtu.be/test1",
        title="Test Video",
        filepath="/downloads/test.mp4",
        mode="video+audio",
        success=True,
    )
    entries = history.all_entries()
    assert len(entries) == 1
    assert entries[0].title == "Test Video"
    assert entries[0].url == "https://youtu.be/test1"
    assert entries[0].success is True


def test_multiple_entries_ordered_newest_first() -> None:
    for i in range(3):
        history.add(
            url=f"https://youtu.be/video{i}",
            title=f"Video {i}",
            filepath=f"/dl/v{i}.mp4",
            mode="audio",
        )
    entries = history.all_entries()
    assert len(entries) == 3
    # Newest first
    assert entries[0].title == "Video 2"


def test_delete_entry() -> None:
    history.add("https://youtu.be/del", "Delete Me", "/dl/del.mp4", "video+audio")
    entries = history.all_entries()
    assert len(entries) == 1
    history.delete(entries[0].id)
    assert history.all_entries() == []


def test_clear() -> None:
    for i in range(5):
        history.add(f"https://youtu.be/v{i}", f"V{i}", f"/dl/v{i}.mp4", "audio")
    history.clear()
    assert history.all_entries() == []


def test_failed_entry() -> None:
    history.add("https://youtu.be/fail", "Fail", "/dl/fail.mp4", "video+audio", success=False)
    entries = history.all_entries()
    assert entries[0].success is False
