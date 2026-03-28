"""
Royalty models for AP Studios.
AP Studios commission: 15% of gross amount from DSPs.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

AP_STUDIOS_COMMISSION_PCT = 15.0


class RoyaltyStatement:
    """
    One line of earnings per release/DSP/territory/period.
    Generated automatically when a DSR is processed.
    """

    def __init__(
        self,
        user_id: str,
        tenant_id: str,
        period: str,  # "2026-01" (YYYY-MM)
        dsp: str,  # "spotify", "apple_music", etc.
        release_id: str,
        release_title: str,
        isrc: Optional[str],
        territory: str,  # "US", "Worldwide", etc.
        streams: int,
        gross_amount: float,  # USD - what the DSP paid
        commission_pct: float = AP_STUDIOS_COMMISSION_PCT,
        currency: str = "USD",
        dsr_id: Optional[str] = None,
        id: Optional[str] = None,
        created_at: Optional[str] = None,
    ):
        self.id = id or str(uuid4())
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.period = period
        self.dsp = dsp
        self.release_id = release_id
        self.release_title = release_title
        self.isrc = isrc
        self.territory = territory
        self.streams = streams
        self.gross_amount = round(gross_amount, 6)
        self.commission_pct = commission_pct
        self.commission_amount = round(gross_amount * commission_pct / 100, 6)
        self.net_amount = round(gross_amount - self.commission_amount, 6)
        self.currency = currency
        self.dsr_id = dsr_id
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "period": self.period,
            "dsp": self.dsp,
            "release_id": self.release_id,
            "release_title": self.release_title,
            "isrc": self.isrc,
            "territory": self.territory,
            "streams": self.streams,
            "gross_amount": self.gross_amount,
            "commission_pct": self.commission_pct,
            "commission_amount": self.commission_amount,
            "net_amount": self.net_amount,
            "currency": self.currency,
            "dsr_id": self.dsr_id,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RoyaltyStatement":
        obj = cls.__new__(cls)
        obj.id = d["id"]
        obj.user_id = d["user_id"]
        obj.tenant_id = d["tenant_id"]
        obj.period = d["period"]
        obj.dsp = d["dsp"]
        obj.release_id = d["release_id"]
        obj.release_title = d.get("release_title", "")
        obj.isrc = d.get("isrc")
        obj.territory = d.get("territory", "Worldwide")
        obj.streams = d.get("streams", 0)
        obj.gross_amount = d.get("gross_amount", 0.0)
        obj.commission_pct = d.get("commission_pct", AP_STUDIOS_COMMISSION_PCT)
        obj.commission_amount = d.get("commission_amount", 0.0)
        obj.net_amount = d.get("net_amount", 0.0)
        obj.currency = d.get("currency", "USD")
        obj.dsr_id = d.get("dsr_id")
        obj.created_at = d.get("created_at", "")
        return obj


class Payout:
    """
    Manual payment from AP Studios to an artist.
    Registered by admin after paying via Zelle/PayPal/transfer.
    """

    VALID_STATUSES = {"pending", "paid", "failed"}
    VALID_METHODS = {"zelle", "paypal", "transferencia", "binance", "otro"}

    def __init__(
        self,
        user_id: str,
        tenant_id: str,
        amount: float,
        currency: str = "USD",
        method: str = "zelle",
        status: str = "pending",
        reference: Optional[str] = None,
        note: Optional[str] = None,
        period_from: Optional[str] = None,  # "2026-01"
        period_to: Optional[str] = None,  # "2026-03"
        statement_ids: Optional[list] = None,
        paid_at: Optional[str] = None,
        created_by: Optional[str] = None,
        id: Optional[str] = None,
        created_at: Optional[str] = None,
    ):
        self.id = id or str(uuid4())
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.amount = round(amount, 2)
        self.currency = currency
        self.method = method
        self.status = status
        self.reference = reference
        self.note = note
        self.period_from = period_from
        self.period_to = period_to
        self.statement_ids = statement_ids or []
        self.paid_at = paid_at
        self.created_by = created_by
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "amount": self.amount,
            "currency": self.currency,
            "method": self.method,
            "status": self.status,
            "reference": self.reference,
            "note": self.note,
            "period_from": self.period_from,
            "period_to": self.period_to,
            "statement_ids": self.statement_ids,
            "paid_at": self.paid_at,
            "created_by": self.created_by,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Payout":
        obj = cls.__new__(cls)
        for k, v in d.items():
            setattr(obj, k, v)
        return obj
