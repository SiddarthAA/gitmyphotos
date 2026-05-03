"""
PhotoVault backend — FastAPI entry point.

Startup sequence
----------------
1. Ensure data dirs exist (cache/thumbs, cache/previews)
2. Load .env (mounted at ENV_FILE)
3. Validate GitHub token if present — if invalid, clear it so auth state
   returns authed=false and the frontend shows the OAuth screen
4. Register routes
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import auth, repo, upload, photos, settings as settings_router
from app.services.auth_service import validate_token_on_startup

logger = logging.getLogger("photovault")
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── startup ──────────────────────────────────────────────────────────────
    logger.info("PhotoVault backend starting up")

    # Ensure cache directories exist (M6-05)
    settings.cache_thumbs_dir.mkdir(parents=True, exist_ok=True)
    settings.cache_previews_dir.mkdir(parents=True, exist_ok=True)

    # Report cache sizes on startup (M6-05)
    from app.services.cache_service import get_cache_stats
    stats = get_cache_stats()
    logger.info(
        "Cache — thumbs: %d files / %.1f MB | previews: %d files / %.1f MB (limit %.1f GB)",
        stats["thumbs"]["files"], stats["thumbs"]["mb"],
        stats["previews"]["files"], stats["previews"]["mb"],
        stats["max_preview_gb"],
    )

    # Validate stored GitHub token (non-fatal — just clears it if bad)
    await validate_token_on_startup()

    yield
    # ── shutdown ─────────────────────────────────────────────────────────────
    logger.info("PhotoVault backend shutting down")
    # Flush any remaining photos in the batch queue before exiting
    try:
        from app.services.pipeline_service import shutdown as pipeline_shutdown
        await pipeline_shutdown()
    except Exception as exc:
        logger.warning("Pipeline shutdown error: %s", exc)


app = FastAPI(title="PhotoVault", version="0.1.0", lifespan=lifespan)

# CORS — frontend Dev server + production container both need access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(auth.router,     prefix="/api")
app.include_router(repo.router,     prefix="/api")
app.include_router(upload.router,   prefix="/api")
app.include_router(photos.router,   prefix="/api")
app.include_router(settings_router.router, prefix="/api")


@app.get("/healthz", tags=["infra"])
async def health():
    return {"status": "ok"}
