from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from app.automation.actions import AutomationActions
from app.automation.events import AutomationEvent
from app.automation.log_store import AutomationLogEntry, AutomationLogStore
from app.automation.settings_store import AutomationSettings


class BaseRule:
    key: str = ""
    name: str = ""

    def matches(self, event: AutomationEvent, settings: AutomationSettings) -> bool:
        raise NotImplementedError

    def execute(self, event: AutomationEvent, settings: AutomationSettings) -> None:
        raise NotImplementedError


class LockOnDeliveryRejectedRule(BaseRule):
    key = "lock_on_delivery_rejected"
    name = "Lock release on delivery rejected"

    def matches(self, event: AutomationEvent, settings: AutomationSettings) -> bool:
        return bool(settings.rules.get(self.key, True)) and event.type == "delivery.rejected" and bool(event.release_id)

    def execute(self, event: AutomationEvent, settings: AutomationSettings) -> None:
        reason = (event.payload or {}).get("reason") or "Delivery rejected"
        try:
            res = AutomationActions.lock_release(release_id=event.release_id, tenant_id=event.tenant_id, reason=reason)
            AutomationLogStore.append(
                AutomationLogEntry(
                    tenant_id=event.tenant_id,
                    event_type=event.type,
                    rule=self.key,
                    action="lock_release",
                    success=res.success,
                    message=res.message,
                    data={"release_id": event.release_id, "reason": reason},
                )
            )
        except Exception as e:
            AutomationLogStore.append(
                AutomationLogEntry(
                    tenant_id=event.tenant_id,
                    event_type=event.type,
                    rule=self.key,
                    action="lock_release",
                    success=False,
                    message=str(e),
                    data={"release_id": event.release_id, "reason": reason},
                )
            )


RULES: List[BaseRule] = [
    LockOnDeliveryRejectedRule(),
]

