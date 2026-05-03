"""
Git Blob API helpers — M6-04.

create_blob()              POST /git/blobs — upload binary content, get SHA back
download_blob_by_sha()     GET  /git/blobs/{sha} — download raw bytes by SHA

Using the Blob API instead of the Contents API gives us:
  • No 1 MB inline limit  (Contents API fails for large originals)
  • No path-resolution step — the SHA is the address, period
  • Consistent performance for any file size
"""

from __future__ import annotations

import logging
from typing import Optional

from app.github.client import get_http_client

logger = logging.getLogger("photovault.github.blobs")


async def create_blob(owner: str, repo: str, content_b64: str) -> str:
    """
    POST /repos/{owner}/{repo}/git/blobs

    Upload base64-encoded binary content and return the blob SHA.
    The SHA is stable — identical content always produces the same SHA.
    """
    async with get_http_client() as client:
        resp = await client.post(
            f"/repos/{owner}/{repo}/git/blobs",
            json={"content": content_b64, "encoding": "base64"},
        )
        resp.raise_for_status()
        sha: str = resp.json()["sha"]
        logger.debug("Created blob %s", sha[:8])
        return sha


async def download_blob_by_sha(
    owner: str,
    repo: str,
    sha: str,
) -> Optional[bytes]:
    """
    GET /repos/{owner}/{repo}/git/blobs/{sha}

    Download raw blob bytes using the blob SHA.
    Uses Accept: application/vnd.github.raw so GitHub streams the raw content
    with no base64 wrapper and no file-size limit.

    Returns None if the blob doesn't exist (404).
    """
    async with get_http_client() as client:
        resp = await client.get(
            f"/repos/{owner}/{repo}/git/blobs/{sha}",
            headers={"Accept": "application/vnd.github.raw"},
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.content
