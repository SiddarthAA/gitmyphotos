"""
Atomic multi-file commit builder using the GitHub Git Tree API.

Every upload batch (and every scaffold operation) results in exactly ONE commit.
This module owns the full 6-step commit flow:

  1.  GET current HEAD commit SHA
  2.  GET current tree SHA from that commit
  3.  Build list of tree items (inline text content, or blob SHA for binary)
  4.  POST new tree
  5.  POST new commit object (parent = old HEAD)
  6.  PATCH branch ref → new commit

Usage:
    new_sha = await commit_files(
        owner="alice",
        repo="my-photos",
        branch="main",
        message="Add 3 photos",
        files=[
            CommitFile(path="manifest.json", text='{"version":"1",...}'),
            CommitFile(path="thumbs/2024/01/xyz.jpg", blob_sha="abc123"),
        ],
    )
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from app.github.tree import (
    get_ref_sha,
    get_commit_tree_sha,
    create_blob,
    create_tree,
    create_commit_object,
    update_ref,
    create_ref,
)

logger = logging.getLogger("photovault.github.commit")


@dataclass
class CommitFile:
    """
    Represents one file in a commit.

    For text files (JSON, YAML, Markdown):
        Set `text` — it will be inlined into the tree directly.

    For binary files (JPEG thumbnails, originals):
        Pass `blob_sha` — a pre-created blob SHA from create_blob().
        Or set `binary_content` (base64-encoded bytes) — this module will
        create the blob automatically.
    """

    path: str
    text: Optional[str] = None           # UTF-8 text content (inline)
    blob_sha: Optional[str] = None        # pre-created blob SHA
    binary_b64: Optional[str] = None      # base64 bytes → auto-create blob
    mode: str = "100644"                  # regular file


async def commit_files(
    owner: str,
    repo: str,
    branch: str,
    message: str,
    files: list[CommitFile],
) -> str:
    """
    Create an atomic commit with all provided files.
    Returns the new commit SHA.
    """
    if not files:
        raise ValueError("commit_files called with empty file list")

    # ── Step 1: Get the current HEAD ─────────────────────────────────────────
    head_sha = await get_ref_sha(owner, repo, branch)
    logger.debug("HEAD SHA for %s/%s@%s: %s", owner, repo, branch, head_sha)

    # ── Step 2: Get the current tree SHA ─────────────────────────────────────
    base_tree_sha: Optional[str] = None
    parent_shas: list[str] = []

    if head_sha:
        base_tree_sha = await get_commit_tree_sha(owner, repo, head_sha)
        parent_shas = [head_sha]

    # ── Step 3: Build tree items ──────────────────────────────────────────────
    tree_items: list[dict] = []

    for f in files:
        item: dict = {"path": f.path, "mode": f.mode, "type": "blob"}

        if f.blob_sha:
            item["sha"] = f.blob_sha

        elif f.binary_b64 is not None:
            # Auto-create a blob for binary content
            sha = await create_blob(owner, repo, f.binary_b64, encoding="base64")
            item["sha"] = sha

        elif f.text is not None:
            # Inline text — simplest path, no extra API call
            item["content"] = f.text

        else:
            raise ValueError(f"CommitFile {f.path!r} has no content or sha")

        tree_items.append(item)

    # ── Step 4: Create the new tree ───────────────────────────────────────────
    new_tree_sha = await create_tree(owner, repo, tree_items, base_tree_sha)
    logger.debug("New tree SHA: %s", new_tree_sha)

    # ── Step 5: Create the commit object ─────────────────────────────────────
    new_commit_sha = await create_commit_object(
        owner, repo, message, new_tree_sha, parent_shas
    )
    logger.debug("New commit SHA: %s", new_commit_sha)

    # ── Step 6: Update (or create) the branch ref ────────────────────────────
    if head_sha:
        await update_ref(owner, repo, branch, new_commit_sha)
    else:
        await create_ref(owner, repo, branch, new_commit_sha)

    logger.info(
        "Committed %d file(s) to %s/%s@%s — %s",
        len(files),
        owner,
        repo,
        branch,
        new_commit_sha[:8],
    )
    return new_commit_sha
