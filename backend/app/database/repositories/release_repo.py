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
        "validation": release.validation or {},
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
