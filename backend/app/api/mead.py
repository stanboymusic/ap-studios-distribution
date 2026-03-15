"""
MEAD endpoints (manual generation and retrieval).
"""
from __future__ import annotations

import os
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel

from app.services.mead_builder import build_mead_message, MEADBuildError
from app.services.mead_store import mead_store
from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/mead", tags=["MEAD"])

AP_STUDIOS_DPID = os.getenv("AP_STUDIOS_DPID", "PA-DPIDA-202402050E-4")


class MEADInput(BaseModel):
    release_id: str
    recipient_dpid: str

    focus_track_isrc: Optional[str] = None
    focus_track_title: Optional[str] = None

    editorial_note: Optional[str] = None
    editorial_note_language: Optional[str] = "en"

    mood: Optional[str] = None
    activity: Optional[str] = None
    theme: Optional[str] = None
    genre: Optional[str] = None
    subgenre: Optional[str] = None

    lyrics_isrc: Optional[str] = None
    lyrics_text: Optional[str] = None
    lyrics_language: Optional[str] = "en"


def _tenant_id(request: Request) -> str:
    return getattr(request.state, "tenant_id", None) or "default"


def _release_to_mead_payload(release, tenant_id: str) -> dict:
    tracks = getattr(release, "tracks", []) or []
    isrcs = []
    for track in tracks:
        isrc = (track.get("isrc") or "").strip().upper()
        if isrc:
            isrcs.append(isrc)

    if not isrcs and getattr(release, "isrc", None):
        isrcs.append(str(release.isrc).strip().upper())

    artist_name = None
    artist_id = getattr(release, "artist_id", None)
    if artist_id:
        artist = CatalogService.get_artist_by_id(artist_id, tenant_id=tenant_id)
        if artist:
            artist_name = artist.name

    return {
        "id": str(release.id),
        "title": release.title or "",
        "upc": getattr(release, "upc", None),
        "artist_name": artist_name,
        "isrcs": isrcs,
    }


@router.post("/generate")
def generate_mead(body: MEADInput, request: Request):
    tenant_id = _tenant_id(request)
    rid = (body.release_id or "").strip()
    try:
        release_uuid = UUID(rid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid release_id (expected UUID)")

    release = CatalogService.get_release_by_id(release_uuid, tenant_id=tenant_id)
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")

    mead_data = body.model_dump(exclude={"release_id", "recipient_dpid"})
    if body.lyrics_isrc and body.lyrics_text:
        mead_data["lyrics"] = {
            "isrc": body.lyrics_isrc,
            "text": body.lyrics_text,
            "language": body.lyrics_language,
        }

    try:
        xml_content = build_mead_message(
            release=_release_to_mead_payload(release, tenant_id),
            mead_data=mead_data,
            sender_dpid=AP_STUDIOS_DPID,
            recipient_dpid=body.recipient_dpid,
        )
    except MEADBuildError as exc:
        raise HTTPException(status_code=422, detail={"message": str(exc)}) from exc

    record = mead_store.save(
        tenant_id=tenant_id,
        release_id=str(release.id),
        recipient_dpid=body.recipient_dpid,
        xml_content=xml_content,
        mead_data=mead_data,
    )

    return {
        "status": "ok",
        "mead_id": record["id"],
        "release_id": str(release.id),
        "recipient_dpid": body.recipient_dpid,
        "message": "MEAD generated and saved as pending delivery",
    }


@router.get("/releases/{release_id}")
def list_mead_for_release(release_id: str, request: Request):
    tenant_id = _tenant_id(request)
    records = mead_store.list_by_release(tenant_id, release_id)
    return {
        "release_id": release_id,
        "mead_messages": [
            {
                "id": r["id"],
                "recipient_dpid": r.get("recipient_dpid"),
                "status": r.get("status"),
                "created_at": r.get("created_at"),
                "has_focus_track": bool(r.get("mead_data", {}).get("focus_track_isrc")),
                "has_editorial_note": bool(r.get("mead_data", {}).get("editorial_note")),
                "has_lyrics": bool(r.get("mead_data", {}).get("lyrics")),
            }
            for r in records
        ],
    }


@router.get("/releases/{release_id}/{mead_id}/xml")
def download_mead_xml(release_id: str, mead_id: str, request: Request):
    tenant_id = _tenant_id(request)
    records = mead_store.list_by_release(tenant_id, release_id)
    record = next((r for r in records if r.get("id") == mead_id), None)
    if not record:
        raise HTTPException(status_code=404, detail="MEAD message not found")
    return Response(
        content=record.get("xml_content", ""),
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{mead_id}.xml"'},
    )
