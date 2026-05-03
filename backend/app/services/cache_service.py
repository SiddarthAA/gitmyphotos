"""
Disk cache service — read/write/evict.

Cache layout (all under settings.cache_dir):
  thumbs/{id}.jpg       — permanent, never evicted
  previews/{id}.jpg     — LRU evicted when total exceeds CACHE_MAX_PREVIEW_GB
  manifest.json         — 5 min TTL copy of GitHub manifest.json

This module owns the physical I/O. Higher-level concerns (TTL, LRU) are
enforced here, not in the callers.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Optional

import aiofiles

from app.config import settings

logger = logging.getLogger("photovault.cache")

MANIFEST_TTL_SECONDS = 300   # 5 minutes


# ── M6-05: Cache statistics ───────────────────────────────────────────────────

def get_cache_stats() -> dict:
    """
    Return sizes and counts for both cache directories.
    Called on startup (logged) and by GET /api/cache/stats.
    """
    def _dir_stats(path: Path) -> dict:
        if not path.exists():
            return {"files": 0, "bytes": 0, "mb": 0.0}
        files = list(path.glob("*.jpg"))
        total_bytes = sum(f.stat().st_size for f in files)
        return {
            "files": len(files),
            "bytes": total_bytes,
            "mb": round(total_bytes / (1024 ** 2), 2),
        }

    return {
        "thumbs": _dir_stats(settings.cache_thumbs_dir),
        "previews": _dir_stats(settings.cache_previews_dir),
        "max_preview_gb": settings.cache_max_preview_gb,
    }


# ── Thumbnail cache (permanent) ───────────────────────────────────────────────

async def get_cached_thumb(photo_id: str) -> Optional[bytes]:
    path = settings.cache_thumbs_dir / f"{photo_id}.jpg"
    return await _read_file(path)


async def save_cached_thumb(photo_id: str, data: bytes) -> None:
    path = settings.cache_thumbs_dir / f"{photo_id}.jpg"
    await _write_file(path, data)


def thumb_cache_path(photo_id: str) -> Path:
    return settings.cache_thumbs_dir / f"{photo_id}.jpg"


# ── Preview cache (LRU evicted) ───────────────────────────────────────────────

async def get_cached_preview(photo_id: str) -> Optional[bytes]:
    path = settings.cache_previews_dir / f"{photo_id}.jpg"
    if not path.exists():
        return None
    # Touch atime so LRU can use it
    path.touch()
    return await _read_file(path)


async def save_cached_preview(photo_id: str, data: bytes, max_preview_gb: float | None = None) -> None:
    await _write_file(settings.cache_previews_dir / f"{photo_id}.jpg", data)
    await _maybe_evict_previews(max_preview_gb)


def preview_cache_path(photo_id: str) -> Path:
    return settings.cache_previews_dir / f"{photo_id}.jpg"


async def _maybe_evict_previews(max_preview_gb: float | None = None) -> None:
    """Evict oldest previews (by atime) until total size is within the limit.

    max_preview_gb: override from .photovault.yml settings block (M6-06).
    Falls back to settings.cache_max_preview_gb (from .env / default 2.0 GB).
    """
    previews_dir = settings.cache_previews_dir
    effective_gb = max_preview_gb if max_preview_gb is not None else settings.cache_max_preview_gb
    max_bytes = int(effective_gb * 1024 ** 3)

    files = list(previews_dir.glob("*.jpg"))
    total = sum(f.stat().st_size for f in files)

    if total <= max_bytes:
        return

    # Sort by last access time ascending (oldest first)
    files.sort(key=lambda f: f.stat().st_atime)
    for f in files:
        if total <= max_bytes:
            break
        size = f.stat().st_size
        try:
            f.unlink()
            total -= size
            logger.debug("Evicted preview cache: %s", f.name)
        except OSError:
            pass


# ── Manifest cache (5 min TTL) ────────────────────────────────────────────────

def get_manifest_cache() -> Optional[bytes]:
    """Return raw manifest bytes if the cached file is fresh, else None."""
    path = settings.manifest_cache_path
    if not path.exists():
        return None
    age = time.time() - path.stat().st_mtime
    if age > MANIFEST_TTL_SECONDS:
        logger.debug("Manifest cache expired (age %.0fs)", age)
        return None
    try:
        return path.read_bytes()
    except OSError:
        return None


def save_manifest_cache(data: bytes) -> None:
    """Write manifest bytes to disk cache and update mtime."""
    path = settings.manifest_cache_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    logger.debug("Manifest cache written (%d bytes)", len(data))


def invalidate_manifest_cache() -> None:
    """Delete the cached manifest so the next request fetches from GitHub."""
    path = settings.manifest_cache_path
    if path.exists():
        path.unlink()
        logger.debug("Manifest cache invalidated")


# ── I/O helpers ───────────────────────────────────────────────────────────────

async def _read_file(path: Path) -> Optional[bytes]:
    if not path.exists():
        return None
    try:
        async with aiofiles.open(path, "rb") as fh:
            return await fh.read()
    except OSError:
        return None


async def _write_file(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(path, "wb") as fh:
        await fh.write(data)
