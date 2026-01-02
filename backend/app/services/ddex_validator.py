import requests

WORKBENCH_VALIDATOR_URL = "https://ddex-workbench.org/api/validator/ern"

def validate_with_workbench(ern_xml: str, profile: str = "AudioAlbum", version: str = "4.3"):
    files = {
        "file": ("ern.xml", ern_xml, "application/xml")
    }

    data = {
        "profile": profile,
        "version": version
    }

    response = requests.post(WORKBENCH_VALIDATOR_URL, files=files, data=data, timeout=30)

    if response.status_code != 200:
        return {
            "status": "error",
            "message": f"Workbench validator unavailable: {response.status_code} {response.text}"
        }

    return response.json()