from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.core.paths import storage_path, tenant_root


TENANTS_INDEX = storage_path("tenants", "index.json")


def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"


class TenantService:
    @staticmethod
    def _ensure_index():
        TENANTS_INDEX.parent.mkdir(parents=True, exist_ok=True)
        if not TENANTS_INDEX.exists():
            TENANTS_INDEX.write_text(json.dumps([], indent=2), encoding="utf-8")

    @staticmethod
    def list_tenants() -> List[Dict[str, Any]]:
        TenantService._ensure_index()
        try:
            return json.loads(TENANTS_INDEX.read_text(encoding="utf-8"))
        except Exception:
            return []

    @staticmethod
    def get_tenant(tenant_id: str) -> Optional[Dict[str, Any]]:
        tid = (tenant_id or "").strip()
        if not tid:
            return None
        for t in TenantService.list_tenants():
            if t.get("id") == tid:
                return t
        return None

    @staticmethod
    def ensure_default_tenant() -> Dict[str, Any]:
        existing = TenantService.get_tenant("default")
        if existing:
            return existing
        return TenantService.create_tenant("default", "Default Tenant")

    @staticmethod
    def create_tenant(tenant_id: str, name: str) -> Dict[str, Any]:
        tid = (tenant_id or "").strip()
        if not tid:
            tid = "tenant-" + str(uuid4())
        tenants = TenantService.list_tenants()
        if any(t.get("id") == tid for t in tenants):
            return next(t for t in tenants if t.get("id") == tid)

        t = {
            "id": tid,
            "name": name or tid,
            "slug": (name or tid).lower().replace(" ", "-"),
            "settings": {"branding": {}, "demo_mode": False},
            "created_at": _now(),
        }
        tenants.append(t)
        TENANTS_INDEX.write_text(json.dumps(tenants, indent=2), encoding="utf-8")

        # Ensure tenant root exists
        tenant_root(tid).mkdir(parents=True, exist_ok=True)

        return t

