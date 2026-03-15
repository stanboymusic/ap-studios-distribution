from __future__ import annotations

from typing import Any, Dict

from app.models.validation_result import ValidationResult
from app.repositories.validation_repository import list_validations, save_validation
from app.services.ern_validator_api_client import validate_with_ern_validator_api


def normalize_response(resp: Dict[str, Any]) -> Dict[str, Any]:
    issues = resp.get("issues") or []
    has_errors = any(str(issue.get("severity", "")).upper() == "ERROR" for issue in issues if isinstance(issue, dict))

    status = "FAILED" if has_errors or str(resp.get("status", "")).lower() in {"failed", "error"} else "VALID"
    normalized: Dict[str, Any] = {
        "status": status,
        "errors": [i for i in issues if isinstance(i, dict) and str(i.get("severity", "")).upper() == "ERROR"],
        "warnings": [i for i in issues if isinstance(i, dict) and str(i.get("severity", "")).upper() == "WARNING"],
        "profile": resp.get("profile"),
        "validator_source": resp.get("validator_source"),
    }
    return normalized


def validate_and_store(
    xml_bytes: bytes,
    release_id: str,
    profile: str = "AudioAlbum",
    version: str = "4.3",
    tenant_id: str = "default",
) -> Dict[str, Any]:
    response = validate_with_ern_validator_api(xml_bytes, profile=profile, version=version)
    normalized = normalize_response(response)

    validation_result = ValidationResult.create(
        release_id=release_id,
        status=normalized["status"],
        raw_response=response if isinstance(response, dict) else {"response": response},
        validator_profile=normalized.get("profile") or profile,
    )
    storage_path = save_validation(validation_result, tenant_id=tenant_id)

    normalized["validation_id"] = validation_result.id
    normalized["storage_path"] = storage_path
    return normalized


def get_stored_validations(release_id: str, tenant_id: str = "default", limit: int = 50) -> list[dict]:
    return [result.model_dump() for result in list_validations(release_id, tenant_id=tenant_id, limit=limit)]
