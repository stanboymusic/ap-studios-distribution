from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel


class DeliveryPackageRecord(BaseModel):
    id: str
    release_id: str
    tenant_id: str
    file_path: str
    status: str
    created_at: datetime
    manifest_path: Optional[str] = None

    @classmethod
    def create(
        cls,
        release_id: str,
        tenant_id: str,
        file_path: str,
        status: str = "PACKAGE_CREATED",
        manifest_path: Optional[str] = None,
    ) -> "DeliveryPackageRecord":
        return cls(
            id=str(uuid4()),
            release_id=release_id,
            tenant_id=tenant_id,
            file_path=file_path,
            status=status,
            created_at=datetime.utcnow(),
            manifest_path=manifest_path,
        )
