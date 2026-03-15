from uuid import UUID, uuid4
from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field

class RightsShare(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    party_reference: str
    rights_type: str
    usage_types: List[str]
    territories: List[str]
    share_percentage: float
    valid_from: date
    valid_to: Optional[date] = None

class RightsConfiguration(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    scope: str
    release_id: UUID
    track_id: Optional[UUID] = None
    shares: List[RightsShare] = []
