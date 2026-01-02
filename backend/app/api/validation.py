from fastapi import APIRouter, HTTPException
from app.ddex.ern_builder import build_ern
from app.services.workbench_client import validate_ern
from app.services.validation_service import validate_release_draft
from app.services.ddex_validator import validate_with_workbench
from app.services.error_mapper import map_ddex_errors
from app.api.releases import RELEASES_DB
from app.ern.builder.ern_builder import ErnBuilder
from app.ern.builder.json_parser import ErnJsonParser
from app.ern.persistence.ern_store import ErnStore

router = APIRouter(prefix="/validation", tags=["Validation"])

@router.post("/validate-draft")
def validate_draft(release_id: str):
    # Find release
    for release in RELEASES_DB:
        if str(release.id) == release_id:
            # Validate draft
            errors = validate_release_draft(release)
            has_errors = any(e.level == "ERROR" for e in errors)
            has_warnings = any(e.level == "WARNING" for e in errors)
            return {
                "has_errors": has_errors,
                "has_warnings": has_warnings,
                "errors": [e.__dict__ for e in errors if e.level == "ERROR"],
                "warnings": [e.__dict__ for e in errors if e.level == "WARNING"]
            }
    raise HTTPException(status_code=404, detail="Release not found")

@router.post("/validate-release")
def validate_release(release_id: str):
    # Find release
    for release in RELEASES_DB:
        if str(release.id) == release_id:
            # Build ERN XML
            xml = build_ern(release)
            # Validate with Workbench
            try:
                result = validate_ern(xml, profile="AudioAlbum", version="4.3")
                return {
                    "status": "validated",
                    "xml": xml,
                    "validation_result": result
                }
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e)
                }
    raise HTTPException(status_code=404, detail="Release not found")

@router.post("/{release_id}/ddex")
def validate_ddex(release_id: str):
    # Find release
    for release in RELEASES_DB:
        if str(release.id) == release_id:
            # Build ERN XML
            ern_xml = build_ern(release)
            # Validate with Workbench
            report = validate_with_workbench(ern_xml, profile="AudioAlbum", version="4.3")

            if report.get("status") == "error":
                return report

            errors = map_ddex_errors(report)

            return {
                "status": "validated" if not errors else "failed",
                "ddex_errors": errors
            }
    raise HTTPException(status_code=404, detail="Release not found")

@router.post("/generate-ern")
def generate_ern(payload: dict):
    parser = ErnJsonParser()
    graph = parser.parse(payload)
    builder = ErnBuilder()
    xml = builder.build(graph)
    context = graph["context"]
    store = ErnStore()
    release_id = payload.get("release_id", "unknown")
    meta = store.save(release_id, xml, context)
    return {
        "status": "generated",
        "meta": meta,
        "xml": xml.decode("utf-8")
    }

@router.get("/ern/{release_id}/xml")
def get_ern_xml(release_id: str):
    # Find latest version
    store = ErnStore()
    base = store.base / release_id / "latest"
    if not base.exists():
        raise HTTPException(status_code=404, detail="ERN not found")

    xml_path = base / "ern.xml"
    if not xml_path.exists():
        raise HTTPException(status_code=404, detail="XML not found")

    xml_content = xml_path.read_bytes().decode('utf-8')
    return {"xml": xml_content}

@router.post("/preview-ern")
def preview_ern(payload: dict):
    # Simple preview based on payload
    context = payload.get("context", {})
    parties = payload.get("parties", {})
    resources = payload.get("resources", {})
    releases = payload.get("releases", {})
    deals = payload.get("deals", {})

    summary = {
        "profile": context.get("profile", "Unknown"),
        "ern_version": context.get("ern_version", "4.3"),
        "releases_count": len(releases),
        "tracks_count": len([r for r in resources.values() if r.get("resource_type") == "SoundRecording"]),
        "territories": "Worldwide",
        "language": context.get("language", "en"),
        "party_id": context.get("sender", {}).get("party_id", "Unknown")
    }

    release_tree = None
    if releases:
        release_id = list(releases.keys())[0]
        release = releases[release_id]
        artist_id = release.get("artist")
        artist_name = parties.get(artist_id, {}).get("display_name", "Unknown") if artist_id else "Unknown"
        tracks = release.get("tracks", [])
        track_details = [
            {
                "title": resources.get(t, {}).get("title", "Unknown"),
                "isrc": resources.get(t, {}).get("isrc", "Unknown"),
                "duration": resources.get(t, {}).get("duration", 0)
            } for t in tracks
        ]
        release_tree = {
            "title": release.get("title", "Unknown"),
            "artist": artist_name,
            "upc": release.get("upc", "Unknown"),
            "release_date": release.get("release_date", "Unknown"),
            "tracks": track_details
        }

    deal_table = [
        {
            "use_type": d.get("commercialModels", [{}])[0].get("type", "Unknown"),
            "start_date": d.get("startDate", "Unknown"),
            "end_date": None,
            "territories": d.get("territories", [])
        } for d in deals.values()
    ]

    assets = []
    for r in resources.values():
        if r.get("resource_type") == "SoundRecording":
            assets.append({
                "type": "audio",
                "filename": r.get("filename", "track.wav"),
                "format": "WAV",
                "duration": r.get("duration", 0),
                "checksum": None
            })
        elif r.get("resource_type") == "Image":
            assets.append({
                "type": "artwork",
                "filename": r.get("filename", "cover.jpg"),
                "dimensions": "3000x3000",
                "format": "JPEG"
            })

    message_header = {
        "message_id": context.get("message", {}).get("message_id", "Unknown"),
        "sender": context.get("sender", {}).get("name", "Unknown"),
        "recipient": context.get("recipient", {}).get("name", "Unknown"),
        "created_at": context.get("message", {}).get("created_at", "Unknown"),
        "language": context.get("language", "en")
    }

    return {
        "summary": summary,
        "release": release_tree,
        "deals": deal_table,
        "assets": assets,
        "header": message_header
    }