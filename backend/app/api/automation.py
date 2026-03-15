from fastapi import APIRouter, Request

from app.automation.settings_store import AutomationSettingsStore, AutomationSettings
from app.automation.log_store import AutomationLogStore

router = APIRouter(prefix="/automation", tags=["Automation"])


def _tenant_id(request: Request) -> str:
    return getattr(request.state, "tenant_id", None) or "default"


@router.get("/settings")
def get_settings(request: Request):
    tenant_id = _tenant_id(request)
    s = AutomationSettingsStore.load(tenant_id)
    return s.to_dict()


@router.post("/settings")
def update_settings(payload: dict, request: Request):
    tenant_id = _tenant_id(request)
    s = AutomationSettings.from_dict(payload or {})
    AutomationSettingsStore.save(s, tenant_id)
    return s.to_dict()


@router.get("/logs")
def list_logs(request: Request, limit: int = 200):
    tenant_id = _tenant_id(request)
    return AutomationLogStore.list_recent(tenant_id, limit=limit)

