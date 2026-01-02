from uuid import UUID, uuid4
from datetime import datetime
from typing import Literal
from pydantic import BaseModel


EventType = Literal[
    "CREATED",
    "UPLOADING",
    "UPLOADED",
    "PROCESSING",
    "ACCEPTED",
    "REJECTED",
    "ERROR"
]


class DeliveryEvent(BaseModel):
    id: UUID
    release_id: UUID
    dsp: str
    event_type: EventType
    message: str
    created_at: datetime

    @classmethod
    def create(
        cls,
        release_id: UUID,
        dsp: str,
        event_type: EventType,
        message: str
    ) -> "DeliveryEvent":
        return cls(
            id=uuid4(),
            release_id=release_id,
            dsp=dsp,
            event_type=event_type,
            message=message,
            created_at=datetime.utcnow()
        )