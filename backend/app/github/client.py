"""
Thin wrapper around PyGithub / httpx for GitHub API access.

Always initialised from settings.github_token — call get_client() after
the OAuth flow has written the token.
"""

from __future__ import annotations

from typing import Optional

import httpx
from github import Github, GithubException

import app.config as _cfg

# Base URL for direct REST calls (used alongside PyGithub)
GITHUB_API = "https://api.github.com"


def get_client() -> Github:
    """Return an authenticated PyGithub client."""
    if not _cfg.settings.github_token:
        raise RuntimeError("GitHub token not set — complete OAuth first")
    return Github(_cfg.settings.github_token)


def get_http_client() -> httpx.AsyncClient:
    """Return a configured httpx async client with GitHub auth headers."""
    if not _cfg.settings.github_token:
        raise RuntimeError("GitHub token not set — complete OAuth first")
    return httpx.AsyncClient(
        base_url=GITHUB_API,
        headers={
            "Authorization": f"Bearer {_cfg.settings.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=30.0,
    )


async def get_authenticated_user(token: str | None = None) -> Optional[dict]:
    """
    Call GET /user with the stored token (or an explicit token).
    Returns the GitHub user payload or None if the token is missing / invalid.
    """
    tok = token or _cfg.settings.github_token
    if not tok:
        return None
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{GITHUB_API}/user",
            headers={
                "Authorization": f"Bearer {tok}",
                "Accept": "application/vnd.github+json",
            },
        )
        if resp.status_code == 200:
            return resp.json()
        return None
