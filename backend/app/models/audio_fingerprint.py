from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AudioFingerprint(BaseModel):
    id: str
    source_type: str
    source_id: str
    fingerprint_hash: str
    fingerprint_vector: list[float]
    duration: float
    sample_rate: int
    asset_path: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
