from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from app.core.paths import tenant_path


@dataclass(frozen=True)
class AnalyticsEvent:
    id: UUID
    event_type: str
    dsp: str
    territory: str
    amount: Decimal
    currency: str
    release_id: Optional[str] = None
    track_id: Optional[str] = None
    artist_id: Optional[str] = None
    timestamp: str = ""

    @staticmethod
    def create(**kwargs) -> "AnalyticsEvent":
        return AnalyticsEvent(
            id=uuid4(),
            timestamp=datetime.utcnow().isoformat() + "Z",
            **kwargs,
        )


class AnalyticsStore:
    @staticmethod
    def _base_dir(tenant_id: str) -> Path:
        return tenant_path(tenant_id, "analytics")

    @classmethod
    def append_event(cls, event: AnalyticsEvent, tenant_id: str) -> Path:
        base = cls._base_dir(tenant_id) / "events"
        base.mkdir(parents=True, exist_ok=True)
        p = base / f"ev-{event.id}.json"
        payload = {
            **event.__dict__,
            "id": str(event.id),
            "amount": str(event.amount),
        }
        p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return p

    @classmethod
    def add_daily_revenue(cls, *, day: date, dsp: str, territory: str, amount: Decimal, currency: str, tenant_id: str) -> Path:
        base = cls._base_dir(tenant_id) / "daily"
        base.mkdir(parents=True, exist_ok=True)
        key = f"{day.isoformat()}__{dsp}__{territory}__{currency}".replace("/", "-")
        p = base / f"{key}.json"
        existing = {"day": day.isoformat(), "dsp": dsp, "territory": territory, "currency": currency, "revenue": "0"}
        if p.exists():
            try:
                existing = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                pass
        revenue = Decimal(str(existing.get("revenue") or "0")) + amount
        existing["revenue"] = str(revenue)
        p.write_text(json.dumps(existing, indent=2), encoding="utf-8")
        return p

    @classmethod
    def overview(cls, tenant_id: str) -> Dict:
        base = cls._base_dir(tenant_id) / "daily"
        if not base.exists():
            return {"total_revenue": 0.0, "currency": "USD", "by_dsp": {}, "by_territory": {}}

        total = Decimal("0")
        currency = "USD"
        by_dsp: Dict[str, Decimal] = {}
        by_territory: Dict[str, Decimal] = {}
        for p in base.glob("*.json"):
            try:
                row = json.loads(p.read_text(encoding="utf-8"))
                rev = Decimal(str(row.get("revenue") or "0"))
                total += rev
                currency = row.get("currency") or currency
                dsp = row.get("dsp") or "unknown"
                terr = row.get("territory") or "unknown"
                by_dsp[dsp] = by_dsp.get(dsp, Decimal("0")) + rev
                by_territory[terr] = by_territory.get(terr, Decimal("0")) + rev
            except Exception:
                continue

        return {
            "total_revenue": float(total),
            "currency": currency,
            "by_dsp": {k: float(v) for k, v in sorted(by_dsp.items(), key=lambda kv: kv[1], reverse=True)},
            "by_territory": {k: float(v) for k, v in sorted(by_territory.items(), key=lambda kv: kv[1], reverse=True)},
        }
