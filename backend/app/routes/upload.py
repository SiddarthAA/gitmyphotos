"""
Upload route — M4.

POST /api/upload
  Accepts a multipart file upload.
  Returns {"id": photo_id, "status": "queued"} immediately.
  The photo is processed in the background and committed to GitHub
  after the batch window closes.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.pipeline_service import process_upload

logger = logging.getLogger("photovault.routes.upload")

router = APIRouter(tags=["upload"])


@router.post("/upload")
async def upload_photo(file: UploadFile = File(...)):
    """
    Upload a single photo.

    The file is validated, thumbnailed, and queued for a batched git commit.
    Returns the photo_id immediately — the commit happens after the batch window.
    """
    try:
        photo_id = await process_upload(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error during upload")
        raise HTTPException(status_code=500, detail="Upload failed") from exc

    return {"id": photo_id, "status": "queued"}
