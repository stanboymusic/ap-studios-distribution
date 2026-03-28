"""
User model for AP Studios.
File-based persistence, same pattern as ReleaseDraft.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


class User:
    def __init__(
        self,
        email: str,
        hashed_password: str,
        role: str = "artist",
        tenant_id: str = "default",
        artist_id: Optional[str] = None,
        id: Optional[UUID] = None,
        is_active: bool = True,
        created_at: Optional[str] = None,
    ):
        self.id: UUID = id or uuid4()
        self.email = email.strip().lower()
        self.hashed_password = hashed_password
        self.role = role
        self.tenant_id = tenant_id
        self.artist_id = artist_id
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "email": self.email,
            "hashed_password": self.hashed_password,
            "role": self.role,
            "tenant_id": self.tenant_id,
            "artist_id": self.artist_id,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }

    def to_public(self) -> dict:
        d = self.to_dict()
        d.pop("hashed_password")
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        return cls(
            id=UUID(data["id"]),
            email=data["email"],
            hashed_password=data["hashed_password"],
            role=data.get("role", "artist"),
            tenant_id=data.get("tenant_id", "default"),
            artist_id=data.get("artist_id"),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at"),
        )
