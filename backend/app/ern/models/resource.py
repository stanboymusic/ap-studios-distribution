from pydantic import BaseModel
from typing import List, Optional

class Resource(BaseModel):
    internal_id: str
    type: str  # SoundRecording, Image, Video
    title: Optional[str] = None
    duration_seconds: Optional[int] = None
    isrc: Optional[str] = None
    file: str
    artists: List[str] = []
    territories: List[str] = []