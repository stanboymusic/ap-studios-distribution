from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import date, datetime
from typing import List, Optional, Literal
from decimal import Decimal

class SaleEvent(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    dsp: str
    release_ref: str
    track_ref: Optional[str] = None
    usage_type: str
    territory: str
    quantity: int
    gross_amount: Decimal
    currency: str
    period_start: date
    period_end: date

class RevenueLineItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    sale_event_id: UUID
    party_reference: str
    role: str
    amount: Decimal
    currency: str
    dsp: str
    usage_type: str
    territory: str
    period_start: date
    period_end: date

class Statement(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    party_reference: str
    period_start: date
    period_end: date
    total_amount: Decimal
    currency: str
    breakdown_by_dsp: dict[str, Decimal] = {}
    breakdown_by_usage: dict[str, Decimal] = {}
    lines: List[RevenueLineItem] = []
