"""
Authentication routes — GitHub OAuth flow.

GET  /api/auth           — M1-04  returns { authed, username, avatar_url, name }
GET  /api/auth/login     — M1-01  redirects browser to GitHub OAuth consent screen
GET  /api/auth/callback  — M1-01  exchanges code for token, redirects to frontend
POST /api/logout         — M1-05  clears token + manifest cache
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse

from app.config import settings
from app.services.auth_service import complete_oauth, get_auth_state, logout

logger = logging.getLogger("photovault.auth")

router = APIRouter(tags=["auth"])

GITHUB_OAUTH_URL = "https://github.com/login/oauth/authorize"
# Scopes: full repo access (read + write) + email address
OAUTH_SCOPES = "repo,user:email"


# ── GET /api/auth ─────────────────────────────────────────────────────────────

@router.get("/auth")
async def auth_state():
    """
    M1-04 — return current authentication state.
    The frontend polls this on load to decide what to render.
    """
    state = await get_auth_state()
    return JSONResponse(state.to_dict())


# ── GET /api/auth/login ───────────────────────────────────────────────────────

@router.get("/auth/login")
async def auth_login():
    """
    M1-01 — redirect the user's browser to the GitHub OAuth consent screen.
    After the user authorises the app, GitHub redirects to /api/auth/callback.
    """
    if not settings.github_client_id:
        raise HTTPException(
            status_code=500,
            detail=(
                "GITHUB_CLIENT_ID is not set. "
                "Copy .env.example to data/.env and fill in your OAuth App credentials."
            ),
        )

    params = (
        f"?client_id={settings.github_client_id}"
        f"&redirect_uri={settings.oauth_callback_url}"
        f"&scope={OAUTH_SCOPES}"
    )
    return RedirectResponse(url=f"{GITHUB_OAUTH_URL}{params}")


# ── GET /api/auth/callback ────────────────────────────────────────────────────

@router.get("/auth/callback")
async def auth_callback(code: str | None = None, error: str | None = None):
    """
    M1-01 / M1-02 — GitHub redirects here after the user authorises the app.
    Exchanges the temporary code for an access token and persists it.
    """
    # GitHub sends ?error=access_denied if the user cancelled
    if error:
        logger.warning("OAuth callback received error: %s", error)
        return RedirectResponse(
            url=f"{settings.frontend_url}?auth_error={error}"
        )

    if not code:
        raise HTTPException(status_code=400, detail="Missing OAuth code in callback")

    auth = await complete_oauth(code)

    if auth is None:
        logger.error("OAuth token exchange failed")
        return RedirectResponse(
            url=f"{settings.frontend_url}?auth_error=token_exchange_failed"
        )

    logger.info("OAuth complete — user: %s", auth.username)

    # Redirect back to the frontend; it will re-poll /api/auth and update state
    return RedirectResponse(url=settings.frontend_url)


# ── POST /api/logout ──────────────────────────────────────────────────────────

@router.post("/logout")
async def auth_logout():
    """
    M1-05 — disconnect GitHub account.
    Clears token from .env and wipes manifest cache.
    Does NOT delete cached thumbnails or previews.
    """
    await logout()
    return {"status": "logged_out"}
