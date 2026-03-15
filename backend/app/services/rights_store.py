from __future__ import annotations

import json
from pathlib import Path
from typing import List

from app.core.paths import tenant_path
from app.models.rights import RightsConfiguration


class RightsStore:
    @staticmethod
    def _base_dir(tenant_id: str) -> Path:
        return tenant_path(tenant_id, "rights")

    @classmethod
    def list_configurations(cls, tenant_id: str) -> List[RightsConfiguration]:
        base = cls._base_dir(tenant_id)
        if not base.exists():
            return []

        configs: List[RightsConfiguration] = []
        for p in sorted(base.glob("config-*.json")):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                configs.append(RightsConfiguration.model_validate(data))
            except Exception:
                continue
        return configs

    @classmethod
    def save_configuration(cls, config: RightsConfiguration, tenant_id: str) -> Path:
        base = cls._base_dir(tenant_id)
        base.mkdir(parents=True, exist_ok=True)

        path = base / f"config-{config.id}.json"
        path.write_text(config.model_dump_json(indent=2), encoding="utf-8")
        return path
