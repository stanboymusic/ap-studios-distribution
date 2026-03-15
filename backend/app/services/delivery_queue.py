from __future__ import annotations

import os
from types import SimpleNamespace
from typing import Any, Dict


def _mode() -> str:
    return (os.getenv("DELIVERY_QUEUE_MODE") or "sync").strip().lower()


def enqueue_delivery(release_id: str, connector_id: str, tenant_id: str = "default") -> Dict[str, Any]:
    mode = _mode()
    if mode == "celery":
        try:
            from workers.delivery_worker import deliver_release_task

            task = deliver_release_task.delay(release_id, connector_id, tenant_id)
            return {
                "status": "queued",
                "mode": "celery",
                "task_id": task.id,
                "release_id": release_id,
                "connector_id": connector_id,
            }
        except Exception as exc:
            # fallback to sync execution if celery is unavailable in this environment
            sync_result = _run_sync(release_id, connector_id, tenant_id)
            sync_result["queue_error"] = str(exc)
            return sync_result

    return _run_sync(release_id, connector_id, tenant_id)


def _run_sync(release_id: str, connector_id: str, tenant_id: str) -> Dict[str, Any]:
    from app.api.delivery import SFTPDeliveryRequest, deliver_via_sftp

    fake_request = SimpleNamespace(state=SimpleNamespace(tenant_id=tenant_id))
    payload = SFTPDeliveryRequest(release_id=release_id, connector_id=connector_id)
    result = deliver_via_sftp(payload, fake_request)
    return {
        "status": "completed",
        "mode": "sync",
        "release_id": release_id,
        "connector_id": connector_id,
        "result": result,
    }
