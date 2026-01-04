from typing import List
from uuid import UUID
from app.models.delivery_event import DeliveryEvent, EventType

# Persistencia simple en memoria (puede migrar a DB después)
DELIVERY_EVENTS_DB: List[DeliveryEvent] = []


def log_event(
    release_id: UUID,
    dsp: str,
    event_type: EventType,
    message: str
) -> DeliveryEvent:
    """Registra un evento de delivery."""
    event = DeliveryEvent.create(
        release_id=release_id,
        dsp=dsp,
        event_type=event_type,
        message=message
    )
    DELIVERY_EVENTS_DB.append(event)
    print(f"[DELIVERY EVENT] {dsp} | {release_id} | {event_type} | {message}")
    return event


def get_events_for_release(release_id: UUID) -> List[DeliveryEvent]:
    """Obtiene todos los eventos para un release específico."""
    return [event for event in DELIVERY_EVENTS_DB if event.release_id == release_id]


def get_all_events() -> List[DeliveryEvent]:
    """Obtiene todos los eventos."""
    return DELIVERY_EVENTS_DB.copy()


def get_latest_event_for_release(release_id: UUID) -> DeliveryEvent | None:
    """Obtiene el evento más reciente para un release."""
    events = get_events_for_release(release_id)
    return max(events, key=lambda e: e.created_at) if events else None