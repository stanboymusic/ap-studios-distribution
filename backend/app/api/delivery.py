from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from app.services.delivery import build_delivery_package
from app.ddex.ern_builder import build_ern
from app.services.catalog_service import CatalogService
from app.services.sftp_connector import SFTPConnector
from app.services.transport_ddex import build_delivery_manifest, upload_with_retry
from app.config.sftp import SFTP_CONNECTORS
from app.services.delivery_logger import log_event
from app.services.delivery_queue import enqueue_delivery
from app.services.mwn_parser import parse_mwn
from app.ern.persistence.ern_store import ErnStore
from app.models.delivery_timeline_event import DeliveryTimelineEvent
from app.services.delivery_timeline_service import DeliveryTimelineService
from app.repositories.delivery_repository import list_delivery_packages
from datetime import datetime
import json
import logging
from pathlib import Path
from uuid import UUID
from app.core.paths import sandbox_dsp_path, tenant_path
from app.automation.engine import AutomationEngine
from app.automation.events import AutomationEvent
from app.core.auth import require_admin
from app.repositories import user_repository as user_repo
from app.services.notification_service import notify_release_delivered

logger = logging.getLogger(__name__)
from typing import List, Optional

router = APIRouter(prefix="/delivery", tags=["Delivery"], dependencies=[Depends(require_admin)])

class SFTPDeliveryRequest(BaseModel):
    release_id: str
    connector_id: str

class DeliveryQueueRequest(BaseModel):
    release_id: str
    connector_id: str

class DeliveryOverview(BaseModel):
    release_id: str
    title: str
    dsp: str
    status: str
    last_event: Optional[str] = None

class DeliveryEvent(BaseModel):
    event_type: str
    dsp: str
    message: str
    created_at: str


def _update_release_pipeline_status(release_obj, tenant_id: str, status: str):
    release_obj.status = status
    release_obj.updated_at = datetime.utcnow().isoformat()
    CatalogService.save_release(release_obj, tenant_id=tenant_id)




def _notify_release_delivered(release_obj, tenant_id: str):
    owner_id = getattr(release_obj, "owner_user_id", None)
    if not owner_id:
        return
    user = user_repo.get_by_id(str(owner_id), tenant_id)
    if not user:
        return
    try:
        notify_release_delivered(
            email=user.email,
            artist_name=user.email.split("@")[0],
            release_title=getattr(release_obj, "title", "Untitled Release"),
            release_type=str(getattr(release_obj, "release_type", "Single")),
            upc=getattr(release_obj, "upc", None),
            release_date=getattr(release_obj, "original_release_date", None),
            territories=", ".join(getattr(release_obj, "territories", []) or ["Worldwide"]),
        )
    except Exception as exc:
        logger.warning("Failed to send release delivery notification: %s", exc)


def _resolve_release_delivery_assets(release_id: str, release, tenant_id: str) -> tuple[str, list, str]:
    # ERN (prefer generated latest)
    store = ErnStore()
    latest_path = store.base / str(release_id) / "latest" / "ern.xml"
    if latest_path.exists():
        ern_xml = latest_path.read_bytes().decode("utf-8")
    else:
        ern_xml = build_ern(release)

    # Cover art
    cover_path = ""
    if getattr(release, "artwork_id", None):
        asset = CatalogService.get_asset_by_id(str(release.artwork_id), tenant_id=tenant_id)
        if asset and asset.get("path"):
            cover_path = asset["path"]

    tracks = getattr(release, "tracks", []) or []
    return ern_xml, tracks, cover_path


def _create_delivery_package_for_release(release_id: str, release, tenant_id: str) -> str:
    ern_xml, tracks, cover_path = _resolve_release_delivery_assets(
        release_id=release_id,
        release=release,
        tenant_id=tenant_id,
    )
    artist_name = "Unknown"
    if release.artist_id:
        artist = CatalogService.get_artist_by_id(release.artist_id, tenant_id=tenant_id)
        if artist:
            artist_name = artist.name
    try:
        return build_delivery_package(
            release_id,
            ern_xml,
            tracks,
            cover_path,
            artist_name,
            tenant_id=tenant_id,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/package/{release_id}")
def create_package(release_id: str, request: Request):
    tenant_id = request.state.tenant_id
    rid = (release_id or "").strip()
    try:
        release_uuid = UUID(rid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid release_id (expected UUID)")

    release = CatalogService.get_release_by_id(release_uuid, tenant_id=tenant_id)
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")

    if release.validation.get("ddex_status") not in ["validated", "external_unavailable", "generated"]:
        raise HTTPException(status_code=400, detail="Release must be validated before packaging")

    package_path = _create_delivery_package_for_release(str(release_uuid), release, tenant_id=tenant_id)
    return {
        "status": "PACKAGE_CREATED",
        "release_id": str(release_uuid),
        "path": package_path,
    }


@router.get("/package/{release_id}")
def get_package_history(release_id: str, request: Request, limit: int = 20):
    tenant_id = request.state.tenant_id
    runs = [item.model_dump() for item in list_delivery_packages(tenant_id=tenant_id, release_id=release_id, limit=limit)]
    return {"release_id": release_id, "packages": runs}


@router.post("/{release_id}/export")
def export(release_id: str, request: Request):
    tenant_id = request.state.tenant_id
    rid = (release_id or "").strip()
    try:
        release_uuid = UUID(rid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid release_id (expected UUID)")

    # Find release
    release = CatalogService.get_release_by_id(release_uuid, tenant_id=tenant_id)
    if release:
        # Check validation status
        if release.validation.get("ddex_status") not in ["validated", "external_unavailable", "generated"]:
            raise HTTPException(
                status_code=400,
                detail="Release must be validated before delivery"
            )

        zip_path = _create_delivery_package_for_release(str(release_uuid), release, tenant_id=tenant_id)

        # Timeline formal: export created zip
        try:
            DeliveryTimelineService.record(DeliveryTimelineEvent.create(
                release_id=release_uuid,
                dsp="EXPORT",
                channel="api",
                event_type="EXPORTED",
                status="success",
                message="Delivery package exported",
                payload_path=str(zip_path),
            ), tenant_id=tenant_id)
        except Exception:
            pass

        return {
            "status": "exported",
            "path": zip_path,
            "package_name": zip_path.split("/")[-1]
        }
    raise HTTPException(status_code=404, detail="Release not found")


@router.post("/sftp")
def deliver_via_sftp(request: SFTPDeliveryRequest, http_request: Request):
    tenant_id = http_request.state.tenant_id
    rid = (request.release_id or "").strip()
    try:
        release_uuid = UUID(rid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid release_id (expected UUID)")

    # Find release
    release = CatalogService.get_release_by_id(release_uuid, tenant_id=tenant_id)
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")

    # Check if connector exists
    if request.connector_id not in SFTP_CONNECTORS:
        raise HTTPException(status_code=400, detail=f"Connector {request.connector_id} not configured")

    config = SFTP_CONNECTORS[request.connector_id]

    # Check validation
    if release.validation.get("ddex_status") not in ["validated", "external_unavailable", "generated"]:
        raise HTTPException(status_code=400, detail="Release must be validated before delivery")

    # Update delivery status
    release.delivery["status"] = "uploading"
    release.delivery["connector_id"] = request.connector_id
    _update_release_pipeline_status(release, tenant_id=tenant_id, status="VALIDATED")

    # Log event (legacy + timeline)
    log_event(
        release_id=release.id,
        dsp=request.connector_id.upper().replace("_", " "),
        event_type="CREATED",
        message=f"Delivery initiated to {request.connector_id}",
        tenant_id=tenant_id,
    )

    zip_path = None
    try:
        zip_path = _create_delivery_package_for_release(request.release_id, release, tenant_id=tenant_id)

        connector = SFTPConnector(
            host=config["host"],
            port=config["port"],
            username=config["username"],
            password=config["password"]
        )

        # Log uploading
        log_event(
            release_id=release.id,
            dsp=request.connector_id.upper().replace("_", " "),
            event_type="UPLOADING",
            message=f"Uploading ZIP to {config['host']}:{config['port']}",
            tenant_id=tenant_id,
        )

        remote_path = f"{config['remote_path']}/delivery_{request.release_id}.zip"

        manifest = upload_with_retry(
            connector=connector,
            local_path=zip_path,
            remote_path=remote_path,
            retries=int(config.get("retries", 3)),
            connect_timeout_seconds=float(config.get("timeout_seconds", 3.0)),
            retry_backoff_seconds=float(config.get("retry_backoff_seconds", 1.5)),
        )

        # Update status
        release.delivery["status"] = "uploaded"
        release.delivery["delivered_at"] = datetime.utcnow().isoformat()
        release.delivery["manifest"] = manifest
        _update_release_pipeline_status(release, tenant_id=tenant_id, status="DELIVERED")
        _notify_release_delivered(release, tenant_id)

        # Log uploaded
        log_event(
            release_id=release.id,
            dsp=request.connector_id.upper().replace("_", " "),
            event_type="UPLOADED",
            message=f"ZIP uploaded successfully to {remote_path} (attempt {manifest.get('attempt')})",
            tenant_id=tenant_id,
        )

        # Timeline formal: include payload path
        try:
            DeliveryTimelineService.record(DeliveryTimelineEvent.create(
                release_id=release.id,
                dsp=request.connector_id.upper().replace("_", " "),
                channel="sftp",
                event_type="UPLOADED",
                status="success",
                message=f"ZIP uploaded to {remote_path} (sha256={manifest.get('sha256')})",
                payload_path=str(zip_path),
            ), tenant_id=tenant_id)
        except Exception:
            pass

        return {
            "status": "delivered",
            "connector": request.connector_id,
            "remote_path": remote_path,
            "manifest": manifest,
        }

    except Exception as e:
        # Fallback for local sandbox if SFTP is not running
        hostname = (config or {}).get("host", "localhost")
        if "localhost" in hostname or "127.0.0.1" in hostname:
            try:
                if not zip_path:
                    raise RuntimeError("No delivery package was generated")
                import shutil
                sandbox_incoming = sandbox_dsp_path("incoming")
                sandbox_incoming.mkdir(parents=True, exist_ok=True)
                dest_path = sandbox_incoming / f"delivery_{request.release_id}.zip"
                shutil.copy2(zip_path, dest_path)
                
                # Update status as if it were uploaded
                release.delivery["status"] = "uploaded"
                release.delivery["delivered_at"] = datetime.utcnow().isoformat()
                release.delivery["manifest"] = build_delivery_manifest(str(dest_path), str(dest_path))
                _update_release_pipeline_status(release, tenant_id=tenant_id, status="DELIVERED")
                _notify_release_delivered(release, tenant_id)

                log_event(
                    release_id=release.id,
                    dsp=request.connector_id.upper().replace("_", " "),
                    event_type="UPLOADED",
                    message=f"SFTP failed, but file copied locally to sandbox: {dest_path}",
                    tenant_id=tenant_id,
                )

                try:
                    DeliveryTimelineService.record(DeliveryTimelineEvent.create(
                        release_id=release.id,
                        dsp=request.connector_id.upper().replace("_", " "),
                        channel="local_fallback",
                        event_type="UPLOADED",
                        status="success",
                        message=f"Local fallback copy to sandbox incoming: {dest_path}",
                        payload_path=str(dest_path),
                    ), tenant_id=tenant_id)
                except Exception:
                    pass
                
                return {
                    "status": "delivered",
                    "connector": request.connector_id,
                    "method": "local_fallback",
                    "remote_path": str(dest_path)
                }
            except Exception as fallback_err:
                logger.error(f"Fallback failed: {fallback_err}")

        release.delivery["status"] = "not_delivered"
        _update_release_pipeline_status(release, tenant_id=tenant_id, status="VALIDATED")
        log_event(
            release_id=release.id,
            dsp=request.connector_id.upper().replace("_", " "),
            event_type="ERROR",
            message=f"Delivery failed: {str(e)}",
            tenant_id=tenant_id,
        )
        try:
            DeliveryTimelineService.record(DeliveryTimelineEvent.create(
                release_id=release.id,
                dsp=request.connector_id.upper().replace("_", " "),
                channel="sftp",
                event_type="ERROR",
                status="error",
                message=f"Delivery failed: {str(e)}",
                payload_path=str(zip_path) if zip_path else None,
            ), tenant_id=tenant_id)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Delivery failed: {str(e)}")


@router.post("/queue")
def queue_delivery(request: DeliveryQueueRequest, http_request: Request):
    tenant_id = http_request.state.tenant_id
    rid = (request.release_id or "").strip()
    try:
        release_uuid = UUID(rid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid release_id (expected UUID)")

    release = CatalogService.get_release_by_id(release_uuid, tenant_id=tenant_id)
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")

    if request.connector_id not in SFTP_CONNECTORS:
        raise HTTPException(status_code=400, detail=f"Connector {request.connector_id} not configured")

    if release.validation.get("ddex_status") not in ["validated", "external_unavailable", "generated"]:
        raise HTTPException(status_code=400, detail="Release must be validated before queueing delivery")

    release.delivery["status"] = "queued"
    release.delivery["connector_id"] = request.connector_id
    _update_release_pipeline_status(release, tenant_id=tenant_id, status="DELIVERY_QUEUED")

    log_event(
        release_id=release.id,
        dsp=request.connector_id.upper().replace("_", " "),
        event_type="CREATED",
        message="Delivery queued for async worker",
        tenant_id=tenant_id,
    )

    enqueue_result = enqueue_delivery(request.release_id, request.connector_id, tenant_id=tenant_id)
    return {"status": "DELIVERY_STARTED", "queue": enqueue_result}


@router.post("/mwn")
async def receive_mwn(request: Request):
    tenant_id = request.state.tenant_id
    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="Empty MWN payload")

    try:
        parsed = parse_mwn(body)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid MWN XML: {exc}") from exc

    if not parsed.release_id:
        raise HTTPException(status_code=400, detail="Could not resolve release_id from MWN payload")

    try:
        release_uuid = UUID(parsed.release_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="MWN release_id is not a valid UUID") from exc

    release = CatalogService.get_release_by_id(release_uuid, tenant_id=tenant_id)
    if not release:
        raise HTTPException(status_code=404, detail="Release not found for MWN message")

    # Persist raw MWN for audit
    now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    mwn_dir = tenant_path(tenant_id, "delivery", str(release_uuid), "mwn")
    mwn_dir.mkdir(parents=True, exist_ok=True)
    payload_path = mwn_dir / f"mwn-{now}.xml"
    payload_path.write_bytes(body)

    if parsed.status == "ACCEPTED":
        release.delivery["status"] = "accepted"
        release.delivery["dsp_status"] = parsed.raw_status or parsed.status
        release.delivery["dsp_issues"] = parsed.issues
        _update_release_pipeline_status(release, tenant_id=tenant_id, status="CONFIRMED")
        event_type = "ACCEPTED"
        severity = "info"
    elif parsed.status == "REJECTED":
        release.delivery["status"] = "rejected"
        release.delivery["dsp_status"] = parsed.raw_status or parsed.status
        release.delivery["dsp_issues"] = parsed.issues
        _update_release_pipeline_status(release, tenant_id=tenant_id, status="REJECTED")
        event_type = "REJECTED"
        severity = "high"
    else:
        release.delivery["status"] = "processing"
        release.delivery["dsp_status"] = parsed.raw_status or parsed.status
        _update_release_pipeline_status(release, tenant_id=tenant_id, status="DELIVERED")
        event_type = "PROCESSING"
        severity = "info"

    release.delivery["last_mwn_id"] = parsed.message_id
    release.delivery["last_mwn_at"] = datetime.utcnow().isoformat() + "Z"
    CatalogService.save_release(release, tenant_id=tenant_id)

    log_event(
        release_id=release.id,
        dsp=(release.delivery.get("connector_id") or "MWN").upper().replace("_", " "),
        event_type=event_type,
        message=f"MWN received: {parsed.raw_status or parsed.status}",
        tenant_id=tenant_id,
    )
    try:
        DeliveryTimelineService.record(
            DeliveryTimelineEvent.create(
                release_id=release.id,
                dsp=(release.delivery.get("connector_id") or "MWN").upper().replace("_", " "),
                channel="api",
                event_type=event_type,
                status="success" if event_type != "REJECTED" else "error",
                message=f"MWN processed with status {parsed.raw_status or parsed.status}",
                payload_path=str(payload_path),
            ),
            tenant_id=tenant_id,
        )
    except Exception:
        pass

    try:
        AutomationEngine.process(
            AutomationEvent(
                type=f"delivery.{event_type.lower()}",
                tenant_id=tenant_id,
                release_id=str(release.id),
                payload={
                    "issues": parsed.issues,
                    "message_id": parsed.message_id,
                    "raw_status": parsed.raw_status,
                    "payload_path": str(payload_path),
                },
                severity=severity,
            )
        )
    except Exception:
        pass

    return {
        "status": "received",
        "release_id": str(release.id),
        "delivery_status": release.delivery.get("status"),
        "pipeline_status": release.status,
        "issues": parsed.issues,
        "message_id": parsed.message_id,
    }


@router.get("/status/{release_id}")
def get_delivery_status(release_id: str, request: Request):
    tenant_id = request.state.tenant_id
    rid = (release_id or "").strip()
    try:
        release_uuid = UUID(rid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid release_id (expected UUID)")

    # Find release
    release = CatalogService.get_release_by_id(release_uuid, tenant_id=tenant_id)
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")

    delivery = release.delivery
    if delivery["status"] == "not_delivered":
        return {
            "release_id": str(release_uuid),
            "status": "NOT_DELIVERED",
            "connector": delivery.get("connector_id"),
            "issues": []
        }

    if delivery["status"] == "uploaded":
        # Check DSP status from sandbox
        connector_id = delivery.get("connector_id")
        if connector_id == "orchard_sandbox":
            accepted_status = sandbox_dsp_path("accepted", str(release_uuid), "status.json")
            rejected_status = sandbox_dsp_path("rejected", str(release_uuid), "status.json")

            if accepted_status.exists():
                with open(accepted_status, 'r') as f:
                    dsp_status = json.load(f)
                if release.delivery["status"] != "accepted":
                    release.delivery["status"] = "accepted"
                    release.delivery["dsp_status"] = dsp_status["status"]
                    release.delivery["dsp_issues"] = dsp_status["issues"]
                    _update_release_pipeline_status(release, tenant_id=tenant_id, status="CONFIRMED")
                    log_event(
                        release_id=release.id,
                        dsp=connector_id.upper().replace("_", " "),
                        event_type="ACCEPTED",
                        message=f"Delivery accepted by DSP: {dsp_status.get('issues', [])}",
                        tenant_id=tenant_id,
                    )
                    try:
                        DeliveryTimelineService.record(DeliveryTimelineEvent.create(
                            release_id=release.id,
                            dsp=connector_id.upper().replace("_", " "),
                            channel="sftp",
                            event_type="ACCEPTED",
                            status="success",
                            message="DSP accepted delivery",
                            payload_path=str(accepted_status),
                        ), tenant_id=tenant_id)
                    except Exception:
                        pass
                    try:
                        AutomationEngine.process(
                            AutomationEvent(
                                type="delivery.accepted",
                                tenant_id=tenant_id,
                                release_id=str(release.id),
                                payload={"issues": dsp_status.get("issues", [])},
                                severity="info",
                            )
                        )
                    except Exception:
                        pass
                return dsp_status
            elif rejected_status.exists():
                with open(rejected_status, 'r') as f:
                    dsp_status = json.load(f)
                if release.delivery["status"] != "rejected":
                    release.delivery["status"] = "rejected"
                    release.delivery["dsp_status"] = dsp_status["status"]
                    release.delivery["dsp_issues"] = dsp_status["issues"]
                    _update_release_pipeline_status(release, tenant_id=tenant_id, status="REJECTED")
                    log_event(
                        release_id=release.id,
                        dsp=connector_id.upper().replace("_", " "),
                        event_type="REJECTED",
                        message=f"Delivery rejected by DSP: {dsp_status.get('issues', [])}",
                        tenant_id=tenant_id,
                    )
                    try:
                        DeliveryTimelineService.record(DeliveryTimelineEvent.create(
                            release_id=release.id,
                            dsp=connector_id.upper().replace("_", " "),
                            channel="sftp",
                            event_type="REJECTED",
                            status="error",
                            message="DSP rejected delivery",
                            payload_path=str(rejected_status),
                        ), tenant_id=tenant_id)
                    except Exception:
                        pass
                    try:
                        AutomationEngine.process(
                            AutomationEvent(
                                type="delivery.rejected",
                                tenant_id=tenant_id,
                                release_id=str(release.id),
                                payload={"issues": dsp_status.get("issues", []), "reason": "DSP rejected"},
                                severity="high",
                            )
                        )
                    except Exception:
                        pass
                return dsp_status
            else:
                # Still processing
                return {
                    "release_id": release_id,
                    "status": "PROCESSING",
                    "connector": connector_id,
                    "issues": []
                }

    # Return current status
    return {
        "release_id": release_id,
        "status": delivery["status"].upper(),
        "connector": delivery.get("connector_id"),
        "issues": delivery.get("dsp_issues", [])
    }


@router.get("/timeline/{release_id}")
def get_delivery_timeline(release_id: UUID, request: Request):
    tenant_id = request.state.tenant_id
    return DeliveryTimelineService.get_timeline(release_id, tenant_id=tenant_id)


@router.get("/events/{release_id}", response_model=List[DeliveryEvent])
def get_delivery_events(release_id: str):
    """Obtiene todos los eventos de delivery para un release."""
    from app.services.delivery_logger import get_events_for_release
    rid = (release_id or "").strip()
    try:
        release_uuid = UUID(rid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid release ID format")

    events = get_events_for_release(release_uuid)
    # Ordenar por timestamp
    events_sorted = sorted(events, key=lambda e: e.created_at)

    return [
        {
            "event_type": event.event_type,
            "dsp": event.dsp,
            "message": event.message,
            "created_at": event.created_at.isoformat() + "Z"
        }
        for event in events_sorted
    ]


@router.get("/test")
def test():
    return {"ok": True}

@router.get("/overview", response_model=List[DeliveryOverview])
def get_delivery_overview(request: Request):
    """Obtiene vista general de todas las entregas."""
    from app.services.delivery_logger import get_latest_event_for_release
    tenant_id = request.state.tenant_id

    overview = []
    releases = CatalogService.get_releases(tenant_id=tenant_id)
    for release in releases:
        delivery = release.delivery
        if delivery.get("status") and delivery["status"] != "not_delivered":
            latest_event = get_latest_event_for_release(release.id)
            overview.append({
                "release_id": str(release.id),
                "title": release.title or "Sin título",
                "dsp": delivery.get("connector_id", "Unknown").upper().replace("_", " "),
                "status": delivery["status"].upper(),
                "last_event": latest_event.created_at.isoformat() + "Z" if latest_event else None
            })

    # Ordenar por último evento (más reciente primero)
    overview_sorted = sorted(
        overview,
        key=lambda x: x["last_event"] or "1970-01-01T00:00:00Z",
        reverse=True
    )

    return overview_sorted
