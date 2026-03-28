"""
Contract acceptance model for AP Studios.
Records artist agreement to distribution terms.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4


# Versión actual del contrato — incrementar cuando cambien los términos
CURRENT_CONTRACT_VERSION = "1.0.0"


class ContractAcceptance:
    def __init__(
        self,
        user_id: str,
        tenant_id: str,
        version: str = CURRENT_CONTRACT_VERSION,
        accepted_at: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        id: Optional[str] = None,
    ):
        self.id = id or str(uuid4())
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.version = version
        self.accepted_at = accepted_at or datetime.now(timezone.utc).isoformat()
        self.ip_address = ip_address
        self.user_agent = user_agent

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "version": self.version,
            "accepted_at": self.accepted_at,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ContractAcceptance":
        return cls(
            id=data.get("id"),
            user_id=data["user_id"],
            tenant_id=data["tenant_id"],
            version=data.get("version", CURRENT_CONTRACT_VERSION),
            accepted_at=data.get("accepted_at"),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
        )
