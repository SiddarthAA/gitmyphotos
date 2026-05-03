"""
Repository routes — M2 + M3.

GET  /api/repo/current          — connected repo info (or null)
GET  /api/repo/list             — M2-01  list user's GitHub repos
POST /api/repo/create           — M2-02  create a new GitHub repo
POST /api/repo/connect          — M2-03/M2-04/M2-05  connect + persist to .env
GET  /api/repo/health           — M3-06  full health / initialisation status
POST /api/repo/scaffold         — M3-04  scaffold a fresh repo
POST /api/repo/repair           — M3-05  fill in missing pieces
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.services.repo_service import (
    check_repo_health,
    connect_repo,
    create_github_repo,
    get_current_connection,
    list_user_repos,
    repair_repo,
    scaffold_repo,
)

logger = logging.getLogger("photovault.routes.repo")

router = APIRouter(tags=["repo"])


# ── Request bodies ─────────────────────────────────────────────────────────────

class ConnectRequest(BaseModel):
    owner: str
    name: str
    branch: str = "main"


class CreateRequest(BaseModel):
    name: str
    private: bool = True
    description: str = "Photo storage managed by PhotoVault"
    branch: str = "main"


# ── GET /api/repo/current ─────────────────────────────────────────────────────

@router.get("/repo/current")
async def get_current_repo():
    """Return the currently connected repo, or null if none is set."""
    conn = get_current_connection()
    if conn is None:
        return {"connected": False, "owner": None, "name": None, "branch": None}
    return {"connected": True, **conn}


# ── GET /api/repo/list — M2-01 ────────────────────────────────────────────────

@router.get("/repo/list")
async def list_repos():
    """
    M2-01 — list all repos owned by the authenticated user.
    Returns name, visibility, last_updated, default_branch.
    """
    if not settings.github_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        repos = await list_user_repos()
    except Exception as exc:
        logger.error("list_repos failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))

    return {
        "repos": [
            {
                "name": r.name,
                "full_name": r.full_name,
                "private": r.private,
                "updated_at": r.updated_at,
                "default_branch": r.default_branch,
                "description": r.description,
            }
            for r in repos
        ]
    }


# ── POST /api/repo/create — M2-02 ────────────────────────────────────────────

@router.post("/repo/create")
async def create_repo(body: CreateRequest):
    """
    M2-02 — create a new private GitHub repo and auto-connect to it.
    The repo is auto-inited (empty README) so a valid HEAD always exists.
    """
    if not settings.github_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        info = await create_github_repo(
            name=body.name,
            private=body.private,
            description=body.description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.error("create_repo failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))

    # Auto-connect after creation using the user-requested branch
    owner = info.full_name.split("/")[0]
    connect_repo(owner=owner, repo=info.name, branch=body.branch)

    return {
        "name": info.name,
        "full_name": info.full_name,
        "private": info.private,
        "default_branch": info.default_branch,
        "connected": True,
    }


# ── POST /api/repo/connect — M2-03 / M2-04 / M2-05 ──────────────────────────

@router.post("/repo/connect")
async def connect_to_repo(body: ConnectRequest):
    """
    M2-03/M2-04/M2-05 — connect to an existing repo.
    Persists GITHUB_OWNER, GITHUB_REPO, GITHUB_BRANCH to data/.env.
    """
    if not settings.github_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    connect_repo(owner=body.owner, repo=body.name, branch=body.branch)

    return {
        "connected": True,
        "owner": body.owner,
        "name": body.name,
        "branch": body.branch,
    }


# ── POST /api/repo/disconnect ─────────────────────────────────────────────────

@router.post("/repo/disconnect")
async def disconnect_repo():
    """Disconnect the current repo — clears owner/repo/branch from .env."""
    from app.config import clear_env_key
    clear_env_key("GITHUB_OWNER")
    clear_env_key("GITHUB_REPO")
    clear_env_key("GITHUB_BRANCH")
    logger.info("Disconnected from repo")
    return {"status": "disconnected"}


# ── GET /api/repo/health — M3-06 ─────────────────────────────────────────────

@router.get("/repo/health")
async def repo_health():
    """
    M3-06 — full repo state:
      yml, manifest, folders (thumbs/originals/meta), photo_count, initialized
    """
    if not settings.repo_is_connected:
        raise HTTPException(status_code=400, detail="No repo connected")

    try:
        health = await check_repo_health(
            owner=settings.github_owner,
            repo=settings.github_repo,
            branch=settings.github_branch,
        )
    except Exception as exc:
        logger.error("repo_health failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))

    return health.to_dict()


# ── POST /api/repo/scaffold — M3-04 ──────────────────────────────────────────

@router.post("/repo/scaffold")
async def scaffold():
    """
    M3-04 — one atomic commit that fully initialises the connected repo.
    Safe to call on a brand-new or empty repo.
    """
    if not settings.repo_is_connected:
        raise HTTPException(status_code=400, detail="No repo connected")

    try:
        commit_sha = await scaffold_repo(
            owner=settings.github_owner,
            repo=settings.github_repo,
            branch=settings.github_branch,
        )
    except Exception as exc:
        logger.error("scaffold failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))

    return {"status": "scaffolded", "commit_sha": commit_sha}


# ── POST /api/repo/repair — M3-05 ────────────────────────────────────────────

@router.post("/repo/repair")
async def repair():
    """
    M3-05 — fill in any missing files/folders in the connected repo.
    No-ops if the repo is already fully initialised.
    """
    if not settings.repo_is_connected:
        raise HTTPException(status_code=400, detail="No repo connected")

    try:
        result = await repair_repo(
            owner=settings.github_owner,
            repo=settings.github_repo,
            branch=settings.github_branch,
        )
    except Exception as exc:
        logger.error("repair failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))

    if result == "already_healthy":
        return {"status": "already_healthy"}
    return {"status": "repaired", "commit_sha": result}
