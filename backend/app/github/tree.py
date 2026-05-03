"""
Low-level GitHub Git Tree API helpers.

Used by commit.py to build atomic multi-file commits.
Also used by repo_service.py to inspect repository structure.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.github.client import get_http_client

logger = logging.getLogger("photovault.github.tree")


async def get_ref_sha(owner: str, repo: str, branch: str) -> Optional[str]:
    """
    GET /repos/{owner}/{repo}/git/ref/heads/{branch}
    Returns the HEAD commit SHA for a branch, or None if it doesn't exist.
    """
    async with get_http_client() as client:
        resp = await client.get(f"/repos/{owner}/{repo}/git/ref/heads/{branch}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()["object"]["sha"]


async def get_commit_tree_sha(owner: str, repo: str, commit_sha: str) -> str:
    """
    GET /repos/{owner}/{repo}/git/commits/{commit_sha}
    Returns the tree SHA for a given commit.
    """
    async with get_http_client() as client:
        resp = await client.get(f"/repos/{owner}/{repo}/git/commits/{commit_sha}")
        resp.raise_for_status()
        return resp.json()["tree"]["sha"]


async def get_root_tree(owner: str, repo: str, branch: str) -> list[dict]:
    """
    Return the list of top-level entries in the repository tree.
    Each entry: { "path": str, "type": "blob"|"tree", "sha": str, "size": int }
    """
    async with get_http_client() as client:
        resp = await client.get(
            f"/repos/{owner}/{repo}/git/trees/{branch}",
            params={"recursive": "0"},
        )
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        return resp.json().get("tree", [])


async def path_exists_in_root(
    owner: str, repo: str, branch: str, path: str
) -> bool:
    """Check whether a specific path (file or dir) exists at the repo root level."""
    tree = await get_root_tree(owner, repo, branch)
    return any(entry["path"] == path for entry in tree)


async def create_blob(
    owner: str, repo: str, content: str, encoding: str = "utf-8"
) -> str:
    """
    POST /repos/{owner}/{repo}/git/blobs
    Creates a blob and returns its SHA. Used for binary content.
    For text content in batch commits, inline `content` in the tree is simpler.
    """
    async with get_http_client() as client:
        resp = await client.post(
            f"/repos/{owner}/{repo}/git/blobs",
            json={"content": content, "encoding": encoding},
        )
        resp.raise_for_status()
        return resp.json()["sha"]


async def create_tree(
    owner: str,
    repo: str,
    tree_items: list[dict],
    base_tree_sha: Optional[str] = None,
) -> str:
    """
    POST /repos/{owner}/{repo}/git/trees
    Creates a new tree and returns its SHA.

    tree_items format:
      [ { "path": "foo/bar.txt", "mode": "100644", "type": "blob",
          "content": "..text.."  }    # OR "sha": "abc123" for blobs
      ]
    """
    payload: dict = {"tree": tree_items}
    if base_tree_sha:
        payload["base_tree"] = base_tree_sha

    async with get_http_client() as client:
        resp = await client.post(f"/repos/{owner}/{repo}/git/trees", json=payload)
        resp.raise_for_status()
        return resp.json()["sha"]


async def create_commit_object(
    owner: str,
    repo: str,
    message: str,
    tree_sha: str,
    parent_shas: list[str],
) -> str:
    """
    POST /repos/{owner}/{repo}/git/commits
    Creates a commit object and returns its SHA.
    """
    async with get_http_client() as client:
        resp = await client.post(
            f"/repos/{owner}/{repo}/git/commits",
            json={
                "message": message,
                "tree": tree_sha,
                "parents": parent_shas,
            },
        )
        resp.raise_for_status()
        return resp.json()["sha"]


async def update_ref(owner: str, repo: str, branch: str, commit_sha: str) -> None:
    """
    PATCH /repos/{owner}/{repo}/git/refs/heads/{branch}
    Moves the branch HEAD to the new commit.
    """
    async with get_http_client() as client:
        resp = await client.patch(
            f"/repos/{owner}/{repo}/git/refs/heads/{branch}",
            json={"sha": commit_sha, "force": False},
        )
        resp.raise_for_status()


async def create_ref(owner: str, repo: str, branch: str, commit_sha: str) -> None:
    """
    POST /repos/{owner}/{repo}/git/refs
    Creates a new branch ref (used when the branch doesn't exist yet).
    """
    async with get_http_client() as client:
        resp = await client.post(
            f"/repos/{owner}/{repo}/git/refs",
            json={"ref": f"refs/heads/{branch}", "sha": commit_sha},
        )
        resp.raise_for_status()
