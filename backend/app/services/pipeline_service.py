"""
Upload pipeline orchestrator — M4-07 + M4-08.

process_upload()   — called by POST /api/upload for each uploaded file
_commit_batch()    — FlushCallback wired into PhotoBatcher; pushes one git commit
shutdown()         — called from main.py lifespan to flush remaining items

Pipeline steps (per photo):
  1. ingest      — MIME check, size check
  2. exif        — extract EXIF without raising
  3. filename    — deterministic safe name from captured_at
  4. image       — open PIL image (with EXIF auto-rotation)
  5. thumbnail   — generate JPEG thumb bytes
  6. save thumb  — write thumb to disk cache immediately (M4-08)
  7. meta        — build PhotoMeta (dimensions, EXIF, GPS, paths)
  8. batch       — queue BatchItem; batcher fires commit after delay

Commit steps (per batch):
  1. append_to_manifest — read current manifest.json, add new entries
  2. build_updated_yml  — update .photovault.yml stats
  3. generate_readme    — rebuild README.md
  4. commit_files       — one atomic Tree API commit
  5. invalidate cache   — manifest disk cache busted
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import UploadFile

from app.config import settings
from app.github.blobs import create_blob
from app.github.commit import CommitFile, commit_files
from app.models.manifest import GPS, ManifestPhoto
from app.pipeline.batcher import BatchItem, FlushCallback, PhotoBatcher
from app.pipeline.exif import extract as extract_exif
from app.pipeline.ingest import ingest
from app.pipeline.meta import build_meta
from app.pipeline.readme import generate_readme
from app.pipeline.thumbnail import generate_thumbnail, save_thumbnail_to_cache
from app.services.manifest_service import (
    append_to_manifest,
    build_updated_yml,
    invalidate,
)
from app.utils.filename import make_filename
from app.utils.image import get_dimensions, open_image
from app.utils.paths import meta_path, original_path, thumb_path

logger = logging.getLogger("photovault.pipeline")

# ── Flush callback ─────────────────────────────────────────────────────────────


async def _commit_batch(items: list[BatchItem]) -> None:
    """
    Execute one atomic GitHub commit for a batch of processed photos.

    Steps (M6-04: blob-SHA approach):
      1. Pre-create blobs for original + thumb in parallel — get SHAs
      2. Back-fill SHAs onto manifest entries (no chicken-and-egg)
      3. Append updated entries to manifest.json
      4. Update .photovault.yml stats + regenerate README.md
      5. commit_files() using blob_sha= (no re-upload) — single Tree API commit
      6. Invalidate manifest disk cache
    """
    if not items:
        return

    if not settings.repo_is_connected:
        logger.error("Batch flush: no repo connected — dropping %d items", len(items))
        return

    logger.info("Committing batch of %d photo(s) to GitHub…", len(items))

    now = datetime.now(timezone.utc)

    # ── Step 1: Pre-create blobs in parallel (M6-04) ─────────────────────────
    async def _upload_item_blobs(item: BatchItem) -> None:
        """Create original + thumb blobs and store SHAs on item and manifest_entry."""
        orig_b64  = base64.b64encode(item.original_bytes).decode()
        thumb_b64 = base64.b64encode(item.thumb_bytes).decode()

        orig_sha, thumb_sha = await asyncio.gather(
            create_blob(settings.github_owner, settings.github_repo, orig_b64),
            create_blob(settings.github_owner, settings.github_repo, thumb_b64),
        )

        item.original_blob_sha = orig_sha
        item.thumb_blob_sha    = thumb_sha
        # Back-fill SHAs onto the manifest entry so they are saved to manifest.json
        item.manifest_entry.original_sha = orig_sha
        item.manifest_entry.thumb_sha    = thumb_sha

    await asyncio.gather(*[_upload_item_blobs(item) for item in items])

    # ── Step 2: Append to manifest (entries now carry SHAs) ──────────────────
    manifest_entries = [item.manifest_entry for item in items]
    updated_manifest, manifest_json = await append_to_manifest(manifest_entries)

    # ── Step 3: Update yml + README ───────────────────────────────────────
    try:
        updated_yml = await build_updated_yml(updated_manifest, last_upload=now)
    except Exception as exc:
        logger.warning("Could not build updated yml: %s", exc)
        updated_yml = None

    readme_md = generate_readme(
        owner=settings.github_owner,
        repo_name=settings.github_repo,
        total_photos=updated_manifest.total_photos,
        total_size_bytes=updated_manifest.total_size_bytes,
        last_upload=updated_manifest.last_updated,
    )

    # ── Step 4: Build CommitFile list ───────────────────────────────────────
    commit_file_list: list[CommitFile] = []

    for item in items:
        # Use the pre-created blob SHAs — no bytes re-uploaded in this step
        commit_file_list.append(CommitFile(
            path=item.repo_original_path,
            blob_sha=item.original_blob_sha,
        ))
        commit_file_list.append(CommitFile(
            path=item.repo_thumb_path,
            blob_sha=item.thumb_blob_sha,
        ))
        commit_file_list.append(CommitFile(
            path=item.repo_meta_path,
            text=item.meta_json,
        ))

    commit_file_list.append(CommitFile(path="manifest.json", text=manifest_json))
    commit_file_list.append(CommitFile(path="README.md", text=readme_md))
    if updated_yml is not None:
        commit_file_list.append(CommitFile(path=".photovault.yml", text=updated_yml))

    # ── Step 5: Single Tree API commit ──────────────────────────────────────
    commit_sha = await commit_files(
        owner=settings.github_owner,
        repo=settings.github_repo,
        branch=settings.github_branch,
        message=f"PhotoVault: add {len(items)} photo(s)",
        files=commit_file_list,
    )

    logger.info(
        "Committed %d photo(s) as %s", len(items), commit_sha[:7] if commit_sha else "?"
    )

    # ── Step 6: Bust manifest cache ────────────────────────────────────────
    invalidate()


# ── Module-level batcher (singleton) ──────────────────────────────────────────

batcher = PhotoBatcher(flush_callback=_commit_batch)


# ── Public API ─────────────────────────────────────────────────────────────────


async def process_upload(upload: UploadFile) -> str:
    """
    Process a single uploaded file end-to-end and add it to the pending batch.
    Returns the photo_id so the caller can return it immediately to the client.

    Raises HTTPException (via ingest) on validation failure.
    """
    if not settings.repo_is_connected:
        raise ValueError("No repo connected — cannot upload photos")

    # 1. Ingest (validate MIME, size, read bytes)
    ingested = await ingest(upload, max_size_mb=100)

    # 2. Extract EXIF (never raises)
    exif = extract_exif(ingested.data)

    # 3. Make deterministic filename
    captured_at: Optional[datetime] = None
    if exif.captured_at:
        try:
            captured_at = datetime.fromisoformat(exif.captured_at)
        except ValueError:
            pass

    filename_base = make_filename(captured_at)
    uploaded_at   = datetime.now(timezone.utc)

    # 4. Open image (EXIF auto-rotate)
    img = open_image(ingested.data)
    width, height = get_dimensions(img)

    # 5. Generate thumbnail bytes
    thumb_bytes = generate_thumbnail(ingested.data, target_width=400, quality=75)

    # 6. Save thumbnail to disk cache immediately (M4-08)
    await save_thumbnail_to_cache(
        thumb_bytes=thumb_bytes,
        photo_id=filename_base,
        cache_thumbs_dir=settings.cache_thumbs_dir,
    )

    # 7. Build PhotoMeta (build_meta requires a non-None captured_at)
    resolved_captured_at = captured_at or uploaded_at
    meta = build_meta(
        photo_id=filename_base,
        original_filename=ingested.original_filename,
        mime_type=ingested.mime_type,
        size_bytes=ingested.size_bytes,
        width=width,
        height=height,
        exif=exif,
        captured_at=resolved_captured_at,
        uploaded_at=uploaded_at,
        filename_base=filename_base,
    )

    # Repo-relative paths
    dt = resolved_captured_at
    ext = ingested.ext
    r_thumb    = thumb_path(filename_base, dt)
    r_original = original_path(filename_base, dt, ext)
    r_meta     = meta_path(filename_base, dt)

    # 8. Build manifest entry
    gps = None
    if exif.gps_lat is not None and exif.gps_lng is not None:
        gps = GPS(
            lat=exif.gps_lat,
            lng=exif.gps_lng,
            altitude=exif.gps_altitude,
        )

    camera_parts = [p for p in [exif.camera_make, exif.camera_model] if p]
    camera_str = " ".join(camera_parts) or None

    manifest_entry = ManifestPhoto(
        id=filename_base,
        captured_at=exif.captured_at or uploaded_at.isoformat(),
        uploaded_at=uploaded_at.isoformat(),
        original_filename=ingested.original_filename,
        mime_type=ingested.mime_type,
        size_bytes=ingested.size_bytes,
        thumb_path=r_thumb,
        original_path=r_original,
        meta_path=r_meta,
        width=width,
        height=height,
        camera=camera_str,
        gps=gps,
    )

    # 9. Build BatchItem + enqueue
    batch_item = BatchItem(
        photo_id=filename_base,
        thumb_bytes=thumb_bytes,
        original_bytes=ingested.data,
        meta_json=json.dumps(meta.model_dump(), indent=2, ensure_ascii=False),
        repo_thumb_path=r_thumb,
        repo_original_path=r_original,
        repo_meta_path=r_meta,
        manifest_entry=manifest_entry,
        size_bytes=ingested.size_bytes,
    )

    await batcher.add(batch_item)

    logger.info("Queued photo '%s' (%d bytes)", filename_base, ingested.size_bytes)
    return filename_base


async def shutdown() -> None:
    """Flush remaining batch items — called from FastAPI lifespan on shutdown."""
    logger.info("Pipeline shutdown: flushing remaining batch…")
    await batcher.flush_now()
