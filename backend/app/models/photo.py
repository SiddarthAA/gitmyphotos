"""
Pydantic models for per-photo data — meta/{id}.json and in-memory pipeline objects.
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


class EXIF(BaseModel):
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    focal_length: Optional[str] = None
    aperture: Optional[str] = None
    shutter_speed: Optional[str] = None
    iso: Optional[int] = None
    flash: Optional[bool] = None
    gps: Optional[GPS] = None


class PhotoMeta(BaseModel):
    id: str
    original_filename: str
    captured_at: str
    uploaded_at: str
    mime_type: str
    size_bytes: int
    width: int
    height: int
    thumb_path: str
    original_path: str
    exif: EXIF = EXIF()
    tags: list[str] = []
    faces: list[str] = []


class Photo(BaseModel):
    """Lightweight photo record stored in manifest.json."""
    id: str
    captured_at: str
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
