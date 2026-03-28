from pydantic import BaseModel
from datetime import date
from enum import Enum
from typing import Optional
from uuid import UUID


class ReleaseType(str, Enum):
    single = "Single"
    ep = "EP"
    album = "Album"


class ReleaseCreate(BaseModel):
    title: str
    release_type: ReleaseType
    original_release_date: Optional[date] = None
    artist_id: Optional[UUID] = None
    language: str = "es"
    territories: list[str] = ["Worldwide"]


class ReleaseUpdate(BaseModel):
    # In Pydantic v2, Optional[...] without a default is still "required".
    # Defaults to None so partial updates don't 422.
    upc: Optional[str] = None
    original_release_date: Optional[date] = None
    artwork_id: Optional[UUID] = None
    artist_id: Optional[UUID] = None

class ReleaseResponse(BaseModel):
    id: UUID
    release_id: UUID
    title: str
    type: str
    status: str
    owner_user_id: Optional[str] = None
    artist_name: Optional[str] = None
