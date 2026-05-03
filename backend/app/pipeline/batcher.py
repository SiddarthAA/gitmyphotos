"""
Async batch queue — M4-06.

Collects fully-processed photo items for a configurable window (default 3 s),
then flushes them all as a single GitHub commit.

Rules:
  - Timer resets on every new item added.
  - Files > LARGE_FILE_THRESHOLD get an extended window
    (max of current delay and LARGE_FILE_EXTRA_SECONDS).
  - The flush callback is called with the full list of BatchItems.
  - A new batch begins immediately after flush.

Usage (in pipeline_service.py):
    batcher = PhotoBatcher(flush_callback=_commit_batch)
    await batcher.add(item)
"""

from __future__ import annotations

import asyncio
import base64
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Awaitable, Callable, Optional

from app.models.manifest import ManifestPhoto

logger = logging.getLogger("photovault.pipeline.batcher")

# ── Tunables ──────────────────────────────────────────────────────────────────

BATCH_DELAY_SECONDS: float = 3.0          # default window
LARGE_FILE_THRESHOLD: int  = 2 * 1024 * 1024  # 2 MB → extended window
LARGE_FILE_DELAY_SECONDS: float = 6.0     # window when any queued file is large

# ── Data types ────────────────────────────────────────────────────────────────


@dataclass
class BatchItem:
    """A single fully-processed photo ready to be committed to GitHub."""
    photo_id: str

    # Raw bytes for the git commit (thumb is also already on disk)
    thumb_bytes: bytes          # stored as blob in GitHub
    original_bytes: bytes       # stored as blob in GitHub
    meta_json: str              # JSON string for meta/{id}.json

    # Relative paths inside the GitHub repo
    repo_thumb_path: str        # thumbs/YYYY/MM/{id}.jpg
    repo_original_path: str     # originals/YYYY/MM/{id}.ext
    repo_meta_path: str         # meta/YYYY/MM/{id}.json

    # Pre-built manifest entry
    manifest_entry: ManifestPhoto

    size_bytes: int             # used to compute batch delay

    # M6-04: populated by pipeline_service after pre-creating blobs
    # allows commit_files to skip re-uploading and manifest to carry SHAs
    original_blob_sha: Optional[str] = None
    thumb_blob_sha: Optional[str] = None


FlushCallback = Callable[[list[BatchItem]], Awaitable[None]]


# ── Batcher ───────────────────────────────────────────────────────────────────


class PhotoBatcher:
    def __init__(self, flush_callback: FlushCallback) -> None:
        self._callback   = flush_callback
        self._queue:  list[BatchItem]          = []
        self._lock    = asyncio.Lock()
        self._timer:  Optional[asyncio.Task]   = None

    async def add(self, item: BatchItem) -> None:
        """Add a processed photo to the pending batch and reset the flush timer."""
        async with self._lock:
            self._queue.append(item)

            # Determine delay: use extended window if any queued item is large
            has_large = any(b.size_bytes > LARGE_FILE_THRESHOLD for b in self._queue)
            delay = LARGE_FILE_DELAY_SECONDS if has_large else BATCH_DELAY_SECONDS

            # Cancel any existing timer and restart
            if self._timer and not self._timer.done():
                self._timer.cancel()

            self._timer = asyncio.get_event_loop().create_task(
                self._delayed_flush(delay)
            )
            logger.debug(
                "Batch queued: %d item(s), flush in %.1fs", len(self._queue), delay
            )

    async def flush_now(self) -> None:
        """Immediately flush the queue (used for testing / shutdown)."""
        async with self._lock:
            if self._timer and not self._timer.done():
                self._timer.cancel()
            items = self._drain()

        if items:
            await self._safe_flush(items)

    # ── Private ───────────────────────────────────────────────────────────────

    async def _delayed_flush(self, delay: float) -> None:
        await asyncio.sleep(delay)
        async with self._lock:
            items = self._drain()
        if items:
            await self._safe_flush(items)

    def _drain(self) -> list[BatchItem]:
        items, self._queue = self._queue, []
        return items

    async def _safe_flush(self, items: list[BatchItem]) -> None:
        try:
            logger.info("Flushing batch of %d photo(s) to GitHub", len(items))
            await self._callback(items)
        except Exception:
            logger.exception("Batch flush failed — photos may not be committed")
