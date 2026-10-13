from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.core.filelock import atomic_write_json, file_lock, read_json
from app.core.paths import is_valid_tenant_id, storage_path, tenant_root


def _index_path():
    # Calculado en cada llamada (no al importar) para poder aislar el storage en tests.
    return storage_path("tenants", "index.json")


def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"


class TenantService:
    @staticmethod
    def _ensure_index():
        path = _index_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(path, "x", encoding="utf-8") as f:
                f.write("[]")
        except FileExistsError:
            pass

    @staticmethod
    def list_tenants() -> List[Dict[str, Any]]:
        TenantService._ensure_index()
        return read_json(_index_path(), list)

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
        if not is_valid_tenant_id(tid):
            raise ValueError("Invalid tenant id")
        TenantService._ensure_index()
        with file_lock(_index_path()):
            tenants = read_json(_index_path(), list)
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
            atomic_write_json(_index_path(), tenants)

        # Ensure tenant root exists
        tenant_root(tid).mkdir(parents=True, exist_ok=True)

        return t

