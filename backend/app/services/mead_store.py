"""
MEAD notification history store.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.core.paths import tenant_path


class MEADStore:
    def __init__(self, storage_base: Optional[str] = None):
        self._base_override = Path(storage_base) if storage_base else None

    def _tenant_dir(self, tenant_id: str) -> Path:
        if self._base_override:
            path = self._base_override / "mead" / tenant_id
        else:
            path = tenant_path(tenant_id, "mead")
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save(
        self,
        tenant_id: str,
        release_id: str,
        recipient_dpid: str,
        xml_content: str,
        mead_data: dict,
        status: str = "pending",
    ) -> dict:
        notification_id = (
            f"mead-{release_id}-{recipient_dpid.replace('-', '').lower()}-"
            f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        )
        now = datetime.now(timezone.utc).isoformat()
        record = {
            "id": notification_id,
            "tenant_id": tenant_id,
            "release_id": release_id,
            "recipient_dpid": recipient_dpid,
            "status": status,
            "xml_content": xml_content,
            "mead_data": mead_data,
            "created_at": now,
            "updated_at": now,
            "delivery_attempts": [],
        }
        path = self._tenant_dir(tenant_id) / f"{notification_id}.json"
        path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        return record

    def list_by_release(self, tenant_id: str, release_id: str) -> list[dict]:
        tenant_dir = self._tenant_dir(tenant_id)
        results = []
        for path in tenant_dir.glob(f"mead-{release_id}-*.json"):
            try:
                results.append(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                continue
        return sorted(results, key=lambda x: x.get("created_at") or "")

    def update_status(
        self,
        tenant_id: str,
        notification_id: str,
        status: str,
        error: Optional[str] = None,
    ) -> Optional[dict]:
        path = self._tenant_dir(tenant_id) / f"{notification_id}.json"
        if not path.exists():
            return None
        record = json.loads(path.read_text(encoding="utf-8"))
        record["status"] = status
        record["updated_at"] = datetime.now(timezone.utc).isoformat()
        record["delivery_attempts"].append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": status,
                "error": error,
            }
        )
        path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        return record


mead_store = MEADStore()
