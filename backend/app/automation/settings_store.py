from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from app.core.paths import tenant_path


DEFAULT_SETTINGS: Dict[str, Any] = {
    "enabled": True,
    "rules": {
        "auto_delivery_on_ern_generated": False,
        "auto_statement_on_dsr_ingested": True,
        "auto_payout_on_threshold": False,
        "lock_on_delivery_rejected": True,
    },
    "payout_threshold": 50.0,
}


@dataclass
class AutomationSettings:
    enabled: bool
    rules: Dict[str, bool]
    payout_threshold: float

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "AutomationSettings":
        merged = {**DEFAULT_SETTINGS, **(d or {})}
        merged_rules = {**DEFAULT_SETTINGS["rules"], **(merged.get("rules") or {})}
        return AutomationSettings(
            enabled=bool(merged.get("enabled", True)),
            rules=merged_rules,
            payout_threshold=float(merged.get("payout_threshold", 50.0)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"enabled": self.enabled, "rules": self.rules, "payout_threshold": self.payout_threshold}


class AutomationSettingsStore:
    @staticmethod
    def _path(tenant_id: str) -> Path:
        return tenant_path(tenant_id, "automation", "settings.json")

    @classmethod
    def load(cls, tenant_id: str) -> AutomationSettings:
        p = cls._path(tenant_id)
        if not p.exists():
            return AutomationSettings.from_dict(DEFAULT_SETTINGS)
        try:
            return AutomationSettings.from_dict(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            return AutomationSettings.from_dict(DEFAULT_SETTINGS)

    @classmethod
    def save(cls, settings: AutomationSettings, tenant_id: str) -> Path:
        p = cls._path(tenant_id)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(settings.to_dict(), indent=2), encoding="utf-8")
        return p

