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
    original_release_date: date
    language: str = "es"
    territories: list[str] = ["Worldwide"]


class ReleaseUpdate(BaseModel):
    upc: Optional[str]
    original_release_date: Optional[date]

class ReleaseResponse(BaseModel):
    id: UUID
    release_id: UUID
    title: str
    type: str
    status: str