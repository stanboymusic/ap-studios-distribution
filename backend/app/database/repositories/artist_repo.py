"""
PostgreSQL artist repository.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.database.models import DBArtist
from app.models.artist import Artist


def _to_domain(row: DBArtist) -> Artist:
    return Artist(id=UUID(row.id), name=row.name, type=row.type, grid=row.grid)


def get_all(tenant_id: str, db: Session) -> list[Artist]:
    rows = db.query(DBArtist).filter(DBArtist.tenant_id == tenant_id).all()
    return [_to_domain(r) for r in rows]


def get_by_id(artist_id: str, tenant_id: str, db: Session) -> Optional[Artist]:
    row = (
        db.query(DBArtist)
        .filter(DBArtist.id == str(artist_id), DBArtist.tenant_id == tenant_id)
        .first()
    )
    return _to_domain(row) if row else None


def find_by_name(name: str, type_: str, tenant_id: str, db: Session) -> Optional[Artist]:
    row = (
        db.query(DBArtist)
        .filter(
            DBArtist.name.ilike(name),
            DBArtist.type == type_,
            DBArtist.tenant_id == tenant_id,
        )
        .first()
    )
    return _to_domain(row) if row else None


def save(artist: Artist, tenant_id: str, db: Session) -> Artist:
    existing = db.query(DBArtist).filter(DBArtist.id == str(artist.id)).first()
    if existing:
        existing.name = artist.name
        existing.type = artist.type
        existing.grid = artist.grid
        db.commit()
        db.refresh(existing)
        return _to_domain(existing)
    row = DBArtist(
        id=str(artist.id),
        name=artist.name,
        type=artist.type,
        grid=artist.grid,
        tenant_id=tenant_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_domain(row)
