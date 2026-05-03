"""
EXIF extraction — M4-02.

Uses exifread for broad format support.
Gracefully returns defaults when EXIF is absent or malformed.
"""

from __future__ import annotations

import io
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import exifread

logger = logging.getLogger("photovault.pipeline.exif")


@dataclass
class ExtractedEXIF:
    # Capture timestamp — None means "use upload time"
    captured_at: Optional[datetime]

    # Camera info
    camera_make: Optional[str]
    camera_model: Optional[str]
    focal_length: Optional[str]
    aperture: Optional[str]
    shutter_speed: Optional[str]
    iso: Optional[int]
    flash: Optional[bool]

    # GPS
    gps_lat: Optional[float]
    gps_lng: Optional[float]
    gps_altitude: Optional[float]


_EMPTY = ExtractedEXIF(
    captured_at=None,
    camera_make=None,
    camera_model=None,
    focal_length=None,
    aperture=None,
    shutter_speed=None,
    iso=None,
    flash=None,
    gps_lat=None,
    gps_lng=None,
    gps_altitude=None,
)


def extract(data: bytes) -> ExtractedEXIF:
    """
    Extract EXIF from raw image bytes.
    Never raises — returns empty EXIF on any failure.
    """
    try:
        tags = exifread.process_file(io.BytesIO(data), details=False)
    except Exception as exc:
        logger.debug("exifread failed: %s", exc)
        return _EMPTY

    if not tags:
        return _EMPTY

    return ExtractedEXIF(
        captured_at=_parse_datetime(tags),
        camera_make=_str_tag(tags, "Image Make"),
        camera_model=_str_tag(tags, "Image Model"),
        focal_length=_focal_length(tags),
        aperture=_aperture(tags),
        shutter_speed=_shutter_speed(tags),
        iso=_iso(tags),
        flash=_flash(tags),
        gps_lat=_gps_coord(tags, "GPSLatitude", "GPSLatitudeRef"),
        gps_lng=_gps_coord(tags, "GPSLongitude", "GPSLongitudeRef"),
        gps_altitude=_gps_altitude(tags),
    )


# ── Tag helpers ───────────────────────────────────────────────────────────────

def _str_tag(tags: dict, key: str) -> Optional[str]:
    tag = tags.get(key)
    if tag is None:
        return None
    value = str(tag).strip()
    return value or None


def _parse_datetime(tags: dict) -> Optional[datetime]:
    """Try EXIF DateTimeOriginal → DateTimeDigitized → DateTime."""
    for key in ("EXIF DateTimeOriginal", "EXIF DateTimeDigitized", "Image DateTime"):
        tag = tags.get(key)
        if not tag:
            continue
        raw = str(tag).strip()
        # Format: "2024:01:15 14:30:22"
        try:
            dt = datetime.strptime(raw, "%Y:%m:%d %H:%M:%S")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _focal_length(tags: dict) -> Optional[str]:
    tag = tags.get("EXIF FocalLength")
    if not tag:
        return None
    try:
        val = tag.values[0]
        mm = float(val.num) / float(val.den) if val.den else float(val.num)
        return f"{round(mm)}mm"
    except Exception:
        return _str_tag(tags, "EXIF FocalLength")


def _aperture(tags: dict) -> Optional[str]:
    tag = tags.get("EXIF FNumber")
    if not tag:
        return None
    try:
        val = tag.values[0]
        f = float(val.num) / float(val.den) if val.den else float(val.num)
        return f"f/{f:.1f}"
    except Exception:
        return _str_tag(tags, "EXIF FNumber")


def _shutter_speed(tags: dict) -> Optional[str]:
    # ExposureTime is more reliable than ShutterSpeedValue
    tag = tags.get("EXIF ExposureTime")
    if not tag:
        return None
    try:
        val = tag.values[0]
        num, den = int(val.num), int(val.den)
        if den == 1:
            return f"{num}s"
        if num == 1:
            return f"1/{den}s"
        # Simplify fraction
        from math import gcd
        g = gcd(abs(num), abs(den))
        return f"{num//g}/{den//g}s"
    except Exception:
        return _str_tag(tags, "EXIF ExposureTime")


def _iso(tags: dict) -> Optional[int]:
    tag = tags.get("EXIF ISOSpeedRatings")
    if not tag:
        return None
    try:
        return int(str(tag).split(",")[0].strip())
    except Exception:
        return None


def _flash(tags: dict) -> Optional[bool]:
    tag = tags.get("EXIF Flash")
    if not tag:
        return None
    try:
        # Flash value is a bitmask; bit 0 = flash fired
        val = int(str(tag))
        return bool(val & 0x01)
    except Exception:
        return None


def _dms_to_decimal(dms_values: list, ref: str) -> float:
    """Convert DMS (degrees, minutes, seconds) ratio values to decimal degrees."""
    d = float(dms_values[0].num) / float(dms_values[0].den)
    m = float(dms_values[1].num) / float(dms_values[1].den)
    s = float(dms_values[2].num) / float(dms_values[2].den)
    decimal = d + m / 60.0 + s / 3600.0
    if ref.upper() in ("S", "W"):
        decimal = -decimal
    return round(decimal, 6)


def _gps_coord(tags: dict, coord_key: str, ref_key: str) -> Optional[float]:
    coord_tag = tags.get(f"GPS {coord_key.replace('GPS', '').strip()}", tags.get(coord_key))
    ref_tag   = tags.get(f"GPS {ref_key.replace('GPS', '').strip()}",   tags.get(ref_key))
    if not coord_tag or not ref_tag:
        return None
    try:
        return _dms_to_decimal(coord_tag.values, str(ref_tag))
    except Exception as exc:
        logger.debug("GPS parse failed for %s: %s", coord_key, exc)
        return None


def _gps_altitude(tags: dict) -> Optional[float]:
    tag = tags.get("GPS GPSAltitude")
    if not tag:
        return None
    try:
        val = tag.values[0]
        alt = float(val.num) / float(val.den)
        ref = tags.get("GPS GPSAltitudeRef")
        if ref and str(ref) == "1":
            alt = -alt
        return round(alt, 1)
    except Exception:
        return None
