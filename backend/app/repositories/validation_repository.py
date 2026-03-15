from __future__ import annotations

import json
from pathlib import Path
from typing import List

from app.core.paths import tenant_path
from app.models.validation_result import ValidationResult


def _results_dir(release_id: str, tenant_id: str) -> Path:
    return tenant_path(tenant_id, "validation", release_id, "results")


def save_validation(result: ValidationResult, tenant_id: str = "default") -> str:
    base = _results_dir(result.release_id, tenant_id=tenant_id)
    base.mkdir(parents=True, exist_ok=True)

    result_file = base / f"{result.id}.json"
    result_file.write_text(result.model_dump_json(indent=2), encoding="utf-8")

    index_file = base / "index.json"
    if index_file.exists():
        try:
            index = json.loads(index_file.read_text(encoding="utf-8"))
        except Exception:
            index = {"release_id": result.release_id, "runs": []}
    else:
        index = {"release_id": result.release_id, "runs": []}

    index["runs"].append(result_file.name)
    index["last_status"] = result.status
    index["last_validation_id"] = result.id
    index_file.write_text(json.dumps(index, indent=2), encoding="utf-8")

    return str(result_file)


def list_validations(release_id: str, tenant_id: str = "default", limit: int = 50) -> List[ValidationResult]:
    base = _results_dir(release_id, tenant_id=tenant_id)
    if not base.exists():
        return []

    index_file = base / "index.json"
    if index_file.exists():
        try:
            index = json.loads(index_file.read_text(encoding="utf-8"))
            run_files = list(reversed(index.get("runs") or []))
        except Exception:
            run_files = []
    else:
        run_files = []

    if not run_files:
        run_files = sorted(
            [p.name for p in base.glob("*.json") if p.name != "index.json"],
            reverse=True,
        )

    results: List[ValidationResult] = []
    for run_file in run_files[: max(limit, 1)]:
        fpath = base / run_file
        if not fpath.exists():
            continue
        try:
            payload = json.loads(fpath.read_text(encoding="utf-8"))
            results.append(ValidationResult(**payload))
        except Exception:
            continue
    return results
