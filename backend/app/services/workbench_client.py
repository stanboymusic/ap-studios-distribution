import requests

WORKBENCH_VALIDATE_URL = "https://ddex-workbench.org/api/validator/ern"

class WorkbenchValidationError(Exception):
    pass

def validate_ern(xml: str, profile: str = "AudioAlbum", version: str = "4.3"):
    files = {
        "file": ("ern.xml", xml, "application/xml")
    }

    data = {
        "profile": profile,
        "version": version
    }

    response = requests.post(
        WORKBENCH_VALIDATE_URL,
        files=files,
        data=data,
        timeout=30
    )

    if response.status_code != 200:
        raise WorkbenchValidationError(
            f"Workbench error {response.status_code}: {response.text}"
        )

    return response.json()

def normalize_validation_result(result):
    errors = []
    warnings = []

    for issue in result.get("issues", []):
        # Extraer sección del location o message
        location = issue.get("location", "")
        section = "Unknown"
        if "MessageHeader" in location:
            section = "MessageHeader"
        elif "Release" in location:
            section = "Release"
        elif "Resource" in location or "SoundRecording" in location:
            section = "Resources"
        elif "Deal" in location:
            section = "Deals"
        elif "Party" in location:
            section = "Parties"

        entry = {
            "type": issue.get("severity", "ERROR"),
            "section": section,
            "message": issue.get("message", ""),
            "path": location,
            "rule": issue.get("ruleId", issue.get("code", ""))
        }

        if issue.get("severity") == "ERROR":
            errors.append(entry)
        else:
            warnings.append(entry)

    return {
        "status": "valid" if not errors else "invalid",
        "errors": errors,
        "warnings": warnings
    }