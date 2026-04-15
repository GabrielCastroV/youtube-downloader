"""Download queue backed by a ThreadPoolExecutor.

Each enqueued :class:`~yt_downloader.models.DownloadOptions` becomes a
:class:`QueueItem` with a lifecycle:
  pending → active → done / error / cancelled

The queue emits item-level status changes via an optional callback so the UI
can react without polling.
"""

from __future__ import annotations

import logging
import queue
import threading
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Literal
from uuid import uuid4

from yt_downloader.downloader import Downloader
from yt_downloader.exceptions import DownloadCancelled, DownloaderError
from yt_downloader.models import DownloadOptions, ProgressEvent

log = logging.getLogger(__name__)

ItemStatus = Literal["queued", "active", "done", "error", "cancelled"]

# Callback type: (item_id, status, event_or_None)
StatusCallback = Callable[["QueueItem", ItemStatus, ProgressEvent | None], None]


@dataclass
class QueueItem:
    id: str = field(default_factory=lambda: str(uuid4()))
    options: DownloadOptions = field(default_factory=DownloadOptions)  # type: ignore[arg-type]
    status: ItemStatus = "queued"
    # Mutable by the worker thread — accessed only under DownloadQueue._lock
    downloader: Downloader | None = field(default=None, repr=False)
    future: Future[None] | None = field(default=None, repr=False)
    event_queue: queue.Queue[ProgressEvent] = field(default_factory=queue.Queue, repr=False)

    @property
    def title(self) -> str:
        return self.options.url


class DownloadQueue:
    """Thread-safe download queue with cancel support."""

    def __init__(
        self,
        max_workers: int = 2,
        on_status: StatusCallback | None = None,
        ffmpeg_path: str = "",
    ) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="dl")
        self._on_status = on_status
        self._ffmpeg_path = ffmpeg_path
        self._lock = threading.Lock()
        self._items: list[QueueItem] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def enqueue(self, options: DownloadOptions) -> QueueItem:
        item = QueueItem(options=options)
        with self._lock:
            self._items.append(item)
        self._notify(item, "queued", None)
        item.future = self._executor.submit(self._run_item, item)
        return item

    def cancel(self, item_id: str) -> None:
        with self._lock:
            item = self._find(item_id)
        if item and item.downloader:
            item.downloader.cancel()

    def cancel_all(self) -> None:
        with self._lock:
            items = list(self._items)
        for it in items:
            if it.downloader:
                it.downloader.cancel()

    @property
    def items(self) -> list[QueueItem]:
        with self._lock:
            return list(self._items)

    def shutdown(self) -> None:
        self.cancel_all()
        self._executor.shutdown(wait=False)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _run_item(self, item: QueueItem) -> None:
        dl = Downloader(item.options, item.event_queue, self._ffmpeg_path)
        with self._lock:
            item.downloader = dl
            item.status = "active"
        self._notify(item, "active", None)
        try:
            dl.run()
            with self._lock:
                item.status = "done"
            self._notify(item, "done", None)
        except DownloadCancelled:
            with self._lock:
                item.status = "cancelled"
            self._notify(item, "cancelled", None)
        except DownloaderError as exc:
            with self._lock:
                item.status = "error"
            ev = ProgressEvent(stage="error", error_key=exc.user_key)
            self._notify(item, "error", ev)
        except Exception:
            log.exception("Unhandled exception in download worker for %s", item.id)
            with self._lock:
                item.status = "error"
            self._notify(item, "error", None)

    def _notify(self, item: QueueItem, status: ItemStatus, ev: ProgressEvent | None) -> None:
        if self._on_status:
            try:
                self._on_status(item, status, ev)
            except Exception:
                log.debug("Status callback raised", exc_info=True)

    def _find(self, item_id: str) -> QueueItem | None:
        return next((it for it in self._items if it.id == item_id), None)
