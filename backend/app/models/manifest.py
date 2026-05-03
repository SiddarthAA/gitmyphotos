"""
Pydantic models for manifest.json — the append-only photo index.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class GPS(BaseModel):
    lat: float
    lng: float
    altitude: Optional[float] = None
    place: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None


class ManifestPhoto(BaseModel):
    id: str                          # 20240115_143022_abc123
    captured_at: str                 # ISO 8601
    uploaded_at: str
    original_filename: str
    mime_type: str
    size_bytes: int
    thumb_path: str
    original_path: str
    meta_path: str
    width: int
    height: int
    camera: Optional[str] = None
    gps: Optional[GPS] = None
    # M6-04: GitHub blob SHAs — enables direct SHA-based download, no path lookup
    thumb_sha: Optional[str] = None
    original_sha: Optional[str] = None


class Manifest(BaseModel):
    version: str = "1"
    last_updated: str
    total_photos: int = 0
    total_size_bytes: int = 0
    photos: list[ManifestPhoto] = []

    def empty(self) -> "Manifest":
        """Return a fresh empty manifest (class method style)."""
        from datetime import datetime, timezone
        return Manifest(
            version="1",
            last_updated=datetime.now(timezone.utc).isoformat(),
            total_photos=0,
            total_size_bytes=0,
            photos=[],
        )

    @classmethod
    def new(cls) -> "Manifest":
        from datetime import datetime, timezone
        return cls(
            version="1",
            last_updated=datetime.now(timezone.utc).isoformat(),
            total_photos=0,
            total_size_bytes=0,
            photos=[],
        )
