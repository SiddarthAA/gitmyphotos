"""
Authentication service — GitHub OAuth flow + token lifecycle.

M1-01  exchange_code_for_token  — swap OAuth code for access token
M1-02  write_token / clear_token — persist / wipe from data/.env
M1-03  validate_token_on_startup — called during lifespan, auto-clears bad tokens
M1-04  get_auth_state            — returns AuthState for the frontend
M1-05  logout                    — alias for clear_token + cache wipe
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

import app.config as _cfg
from app.config import settings, write_env_key, clear_env_key
from app.github.client import get_authenticated_user

logger = logging.getLogger("photovault.auth")

GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"


# ── Data objects ──────────────────────────────────────────────────────────────

class AuthState:
    def __init__(
        self,
        authed: bool,
        username: Optional[str] = None,
        avatar_url: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        self.authed = authed
        self.username = username
        self.avatar_url = avatar_url
        self.name = name

    def to_dict(self) -> dict:
        return {
            "authed": self.authed,
            "username": self.username,
            "avatar_url": self.avatar_url,
            "name": self.name,
        }


# ── Core functions ─────────────────────────────────────────────────────────────

async def validate_token_on_startup() -> None:
    if not _cfg.settings.github_token:
        logger.info("No GitHub token stored — OAuth required")
        return

    user = await get_authenticated_user()
    if user is None:
        logger.warning("Stored GitHub token is invalid — clearing it")
        _clear_token()
    else:
        logger.info("GitHub token valid — authenticated as %s", user.get("login"))


async def get_auth_state() -> AuthState:
    """
    M1-04 — returns current auth state.
    """
    if not _cfg.settings.github_token:
        return AuthState(authed=False)

    user = await get_authenticated_user()
    if user is None:
        _clear_token()
        return AuthState(authed=False)

    return AuthState(
        authed=True,
        username=user.get("login"),
        avatar_url=user.get("avatar_url"),
        name=user.get("name"),
    )


async def exchange_code_for_token(code: str) -> Optional[str]:
    """
    M1-01 — exchange the OAuth callback code for an access token.
    Returns the token string, or None if the exchange failed.
    """
    if not settings.github_client_id or not settings.github_client_secret:
        raise RuntimeError(
            "GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET must be set in data/.env"
        )

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            GITHUB_TOKEN_URL,
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )

    if resp.status_code != 200:
        logger.error("Token exchange failed: HTTP %d", resp.status_code)
        return None

    data = resp.json()
    token: Optional[str] = data.get("access_token")
    if not token:
        error = data.get("error_description", data.get("error", "unknown"))
        logger.error("Token exchange error: %s", error)
        return None

    return token


def _write_token(token: str) -> None:
    """M1-02 — persist token to data/.env."""
    write_env_key("GITHUB_TOKEN", token)
    logger.info("GitHub token written to .env")


def _clear_token() -> None:
    """M1-02/M1-05 — remove token from data/.env."""
    clear_env_key("GITHUB_TOKEN")
    logger.info("GitHub token cleared from .env")


async def complete_oauth(code: str) -> Optional[AuthState]:
    """
    Full OAuth completion sequence:
    1. Exchange code → token
    2. Verify the token is valid BEFORE writing to .env (avoids write-then-clear race)
    3. Persist token
    4. Return AuthState
    """
    token = await exchange_code_for_token(code)
    if not token:
        return None

    # Verify with the raw token BEFORE persisting — avoids the stale-settings trap
    user = await get_authenticated_user(token=token)
    if user is None:
        logger.error("Token exchange succeeded but /user verification failed")
        return None

    _write_token(token)

    return AuthState(
        authed=True,
        username=user.get("login"),
        avatar_url=user.get("avatar_url"),
        name=user.get("name"),
    )


async def logout() -> None:
    """
    M1-05 — clear token and evict cached data.
    Does NOT wipe owner/repo/branch so the user doesn't have to reconnect
    their repo after re-authenticating.
    """
    _clear_token()

    # Wipe manifest cache — it may contain data scoped to the old token
    manifest_cache = settings.manifest_cache_path
    if manifest_cache.exists():
        manifest_cache.unlink()
        logger.info("Manifest cache cleared on logout")

    # Previews cache is user-data-neutral (resized images), keep it.
