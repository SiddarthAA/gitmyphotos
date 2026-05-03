"""
Repository service — M2 + M3.

M2: List repos, create repo, connect repo, persist config to .env
M3: Health check, scaffold fresh repo, partial repair
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import httpx

from app.config import settings, write_env_key
from app.github.client import get_http_client
from app.github.commit import CommitFile, commit_files
from app.github.files import file_exists, read_file_text
from app.github.tree import get_root_tree
from app.models.config import PhotovaultConfig
from app.models.manifest import Manifest
from app.pipeline.readme import generate_readme

logger = logging.getLogger("photovault.repo")

GITHUB_API = "https://api.github.com"

# ── Data classes returned to routes ───────────────────────────────────────────


@dataclass
class RepoInfo:
    name: str
    full_name: str
    private: bool
    updated_at: str
    default_branch: str
    description: Optional[str]


@dataclass
class RepoHealth:
    yml: bool
    manifest: bool
    folders_thumbs: bool
    folders_originals: bool
    folders_meta: bool
    photo_count: int

    @property
    def folders_ok(self) -> bool:
        return self.folders_thumbs and self.folders_originals and self.folders_meta

    @property
    def initialized(self) -> bool:
        return self.yml and self.manifest and self.folders_ok

    def to_dict(self) -> dict:
        return {
            "connected": True,
            "yml": self.yml,
            "manifest": self.manifest,
            "folders": self.folders_ok,
            "photo_count": self.photo_count,
            "last_upload": None,
            "total_size_mb": None,
            "initialized": self.initialized,
        }


# ── M2-01: List repos ─────────────────────────────────────────────────────────


async def list_user_repos() -> list[RepoInfo]:
    """
    Fetch all repos owned by the authenticated user.
    Pages through up to 200 results (2 pages × 100).
    Returns sorted by updated_at descending.
    """
    repos: list[RepoInfo] = []

    async with get_http_client() as client:
        for page in range(1, 3):  # pages 1 and 2
            resp = await client.get(
                "/user/repos",
                params={
                    "type": "owner",
                    "sort": "updated",
                    "direction": "desc",
                    "per_page": 100,
                    "page": page,
                    "affiliation": "owner",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            if not data:
                break

            for r in data:
                repos.append(
                    RepoInfo(
                        name=r["name"],
                        full_name=r["full_name"],
                        private=r["private"],
                        updated_at=r.get("updated_at", ""),
                        default_branch=r.get("default_branch", "main"),
                        description=r.get("description"),
                    )
                )

    return repos


# ── M2-02: Create new repo ────────────────────────────────────────────────────


async def create_github_repo(
    name: str,
    private: bool = True,
    description: str = "Photo storage managed by PhotoVault",
) -> RepoInfo:
    """
    Create a new GitHub repository under the authenticated user.
    Defaults to private. Auto-inits with an empty README (ensures a HEAD exists).
    """
    async with get_http_client() as client:
        resp = await client.post(
            "/user/repos",
            json={
                "name": name,
                "private": private,
                "description": description,
                "auto_init": True,  # creates initial commit so branch HEAD exists
            },
        )
        if resp.status_code == 422:
            errors = resp.json().get("errors", [])
            raise ValueError(f"Cannot create repo: {errors}")
        resp.raise_for_status()
        r = resp.json()

    return RepoInfo(
        name=r["name"],
        full_name=r["full_name"],
        private=r["private"],
        updated_at=r.get("updated_at", ""),
        default_branch=r.get("default_branch", "main"),
        description=r.get("description"),
    )


# ── M2-03 / M2-04 / M2-05: Connect repo ──────────────────────────────────────


def connect_repo(owner: str, repo: str, branch: str = "main") -> None:
    """
    Persist owner/repo/branch to data/.env.
    Config survives container restarts via volume mount.
    """
    write_env_key("GITHUB_OWNER", owner)
    write_env_key("GITHUB_REPO", repo)
    write_env_key("GITHUB_BRANCH", branch)
    logger.info("Connected to %s/%s@%s", owner, repo, branch)


def get_current_connection() -> Optional[dict]:
    """Return the currently connected repo info, or None if not connected."""
    if not settings.repo_is_connected:
        return None
    return {
        "owner": settings.github_owner,
        "name": settings.github_repo,
        "branch": settings.github_branch,
    }


# ── M3-01 / M3-02 / M3-03 / M3-06: Health check ─────────────────────────────


async def check_repo_health(
    owner: str, repo: str, branch: str
) -> RepoHealth:
    """
    M3-06 — full repo state inspection:
      M3-01  check .photovault.yml
      M3-02  check thumbs/ originals/ meta/ folders
      M3-03  check manifest.json (+ schema version)
    """
    # Fetch root tree once — avoids 3 separate API calls for folder checks
    root_entries = await get_root_tree(owner, repo, branch)
    root_names = {e["path"] for e in root_entries}

    yml_exists = ".photovault.yml" in root_names
    manifest_exists = "manifest.json" in root_names
    thumbs_exists = "thumbs" in root_names
    originals_exists = "originals" in root_names
    meta_exists = "meta" in root_names

    # Get photo count if manifest is present
    photo_count = 0
    if manifest_exists:
        try:
            raw = await read_file_text(owner, repo, "manifest.json", branch)
            if raw:
                data = json.loads(raw)
                photo_count = data.get("total_photos", len(data.get("photos", [])))
        except Exception as exc:
            logger.warning("Could not parse manifest.json: %s", exc)

    return RepoHealth(
        yml=yml_exists,
        manifest=manifest_exists,
        folders_thumbs=thumbs_exists,
        folders_originals=originals_exists,
        folders_meta=meta_exists,
        photo_count=photo_count,
    )


# ── M3-04: Scaffold fresh repo ────────────────────────────────────────────────


async def scaffold_repo(owner: str, repo: str, branch: str) -> str:
    """
    M3-04 — initialise an empty (or brand-new) repo with the full PhotoVault
    directory structure in ONE atomic commit.

    Creates:
      thumbs/.gitkeep
      originals/.gitkeep
      meta/.gitkeep
      manifest.json
      .photovault.yml
      README.md
    """
    logger.info("Scaffolding %s/%s@%s", owner, repo, branch)
    now = datetime.now(timezone.utc).isoformat()

    config = PhotovaultConfig.new(owner=owner, name=repo, branch=branch)
    manifest = Manifest.new()
    readme = generate_readme(
        owner=owner,
        repo_name=repo,
        total_photos=0,
        total_size_bytes=0,
        last_upload=None,
        created_at=now,
    )

    files = [
        CommitFile(path="thumbs/.gitkeep",     text=""),
        CommitFile(path="originals/.gitkeep",  text=""),
        CommitFile(path="meta/.gitkeep",        text=""),
        CommitFile(
            path="manifest.json",
            text=json.dumps(manifest.model_dump(), indent=2, ensure_ascii=False),
        ),
        CommitFile(path=".photovault.yml",      text=config.to_yaml()),
        CommitFile(path="README.md",            text=readme),
    ]

    commit_sha = await commit_files(
        owner=owner,
        repo=repo,
        branch=branch,
        message="chore: initialise PhotoVault repository structure",
        files=files,
    )
    logger.info("Scaffold commit: %s", commit_sha)
    return commit_sha


# ── M3-05: Partial repair ─────────────────────────────────────────────────────


async def repair_repo(owner: str, repo: str, branch: str) -> str:
    """
    M3-05 — re-create only the pieces that are missing.
    Reads current health and fills in the gaps with one commit.
    """
    health = await check_repo_health(owner, repo, branch)

    if health.initialized:
        logger.info("Repo %s/%s is healthy — nothing to repair", owner, repo)
        return "already_healthy"

    logger.info(
        "Repairing %s/%s: yml=%s manifest=%s thumbs=%s originals=%s meta=%s",
        owner, repo,
        health.yml, health.manifest,
        health.folders_thumbs, health.folders_originals, health.folders_meta,
    )

    now = datetime.now(timezone.utc).isoformat()
    files: list[CommitFile] = []

    if not health.folders_thumbs:
        files.append(CommitFile(path="thumbs/.gitkeep", text=""))
    if not health.folders_originals:
        files.append(CommitFile(path="originals/.gitkeep", text=""))
    if not health.folders_meta:
        files.append(CommitFile(path="meta/.gitkeep", text=""))

    if not health.manifest:
        manifest = Manifest.new()
        files.append(CommitFile(
            path="manifest.json",
            text=json.dumps(manifest.model_dump(), indent=2, ensure_ascii=False),
        ))

    if not health.yml:
        config = PhotovaultConfig.new(owner=owner, name=repo, branch=branch)
        files.append(CommitFile(path=".photovault.yml", text=config.to_yaml()))

    # Always regenerate README on repair
    readme = generate_readme(
        owner=owner,
        repo_name=repo,
        total_photos=health.photo_count,
        total_size_bytes=0,
        last_upload=None,
        created_at=now,
    )
    files.append(CommitFile(path="README.md", text=readme))

    commit_sha = await commit_files(
        owner=owner,
        repo=repo,
        branch=branch,
        message="chore: repair PhotoVault repository structure",
        files=files,
    )
    logger.info("Repair commit: %s", commit_sha)
    return commit_sha
