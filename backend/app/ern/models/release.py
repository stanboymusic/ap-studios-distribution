from pydantic import BaseModel
from typing import List, Optional

class Release(BaseModel):
    internal_id: str
    type: str  # Album, Single
    title: str
    upc: Optional[str] = None
    original_release_date: str
    resources: List[str]
    display_artists: List[str]
    label: str
    rights: Optional[dict] = None
