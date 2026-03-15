from __future__ import annotations

from datetime import datetime
from typing import Optional, Literal, Any
from uuid import UUID, uuid4

from pydantic import BaseModel


DeliveryChannel = Literal["sftp", "api", "local_fallback", "unknown"]
DeliveryStatus = Literal["success", "error", "info"]


class DeliveryTimelineEvent(BaseModel):
    id: UUID
    release_id: UUID

    dsp: str
    channel: DeliveryChannel = "unknown"

    event_type: str
    status: DeliveryStatus = "info"

    message: Optional[str] = None
    payload_path: Optional[str] = None

    created_at: datetime

    @classmethod
    def create(cls, **kwargs: Any) -> "DeliveryTimelineEvent":
        return cls(
            id=uuid4(),
            created_at=datetime.utcnow(),
            **kwargs,
        )

