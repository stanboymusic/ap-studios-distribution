"""
PostgreSQL user repository.
Misma interfaz que app/repositories/user_repository.py (file-based).
El sistema elige automáticamente cuál usar según DB_AVAILABLE.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.database.models import DBUser
from app.models.user import User


def _to_domain(db_user: DBUser) -> User:
    return User(
        id=db_user.id,
        email=db_user.email,
        hashed_password=db_user.hashed_password,
        role=db_user.role,
        tenant_id=db_user.tenant_id,
        artist_id=db_user.artist_id,
        is_active=db_user.is_active,
        created_at=db_user.created_at.isoformat() if db_user.created_at else None,
    )


def get_by_email(email: str, tenant_id: str, db: Session) -> Optional[User]:
    row = (
        db.query(DBUser)
        .filter(DBUser.email == email.lower(), DBUser.tenant_id == tenant_id)
        .first()
    )
    return _to_domain(row) if row else None


def get_by_id(user_id: str, tenant_id: str, db: Session) -> Optional[User]:
    row = (
        db.query(DBUser)
        .filter(DBUser.id == str(user_id), DBUser.tenant_id == tenant_id)
        .first()
    )
    return _to_domain(row) if row else None


def create(user: User, db: Session) -> User:
    db_user = DBUser(
        id=str(user.id),
        email=user.email,
        hashed_password=user.hashed_password,
        role=user.role,
        tenant_id=user.tenant_id,
        artist_id=user.artist_id,
        is_active=user.is_active,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return _to_domain(db_user)
