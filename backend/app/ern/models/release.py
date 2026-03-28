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
    genre: Optional[str] = None
    subgenre: Optional[str] = None
    c_line: Optional[str] = None
    p_line: Optional[str] = None
    meta_language: Optional[str] = None
    product_version: Optional[str] = None
    product_code: Optional[str] = None
    sale_date: Optional[str] = None
    preorder_date: Optional[str] = None
    preorder_previewable: bool = False
    excluded_territories: Optional[List[str]] = None
    album_price: Optional[str] = None
    track_price: Optional[str] = None
