"""
Thumbnail generation — M4-04.

Resizes to target_width (default 400px), outputs JPEG bytes.
Saves to local disk cache (M4-08) immediately after generation.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import aiofiles

from app.utils.image import open_image, make_thumbnail

logger = logging.getLogger("photovault.pipeline.thumbnail")


def generate_thumbnail(
    data: bytes,
    target_width: int = 400,
    quality: int = 75,
) -> bytes:
    """
    Generate a JPEG thumbnail from raw image bytes.
    Returns JPEG bytes. Synchronous — wrap in run_in_executor for async contexts.
    """
    img = open_image(data)
    return make_thumbnail(img, target_width=target_width, quality=quality)


async def save_thumbnail_to_cache(
    thumb_bytes: bytes,
    photo_id: str,
    cache_thumbs_dir: Path,
) -> Path:
    """
    M4-08 — write thumbnail JPEG to  cache/thumbs/{id}.jpg  immediately after
    generation, before the GitHub commit completes.
    The cache is permanent (never evicted) so the grid view is warm on next load.
    """
    cache_thumbs_dir.mkdir(parents=True, exist_ok=True)
    dest = cache_thumbs_dir / f"{photo_id}.jpg"
    async with aiofiles.open(dest, "wb") as fh:
        await fh.write(thumb_bytes)
    logger.debug("Thumbnail cached: %s", dest)
    return dest
