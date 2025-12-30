from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class ArtistCreate(BaseModel):
    name: str
    type: str  # SOLO / GROUP

class ArtistResponse(BaseModel):
    id: UUID
    name: str
    type: str