from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel
from pathlib import Path
from uuid import UUID
import hashlib
import json

from app.catalog.catalog_service import (
    create_release as create_catalog_release,
    create_track as create_catalog_track,
)
from app.catalog.identifier_service import create_isrc, create_upc
from app.services.catalog_service import CatalogService
from app.ern.persistence.ern_store import ErnStore
from app.services.validation_history_service import ValidationHistoryService
from app.core.auth import ensure_release_access


router = APIRouter(prefix="/catalog", tags=["Catalog"])


class CatalogTrackCreateRequest(BaseModel):
    title: str
    artist_id: str
    isrc: str | None = None


class CatalogReleaseCreateRequest(BaseModel):
    title: str
    artist_id: str
    upc: str | None = None


@router.post("/identifiers/isrc")
def generate_isrc_identifier(request: Request):
    tenant_id = request.state.tenant_id
    return {"isrc": create_isrc(tenant_id=tenant_id, source="catalog-api")}


@router.post("/identifiers/upc")
def generate_upc_identifier(request: Request):
    tenant_id = request.state.tenant_id
    return {"upc": create_upc(tenant_id=tenant_id, source="catalog-api")}


@router.post("/track")
def create_catalog_track_entry(payload: CatalogTrackCreateRequest, request: Request):
    tenant_id = request.state.tenant_id
    try:
        return create_catalog_track(
            title=payload.title,
            artist_id=payload.artist_id,
            tenant_id=tenant_id,
            isrc=payload.isrc,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/release")
def create_catalog_release_entry(payload: CatalogReleaseCreateRequest, request: Request):
    tenant_id = request.state.tenant_id
    try:
        return create_catalog_release(
            title=payload.title,
            artist_id=payload.artist_id,
            tenant_id=tenant_id,
            upc=payload.upc,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _sha256(path: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


@router.get("/releases/{release_id}")
def get_release_detail(
    release_id: UUID,
    include_ern_xml: bool = Query(False),
    request: Request = None,
):
    tenant_id = request.state.tenant_id if request else "default"
    release = CatalogService.get_release_by_id(release_id, tenant_id=tenant_id)
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")
    if request:
        ensure_release_access(request, release)

    # Artist
    artist = None
    if getattr(release, "artist_id", None):
        artist_obj = CatalogService.get_artist_by_id(release.artist_id, tenant_id=tenant_id)
        if artist_obj:
            artist = {
                "id": str(artist_obj.id),
                "name": artist_obj.name,
                "party_reference": "P-1",
                "party_id": None,
            }

    # Tracks (legacy compatibility: release.tracks is list[dict])
    tracks_out = []
    for t in (getattr(release, "tracks", None) or []):
        file_path = t.get("file_path")
        p = Path(file_path) if file_path else None
        duration = t.get("duration_seconds") or t.get("duration") or 0
        tracks_out.append({
            "id": t.get("track_id") or t.get("id") or "",
            "title": t.get("title") or "",
            "isrc": t.get("isrc") or "",
            "duration": int(duration) if isinstance(duration, (int, float)) else duration,
            "audio_asset": {
                "path": file_path,
                "format": (p.suffix[1:].upper() if p and p.suffix else None),
                "checksum": _sha256(p) if p and p.exists() else None,
            }
        })

    # Artwork
    artwork = None
    if getattr(release, "artwork_id", None):
        asset = CatalogService.get_asset_by_id(str(release.artwork_id), tenant_id=tenant_id)
        if asset and asset.get("path"):
            ap = Path(asset["path"])
            res = None
            if asset.get("width") and asset.get("height"):
                res = f"{asset['width']}x{asset['height']}"
            artwork = {
                "id": asset.get("id"),
                "path": asset.get("path"),
                "resolution": res,
                "format": asset.get("format") or (ap.suffix[1:].upper() if ap.suffix else None),
            }

    # ERN info
    store = ErnStore()
    latest_dir = store.base / str(release_id) / "latest"
    xml_path = latest_dir / "ern.xml"
    meta_path = latest_dir / "meta.json"
    ern = {
        "generated": xml_path.exists(),
        "last_generated_at": None,
        "xml_path": str(xml_path) if xml_path.exists() else None,
        "xml": None,
    }
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            ern["last_generated_at"] = meta.get("generated_at")
        except Exception:
            pass
    if include_ern_xml and xml_path.exists():
        try:
            ern["xml"] = xml_path.read_text(encoding="utf-8")
        except Exception:
            ern["xml"] = None

    # Validation history
    validation = release.validation or {}
    stored_history = ValidationHistoryService.get_history(release_id, tenant_id=tenant_id)
    # Prefer auditable runs if present, else fallback to embedded legacy history.
    history = stored_history.get("runs") or (validation.get("history") or [])

    # Delivery timeline (persisted)
    delivery_events = CatalogService.get_delivery_events_for_release(release_id, tenant_id=tenant_id)
    delivery_events_sorted = sorted(delivery_events, key=lambda e: e.get("created_at") or "")

    return {
        "id": str(release.id),
        "status": release.status,
        "profile": (release.ddex or {}).get("release_profile"),
        "release": {
            "title": release.title,
            "version": None,
            "type": (release.release_type.value if hasattr(release.release_type, "value") else str(release.release_type)),
            "original_release_date": (
                release.original_release_date.isoformat()
                if getattr(release, "original_release_date", None)
                else None
            ),
            "language": release.language,
            "upc": release.upc,
        },
        "artist": artist,
        "tracks": tracks_out,
        "artwork": artwork,
        "ern": ern,
        "validation": {
            "last_status": validation.get("ddex_status"),
            "signed": validation.get("signed"),
            "signature_algorithm": validation.get("signature_algorithm"),
            "history": history,
        },
        "delivery": {
            "current_status": (release.delivery or {}).get("status"),
            "timeline": [
                {
                    "event": e.get("event_type"),
                    "timestamp": e.get("created_at"),
                    "source": "system",
                    "dsp": e.get("dsp"),
                    "message": e.get("message"),
                }
                for e in delivery_events_sorted
            ]
        }
    }
