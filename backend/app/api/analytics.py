from fastapi import APIRouter, Request

from app.services.analytics_store import AnalyticsStore

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _tenant_id(request: Request) -> str:
    return getattr(request.state, "tenant_id", None) or "default"


@router.get("/overview")
def overview(request: Request):
    tenant_id = _tenant_id(request)
    return AnalyticsStore.overview(tenant_id)

