"""
Pydantic model for .photovault.yml — per-repo configuration file.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class RepoConfig(BaseModel):
    owner: str
    name: str
    branch: str = "main"


class RepoStats(BaseModel):
    total_photos: int = 0
    total_size_bytes: int = 0
    last_upload: Optional[str] = None
    last_sync: Optional[str] = None


class RepoSettings(BaseModel):
    thumb_width: int = 400
    thumb_quality: int = 75
    preview_width: int = 1200
    preview_quality: int = 85
    batch_delay_seconds: int = 3
    max_file_size_mb: int = 100
    # M6-06: LRU eviction threshold for the previews cache
    cache_max_preview_gb: float = 2.0


class PhotovaultConfig(BaseModel):
    version: str = "1"
    created_at: str
    repo: RepoConfig
    stats: RepoStats = RepoStats()
    settings: RepoSettings = RepoSettings()

    @classmethod
    def new(cls, owner: str, name: str, branch: str = "main") -> "PhotovaultConfig":
        from datetime import datetime, timezone
        return cls(
            version="1",
            created_at=datetime.now(timezone.utc).isoformat(),
            repo=RepoConfig(owner=owner, name=name, branch=branch),
            stats=RepoStats(),
            settings=RepoSettings(),
        )

    def to_yaml(self) -> str:
        import yaml
        data = {
            "version": self.version,
            "created_at": self.created_at,
            "repo": {
                "owner": self.repo.owner,
                "name": self.repo.name,
                "branch": self.repo.branch,
            },
            "stats": {
                "total_photos": self.stats.total_photos,
                "total_size_bytes": self.stats.total_size_bytes,
                "last_upload": self.stats.last_upload,
                "last_sync": self.stats.last_sync,
            },
            "settings": {
                "thumb_width": self.settings.thumb_width,
                "thumb_quality": self.settings.thumb_quality,
                "preview_width": self.settings.preview_width,
                "preview_quality": self.settings.preview_quality,
                "batch_delay_seconds": self.settings.batch_delay_seconds,
                "max_file_size_mb": self.settings.max_file_size_mb,
                "cache_max_preview_gb": self.settings.cache_max_preview_gb,
            },
        }
        return yaml.dump(data, default_flow_style=False, allow_unicode=True)

    @classmethod
    def from_yaml(cls, raw: str) -> "PhotovaultConfig":
        import yaml
        data = yaml.safe_load(raw)
        return cls(
            version=str(data.get("version", "1")),
            created_at=data.get("created_at", ""),
            repo=RepoConfig(**data["repo"]),
            stats=RepoStats(**data.get("stats", {})),
            settings=RepoSettings(**data.get("settings", {})),
        )
