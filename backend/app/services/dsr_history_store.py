from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from typing import Optional

from app.core.paths import tenant_path


class DSRHistoryStore:
    @staticmethod
    def _base_dir(tenant_id: str) -> Path:
        return tenant_path(tenant_id, "dsr", "history")

    @classmethod
    def record(
        cls,
        *,
        tenant_id: str,
        filename: Optional[str],
        status: str,
        dsrf_version: Optional[str] = None,
        errors: Optional[list[str]] = None,
        warnings: Optional[list[str]] = None,
        summary: Optional[dict] = None,
        row_count: Optional[int] = None,
    ) -> Path:
        base = cls._base_dir(tenant_id)
        base.mkdir(parents=True, exist_ok=True)
        now = datetime.utcnow().isoformat() + "Z"
        payload = {
            "id": str(uuid4()),
            "timestamp": now,
            "filename": filename,
            "status": status,
            "dsrf_version": dsrf_version,
            "errors": errors or [],
            "warnings": warnings or [],
            "summary": summary or {},
            "row_count": row_count,
        }
        path = base / f"dsr-{payload['id']}.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path
