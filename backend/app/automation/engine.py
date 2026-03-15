from __future__ import annotations

from app.automation.events import AutomationEvent
from app.automation.rules import RULES
from app.automation.settings_store import AutomationSettingsStore


class AutomationEngine:
    @staticmethod
    def process(event: AutomationEvent) -> None:
        settings = AutomationSettingsStore.load(event.tenant_id)
        if not settings.enabled:
            return

        for rule in RULES:
            try:
                if rule.matches(event, settings):
                    rule.execute(event, settings)
            except Exception:
                # rule is responsible for writing its own log entry
                continue

