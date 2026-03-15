from __future__ import annotations

import json
from pathlib import Path
from typing import List

from app.core.paths import tenant_path
from app.models.delivery_package import DeliveryPackageRecord


def _packages_dir(tenant_id: str) -> Path:
    return tenant_path(tenant_id, "packages")


def save_delivery_package(record: DeliveryPackageRecord) -> str:
    base = _packages_dir(record.tenant_id)
    base.mkdir(parents=True, exist_ok=True)

    records_dir = base / "records"
    records_dir.mkdir(parents=True, exist_ok=True)
    record_file = records_dir / f"{record.id}.json"
    record_file.write_text(record.model_dump_json(indent=2), encoding="utf-8")

    index_file = records_dir / "index.json"
    if index_file.exists():
        try:
            index = json.loads(index_file.read_text(encoding="utf-8"))
        except Exception:
            index = {"runs": []}
    else:
        index = {"runs": []}

    index["runs"].append(record_file.name)
    index["last_package_id"] = record.id
    index["last_release_id"] = record.release_id
    index["last_status"] = record.status
    index_file.write_text(json.dumps(index, indent=2), encoding="utf-8")

    return str(record_file)


def list_delivery_packages(tenant_id: str, release_id: str | None = None, limit: int = 50) -> List[DeliveryPackageRecord]:
    records_dir = _packages_dir(tenant_id) / "records"
    if not records_dir.exists():
        return []

    files = sorted(
        [p for p in records_dir.glob("*.json") if p.name != "index.json"],
        key=lambda p: p.name,
        reverse=True,
    )
    results: List[DeliveryPackageRecord] = []
    for file_path in files:
        if len(results) >= max(limit, 1):
            break
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
            record = DeliveryPackageRecord(**payload)
            if release_id and record.release_id != release_id:
                continue
            results.append(record)
        except Exception:
            continue
    return results
