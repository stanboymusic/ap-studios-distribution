from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.delivery import build_delivery_package
from app.ddex.ern_builder import build_ern
from app.api.releases import RELEASES_DB
from app.services.sftp_connector import SFTPConnector
from app.config.sftp import SFTP_CONNECTORS
from app.services.delivery_logger import log_event
from datetime import datetime
import json
from pathlib import Path

router = APIRouter(prefix="/delivery", tags=["Delivery"])

class SFTPDeliveryRequest(BaseModel):
    release_id: str
    connector_id: str


@router.post("/{release_id}/export")
def export(release_id: str):
    # Find release
    for release in RELEASES_DB:
        if str(release.id) == release_id:
            # Check validation status
            if release.validation.get("ddex_status") != "validated":
                raise HTTPException(
                    status_code=400,
                    detail="Release must be validated before delivery"
                )

            # Build ERN XML
            ern_xml = build_ern(release)
            # Get artist name
            artist_name = release.artist.get("display_name", "Unknown") if release.artist else "Unknown"
            # Build delivery package
            zip_path = build_delivery_package(
                release_id,
                ern_xml,
                release.tracks,
                release.artwork or "",
                artist_name
            )

            return {
                "status": "exported",
                "path": zip_path,
                "package_name": zip_path.split("/")[-1]
            }
    raise HTTPException(status_code=404, detail="Release not found")


@router.post("/sftp")
def deliver_via_sftp(request: SFTPDeliveryRequest):
    # Find release
    release = None
    for r in RELEASES_DB:
        if str(r.id) == request.release_id:
            release = r
            break
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")

    # Check if connector exists
    if request.connector_id not in SFTP_CONNECTORS:
        raise HTTPException(status_code=400, detail=f"Connector {request.connector_id} not configured")

    # Check validation
    if release.validation.get("ddex_status") != "validated":
        raise HTTPException(status_code=400, detail="Release must be validated before delivery")

    # Update delivery status
    release.delivery["status"] = "uploading"
    release.delivery["connector_id"] = request.connector_id
    release.updated_at = datetime.utcnow().isoformat()

    # Log event
    log_event(
        release_id=release.id,
        dsp=request.connector_id.upper().replace("_", " "),
        event_type="CREATED",
        message=f"Delivery initiated to {request.connector_id}"
    )

    try:
        # Build delivery package if not exists
        zip_path = build_delivery_package(
            request.release_id,
            build_ern(release),
            release.tracks,
            release.artwork or "",
            release.artist.get("display_name", "Unknown") if release.artist else "Unknown"
        )

        # Get connector config
        config = SFTP_CONNECTORS[request.connector_id]
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
            message=f"Uploading ZIP to {config['host']}:{config['port']}"
        )

        # Connect and upload
        connector.connect()
        remote_path = f"{config['remote_path']}/delivery_{request.release_id}.zip"
        connector.upload(zip_path, remote_path)
        connector.disconnect()

        # Update status
        release.delivery["status"] = "uploaded"
        release.delivery["delivered_at"] = datetime.utcnow().isoformat()

        # Log uploaded
        log_event(
            release_id=release.id,
            dsp=request.connector_id.upper().replace("_", " "),
            event_type="UPLOADED",
            message=f"ZIP uploaded successfully to {remote_path}"
        )

        return {
            "status": "delivered",
            "connector": request.connector_id,
            "remote_path": remote_path
        }

    except Exception as e:
        release.delivery["status"] = "not_delivered"
        log_event(
            release_id=release.id,
            dsp=request.connector_id.upper().replace("_", " "),
            event_type="ERROR",
            message=f"Delivery failed: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=f"Delivery failed: {str(e)}")


@router.get("/status/{release_id}")
def get_delivery_status(release_id: str):
    # Find release
    release = None
    for r in RELEASES_DB:
        if str(r.id) == release_id:
            release = r
            break
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")

    delivery = release.delivery
    if delivery["status"] == "not_delivered":
        return {
            "release_id": release_id,
            "status": "NOT_DELIVERED",
            "connector": delivery.get("connector_id"),
            "issues": []
        }

    if delivery["status"] == "uploaded":
        # Check DSP status from sandbox
        connector_id = delivery.get("connector_id")
        if connector_id == "orchard_sandbox":
            sandbox_dir = Path("./sandbox-dsp")
            accepted_status = sandbox_dir / "accepted" / release_id / "status.json"
            rejected_status = sandbox_dir / "rejected" / release_id / "status.json"

            if accepted_status.exists():
                with open(accepted_status, 'r') as f:
                    dsp_status = json.load(f)
                if release.delivery["status"] != "accepted":
                    release.delivery["status"] = "accepted"
                    release.delivery["dsp_status"] = dsp_status["status"]
                    release.delivery["dsp_issues"] = dsp_status["issues"]
                    log_event(
                        release_id=release.id,
                        dsp=connector_id.upper().replace("_", " "),
                        event_type="ACCEPTED",
                        message=f"Delivery accepted by DSP: {dsp_status.get('issues', [])}"
                    )
                return dsp_status
            elif rejected_status.exists():
                with open(rejected_status, 'r') as f:
                    dsp_status = json.load(f)
                if release.delivery["status"] != "rejected":
                    release.delivery["status"] = "rejected"
                    release.delivery["dsp_status"] = dsp_status["status"]
                    release.delivery["dsp_issues"] = dsp_status["issues"]
                    log_event(
                        release_id=release.id,
                        dsp=connector_id.upper().replace("_", " "),
                        event_type="REJECTED",
                        message=f"Delivery rejected by DSP: {dsp_status.get('issues', [])}"
                    )
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


@router.get("/events/{release_id}")
def get_delivery_events(release_id: str):
    """Obtiene todos los eventos de delivery para un release."""
    from app.services.delivery_logger import get_events_for_release
    try:
        release_uuid = UUID(release_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid release ID format")

    events = get_events_for_release(release_uuid)
    # Ordenar por timestamp
    events_sorted = sorted(events, key=lambda e: e.created_at)

    return [
        {
            "event_type": event.event_type,
            "message": event.message,
            "created_at": event.created_at.isoformat() + "Z"
        }
        for event in events_sorted
    ]


@router.get("/overview")
def get_delivery_overview():
    """Obtiene vista general de todas las entregas."""
    from app.services.delivery_logger import get_latest_event_for_release
    from app.api.releases import RELEASES_DB

    overview = []
    for release in RELEASES_DB:
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