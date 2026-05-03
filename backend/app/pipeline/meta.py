"""
Meta JSON builder — M4-05.

Assembles the per-photo metadata object that is written to
meta/{YYYY}/{MM}/{id}.json in the GitHub repo.

Schema is locked. tags: [] and faces: [] are reserved for v2 AI pipeline.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.models.photo import EXIF as EXIFModel
from app.models.photo import GPS as GPSModel
from app.models.photo import PhotoMeta
from app.pipeline.exif import ExtractedEXIF
from app.utils.paths import meta_path, original_path, thumb_path


def build_meta(
    photo_id: str,
    original_filename: str,
    mime_type: str,
    size_bytes: int,
    width: int,
    height: int,
    exif: ExtractedEXIF,
    captured_at: datetime,
    uploaded_at: datetime,
    filename_base: str,
) -> PhotoMeta:
    """
    Build a fully populated PhotoMeta object.

    Parameters
    ----------
    photo_id:
        The {YYYYMMDD}_{HHMMSS}_{6uid} identifier.
    filename_base:
        Same as photo_id — used to derive path strings.
    captured_at:
        Final resolved capture timestamp (EXIF date or upload time).
    """
    gps_model: GPSModel | None = None
    if exif.gps_lat is not None and exif.gps_lng is not None:
        gps_model = GPSModel(
            lat=exif.gps_lat,
            lng=exif.gps_lng,
            altitude=exif.gps_altitude,
        )

    exif_model = EXIFModel(
        camera_make=exif.camera_make,
        camera_model=exif.camera_model,
        focal_length=exif.focal_length,
        aperture=exif.aperture,
        shutter_speed=exif.shutter_speed,
        iso=exif.iso,
        flash=exif.flash,
        gps=gps_model,
    )

    # Derive the original file extension from mime_type
    ext = _mime_to_ext(mime_type)

    return PhotoMeta(
        id=photo_id,
        original_filename=original_filename,
        captured_at=captured_at.isoformat(),
        uploaded_at=uploaded_at.isoformat(),
        mime_type=mime_type,
        size_bytes=size_bytes,
        width=width,
        height=height,
        thumb_path=thumb_path(filename_base, captured_at),
        original_path=original_path(filename_base, captured_at, ext),
        exif=exif_model,
        tags=[],
        faces=[],
    )


def _mime_to_ext(mime_type: str) -> str:
    table = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "image/heic": "heic",
        "image/heif": "heic",
        "image/tiff": "tiff",
        "image/gif": "gif",
        "image/bmp": "bmp",
        "image/x-canon-cr2": "cr2",
        "image/x-canon-cr3": "cr3",
        "image/x-nikon-nef": "nef",
        "image/x-sony-arw": "arw",
        "image/x-adobe-dng": "dng",
        "image/x-fuji-raf": "raf",
        "image/x-olympus-orf": "orf",
        "image/x-panasonic-rw2": "rw2",
        "image/raw": "raw",
        "image/x-raw": "raw",
    }
    return table.get(mime_type, "jpg")
