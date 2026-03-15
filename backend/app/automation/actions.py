from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import HTTPException

from app.services.catalog_service import CatalogService


@dataclass(frozen=True)
class ActionResult:
    success: bool
    message: str


class AutomationActions:
    @staticmethod
    def ensure_ern_generated(*, release_id: str, tenant_id: str) -> ActionResult:
        return ActionResult(success=True, message="noop")

    @staticmethod
    def deliver_to_connector(*, release_id: str, connector_id: str, tenant_id: str) -> ActionResult:
        return ActionResult(success=False, message="deliver_to_connector not implemented in automation yet")

    @staticmethod
    def lock_release(*, release_id: str, tenant_id: str, reason: str) -> ActionResult:
        rid = UUID(release_id)
        release = CatalogService.get_release_by_id(rid, tenant_id=tenant_id)
        if not release:
            raise HTTPException(status_code=404, detail="Release not found")
        release.status = "locked"
        release.validation["lock_reason"] = reason
        CatalogService.save_release(release, tenant_id=tenant_id)
        return ActionResult(success=True, message="Release locked")
