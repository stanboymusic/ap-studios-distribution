from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, List, Literal, Any
from pydantic import BaseModel


Validator = Literal["local", "workbench", "external"]
ValidationType = Literal["XSD", "Schematron", "BusinessRules", "XSD+Schematron", "DDEX"]
RunStatus = Literal["passed", "failed"]


class ValidationError(BaseModel):
    code: str
    message: str
    location: Optional[str] = None


class ValidationRun(BaseModel):
    id: UUID
    release_id: UUID

    validator: Validator
    validator_version: str

    validation_type: ValidationType
    profile: str

    status: RunStatus
    errors: List[ValidationError]

    xml_path: str
    xml_hash: str

    created_at: datetime

    @classmethod
    def create(cls, **kwargs: Any) -> "ValidationRun":
        return cls(
            id=uuid4(),
            created_at=datetime.utcnow(),
            **kwargs,
        )

