"""
Pillow image helpers — M4-04.

Handles:
  - Open any supported image format (JPEG, PNG, WEBP, TIFF, GIF, BMP)
  - HEIC conversion via pillow-heif (optional, gracefully degraded)
  - Thumbnail generation: resize to target_width, JPEG output, quality configurable
  - Dimension reading without full decode
"""

from __future__ import annotations

import io
import logging
from typing import Optional

from PIL import Image, ImageOps, UnidentifiedImageError

logger = logging.getLogger("photovault.image")

# Try to register HEIF/HEIC opener (requires pillow-heif package)
_HEIF_AVAILABLE = False
try:
    import pillow_heif  # type: ignore
    pillow_heif.register_heif_opener()
    _HEIF_AVAILABLE = True
    logger.info("pillow-heif available — HEIC/HEIF files supported")
except ImportError:
    logger.info(
        "pillow-heif not installed — HEIC/HEIF uploads will be rejected. "
        "Install pillow-heif to enable HEIC support."
    )


def open_image(data: bytes) -> Image.Image:
    """
    Open image bytes as a PIL Image.
    Applies EXIF orientation correction automatically.
    Raises ValueError for unsupported / corrupted files.
    """
    try:
        img = Image.open(io.BytesIO(data))
        img.load()  # force decode so we catch corrupt files early
    except UnidentifiedImageError as exc:
        raise ValueError(f"Cannot decode image: {exc}") from exc
    except Exception as exc:
        raise ValueError(f"Failed to open image: {exc}") from exc

    # Auto-rotate based on EXIF orientation tag
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass  # non-fatal

    return img


def make_thumbnail(
    img: Image.Image,
    target_width: int = 400,
    quality: int = 75,
) -> bytes:
    """
    Resize to target_width (maintaining aspect ratio), convert to JPEG, return bytes.
    Always returns JPEG regardless of input format.
    """
    w, h = img.size
    if w == 0 or h == 0:
        raise ValueError("Image has zero dimension")

    scale = target_width / w
    new_h = max(1, round(h * scale))
    thumb = img.convert("RGB").resize((target_width, new_h), Image.LANCZOS)

    buf = io.BytesIO()
    thumb.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def get_dimensions(img: Image.Image) -> tuple[int, int]:
    """Return (width, height) of the opened image."""
    return img.size  # (w, h)


def encode_jpeg(img: Image.Image, quality: int = 85) -> bytes:
    """Re-encode an image as JPEG bytes."""
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()
