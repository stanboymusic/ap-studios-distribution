from __future__ import annotations

import os
from typing import Any, Dict

import requests
from celery import Celery


BROKER_URL = os.getenv("CELERY_BROKER_URL") or "redis://redis:6379/0"
BACKEND_URL = os.getenv("CELERY_RESULT_BACKEND") or BROKER_URL
INTERNAL_API_BASE_URL = (os.getenv("INTERNAL_API_BASE_URL") or "http://127.0.0.1:8000").rstrip("/")

celery_app = Celery("delivery", broker=BROKER_URL, backend=BACKEND_URL)


@celery_app.task(name="delivery.deliver_release", bind=True, max_retries=5)
def deliver_release_task(self, release_id: str, connector_id: str, tenant_id: str = "default") -> Dict[str, Any]:
    url = f"{INTERNAL_API_BASE_URL}/api/delivery/sftp"
    try:
        response = requests.post(
            url,
            json={
                "release_id": release_id,
                "connector_id": connector_id,
            },
            headers={
                "X-Tenant-Id": tenant_id,
                "Content-Type": "application/json",
            },
            timeout=120,
        )
    except requests.RequestException as exc:
        # Network/transient transport issue.
        raise self.retry(exc=exc, countdown=30 * (self.request.retries + 1))

    payload: Dict[str, Any]
    try:
        payload = response.json()
    except Exception:
        payload = {"raw": response.text}

    if response.status_code >= 500:
        # Backend-side transient fault: retry with linear backoff.
        raise self.retry(
            exc=RuntimeError(f"Delivery API server error ({response.status_code}): {payload}"),
            countdown=30 * (self.request.retries + 1),
        )

    if response.status_code >= 400:
        # Client/domain errors should not be retried blindly.
        raise RuntimeError(f"Delivery API failed ({response.status_code}): {payload}")

    return payload
