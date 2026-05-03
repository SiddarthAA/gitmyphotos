"""
Read / write single files in a GitHub repository via the Contents API.

Used for:
  - Fetching .photovault.yml (plain YAML text)
  - Fetching manifest.json (JSON text)
  - Quick existence checks

For WRITES, always use commit.py (Git Tree API) to maintain the invariant
that every write is part of an atomic commit. This module is read-only.
"""

from __future__ import annotations

import base64
import logging
from typing import Optional

from app.github.client import get_http_client

logger = logging.getLogger("photovault.github.files")


async def read_file_text(
    owner: str, repo: str, path: str, branch: str = "main"
) -> Optional[str]:
    """
    Fetch a file's decoded text content via the Contents API.
    Returns None if the file does not exist (404).
    Raises on other errors.
    """
    async with get_http_client() as client:
        resp = await client.get(
            f"/repos/{owner}/{repo}/contents/{path}",
            params={"ref": branch},
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()

    data = resp.json()
    raw: str = data.get("content", "")
    # GitHub returns base64-encoded content with newlines
    decoded = base64.b64decode(raw.replace("\n", "")).decode("utf-8")
    return decoded


async def file_exists(
    owner: str, repo: str, path: str, branch: str = "main"
) -> bool:
    """Return True if the given path exists in the repo."""
    async with get_http_client() as client:
        resp = await client.get(
            f"/repos/{owner}/{repo}/contents/{path}",
            params={"ref": branch},
        )
        return resp.status_code == 200


async def get_file_sha(
    owner: str, repo: str, path: str, branch: str = "main"
) -> Optional[str]:
    """
    Return the blob SHA of an existing file (needed for Contents API updates).
    Returns None if the file does not exist.
    """
    async with get_http_client() as client:
        resp = await client.get(
            f"/repos/{owner}/{repo}/contents/{path}",
            params={"ref": branch},
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
    return resp.json().get("sha")
