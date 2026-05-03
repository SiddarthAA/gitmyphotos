"""
File ingestion — M4-01.

Validates MIME type and file size, returns raw bytes + metadata.
Accepted formats: JPEG, PNG, WEBP, HEIC, TIFF, GIF, RAW (CR2, NEF, etc.)
"""

from __future__ import annotations

import logging
import mimetypes
from dataclasses import dataclass

from fastapi import UploadFile

logger = logging.getLogger("photovault.pipeline.ingest")

# ── Allowed MIME types and extensions ─────────────────────────────────────────

ALLOWED_MIMES: frozenset[str] = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/heic",
        "image/heif",
        "image/tiff",
        "image/gif",
        "image/bmp",
        # RAW formats
        "image/x-canon-cr2",
        "image/x-canon-cr3",
        "image/x-nikon-nef",
        "image/x-sony-arw",
        "image/x-adobe-dng",
        "image/x-fuji-raf",
        "image/x-olympus-orf",
        "image/x-panasonic-rw2",
        "image/raw",
        "image/x-raw",
    }
)

# Extension → MIME overrides (browsers often send application/octet-stream for RAW)
_EXT_MIME_OVERRIDE: dict[str, str] = {
    ".heic": "image/heic",
    ".heif": "image/heif",
    ".cr2":  "image/x-canon-cr2",
    ".cr3":  "image/x-canon-cr3",
    ".nef":  "image/x-nikon-nef",
    ".arw":  "image/x-sony-arw",
    ".dng":  "image/x-adobe-dng",
    ".raf":  "image/x-fuji-raf",
    ".orf":  "image/x-olympus-orf",
    ".rw2":  "image/x-panasonic-rw2",
    ".raw":  "image/raw",
}

# Extension → canonical file extension we store in originals/
_EXT_CANONICAL: dict[str, str] = {
    ".jpg": "jpg",
    ".jpeg": "jpg",
    ".png": "png",
    ".webp": "webp",
    ".heic": "heic",
    ".heif": "heic",
    ".tiff": "tiff",
    ".tif": "tiff",
    ".gif": "gif",
    ".bmp": "bmp",
    ".cr2": "cr2",
    ".cr3": "cr3",
    ".nef": "nef",
    ".arw": "arw",
    ".dng": "dng",
    ".raf": "raf",
    ".orf": "orf",
    ".rw2": "rw2",
    ".raw": "raw",
}


@dataclass
class IngestedFile:
    data: bytes
    original_filename: str
    mime_type: str
    size_bytes: int
    ext: str               # canonical lowercase extension, no dot (e.g. "jpg")
    is_raw: bool


async def ingest(upload: UploadFile, max_size_mb: int = 100) -> IngestedFile:
    """
    Read and validate an uploaded file.
    Raises ValueError with a user-facing message on rejection.
    """
    original_filename = upload.filename or "unknown"
    raw_suffix = _get_extension(original_filename)

    # Resolve MIME — override if browser sent a generic type for known extension
    content_type: str = upload.content_type or "application/octet-stream"
    if content_type in ("application/octet-stream", "binary/octet-stream"):
        content_type = _EXT_MIME_OVERRIDE.get(raw_suffix, content_type)

    if content_type not in ALLOWED_MIMES:
        raise ValueError(
            f"Unsupported file type '{content_type}'. "
            f"Accepted: JPEG, PNG, WEBP, HEIC, TIFF, GIF, RAW."
        )

    data = await upload.read()
    size_bytes = len(data)
    max_bytes = max_size_mb * 1024 * 1024

    if size_bytes == 0:
        raise ValueError("Uploaded file is empty.")
    if size_bytes > max_bytes:
        raise ValueError(
            f"File too large: {size_bytes / 1024**2:.1f} MB. "
            f"Maximum allowed: {max_size_mb} MB."
        )

    ext = _EXT_CANONICAL.get(raw_suffix, raw_suffix.lstrip(".") or "jpg")
    is_raw = ext in {
        "cr2", "cr3", "nef", "arw", "dng", "raf", "orf", "rw2", "raw"
    }

    logger.debug(
        "Ingested %s (%s, %.1f KB)",
        original_filename, content_type, size_bytes / 1024,
    )

    return IngestedFile(
        data=data,
        original_filename=original_filename,
        mime_type=content_type,
        size_bytes=size_bytes,
        ext=ext,
        is_raw=is_raw,
    )


def _get_extension(filename: str) -> str:
    """Return lowercase extension including the dot, e.g. '.jpg'."""
    idx = filename.rfind(".")
    if idx == -1:
        return ""
    return filename[idx:].lower()
