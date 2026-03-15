from pydantic import BaseModel
from typing import List, Optional

class Deal(BaseModel):
    deal_reference: str
    party_reference: str
    commercial_model: str
    use_types: List[str]
    territory_codes: List[str]
    valid_from: str
    valid_to: Optional[str] = None
    release_reference: str
    track_references: List[str] = []
