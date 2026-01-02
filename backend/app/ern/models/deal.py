from pydantic import BaseModel
from typing import List

class CommercialModel(BaseModel):
    model: str
    use_type: str

class Deal(BaseModel):
    internal_id: str
    release: str
    territories: List[str]
    start_date: str
    commercial_models: List[CommercialModel]