"""
Photo serving routes — M6.

GET /api/manifest              — return full manifest.json (cache-first, 5 min TTL)
GET /api/thumb/{id}            — 400 px JPEG thumbnail (disk cache permanent)     M6-01
GET /api/preview/{id}          — resized preview (disk cache, LRU-evicted)        M6-02
GET /api/original/{id}         — stream original from GitHub (never cached)       M6-03

M6-04: blob SHA resolution
  When a manifest photo has thumb_sha / original_sha we use the Git Blobs API
  (no path-lookup step, no 1 MB cap).  Legacy / repaired photos fall back to
  the Contents API path.

M6-06: LRU threshold
  Preview eviction limit is read from .photovault.yml settings.cache_max_preview_gb;
  falls back to settings.cache_max_preview_gb from .env.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.config import settings
from app.github.blobs import download_blob_by_sha
from app.github.client import get_http_client
from app.models.manifest import Manifest, ManifestPhoto
from app.services.cache_service import (
    get_cached_preview,
    get_cached_thumb,
    save_cached_preview,
    save_cached_thumb,
)
from app.services.manifest_service import fetch_manifest, get_manifest_json
from app.utils.image import make_thumbnail, open_image

logger = logging.getLogger("photovault.routes.photos")

router = APIRouter(tags=["photos"])


# ── Manifest ──────────────────────────────────────────────────────────────────


@router.get("/manifest")
async def get_manifest():
    """Return manifest.json. Served from 5-min disk cache when hot."""
    raw = await get_manifest_json()
    return Response(content=raw, media_type="application/json")


# ── M6-01: Thumbnails (permanent cache) ──────────────────────────────────────


@router.get("/thumb/{photo_id}")
async def get_thumb(photo_id: str):
    """
    M6-01: 400 px JPEG thumbnail.
    Permanent disk cache — never evicted.
    Cache miss: fetch from GitHub by SHA (M6-04) or path (legacy fallback).
    """
    cached = await get_cached_thumb(photo_id)
    if cached is not None:
        return Response(content=cached, media_type="image/jpeg",
                        headers={"X-Cache": "HIT"})

    photo = await _find_photo_in_manifest(photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")

    thumb_data = await _download_photo_bytes(photo, kind="thumb")
    if thumb_data is None:
        raise HTTPException(status_code=404, detail="Thumbnail not found in GitHub repo")

    await save_cached_thumb(photo_id, thumb_data)
    return Response(content=thumb_data, media_type="image/jpeg",
                    headers={"X-Cache": "MISS"})


# ── M6-02: Previews (LRU cache) ───────────────────────────────────────────


@router.get("/preview/{photo_id}")
async def get_preview(photo_id: str):
    """
    M6-02: Medium-resolution preview (default 1200 px wide).
    LRU-evicted disk cache — threshold from .photovault.yml (M6-06).
    Cache miss: fetch original, resize in-memory, cache, stream.
    """
    cached = await get_cached_preview(photo_id)
    if cached is not None:
        return Response(content=cached, media_type="image/jpeg",
                        headers={"X-Cache": "HIT"})

    photo = await _find_photo_in_manifest(photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")

    original_data = await _download_photo_bytes(photo, kind="original")
    if original_data is None:
        raise HTTPException(status_code=404, detail="Original not found in GitHub repo")

    # M6-06: read preview width + LRU limit from .photovault.yml when available
    preview_width, max_preview_gb = await _load_preview_settings()

    try:
        preview_bytes = make_thumbnail(
            open_image(original_data),
            target_width=preview_width,
            quality=82,
        )
    except Exception as exc:
        logger.warning("Preview generation failed for %s: %s", photo_id, exc)
        raise HTTPException(status_code=500, detail="Preview generation failed") from exc

    await save_cached_preview(photo_id, preview_bytes, max_preview_gb=max_preview_gb)
    return Response(content=preview_bytes, media_type="image/jpeg",
                    headers={"X-Cache": "MISS"})


# ── M6-03: Originals (never cached) ─────────────────────────────────────────


@router.get("/original/{photo_id}")
async def get_original(photo_id: str):
    """
    M6-03: Stream the original file directly from GitHub — never cached.
    Preserves original MIME type. Explicit download intent only.
    """
    photo = await _find_photo_in_manifest(photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")

    data = await _download_photo_bytes(photo, kind="original")
    if data is None:
        raise HTTPException(status_code=404, detail="File not found in GitHub repo")

    return Response(
        content=data,
        media_type=photo.mime_type,
        headers={"Content-Disposition": f'attachment; filename="{photo.original_filename}"'},
    )


# ── M6-04: SHA-aware download helpers ───────────────────────────────────────


async def _find_photo_in_manifest(photo_id: str) -> Optional[ManifestPhoto]:
    """Look up a ManifestPhoto entry, returning None on any error."""
    try:
        manifest = await fetch_manifest()
    except Exception:
        return None
    for p in manifest.photos:
        if p.id == photo_id:
            return p
    return None


async def _download_photo_bytes(photo: ManifestPhoto, kind: str) -> Optional[bytes]:
    """
    M6-04: Prefer direct SHA-based download from Git Blobs API.
    Falls back to path-based Contents API download for photos committed
    before M6 (no SHA stored) or after a repo repair.
    """
    if not settings.repo_is_connected:
        return None

    sha   = photo.thumb_sha    if kind == "thumb" else photo.original_sha
    path  = photo.thumb_path   if kind == "thumb" else photo.original_path

    if sha:
        # Fast path: no tree walk, no path resolution, no size limit
        data = await download_blob_by_sha(
            settings.github_owner,
            settings.github_repo,
            sha,
        )
        if data is not None:
            return data
        logger.warning(
            "Blob SHA %s not found for %s (kind=%s); falling back to path",
            sha[:8], photo.id, kind,
        )

    # Fallback: Contents API with raw Accept header (handles any file size)
    return await _download_by_path(path)


async def _download_by_path(repo_path: str) -> Optional[bytes]:
    """
    Download a file from the GitHub Contents API using Accept: application/vnd.github.raw.
    This returns raw bytes directly (no base64 wrapper) and works for any file size.
    Returns None on 404.
    """
    if not settings.repo_is_connected:
        return None

    rel_url = (
        f"/repos/{settings.github_owner}/{settings.github_repo}"
        f"/contents/{repo_path}"
    )

    async with get_http_client() as client:
        resp = await client.get(
            rel_url,
            params={"ref": settings.github_branch},
            headers={"Accept": "application/vnd.github.raw"},
        )

    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.content


# ── M6-06: Load preview settings from .photovault.yml ─────────────────────────


async def _load_preview_settings() -> tuple[int, Optional[float]]:
    """
    Return (preview_width, max_preview_gb) from .photovault.yml when available.
    Falls back to (1200, None) so cache_service uses settings.cache_max_preview_gb.
    """
    if not settings.repo_is_connected:
        return 1200, None
    try:
        from app.github.files import read_file_text
        from app.models.config import PhotovaultConfig
        raw = await read_file_text(
            owner=settings.github_owner,
            repo=settings.github_repo,
            path=".photovault.yml",
            branch=settings.github_branch,
        )
        if raw:
            cfg = PhotovaultConfig.from_yaml(raw)
            return cfg.settings.preview_width, cfg.settings.cache_max_preview_gb
    except Exception as exc:
        logger.debug("Could not read .photovault.yml for preview settings: %s", exc)
    return 1200, None
