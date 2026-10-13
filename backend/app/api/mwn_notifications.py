from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from uuid import UUID

from app.core.auth import ensure_release_access, is_admin
from app.services.catalog_service import CatalogService
from app.services.mwn_store import mwn_store


def _authorize(request: Request, release_id: str, tenant_id: str) -> None:
    try:
        rid = UUID(str(release_id))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid release_id")
    release = CatalogService.get_release_by_id(rid, tenant_id=tenant_id)
    if release is None:
        if is_admin(request):
            return
        raise HTTPException(status_code=404, detail="Release not found")
    ensure_release_access(request, release)

router = APIRouter(prefix="/releases", tags=["MWN"])


@router.get("/{release_id}/mwn")
async def list_mwn_for_release(release_id: str, request: Request):
    tenant_id = request.state.tenant_id
    _authorize(request, release_id, tenant_id)
    notifications = mwn_store.list_by_release(tenant_id, release_id)
    return {
        "release_id": release_id,
        "notifications": [
            {
                "id": n["id"],
                "recipient_dpid": n.get("recipient_dpid"),
                "status": n.get("status"),
                "created_at": n.get("created_at"),
                "updated_at": n.get("updated_at"),
            }
            for n in notifications
        ],
    }


@router.get("/{release_id}/mwn/{notification_id}/xml")
async def get_mwn_xml(release_id: str, notification_id: str, request: Request):
    tenant_id = request.state.tenant_id
    _authorize(request, release_id, tenant_id)
    notifications = mwn_store.list_by_release(tenant_id, release_id)
    notif = next((n for n in notifications if n.get("id") == notification_id), None)
    if not notif:
        raise HTTPException(status_code=404, detail="MWN notification not found")
    return Response(
        content=notif.get("xml_content", ""),
        media_type="application/xml",
        headers={
            "Content-Disposition": f'attachment; filename="{notification_id}.xml"'
        },
    )
