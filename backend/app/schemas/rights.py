from pydantic import BaseModel, Field
from uuid import UUID
from typing import List, Optional
from datetime import date

class RightsShareCreate(BaseModel):
    party_reference: str
    rights_type: str
    usage_types: List[str]
    territories: List[str]
    share_percentage: float = Field(gt=0, le=100)
    valid_from: date
    valid_to: Optional[date] = None

class RightsPartyCreate(BaseModel):
    name: str
    role: Optional[str] = None
    ipi_name_number: Optional[str] = None
    share_pct: Optional[float] = None
    recipient_dpid: Optional[str] = None

class RightsConfigurationCreate(BaseModel):
    scope: str
    release_id: UUID
    track_id: Optional[UUID] = None
    shares: List[RightsShareCreate]
    work_title: Optional[str] = None
    iswc: Optional[str] = None
    territory: Optional[str] = None
    composers: List[RightsPartyCreate] = Field(default_factory=list)
    publishers: List[RightsPartyCreate] = Field(default_factory=list)
