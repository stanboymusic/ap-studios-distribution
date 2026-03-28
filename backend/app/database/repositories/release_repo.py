"""
PostgreSQL release repository.
"""
from __future__ import annotations

import uuid
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.database.models import DBRelease, DBTrack
from app.models.release import ReleaseDraft


def _to_domain(row: DBRelease) -> ReleaseDraft:
    r = ReleaseDraft()
    r.id = UUID(row.id)
    r.release_id = r.id
    r.title = row.title
    r.release_type = row.release_type
    r.status = row.status
    r.upc = row.upc
    r.isrc = row.isrc
    r.language = row.language
    r.original_release_date = row.original_release_date
    r.territories = row.territories or ["Worldwide"]
    r.artist_id = UUID(row.artist_id) if row.artist_id else None
    r.owner_user_id = row.owner_user_id
    r.artwork_id = UUID(row.artwork_id) if row.artwork_id else None
    r.validation = row.validation or {}
    r.delivery = row.delivery or {}
    r.ddex = row.ddex or {}
    r.featuring_artists = row.validation.get("featuring_artists") if isinstance(row.validation, dict) else None
    r.producer = row.validation.get("producer") if isinstance(row.validation, dict) else None
    r.composer = row.validation.get("composer") if isinstance(row.validation, dict) else None
    r.remixer = row.validation.get("remixer") if isinstance(row.validation, dict) else None
    r.genre = row.validation.get("genre") if isinstance(row.validation, dict) else None
    r.subgenre = row.validation.get("subgenre") if isinstance(row.validation, dict) else None
    r.label_name = row.validation.get("label_name") if isinstance(row.validation, dict) else None
    r.c_line = row.validation.get("c_line") if isinstance(row.validation, dict) else None
    r.p_line = row.validation.get("p_line") if isinstance(row.validation, dict) else None
    r.meta_language = row.validation.get("meta_language") if isinstance(row.validation, dict) else None
    r.product_version = row.validation.get("product_version") if isinstance(row.validation, dict) else None
    r.product_code = row.validation.get("product_code") if isinstance(row.validation, dict) else None
    r.sale_date = row.validation.get("sale_date") if isinstance(row.validation, dict) else None
    r.preorder_date = row.validation.get("preorder_date") if isinstance(row.validation, dict) else None
    r.preorder_previewable = (row.validation or {}).get("preorder_previewable", False) if isinstance(row.validation, dict) else False
    r.excluded_territories = (row.validation or {}).get("excluded_territories") if isinstance(row.validation, dict) else None
    r.album_price = (row.validation or {}).get("album_price") if isinstance(row.validation, dict) else None
    r.track_price = (row.validation or {}).get("track_price") if isinstance(row.validation, dict) else None
    r.publishing = (row.validation or {}).get("publishing") if isinstance(row.validation, dict) else None
    r.tracks = [
        {
            "track_id": t.id,
            "title": t.title,
            "track_number": t.track_number,
            "isrc": t.isrc,
            "duration_seconds": t.duration_seconds,
            "explicit": t.explicit,
            "file_path": t.file_path,
        }
        for t in (row.tracks or [])
    ]
    return r


def get_all(tenant_id: str, db: Session) -> list[ReleaseDraft]:
    rows = db.query(DBRelease).filter(DBRelease.tenant_id == tenant_id).all()
    return [_to_domain(r) for r in rows]


def get_by_id(release_id: str, tenant_id: str, db: Session) -> Optional[ReleaseDraft]:
    row = (
        db.query(DBRelease)
        .filter(DBRelease.id == str(release_id), DBRelease.tenant_id == tenant_id)
        .first()
    )
    return _to_domain(row) if row else None


def save(release: ReleaseDraft, tenant_id: str, db: Session) -> ReleaseDraft:
    existing = db.query(DBRelease).filter(DBRelease.id == str(release.id)).first()

    data = {
        "title": release.title or "",
        "release_type": (
            release.release_type.value
            if hasattr(release.release_type, "value")
            else str(release.release_type or "Single")
        ),
        "status": release.status or "CREATED",
        "upc": release.upc,
        "isrc": release.isrc,
        "language": release.language or "es",
        "original_release_date": (
            release.original_release_date.isoformat()
            if hasattr(release.original_release_date, "isoformat")
            else release.original_release_date
        ),
        "territories": release.territories or ["Worldwide"],
        "artist_id": str(release.artist_id) if release.artist_id else None,
        "owner_user_id": release.owner_user_id,
        "artwork_id": str(release.artwork_id) if release.artwork_id else None,
        "validation": {
            **(release.validation or {}),
            "featuring_artists": getattr(release, "featuring_artists", None),
            "producer": getattr(release, "producer", None),
            "composer": getattr(release, "composer", None),
            "remixer": getattr(release, "remixer", None),
            "genre": getattr(release, "genre", None),
            "subgenre": getattr(release, "subgenre", None),
            "label_name": getattr(release, "label_name", None),
            "c_line": getattr(release, "c_line", None),
            "p_line": getattr(release, "p_line", None),
            "meta_language": getattr(release, "meta_language", None),
            "product_version": getattr(release, "product_version", None),
            "product_code": getattr(release, "product_code", None),
            "sale_date": getattr(release, "sale_date", None),
            "preorder_date": getattr(release, "preorder_date", None),
            "preorder_previewable": getattr(release, "preorder_previewable", False),
            "excluded_territories": getattr(release, "excluded_territories", None),
            "album_price": getattr(release, "album_price", None),
            "track_price": getattr(release, "track_price", None),
            "publishing": getattr(release, "publishing", None),
        },
        "delivery": release.delivery or {},
        "ddex": release.ddex or {},
        "tenant_id": tenant_id,
    }

    if existing:
        for k, v in data.items():
            setattr(existing, k, v)
        db.commit()
        db.refresh(existing)

        db.query(DBTrack).filter(DBTrack.release_id == str(release.id)).delete(
            synchronize_session=False
        )
        for t in (getattr(release, "tracks", None) or []):
            db.add(
                DBTrack(
                    id=t.get("track_id") or str(uuid.uuid4()),
                    release_id=str(release.id),
                    title=t.get("title", ""),
                    track_number=t.get("track_number", 1),
                    isrc=t.get("isrc"),
                    duration_seconds=t.get("duration_seconds"),
                    explicit=t.get("explicit", False),
                    file_path=t.get("file_path"),
                    tenant_id=tenant_id,
                )
            )
        db.commit()
        return _to_domain(existing)

    row = DBRelease(id=str(release.id), **data)
    db.add(row)
    db.commit()

    for t in (getattr(release, "tracks", None) or []):
        db.add(
            DBTrack(
                id=t.get("track_id") or str(uuid.uuid4()),
                release_id=str(release.id),
                title=t.get("title", ""),
                track_number=t.get("track_number", 1),
                isrc=t.get("isrc"),
                duration_seconds=t.get("duration_seconds"),
                explicit=t.get("explicit", False),
                file_path=t.get("file_path"),
                tenant_id=tenant_id,
            )
        )
    db.commit()
    db.refresh(row)
    return _to_domain(row)
