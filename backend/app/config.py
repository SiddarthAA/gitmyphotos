"""
Central settings — reads from the .env file mounted at ENV_FILE.

The .env file lives at  data/.env  (host) → /app/.env  (container).
It is the sole source of truth for credentials and repo config.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import dotenv_values, set_key
from pydantic_settings import BaseSettings, SettingsConfigDict


# Path to the writable .env — can be overridden via ENV_FILE env var.
# Docker sets ENV_FILE=/app/.env explicitly.
# Local dev falls back to <project_root>/data/.env (3 levels up from this file).
_DEFAULT_ENV_FILE = Path(__file__).resolve().parent.parent.parent / "data" / ".env"
ENV_FILE: Path = Path(os.getenv("ENV_FILE", str(_DEFAULT_ENV_FILE)))


def _ensure_env_file() -> None:
    """Create an empty .env if it doesn't exist yet (first run)."""
    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not ENV_FILE.exists():
        ENV_FILE.touch(mode=0o600)


_ensure_env_file()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── OAuth app credentials (set once by user in data/.env) ─────────────
    github_client_id: str = ""
    github_client_secret: str = ""

    # ── Set by the app after OAuth callback ───────────────────────────────
    github_token: str = ""

    # ── Set by the app after repo connection ──────────────────────────────
    github_owner: str = ""
    github_repo: str = ""
    github_branch: str = "main"

    # ── Cache ─────────────────────────────────────────────────────────────
    cache_max_preview_gb: float = 2.0
    cache_dir: Path = Path(
        os.getenv(
            "CACHE_DIR",
            str(Path(__file__).resolve().parent.parent.parent / "data" / "cache"),
        )
    )

    # ── Service URLs ──────────────────────────────────────────────────────
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    backend_url: str = os.getenv("BACKEND_URL", "http://localhost:8000")

    # ── Derived paths (not from .env) ─────────────────────────────────────
    @property
    def cache_thumbs_dir(self) -> Path:
        return self.cache_dir / "thumbs"

    @property
    def cache_previews_dir(self) -> Path:
        return self.cache_dir / "previews"

    @property
    def manifest_cache_path(self) -> Path:
        return self.cache_dir / "manifest.json"

    @property
    def oauth_callback_url(self) -> str:
        return f"{self.backend_url}/api/auth/callback"

    @property
    def is_configured(self) -> bool:
        """True once a GitHub token has been obtained via OAuth."""
        return bool(self.github_token)

    @property
    def repo_is_connected(self) -> bool:
        return bool(self.github_token and self.github_owner and self.github_repo)


def write_env_key(key: str, value: str) -> None:
    """Persist a single key=value pair to the writable .env file."""
    _ensure_env_file()
    set_key(str(ENV_FILE), key, value, quote_mode="never")
    # Reload the global settings object so the new value is immediately visible
    _reload_settings()


def clear_env_key(key: str) -> None:
    """Remove a key from the writable .env file."""
    _ensure_env_file()
    lines = ENV_FILE.read_text().splitlines(keepends=True)
    filtered = [l for l in lines if not l.startswith(f"{key}=")]
    ENV_FILE.write_text("".join(filtered))
    _reload_settings()


def _reload_settings() -> None:
    """
    Force settings to re-read the .env file.

    Mutates the EXISTING settings object in place rather than replacing it,
    so every module that did `from app.config import settings` keeps a valid
    live reference — no stale-snapshot bugs.
    """
    new = Settings()
    for field in settings.model_fields:
        object.__setattr__(settings, field, getattr(new, field))


settings: Settings = Settings()
