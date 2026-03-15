from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


@dataclass(frozen=True)
class AutomationEvent:
    id: UUID = field(default_factory=uuid4)
    type: str = ""
    tenant_id: str = "default"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    release_id: Optional[str] = None
    party_reference: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    severity: str = "info"  # info|warning|high

