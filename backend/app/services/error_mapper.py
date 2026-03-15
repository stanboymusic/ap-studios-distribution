def map_ddex_errors(report: dict):
    mapped = []

    raw_issues = []
    raw_issues.extend(report.get("issues", []) or [])
    raw_issues.extend(report.get("errors", []) or [])
    raw_issues.extend(report.get("warnings", []) or [])

    for error in raw_issues:
        if not isinstance(error, dict):
            error = {"message": str(error), "severity": "ERROR"}

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
            "type": error.get("severity", error.get("level", "ERROR")),
            "section": section,
            "message": error.get("message", ""),
            "path": location,
            "rule": error.get("ruleId", error.get("code", error.get("rule", "")))
        })

    return mapped
