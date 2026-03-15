from typing import List
from uuid import UUID
from datetime import datetime
from app.models.delivery_event import DeliveryEvent, EventType
from app.models.delivery_timeline_event import DeliveryTimelineEvent
from app.services.catalog_service import CatalogService
from app.services.delivery_timeline_service import DeliveryTimelineService


def log_event(
    release_id: UUID,
    dsp: str,
    event_type: EventType,
    message: str,
    tenant_id: str = "default",
) -> DeliveryEvent:
    """Registra un evento de delivery."""
    event = DeliveryEvent.create(
        release_id=release_id,
        dsp=dsp,
        event_type=event_type,
        message=message
    )
    CatalogService.save_delivery_event({
        "id": str(event.id),
        "release_id": str(event.release_id),
        "dsp": event.dsp,
        "event_type": event.event_type,
        "message": event.message,
        "created_at": event.created_at.isoformat() + "Z",
    }, tenant_id=tenant_id)

    # Timeline formal (persistente en disco)
    try:
        DeliveryTimelineService.record(DeliveryTimelineEvent.create(
            release_id=release_id,
            dsp=dsp,
            channel="sftp",
            event_type=event_type,
            status="info" if event_type not in ("ERROR",) else "error",
            message=message,
            payload_path=None,
        ), tenant_id=tenant_id)
    except Exception:
        pass
    print(f"[DELIVERY EVENT] {dsp} | {release_id} | {event_type} | {message}")
    return event


def get_events_for_release(release_id: UUID) -> List[DeliveryEvent]:
    """Obtiene todos los eventos para un release específico."""
    events = CatalogService.get_delivery_events_for_release(release_id)
    out: List[DeliveryEvent] = []
    for e in events:
        try:
            created_at = e.get("created_at")
            if isinstance(created_at, str) and created_at.endswith("Z"):
                created_at = created_at[:-1]
            out.append(DeliveryEvent(
                id=UUID(e["id"]),
                release_id=UUID(e["release_id"]),
                dsp=e["dsp"],
                event_type=e["event_type"],
                message=e["message"],
                created_at=datetime.fromisoformat(created_at) if isinstance(created_at, str) else created_at,
            ))
        except Exception:
            continue
    return out


def get_all_events() -> List[DeliveryEvent]:
    """Obtiene todos los eventos."""
    events = CatalogService.get_delivery_events()
    out: List[DeliveryEvent] = []
    for e in events:
        try:
            created_at = e.get("created_at")
            if isinstance(created_at, str) and created_at.endswith("Z"):
                created_at = created_at[:-1]
            out.append(DeliveryEvent(
                id=UUID(e["id"]),
                release_id=UUID(e["release_id"]),
                dsp=e["dsp"],
                event_type=e["event_type"],
                message=e["message"],
                created_at=datetime.fromisoformat(created_at) if isinstance(created_at, str) else created_at,
            ))
        except Exception:
            continue
    return out


def get_latest_event_for_release(release_id: UUID) -> DeliveryEvent | None:
    """Obtiene el evento más reciente para un release."""
    events = get_events_for_release(release_id)
    return max(events, key=lambda e: e.created_at) if events else None
