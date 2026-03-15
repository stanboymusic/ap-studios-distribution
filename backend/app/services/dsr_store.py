from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from app.core.paths import tenant_path
from app.models.dsr import SaleEvent, RevenueLineItem


class DsrStore:
    @staticmethod
    def _base_dir(tenant_id: str) -> Path:
        return tenant_path(tenant_id, "dsr")

    @classmethod
    def append_sales(cls, sales: List[SaleEvent], tenant_id: str) -> List[Path]:
        base = cls._base_dir(tenant_id) / "sales"
        base.mkdir(parents=True, exist_ok=True)
        paths: List[Path] = []
        for s in sales:
            p = base / f"sale-{s.id}.json"
            p.write_text(s.model_dump_json(indent=2), encoding="utf-8")
            paths.append(p)
        return paths

    @classmethod
    def append_line_items(cls, items: List[RevenueLineItem], tenant_id: str) -> List[Path]:
        base = cls._base_dir(tenant_id) / "ledger"
        base.mkdir(parents=True, exist_ok=True)
        paths: List[Path] = []
        for li in items:
            p = base / f"li-{li.id}.json"
            p.write_text(li.model_dump_json(indent=2), encoding="utf-8")
            paths.append(p)
        return paths

    @classmethod
    def list_ledger(cls, tenant_id: str) -> List[RevenueLineItem]:
        base = cls._base_dir(tenant_id) / "ledger"
        if not base.exists():
            return []
        items: List[RevenueLineItem] = []
        for p in sorted(base.glob("li-*.json")):
            try:
                items.append(RevenueLineItem.model_validate(json.loads(p.read_text(encoding="utf-8"))))
            except Exception:
                continue
        return items

    @classmethod
    def get_ledger_item(cls, item_id: UUID, tenant_id: str) -> Optional[RevenueLineItem]:
        p = cls._base_dir(tenant_id) / "ledger" / f"li-{item_id}.json"
        if not p.exists():
            return None
        return RevenueLineItem.model_validate(json.loads(p.read_text(encoding="utf-8")))
