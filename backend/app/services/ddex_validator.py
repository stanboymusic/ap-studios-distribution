import requests

from app.services.ern_validator_api_client import (
    ExternalValidatorUnavailable,
    validate_with_ern_validator_api_sync,
)

# Public fallback endpoints.
VALIDATOR_ENDPOINTS = [
    "https://ddex-workbench.org/api/validator/ern",
    "https://xml-validator.smecde.com/api/validator/ern",
]


def validate_with_workbench(ern_xml: str, profile: str = "AudioAlbum", version: str = "4.3"):
    xml_bytes = ern_xml.encode("utf-8") if isinstance(ern_xml, str) else ern_xml

    # Priority path: self-hosted ddexnet/ern-validator-api.
    try:
        return validate_with_ern_validator_api_sync(xml_bytes, profile=profile, version=version)
    except ExternalValidatorUnavailable as exc:
        last_error = str(exc)
    except Exception as exc:
        last_error = str(exc)

    # Legacy fallback path: public validators.
    for url in VALIDATOR_ENDPOINTS:
        try:
            files = {"file": ("ern.xml", xml_bytes, "application/xml")}
            data = {"profile": profile, "version": version}
            response = requests.post(url, files=files, data=data, timeout=20)
            if response.status_code == 200:
                payload = response.json()
                payload["validator_source"] = "public-workbench"
                return payload
            last_error = f"Status {response.status_code} from {url}"
        except Exception as exc:
            last_error = str(exc)

    return {
        "status": "error",
        "message": f"All validators failed. Last error: {last_error}",
        "raw_response": "Could not get a valid JSON response from validator API or public fallback services.",
        "validator_source": "unavailable",
    }
