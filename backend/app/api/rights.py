from fastapi import APIRouter, HTTPException, Request
from app.schemas.rights import RightsConfigurationCreate
from app.models.rights import RightsConfiguration, RightsShare, RightsParty
from app.services.rights_engine import validate_rights_configuration, RightsValidationError
from app.services.rights_store import RightsStore
from app.services.catalog_service import CatalogService
from app.services.mwn_builder import build_mwn_message, MWNBuildError
from app.services.mwn_store import mwn_store
from uuid import UUID
import logging
import os

router = APIRouter(prefix="/rights", tags=["Rights"])
logger = logging.getLogger(__name__)
AP_STUDIOS_DPID = os.getenv("AP_STUDIOS_DPID", "PA-DPIDA-202402050E-4")

def _tenant_id(request: Request) -> str:
    return getattr(request.state, "tenant_id", None) or "default"

def _release_to_mwn_payload(release, tenant_id: str) -> dict:
    tracks = getattr(release, "tracks", []) or []
    isrcs = []
    track_entries = []
    for idx, track in enumerate(tracks, start=1):
        isrc = (track.get("isrc") or "").strip().upper() or None
        if isrc:
            isrcs.append(isrc)
        track_entries.append(
            {
                "title": track.get("title") or release.title or "Unknown",
                "isrc": isrc,
                "track_id": track.get("track_id") or f"track-{idx}",
            }
        )

    if not track_entries:
        track_entries = [
            {
                "title": release.title or "Unknown",
                "isrc": getattr(release, "isrc", None),
                "track_id": "track-1",
            }
        ]
        if track_entries[0]["isrc"]:
            isrcs.append(track_entries[0]["isrc"])

    artist_name = None
    artist_id = getattr(release, "artist_id", None)
    if artist_id:
        artist = CatalogService.get_artist_by_id(artist_id, tenant_id=tenant_id)
        if artist:
            artist_name = artist.name

    return {
        "id": str(release.id),
        "title": release.title or "Untitled",
        "upc": getattr(release, "upc", None),
        "release_date": getattr(release, "original_release_date", None) or getattr(release, "release_date", None),
        "isrcs": isrcs,
        "tracks": track_entries,
        "artist_name": artist_name,
        "release_type": getattr(release, "release_type", None),
        "language": getattr(release, "language", None),
    }

def _trigger_mwn_if_needed(tenant_id: str, rights_config: RightsConfiguration, release) -> None:
    publishers_with_dpid = [
        p for p in (rights_config.publishers or [])
        if getattr(p, "recipient_dpid", None)
    ]

    if not publishers_with_dpid:
        logger.info(
            "No publishers with recipient_dpid for release %s - skipping MWN generation",
            rights_config.release_id,
        )
        return

    release_payload = _release_to_mwn_payload(release, tenant_id)
    rights_payload = rights_config.model_dump()

    for publisher in publishers_with_dpid:
        try:
            xml_content = build_mwn_message(
                rights_config=rights_payload,
                release=release_payload,
                sender_dpid=AP_STUDIOS_DPID,
                recipient_dpid=publisher.recipient_dpid,
            )
            mwn_store.save(
                tenant_id=tenant_id,
                release_id=str(rights_config.release_id),
                rights_config_id=str(rights_config.id),
                recipient_dpid=publisher.recipient_dpid,
                xml_content=xml_content,
                status="pending",
            )
            logger.info(
                "MWN generated for release %s -> %s",
                rights_config.release_id,
                publisher.recipient_dpid,
            )
        except MWNBuildError as exc:
            logger.error(
                "MWN build failed for release %s: %s",
                rights_config.release_id,
                exc,
            )

@router.get("/configurations")
def list_rights_configurations(request: Request):
    tenant_id = _tenant_id(request)
    return [c.model_dump() for c in RightsStore.list_configurations(tenant_id)]

@router.post("/configurations")
def create_rights_configuration(payload: RightsConfigurationCreate, request: Request):
    tenant_id = _tenant_id(request)
    config = RightsConfiguration(
        scope=payload.scope,
        release_id=payload.release_id,
        track_id=payload.track_id,
        work_title=payload.work_title,
        iswc=payload.iswc,
        territory=payload.territory,
    )

    for s in payload.shares:
        config.shares.append(
            RightsShare(
                party_reference=s.party_reference,
                rights_type=s.rights_type,
                usage_types=s.usage_types,
                territories=s.territories,
                share_percentage=s.share_percentage,
                valid_from=s.valid_from,
                valid_to=s.valid_to
            )
        )

    for composer in payload.composers or []:
        config.composers.append(
            RightsParty(
                name=composer.name,
                role=composer.role,
                ipi_name_number=composer.ipi_name_number,
                share_pct=composer.share_pct,
                recipient_dpid=composer.recipient_dpid,
            )
        )

    for publisher in payload.publishers or []:
        config.publishers.append(
            RightsParty(
                name=publisher.name,
                role=publisher.role,
                ipi_name_number=publisher.ipi_name_number,
                share_pct=publisher.share_pct,
                recipient_dpid=publisher.recipient_dpid,
            )
        )

    try:
        validate_rights_configuration(config)
    except RightsValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    RightsStore.save_configuration(config, tenant_id=tenant_id)

    try:
        release = CatalogService.get_release_by_id(UUID(str(config.release_id)), tenant_id=tenant_id)
    except Exception:
        release = None
    if release:
        _trigger_mwn_if_needed(tenant_id, config, release)

    return {
        "id": config.id,
        "status": "VALID",
        "shares": len(config.shares)
    }
