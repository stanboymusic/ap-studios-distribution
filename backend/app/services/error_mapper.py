def map_ddex_errors(report: dict):
    mapped = []

    for error in report.get("issues", []):
        # Extraer sección del location
        location = error.get("location", "")
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

        mapped.append({
            "type": error.get("severity", "ERROR"),
            "section": section,
            "message": error.get("message", ""),
            "path": location,
            "rule": error.get("ruleId", error.get("code", ""))
        })

    return mapped