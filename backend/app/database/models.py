"""
SQLAlchemy ORM models for AP Studios.
Only the core catalog models - others remain file-based for now.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class DBUser(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="artist")
    tenant_id: Mapped[str] = mapped_column(String(100), default="default")
    artist_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (Index("ix_users_email_tenant", "email", "tenant_id", unique=True),)


class DBArtist(Base):
    __tablename__ = "artists"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), default="SOLO")
    grid: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tenant_id: Mapped[str] = mapped_column(String(100), default="default")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    releases: Mapped[list["DBRelease"]] = relationship(
        back_populates="artist", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_artists_tenant", "tenant_id"),
        Index("ix_artists_name_tenant", "name", "tenant_id"),
    )


class DBRelease(Base):
    __tablename__ = "releases"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    release_type: Mapped[str] = mapped_column(String(100), default="Single")
    status: Mapped[str] = mapped_column(String(100), default="CREATED")
    upc: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    isrc: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="es")
    original_release_date: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )
    territories: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    artist_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("artists.id"), nullable=True
    )
    tenant_id: Mapped[str] = mapped_column(String(100), default="default")
    owner_user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    artwork_id: Mapped[Optional[str]] = mapped_column(UUID(as_uuid=False), nullable=True)
    validation: Mapped[dict] = mapped_column(JSON, default=dict)
    delivery: Mapped[dict] = mapped_column(JSON, default=dict)
    ddex: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    artist: Mapped[Optional["DBArtist"]] = relationship(back_populates="releases")
    tracks: Mapped[list["DBTrack"]] = relationship(
        back_populates="release",
        cascade="all, delete-orphan",
        order_by="DBTrack.track_number",
    )

    __table_args__ = (
        Index("ix_releases_tenant", "tenant_id"),
        Index("ix_releases_upc", "upc"),
        Index("ix_releases_artist", "artist_id"),
        Index("ix_releases_status", "status"),
    )


class DBTrack(Base):
    __tablename__ = "tracks"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    release_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("releases.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    track_number: Mapped[int] = mapped_column(default=1)
    isrc: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(nullable=True)
    explicit: Mapped[bool] = mapped_column(Boolean, default=False)
    file_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tenant_id: Mapped[str] = mapped_column(String(100), default="default")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    release: Mapped["DBRelease"] = relationship(back_populates="tracks")

    __table_args__ = (
        Index("ix_tracks_release", "release_id"),
        Index("ix_tracks_isrc", "isrc"),
        Index("ix_tracks_tenant", "tenant_id"),
    )
