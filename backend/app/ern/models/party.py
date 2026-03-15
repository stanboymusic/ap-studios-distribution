from uuid import UUID, uuid4
from typing import List, Optional, Dict
from enum import Enum
from pydantic import BaseModel, Field

class PartyType(str, Enum):
    PERSON = "Person"
    ORGANIZATION = "Organization"

class PartyIdentifier(BaseModel):
    namespace: str  # ISNI, IPI, DPID, Proprietary
    value: str
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None

class PartyAlias(BaseModel):
    name: str
    locale: Optional[str] = None
    usage_context: Optional[str] = None

class Party(BaseModel):
    internal_party_id: UUID = Field(default_factory=uuid4)
    display_name: str = Field(..., alias="name")
    type: PartyType = PartyType.PERSON
    identifiers: List[PartyIdentifier] = []
    aliases: List[PartyAlias] = []
    
    model_config = {
        "populate_by_name": True
    }
    
    # Backward compatibility fields for ERN
    @property
    def name(self):
        return self.display_name
        
    @property
    def internal_id(self):
        return str(self.internal_party_id)
