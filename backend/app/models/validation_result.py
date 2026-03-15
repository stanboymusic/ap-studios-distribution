from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel


class ValidationResult(BaseModel):
    id: str
    release_id: str
    status: str
    validator_profile: Optional[str] = None
    raw_response: Dict[str, Any]
    created_at: datetime

    @classmethod
    def create(
        cls,
        release_id: str,
        status: str,
        raw_response: Dict[str, Any],
        validator_profile: Optional[str] = None,
    ) -> "ValidationResult":
        return cls(
            id=str(uuid4()),
            release_id=release_id,
            status=status,
            validator_profile=validator_profile,
            raw_response=raw_response,
            created_at=datetime.utcnow(),
        )
