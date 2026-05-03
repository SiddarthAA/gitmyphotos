"""
Manifest service — M5.

M5-01  fetch_manifest     — GET manifest.json from GitHub, cache with 5 min TTL
M5-02  append_to_manifest — read current manifest, append new entries, return
                            updated Manifest (caller includes it in git commit)
M5-03  invalidate         — wipe disk cache after every successful commit
M5-04  get_manifest_json  — serve cached bytes to /api/manifest (fast path)
M5-05  update_yml_stats   — update stats block in .photovault.yml (same commit)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from app.config import settings
from app.github.files import read_file_text
from app.models.config import PhotovaultConfig
from app.models.manifest import Manifest, ManifestPhoto
from app.services.cache_service import (
    get_manifest_cache,
    invalidate_manifest_cache,
    save_manifest_cache,
)

logger = logging.getLogger("photovault.manifest")


# ── M5-01: Fetch manifest (cache-first) ───────────────────────────────────────

async def fetch_manifest() -> Manifest:
    """
    Return the current manifest.  Cache-first with 5 min TTL.
    On cache miss, fetches from GitHub and refreshes the cache.
    """
    cached = get_manifest_cache()
    if cached is not None:
        logger.debug("Manifest served from disk cache")
        return Manifest.model_validate_json(cached)

    return await _fetch_from_github_and_cache()


async def _fetch_from_github_and_cache() -> Manifest:
    if not settings.repo_is_connected:
        raise RuntimeError("No repo connected — cannot fetch manifest")

    raw = await read_file_text(
        owner=settings.github_owner,
        repo=settings.github_repo,
        path="manifest.json",
        branch=settings.github_branch,
    )

    if raw is None:
        # Repo not scaffolded yet — return empty manifest without caching
        return Manifest.new()

    manifest = Manifest.model_validate_json(raw)
    save_manifest_cache(raw.encode())
    logger.info("Manifest fetched from GitHub (%d photos)", manifest.total_photos)
    return manifest


# ── M5-02: Append new photos ──────────────────────────────────────────────────

async def append_to_manifest(
    new_entries: list[ManifestPhoto],
) -> tuple[Manifest, str]:
    """
    M5-02 — read current manifest, append new entries, return:
      (updated_manifest, updated_json_string)

    The json string is what goes into the git commit. Never rewrites from scratch.
    """
    try:
        manifest = await fetch_manifest()
    except Exception:
        manifest = Manifest.new()

    for entry in new_entries:
        manifest.photos.append(entry)

    manifest.total_photos = len(manifest.photos)
    manifest.total_size_bytes = sum(p.size_bytes for p in manifest.photos)
    manifest.last_updated = datetime.now(timezone.utc).isoformat()

    updated_json = json.dumps(manifest.model_dump(), indent=2, ensure_ascii=False)
    return manifest, updated_json


# ── M5-03: Invalidate cache ────────────────────────────────────────────────────

def invalidate() -> None:
    """M5-03 — call after every successful GitHub commit."""
    invalidate_manifest_cache()


# ── M5-04: Serve manifest JSON to frontend ────────────────────────────────────

async def get_manifest_json() -> bytes:
    """
    M5-04 — return raw manifest JSON bytes.
    Hits the disk cache whenever possible; falls back to GitHub on miss.
    """
    cached = get_manifest_cache()
    if cached is not None:
        return cached

    manifest = await _fetch_from_github_and_cache()
    # Cache was populated inside _fetch; return bytes
    raw_bytes = get_manifest_cache()
    if raw_bytes:
        return raw_bytes
    # Fallback: serialise in-memory copy
    return json.dumps(manifest.model_dump(), indent=2, ensure_ascii=False).encode()


# ── M5-05: Update .photovault.yml stats ───────────────────────────────────────

async def build_updated_yml(manifest: Manifest, last_upload: datetime) -> str:
    """
    M5-05 — fetch current .photovault.yml, update the stats block,
    return the updated YAML string ready for the git commit.
    Gracefully creates a fresh config if the file is missing.
    """
    raw_yml: Optional[str] = None
    if settings.repo_is_connected:
        try:
            raw_yml = await read_file_text(
                owner=settings.github_owner,
                repo=settings.github_repo,
                path=".photovault.yml",
                branch=settings.github_branch,
            )
        except Exception as exc:
            logger.warning("Could not fetch .photovault.yml: %s", exc)

    if raw_yml:
        config = PhotovaultConfig.from_yaml(raw_yml)
    else:
        config = PhotovaultConfig.new(
            owner=settings.github_owner,
            name=settings.github_repo,
            branch=settings.github_branch,
        )

    config.stats.total_photos     = manifest.total_photos
    config.stats.total_size_bytes  = manifest.total_size_bytes
    config.stats.last_upload       = last_upload.isoformat()
    config.stats.last_sync         = datetime.now(timezone.utc).isoformat()

    return config.to_yaml()
