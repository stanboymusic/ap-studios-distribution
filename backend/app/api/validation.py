from fastapi import APIRouter, HTTPException
from datetime import datetime
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

def sync_release_db(payload: dict):
    """Sincroniza los datos del payload del frontend con la RELEASES_DB del backend."""
    from app.api.releases import RELEASES_DB
    from app.models.release import ReleaseDraft
    from uuid import UUID
    
    release_id = payload.get("release_id")
    if not release_id:
        return
    
    # Extraer artista
    parties = payload.get("parties", {})
    artist_data = None
    for p_id, p_data in parties.items():
        if "artist" in p_id.lower():
            artist_data = p_data
            break
            
    # Buscar release o crear si no existe (para recuperarse de reinicios del server)
    release_obj = None
    for r in RELEASES_DB:
        if str(r.id) == release_id:
            release_obj = r
            break
    
    if not release_obj:
        # Reconstruir release básico desde el payload
        releases = payload.get("releases", {})
        release_info = list(releases.values())[0] if releases else {}
        
        release_obj = ReleaseDraft()
        release_obj.id = UUID(release_id)
        release_obj.title = release_info.get("title", "Recovered Release")
        RELEASES_DB.append(release_obj)
        import logging
        logging.getLogger(__name__).info(f"Recovered missing release {release_id} in memory")

    if artist_data:
        release_obj.artist = artist_data
    
    # Sincronizar tracks si están presentes en el payload
    resources = payload.get("resources", {})
    if resources:
        payload_tracks = []
        # El frontend envía tracks en releases[release_id].tracks
        releases = payload.get("releases", {})
        release_info = list(releases.values())[0] if releases else {}
        track_refs = release_info.get("tracks", [])
        
        for ref in track_refs:
            res = resources.get(ref)
            if res and res.get("type") == "SoundRecording":
                # Mapear de vuelta al formato esperado por ReleaseDraft.tracks
                track_entry = {
                    "track_id": res.get("track_id") or ref,
                    "title": res.get("title"),
                    "track_number": res.get("track_number"),
                    "duration_seconds": res.get("duration_seconds") or res.get("duration", 0),
                    "explicit": res.get("explicit", False),
                    "isrc": res.get("isrc"),
                    "file_path": res.get("file_path") or res.get("file")
                }
                payload_tracks.append(track_entry)
        
        if payload_tracks:
            release_obj.tracks = payload_tracks

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
    # Find saved ERN
    store = ErnStore()
    latest_path = store.base / release_id / "latest" / "ern.xml"
    
    # Find release in DB to update status later
    release_obj = None
    for r in RELEASES_DB:
        if str(r.id) == release_id:
            release_obj = r
            break

    if latest_path.exists():
        ern_xml = latest_path.read_bytes().decode('utf-8')
    else:
        # Fallback to building from DB if not generated yet
        if not release_obj:
            raise HTTPException(status_code=404, detail="Release or generated ERN not found")
        ern_xml = build_ern(release_obj)

    # Validate with Workbench
    report = validate_with_workbench(ern_xml, profile="AudioAlbum", version="4.3")

    # Get pre-validation status if possible
    pre_validation = {"valid": True}
    latest_meta_path = store.base / release_id / "latest" / "meta.json"
    if latest_meta_path.exists():
        try:
            import json
            meta = json.loads(latest_meta_path.read_text())
            if meta.get("validation"):
                # Check if all steps in validation are valid
                v = meta["validation"]
                all_valid = all(step.get("valid", True) for step in v.values() if isinstance(step, dict))
                pre_validation = {"valid": all_valid, "details": v}
        except:
            pass

    status = "validated"
    if report.get("status") == "error":
        report.update({
            "pre_validation": pre_validation,
            "ern_generated": latest_path.exists()
        })
        if pre_validation.get("valid"):
            status = "external_unavailable"
            report["status"] = status
        else:
            status = "failed"
        
        if release_obj:
            release_obj.validation["ddex_status"] = status
            
        return report

    errors = map_ddex_errors(report)
    status = "validated" if not errors else "failed"
    
    if release_obj:
        release_obj.validation["ddex_status"] = status

    return {
        "status": status,
        "ddex_errors": errors,
        "pre_validation": pre_validation,
        "ern_generated": latest_path.exists()
    }

@router.post("/generate-ern")
def generate_ern(payload: dict):
    from app.services.profile_validator import validate_profile
    from app.services.post_build_validator import post_build_validate
    from app.config.ddex import ERNProfile
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Generating ERN for payload: {payload.get('release_id')}")
        ern = payload.get("ern", {})
        profile_str = ern.get("profile", "AudioAlbum")
        logger.info(f"Profile: {profile_str}")
        profile = ERNProfile(profile_str)
        
        logger.info("Validating profile...")
        validate_profile(profile, payload)

        # Sincronizar datos con RELEASES_DB
        logger.info("Syncing with RELEASES_DB...")
        sync_release_db(payload)

        logger.info("Parsing payload with ErnJsonParser...")
        parser = ErnJsonParser()
        graph = parser.parse(payload)
        
        logger.info("Building XML with ErnBuilder...")
        builder = ErnBuilder()
        xml = builder.build(graph)
        context = graph["context"]

        # Post-build validation
        logger.info("Running post-build validation...")
        validation_results = post_build_validate(xml, context.version, context.profile)
        
        store = ErnStore()
        release_id = payload.get("release_id", "unknown")
        logger.info(f"Saving ERN for release {release_id}...")
        meta = store.save(release_id, xml, context, validation_results=validation_results)

        status = "generated"
        if not all(r.get("valid", True) for r in validation_results.values() if isinstance(r, dict)):
            status = "validation_failed"
            logger.warning(f"Validation failed for release {release_id}")

        return {
            "status": status,
            "meta": meta,
            "xml": xml.decode("utf-8"),
            "validation": validation_results
        }
    except Exception as e:
        logger.error(f"Error in generate_ern: {str(e)}", exc_info=True)
        raise e

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
    import logging
    logger = logging.getLogger(__name__)
    try:
        # Sincronizar datos con RELEASES_DB
        logger.info(f"Previewing ERN for payload: {payload.get('release_id')}")
        sync_release_db(payload)
        
        # Simple preview based on payload
        ern = payload.get("ern", {})
        parties = payload.get("parties", {})
        resources = payload.get("resources", {})
        releases = payload.get("releases", {})
        deals = payload.get("deals", {})

        summary = {
            "profile": ern.get("profile", "Unknown"),
            "ern_version": ern.get("version", "4.3"),
            "releases_count": len(releases),
            "tracks_count": len([r for r in resources.values() if r.get("type") == "SoundRecording" or r.get("resource_type") == "SoundRecording"]),
            "territories": "Worldwide",
            "party_id": ern.get("sender", {}).get("party_id", "Unknown")
        }

        release_tree = None
        if releases:
            release_id = list(releases.keys())[0]
            release = releases[release_id]
            artist_id = release.get("artist")
            artist_name = parties.get(artist_id, {}).get("display_name", "Unknown") if artist_id else "Unknown"
            tracks = release.get("tracks", [])
            track_details = []
            for t in tracks:
                res = resources.get(t, {})
                track_details.append({
                    "title": res.get("title", "Unknown"),
                    "isrc": res.get("isrc", "Unknown"),
                    "duration": res.get("duration_seconds") or res.get("duration") or 0
                })
            
            release_tree = {
                "title": release.get("title", "Unknown"),
                "artist": artist_name,
                "upc": release.get("upc", "Unknown"),
                "release_date": release.get("release_date", "Unknown"),
                "tracks": track_details
            }

        deal_table = [
            {
                "use_type": d.get("commercialModels", [{}])[0].get("use_type", "Unknown"),
                "model": d.get("commercialModels", [{}])[0].get("model", "Unknown"),
                "start_date": d.get("startDate", "Unknown"),
                "end_date": None,
                "territories": d.get("territories", [])
            } for d in deals.values()
        ]

        assets = []
        for r in resources.values():
            r_type = r.get("type") or r.get("resource_type")
            r_file = r.get("file") or r.get("filename")
            r_duration = r.get("duration_seconds") or r.get("duration") or 0
            
            if r_type == "SoundRecording":
                assets.append({
                    "type": "audio",
                    "filename": r_file or "track.wav",
                    "format": "WAV",
                    "duration": r_duration,
                    "checksum": None
                })
            elif r_type == "Image":
                assets.append({
                    "type": "artwork",
                    "filename": r_file or "cover.jpg",
                    "dimensions": "3000x3000",
                    "format": "JPEG"
                })

        message_header = {
            "message_id": ern.get("message_id", "Unknown"),
            "sender": ern.get("sender", {}).get("name", "Unknown"),
            "recipient": ern.get("recipient", {}).get("name", "Unknown"),
            "created_at": datetime.utcnow().isoformat() + "Z",
            "language": "en"
        }

        return {
            "summary": summary,
            "release": release_tree,
            "deals": deal_table,
            "assets": assets,
            "header": message_header
        }
    except Exception as e:
        logger.error(f"Error in preview_ern: {str(e)}", exc_info=True)
        raise e