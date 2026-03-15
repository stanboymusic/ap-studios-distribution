from __future__ import annotations

from app.catalog.identifier_service import claim_manual_isrc, claim_manual_upc, create_isrc, create_upc


def create_track(title: str, artist_id: str, tenant_id: str = "default", isrc: str | None = None) -> dict:
    if isrc:
        resolved_isrc = claim_manual_isrc(
            isrc,
            tenant_id=tenant_id,
            source=f"track:{artist_id or 'unknown'}",
        )
    else:
        resolved_isrc = create_isrc(
            tenant_id=tenant_id,
            source=f"track:{artist_id or 'unknown'}",
        )
    return {
        "title": title,
        "artist_id": artist_id,
        "isrc": resolved_isrc,
    }


def create_release(title: str, artist_id: str, tenant_id: str = "default", upc: str | None = None) -> dict:
    if upc:
        resolved_upc = claim_manual_upc(
            upc,
            tenant_id=tenant_id,
            source=f"release:{artist_id or 'unknown'}",
        )
    else:
        resolved_upc = create_upc(
            tenant_id=tenant_id,
            source=f"release:{artist_id or 'unknown'}",
        )
    return {
        "title": title,
        "artist_id": artist_id,
        "upc": resolved_upc,
    }
