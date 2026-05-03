"""
Filename generator — M4-03.

Produces:  {YYYYMMDD}_{HHMMSS}_{6uid}
Date / time come from EXIF captured_at when available; fallback is upload time.
The 6-char nanoid suffix makes every filename collision-proof.

The same base filename is used across thumbs/, originals/, meta/.
"""

from __future__ import annotations

from datetime import datetime, timezone

from nanoid import generate as _nanoid

# URL-safe alphabet (no confusing chars like 0/O, 1/l/I)
_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"


def make_filename(captured_at: datetime | None = None) -> str:
    """
    Return  {YYYYMMDD}_{HHMMSS}_{6uid}  (no extension).

    Parameters
    ----------
    captured_at:
        EXIF capture timestamp. If None, the current UTC time is used.
    """
    dt = captured_at or datetime.now(timezone.utc)
    uid = _nanoid(alphabet=_ALPHABET, size=6)
    return f"{dt.strftime('%Y%m%d_%H%M%S')}_{uid}"
