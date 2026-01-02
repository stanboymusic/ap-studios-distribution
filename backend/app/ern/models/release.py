from pydantic import BaseModel
from typing import List

class Release(BaseModel):
    internal_id: str
    type: str  # Album, Single
    title: str
    original_release_date: str
    resources: List[str]
    display_artists: List[str]
    label: str