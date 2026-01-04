from pydantic import BaseModel, field_validator
from typing import List, Optional, Union

class Resource(BaseModel):
    internal_id: str
    type: str  # SoundRecording, Image, Video
    title: Optional[str] = None
    duration_seconds: Optional[Union[int, float]] = None
    isrc: Optional[str] = None
    file: str
    artists: List[str] = []
    territories: List[str] = []

    @field_validator('duration_seconds')
    @classmethod
    def round_duration(cls, v):
        if v is not None:
            return int(float(v))
        return v