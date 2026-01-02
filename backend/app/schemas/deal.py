from pydantic import BaseModel
from datetime import date
from typing import List


class Deal(BaseModel):
    territories: List[str]  # ISO 3166-1 or "Worldwide"
    start_date: date
    commercial_model: str   # Streaming, Download