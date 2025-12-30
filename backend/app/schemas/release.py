from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import date

class ReleaseCreate(BaseModel):
    title: str
    artist_id: UUID

class ReleaseUpdate(BaseModel):
    upc: Optional[str]
    original_release_date: Optional[date]

class ReleaseResponse(BaseModel):
    id: UUID
    title: str
    type: str
    status: str