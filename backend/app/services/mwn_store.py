"""
Store for MWN notification history.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.core.paths import tenant_path


class MWNStore:
    def __init__(self, storage_base: Optional[str] = None):
        self._base_override = Path(storage_base) if storage_base else None

    def _tenant_dir(self, tenant_id: str) -> Path:
        if self._base_override:
            path = self._base_override / "mwn" / tenant_id
        else:
            path = tenant_path(tenant_id, "mwn")
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save(
        self,
        tenant_id: str,
        release_id: str,
        rights_config_id: str,
        recipient_dpid: str,
        xml_content: str,
        status: str = "pending",
    ) -> dict:
        notification_id = f"mwn-{release_id}-{rights_config_id}"
        now = datetime.now(timezone.utc).isoformat()
        record = {
            "id": notification_id,
            "tenant_id": tenant_id,
            "release_id": release_id,
            "rights_config_id": rights_config_id,
            "recipient_dpid": recipient_dpid,
            "status": status,
            "xml_content": xml_content,
            "created_at": now,
            "updated_at": now,
            "delivery_attempts": [],
        }
        path = self._tenant_dir(tenant_id) / f"{notification_id}.json"
        path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        return record

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

    def list_by_release(self, tenant_id: str, release_id: str) -> list[dict]:
        tenant_dir = self._tenant_dir(tenant_id)
        results = []
        for path in tenant_dir.glob(f"mwn-{release_id}-*.json"):
            try:
                results.append(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                continue
        return sorted(results, key=lambda x: x.get("created_at") or "")

    def list_pending(self, tenant_id: str) -> list[dict]:
        tenant_dir = self._tenant_dir(tenant_id)
        results = []
        for path in tenant_dir.glob("mwn-*.json"):
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if record.get("status") == "pending":
                results.append(record)
        return results


mwn_store = MWNStore()
