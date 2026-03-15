from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from app.core.paths import tenant_path


@dataclass(frozen=True)
class AutomationLogEntry:
    id: UUID = field(default_factory=uuid4)
    tenant_id: str = "default"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    event_type: str = ""
    rule: str = ""
    action: str = ""
    success: bool = True
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)


class AutomationLogStore:
    @staticmethod
    def _base_dir(tenant_id: str) -> Path:
        return tenant_path(tenant_id, "automation", "logs")

    @classmethod
    def append(cls, entry: AutomationLogEntry) -> Path:
        base = cls._base_dir(entry.tenant_id)
        base.mkdir(parents=True, exist_ok=True)
        p = base / f"log-{entry.created_at.replace(':','-')}-{entry.id}.json"
        payload = asdict(entry)
        payload["id"] = str(entry.id)
        p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return p

    @classmethod
    def list_recent(cls, tenant_id: str, limit: int = 200) -> List[Dict[str, Any]]:
        base = cls._base_dir(tenant_id)
        if not base.exists():
            return []
        files = sorted(base.glob("log-*.json"), key=lambda p: p.name, reverse=True)
        out: List[Dict[str, Any]] = []
        for p in files[:limit]:
            try:
                out.append(json.loads(p.read_text(encoding="utf-8")))
            except Exception:
                continue
        return out

