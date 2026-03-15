from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from uuid import UUID

from app.core.paths import tenant_path
from app.models.validation_run import ValidationRun


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class ValidationHistoryService:
    @staticmethod
    def base_dir(release_id: UUID, tenant_id: str = "default") -> Path:
        return tenant_path(tenant_id, "validation", str(release_id))

    @staticmethod
    def save_run(run: ValidationRun, xml_bytes: Optional[bytes] = None, tenant_id: str = "default") -> Dict[str, Any]:
        base = ValidationHistoryService.base_dir(run.release_id, tenant_id=tenant_id)
        base.mkdir(parents=True, exist_ok=True)

        run_file = base / f"run-{run.id}.json"
        run_file.write_text(run.model_dump_json(indent=2), encoding="utf-8")

        index_path = base / "index.json"
        if index_path.exists():
            try:
                index = json.loads(index_path.read_text(encoding="utf-8"))
            except Exception:
                index = {"release_id": str(run.release_id), "runs": []}
        else:
            index = {"release_id": str(run.release_id), "runs": []}

        index["runs"].append(run_file.name)
        index["last_status"] = run.status
        index["last_run_id"] = str(run.id)
        index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")

        return index

    @staticmethod
    def get_history(release_id: UUID, tenant_id: str = "default") -> Dict[str, Any]:
        base = ValidationHistoryService.base_dir(release_id, tenant_id=tenant_id)
        if not base.exists():
            return {"last_status": None, "runs": []}

        index_path = base / "index.json"
        if not index_path.exists():
            return {"last_status": None, "runs": []}

        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
        except Exception:
            return {"last_status": None, "runs": []}

        runs: List[Dict[str, Any]] = []
        for fname in index.get("runs", []):
            fpath = base / fname
            if not fpath.exists():
                continue
            try:
                runs.append(json.loads(fpath.read_text(encoding="utf-8")))
            except Exception:
                continue

        return {
            "last_status": index.get("last_status"),
            "runs": runs,
        }

    @staticmethod
    def build_xml_hash(xml_bytes: bytes) -> str:
        return _sha256_bytes(xml_bytes)
