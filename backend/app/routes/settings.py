"""
Settings routes — M6-05 + M7 stub.

GET  /api/settings           — repo settings from .photovault.yml (or defaults)
PATCH /api/settings          — M7 stub (not implemented yet)
GET  /api/cache/stats        — M6-05: cache directory sizes for the frontend
"""
from __future__ import annotations

import logging

from fastapi import APIRouter

from app.config import settings
from app.services.cache_service import get_cache_stats

logger = logging.getLogger("photovault.routes.settings")

router = APIRouter(tags=["settings"])


@router.get("/settings")
async def get_settings():
    """
    Return the current repo settings from .photovault.yml
    (preview_width, thumb_width, batch_delay, etc.).
    Returns defaults when no repo is connected or yml is missing.
    """
    if not settings.repo_is_connected:
        from app.models.config import RepoSettings
        return RepoSettings().model_dump()

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
            return cfg.settings.model_dump()
    except Exception as exc:
        logger.warning("Could not load .photovault.yml: %s", exc)

    from app.models.config import RepoSettings
    return RepoSettings().model_dump()


@router.patch("/settings")
async def update_settings():
    """M7 stub — editing repo settings via the UI."""
    return {"status": "not_implemented"}


# ── M6-05: Cache stats ────────────────────────────────────────────────────────


@router.get("/cache/stats")
async def get_cache_stats_route():
    """
    M6-05: Return disk cache sizes so the frontend can display storage usage.

    Response shape:
    {
      "thumbs":   { "files": int, "bytes": int, "mb": float },
      "previews": { "files": int, "bytes": int, "mb": float },
      "max_preview_gb": float
    }
    """
    return get_cache_stats()
