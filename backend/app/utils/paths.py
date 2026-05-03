"""
Path builders — derive folder paths from a capture date.

All paths are relative to the GitHub repo root (not to the local filesystem).
"""

from __future__ import annotations

from datetime import datetime


def year_month_folder(dt: datetime) -> str:
    """Return  YYYY/MM  e.g. '2024/01'."""
    return f"{dt.year:04d}/{dt.month:02d}"


def thumb_path(base_filename: str, dt: datetime) -> str:
    """thumbs/YYYY/MM/{base_filename}.jpg"""
    return f"thumbs/{year_month_folder(dt)}/{base_filename}.jpg"


def original_path(base_filename: str, dt: datetime, ext: str = "jpg") -> str:
    """originals/YYYY/MM/{base_filename}.{ext}"""
    clean_ext = ext.lstrip(".").lower()
    return f"originals/{year_month_folder(dt)}/{base_filename}.{clean_ext}"


def meta_path(base_filename: str, dt: datetime) -> str:
    """meta/YYYY/MM/{base_filename}.json"""
    return f"meta/{year_month_folder(dt)}/{base_filename}.json"
