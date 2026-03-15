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

class RightsParty(BaseModel):
    name: str
    role: Optional[str] = None
    ipi_name_number: Optional[str] = None
    share_pct: Optional[float] = None
    recipient_dpid: Optional[str] = None

class RightsConfiguration(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    scope: str
    release_id: UUID
    track_id: Optional[UUID] = None
    shares: List[RightsShare] = Field(default_factory=list)
    work_title: Optional[str] = None
    iswc: Optional[str] = None
    territory: Optional[str] = None
    composers: List[RightsParty] = Field(default_factory=list)
    publishers: List[RightsParty] = Field(default_factory=list)
