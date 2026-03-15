from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.services.catalog_service import CatalogService


def update_release_status(release_id: str, status: str, tenant_id: str = "default") -> bool:
    try:
        release_uuid = UUID((release_id or "").strip())
    except Exception:
        return False

    release = CatalogService.get_release_by_id(release_uuid, tenant_id=tenant_id)
    if not release:
        return False

    release.status = status
    release.updated_at = datetime.utcnow().isoformat()
    CatalogService.save_release(release, tenant_id=tenant_id)
    return True
