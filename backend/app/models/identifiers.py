from __future__ import annotations

from datetime import datetime
from typing import Dict

from pydantic import BaseModel, Field


class IdentifierPool(BaseModel):
    type: str
    prefix: str
    last_value: int


class IdentifierState(BaseModel):
    isrc_sequences: Dict[str, int] = Field(default_factory=dict)
    upc_sequences: Dict[str, int] = Field(default_factory=dict)
    reserved_isrc: Dict[str, dict] = Field(default_factory=dict)
    reserved_upc: Dict[str, dict] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
