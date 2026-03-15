from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from app.services.mwn_store import mwn_store

router = APIRouter(prefix="/releases", tags=["MWN"])


@router.get("/{release_id}/mwn")
async def list_mwn_for_release(release_id: str, request: Request):
    tenant_id = request.state.tenant_id
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
