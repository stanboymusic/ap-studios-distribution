from pydantic import BaseModel
from typing import Optional


class TrackCreate(BaseModel):
    title: str
    track_number: int
    explicit: bool = False
    isrc: Optional[str] = None