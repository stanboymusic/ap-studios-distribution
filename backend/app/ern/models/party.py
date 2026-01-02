from pydantic import BaseModel
from typing import List, Optional

class Party(BaseModel):
    internal_id: str
    name: str
    party_id: Optional[str] = None
    roles: List[str] = []