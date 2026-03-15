from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
from uuid import UUID

from app.core.paths import tenant_path
from app.models.delivery_timeline_event import DeliveryTimelineEvent


class DeliveryTimelineService:
    @staticmethod
    def base_dir(release_id: UUID, tenant_id: str = "default") -> Path:
        return tenant_path(tenant_id, "delivery", str(release_id))

    @staticmethod
    def record(event: DeliveryTimelineEvent, tenant_id: str = "default") -> Dict[str, Any]:
        base = DeliveryTimelineService.base_dir(event.release_id, tenant_id=tenant_id)
        base.mkdir(parents=True, exist_ok=True)

        event_file = base / f"event-{event.id}.json"
        event_file.write_text(event.model_dump_json(indent=2), encoding="utf-8")

        index_path = base / "index.json"
        if index_path.exists():
            try:
                index = json.loads(index_path.read_text(encoding="utf-8"))
            except Exception:
                index = {"release_id": str(event.release_id), "events": []}
        else:
            index = {"release_id": str(event.release_id), "events": []}

        index["events"].append(event_file.name)
        index["last_event"] = event.event_type
        index["last_status"] = event.status
        index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")

        return index

    @staticmethod
    def get_timeline(release_id: UUID, tenant_id: str = "default") -> Dict[str, Any]:
        base = DeliveryTimelineService.base_dir(release_id, tenant_id=tenant_id)
        if not base.exists():
            return {"last_event": None, "events": []}

        index_path = base / "index.json"
        if not index_path.exists():
            return {"last_event": None, "events": []}

        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
        except Exception:
            return {"last_event": None, "events": []}

        events: List[Dict[str, Any]] = []
        for fname in index.get("events", []):
            fpath = base / fname
            if not fpath.exists():
                continue
            try:
                events.append(json.loads(fpath.read_text(encoding="utf-8")))
            except Exception:
                continue

        # Sort by created_at if present
        events_sorted = sorted(events, key=lambda e: e.get("created_at") or "")

        return {
            "last_event": index.get("last_event"),
            "events": events_sorted,
        }
