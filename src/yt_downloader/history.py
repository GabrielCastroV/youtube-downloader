"""Download history backed by a SQLite database (stdlib only)."""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager

from yt_downloader.models import DownloadMode, HistoryEntry
from yt_downloader.paths import db_path

log = logging.getLogger(__name__)

_DDL = """
CREATE TABLE IF NOT EXISTS history (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    url       TEXT    NOT NULL,
    title     TEXT    NOT NULL,
    filepath  TEXT    NOT NULL,
    mode      TEXT    NOT NULL,
    timestamp TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    success   INTEGER NOT NULL DEFAULT 1
);
"""


@contextmanager
def _conn() -> Generator[sqlite3.Connection, None, None]:
    con = sqlite3.connect(db_path())
    con.row_factory = sqlite3.Row
    try:
        con.execute(_DDL)
        con.commit()
        yield con
    finally:
        con.close()


def add(
    url: str,
    title: str,
    filepath: str,
    mode: DownloadMode,
    success: bool = True,
) -> None:
    try:
        with _conn() as con:
            con.execute(
                "INSERT INTO history (url, title, filepath, mode, success) VALUES (?,?,?,?,?)",
                (url, title, filepath, mode, int(success)),
            )
            con.commit()
    except sqlite3.Error:
        log.warning("Failed to write history entry", exc_info=True)


def all_entries(limit: int = 200) -> list[HistoryEntry]:
    try:
        with _conn() as con:
            rows = con.execute(
                "SELECT id, url, title, filepath, mode, timestamp, success "
                "FROM history ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            HistoryEntry(
                id=r["id"],
                url=r["url"],
                title=r["title"],
                filepath=r["filepath"],
                mode=r["mode"],  # type: ignore[arg-type]
                timestamp=r["timestamp"],
                success=bool(r["success"]),
            )
            for r in rows
        ]
    except sqlite3.Error:
        log.warning("Failed to read history", exc_info=True)
        return []


def delete(entry_id: int) -> None:
    try:
        with _conn() as con:
            con.execute("DELETE FROM history WHERE id = ?", (entry_id,))
            con.commit()
    except sqlite3.Error:
        log.warning("Failed to delete history entry %d", entry_id, exc_info=True)


def clear() -> None:
    try:
        with _conn() as con:
            con.execute("DELETE FROM history")
            con.commit()
    except sqlite3.Error:
        log.warning("Failed to clear history", exc_info=True)
