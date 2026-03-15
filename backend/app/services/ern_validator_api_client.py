from __future__ import annotations

import os
from typing import Any, Dict, List

import requests


class ExternalValidatorUnavailable(Exception):
    pass


def _candidate_urls() -> List[str]:
    base = (os.getenv("VALIDATOR_API_URL") or "http://localhost:6060").rstrip("/")
    return [
        f"{base}/api/json/validate",
        f"{base}/json/validate",
        f"{base}/api/validate",
        f"{base}/validate",
    ]


def _normalize_issue(raw: Any, severity: str = "ERROR") -> Dict[str, str]:
    if isinstance(raw, dict):
        return {
            "severity": str(raw.get("severity") or raw.get("level") or severity).upper(),
            "message": str(raw.get("message") or raw.get("detail") or raw.get("description") or raw),
            "location": str(raw.get("location") or raw.get("path") or ""),
            "ruleId": str(raw.get("ruleId") or raw.get("code") or raw.get("rule") or ""),
        }
    return {
        "severity": severity,
        "message": str(raw),
        "location": "",
        "ruleId": "",
    }


def _normalize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    issues: List[Dict[str, str]] = []

    for issue in payload.get("issues", []) or []:
        issues.append(_normalize_issue(issue, severity="ERROR"))

    for issue in payload.get("errors", []) or []:
        issues.append(_normalize_issue(issue, severity="ERROR"))

    for issue in payload.get("warnings", []) or []:
        issues.append(_normalize_issue(issue, severity="WARNING"))

    for issue in payload.get("messages", []) or []:
        issues.append(_normalize_issue(issue, severity="ERROR"))

    if payload.get("message"):
        issues.append(_normalize_issue(payload.get("message"), severity="ERROR"))

    if payload.get("errorMessage"):
        issues.append(_normalize_issue(payload.get("errorMessage"), severity="ERROR"))

    valid_flags = [payload.get("valid"), payload.get("isValid")]
    if payload.get("error") is True:
        valid = False
    elif any(v is True for v in valid_flags):
        valid = True
    elif any(v is False for v in valid_flags):
        valid = False
    elif payload.get("status") is not None:
        valid = str(payload["status"]).lower() in {"ok", "valid", "validated", "success", "passed"}
    else:
        # If the service answered without explicit validity state, infer from issue list.
        valid = not issues

    return {
        "status": "validated" if valid else "failed",
        "issues": issues,
        "validator_source": "ern-validator-api",
        "raw_response": payload,
    }


def _schema_version_id(version: str) -> str:
    normalized = (version or "").strip()
    mapping = {
        "4.3": "ern/411",
        "4.2": "ern/411",
        "4.1.1": "ern/411",
        "4.1": "ern/411",
        "4.0": "ern/41",
        "3.8.3": "ern/383",
        "3.8.2": "ern/382",
        "3.7.1": "ern/371",
        "3.4.1": "ern/341",
    }
    return mapping.get(normalized, "ern/411")


def _release_profile_id(schema_id: str, profile: str) -> str:
    if "/" in (profile or ""):
        return profile
    schema_key = (schema_id or "").replace("/", "")
    schema_profile_version = {
        "ern371": "13",
        "ern382": "14",
        "ern383": "14",
        "ern41": "21",
        "ern411": "21",
    }
    version = schema_profile_version.get(schema_key)
    if not version:
        return ""
    return f"commonreleasetypes/{version}/{(profile or '').strip()}"


def _normalize_java_validator_payload(payload: List[Any]) -> Dict[str, Any]:
    issues: List[Dict[str, str]] = []
    first = payload[0] if payload and isinstance(payload[0], dict) else {}

    schema_message = str(first.get("schema") or "")
    if schema_message and "validates against schema version" not in schema_message.lower():
        issues.append(
            {
                "severity": "ERROR",
                "message": schema_message,
                "location": "",
                "ruleId": "XSD",
            }
        )

    def ingest_schematron_entries(entries: Any) -> None:
        if not isinstance(entries, list):
            return
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            if entry.get("noError"):
                continue
            if entry.get("msg"):
                role = str(entry.get("role") or "Error")
                sev = "WARNING" if "conditional" in role.lower() else "ERROR"
                issues.append(
                    {
                        "severity": sev,
                        "message": str(entry.get("msg")),
                        "location": "",
                        "ruleId": role,
                    }
                )

    ingest_schematron_entries(first.get("schematron"))
    ingest_schematron_entries(first.get("businessProfileSchematron"))

    has_error = any(i.get("severity") == "ERROR" for i in issues)
    return {
        "status": "failed" if has_error else "validated",
        "issues": issues,
        "validator_source": "ern-validator-api",
        "raw_response": payload,
    }


def validate_with_ern_validator_api(
    xml_bytes: bytes,
    profile: str = "AudioAlbum",
    version: str = "4.3",
    timeout_seconds: float = 30.0,
) -> Dict[str, Any]:
    last_error: str | None = None
    schema_id = _schema_version_id(version)
    profile_id = _release_profile_id(schema_id, profile)

    for url in _candidate_urls():
        try:
            if url.endswith("/api/json/validate") or url.endswith("/json/validate"):
                data = {"messageSchemaVersionId": schema_id}
                if profile_id:
                    data["releaseProfileVersionId"] = profile_id
                response = requests.post(
                    url,
                    files={"messageFile": ("ern.xml", xml_bytes, "application/xml")},
                    data=data,
                    timeout=timeout_seconds,
                )
                if response.status_code in {200, 400, 422}:
                    payload = response.json()
                    if isinstance(payload, list):
                        return _normalize_java_validator_payload(payload)
                    if isinstance(payload, dict):
                        return _normalize_payload(payload)
                    return _normalize_payload({"messages": [str(payload)]})

            # Attempt 1: raw XML body.
            response = requests.post(
                url,
                data=xml_bytes,
                headers={
                    "Content-Type": "application/xml",
                    "X-DDEX-Profile": profile,
                    "X-DDEX-Version": version,
                },
                timeout=timeout_seconds,
            )
            if response.status_code in {200, 400, 422}:
                payload = response.json()
                return _normalize_payload(payload if isinstance(payload, dict) else {"messages": [payload]})

            # Attempt 2: multipart upload (some validator APIs expect file form data).
            response = requests.post(
                url,
                files={"file": ("ern.xml", xml_bytes, "application/xml")},
                data={"profile": profile, "version": version},
                timeout=timeout_seconds,
            )
            if response.status_code in {200, 400, 422}:
                payload = response.json()
                return _normalize_payload(payload if isinstance(payload, dict) else {"messages": [payload]})

            last_error = f"{url} returned HTTP {response.status_code}"
        except requests.RequestException as exc:
            last_error = f"{url} request failed: {exc}"
        except ValueError:
            last_error = f"{url} returned non-JSON response"

    raise ExternalValidatorUnavailable(last_error or "Validator API unavailable")
