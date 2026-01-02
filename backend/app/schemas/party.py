from pydantic import BaseModel
from typing import Optional


class Party(BaseModel):
    party_id: str
    name: str
    role: str