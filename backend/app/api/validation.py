from datetime import datetime
import json
import logging
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel

from app.core.paths import tenant_path
from app.ddex.ern_builder import build_ern
from app.ern.builder.ern_builder import ErnBuilder
from app.ern.builder.json_parser import ErnJsonParser
from app.ern.persistence.ern_store import ErnStore
from app.models.release import ReleaseDraft
from app.models.validation_run import ValidationError, ValidationRun
from app.services.catalog_service import CatalogService
from app.services.ddex_validator import validate_with_workbench
from app.services.ern_parser import parse_xml_to_json, persist_parsed_release
from app.services.ern_validator_api_client import (
    ExternalValidatorUnavailable,
    validate_with_ern_validator_api,
)
from app.services.error_mapper import map_ddex_errors
from app.services.ern_validation_service import (
    get_stored_validations,
    validate_and_store,
)
from app.services.post_build_validator import post_build_validate
from app.services.xml_signer import XMLSigningError, sign_ern_xml
from app.services.validation_history_service import ValidationHistoryService
from app.services.validation_service import validate_release_draft
from app.services.workbench_client import validate_ern
from app.core.auth import ensure_release_access, require_admin

router = APIRouter(prefix="/validation", tags=["Validation"])
logger = logging.getLogger(__name__)


class ManualValidationDecisionRequest(BaseModel):
    reason: str | None = None
    actor: str | None = None


def _manual_validation_state(release_obj: ReleaseDraft) -> str:
    manual_review = (release_obj.validation or {}).get("manual_review") or {}
    manual_status = (manual_review.get("status") or "").strip().lower()
    if manual_status in {"approved", "rejected"}:
        return manual_status

    ddex_status = ((release_obj.validation or {}).get("ddex_status") or "").strip().lower()
    if ddex_status in {"validated", "external_unavailable"}:
        return "approved_auto"
    if ddex_status in {"failed"}:
        return "pending"
    return "pending"


def _append_manual_validation_history(
    release_obj: ReleaseDraft,
    *,
    status: str,
    actor: str,
    reason: str | None,
) -> None:
    history = release_obj.validation.get("history") or []
    errors = [] if status == "passed" else [reason or "Manual rejection"]
    history.append(
        {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "validator": actor,
            "type": "MANUAL_REVIEW",
            "status": status,
            "errors": errors,
        }
    )
    release_obj.validation["history"] = history

def sync_release_db(payload: dict):
    """Sincroniza los datos del payload del frontend con el Catálogo del backend."""
    import logging
    logger = logging.getLogger(__name__)
    
    release_id = (payload.get("release_id") or "").strip()
    if not release_id:
        return
    
    # Extraer artista
    parties = payload.get("parties", {})
    artist_id = None
    for p_id, p_data in parties.items():
        if "artist" in p_id.lower():
            # Intentar obtener artist_id del payload o del catálogo
            artist_id = p_data.get("artist_id")
            break
            
    # Tenant-aware: caller may inject tenant_id into payload; fallback to default.
    tenant_id = payload.get("tenant_id") or "default"

    # Buscar release o crear si no existe
    try:
        release_uuid = UUID(release_id)
    except Exception:
        return

    release_obj = CatalogService.get_release_by_id(release_uuid, tenant_id=tenant_id)
    
    if not release_obj:
        # Reconstruir release básico desde el payload
        releases = payload.get("releases", {})
        release_info = list(releases.values())[0] if releases else {}
        
        release_obj = ReleaseDraft()
        release_obj.id = release_uuid
        release_obj.title = release_info.get("title", "Recovered Release")
        logger.info(f"Recovered missing release {release_id} in catalog")

    if artist_id:
        release_obj.artist_id = UUID(artist_id)
    
    # Sincronizar tracks si están presentes en el payload
    resources = payload.get("resources", {})
    if resources:
        payload_tracks = []
        releases = payload.get("releases", {})
        release_info = list(releases.values())[0] if releases else {}
        track_refs = release_info.get("tracks", [])
        
        for ref in track_refs:
            res = resources.get(ref)
            if res and res.get("type") == "SoundRecording":
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
            # Note: We should probably use track_ids in the future, 
            # but for now we keep tracks as a list of dicts in ReleaseDraft for compatibility
            release_obj.tracks = payload_tracks

    CatalogService.save_release(release_obj, tenant_id=tenant_id)


def _load_ern_xml(release_uuid: UUID, release_obj: ReleaseDraft | None) -> tuple[bytes, Path]:
    store = ErnStore()
    latest_path = store.base / str(release_uuid) / "latest" / "ern.xml"

    if latest_path.exists():
        return latest_path.read_bytes(), latest_path

    if not release_obj:
        raise HTTPException(status_code=404, detail="Release or generated ERN not found")

    return build_ern(release_obj).encode("utf-8"), latest_path


def _read_pre_validation(store: ErnStore, release_uuid: UUID) -> dict:
    latest_meta_path = store.base / str(release_uuid) / "latest" / "meta.json"
    if not latest_meta_path.exists():
        return {"valid": True}
    try:
        meta = json.loads(latest_meta_path.read_text(encoding="utf-8"))
        validation = meta.get("validation") or {}
        all_valid = all(step.get("valid", True) for step in validation.values() if isinstance(step, dict))
        return {"valid": all_valid, "details": validation}
    except Exception:
        return {"valid": True}


def _save_parsed_ern(release_uuid: UUID, tenant_id: str, xml_bytes: bytes) -> str | None:
    try:
        parsed = parse_xml_to_json(xml_bytes)
        return persist_parsed_release(str(release_uuid), tenant_id=tenant_id, parsed_payload=parsed)
    except Exception as exc:
        logger.warning("Unable to parse ERN %s to JSON: %s", release_uuid, exc)
        return None


def _set_release_status(release_obj: ReleaseDraft | None, tenant_id: str, status: str) -> None:
    if not release_obj:
        return
    release_obj.status = status
    release_obj.updated_at = datetime.utcnow().isoformat()
    CatalogService.save_release(release_obj, tenant_id=tenant_id)


@router.post("/external")
async def external_validate(
    request: Request,
    file: UploadFile = File(...),
    profile: str = "AudioAlbum",
    version: str = "4.3",
    release_id: str | None = None,
):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty XML payload")
    try:
        if release_id:
            tenant_id = request.state.tenant_id
            try:
                rid = UUID(release_id)
                release_obj = CatalogService.get_release_by_id(rid, tenant_id=tenant_id)
                if release_obj:
                    ensure_release_access(request, release_obj)
            except Exception:
                pass
            return validate_and_store(
                content,
                release_id=release_id,
                profile=profile,
                version=version,
                tenant_id=tenant_id,
            )
        return await validate_with_ern_validator_api(content, profile=profile, version=version)
    except ExternalValidatorUnavailable as exc:
        raise HTTPException(status_code=502, detail=f"Validator unavailable: {exc}") from exc


@router.get("/results/{release_id}")
def get_external_validation_results(release_id: str, request: Request, limit: int = 50):
    tenant_id = request.state.tenant_id
    try:
        rid = UUID(release_id)
        release_obj = CatalogService.get_release_by_id(rid, tenant_id=tenant_id)
        if release_obj:
            ensure_release_access(request, release_obj)
    except Exception:
        pass
    return {
        "release_id": release_id,
        "runs": get_stored_validations(release_id, tenant_id=tenant_id, limit=limit),
    }


@router.post("/sign/{release_id}")
def sign_existing_ern(release_id: str, request: Request):
    tenant_id = request.state.tenant_id
    store = ErnStore()
    latest_path = store.base / release_id / "latest" / "ern.xml"
    if not latest_path.exists():
        raise HTTPException(status_code=404, detail="ERN not found")

    try:
        signed = sign_ern_xml(latest_path.read_bytes(), force=True)
    except XMLSigningError as exc:
        raise HTTPException(status_code=500, detail=f"Signing failed: {exc}") from exc

    if not signed.applied:
        raise HTTPException(status_code=400, detail=signed.message or "Signing not applied")

    latest_path.write_bytes(signed.signed_xml)
    try:
        rid = UUID(release_id)
        release_obj = CatalogService.get_release_by_id(rid, tenant_id=tenant_id)
        if release_obj:
            ensure_release_access(request, release_obj)
            release_obj.validation["signed"] = True
            release_obj.validation["signature_algorithm"] = signed.signature_algorithm
            release_obj.status = "SIGNED"
            CatalogService.save_release(release_obj, tenant_id=tenant_id)
    except HTTPException:
        raise
    except Exception:
        pass

    return {
        "status": "signed",
        "signature_algorithm": signed.signature_algorithm,
        "digest_algorithm": signed.digest_algorithm,
        "message": signed.message,
    }

@router.post("/validate-draft")
def validate_draft(release_id: str, request: Request):
    tenant_id = request.state.tenant_id
    rid = (release_id or "").strip()
    try:
        release_uuid = UUID(rid)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid release_id (expected UUID)")

    release = CatalogService.get_release_by_id(release_uuid, tenant_id=tenant_id)
    if release:
        ensure_release_access(request, release)
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
def validate_release(release_id: str, request: Request):
    tenant_id = request.state.tenant_id
    rid = (release_id or "").strip()
    try:
        release_uuid = UUID(rid)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid release_id (expected UUID)")

    release = CatalogService.get_release_by_id(release_uuid, tenant_id=tenant_id)
    if release:
        ensure_release_access(request, release)
        xml = build_ern(release)
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
def validate_ddex(release_id: str, request: Request):
    tenant_id = request.state.tenant_id
    rid = (release_id or "").strip()
    try:
        release_uuid = UUID(rid)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid release_id (expected UUID)")

    store = ErnStore()
    release_obj = CatalogService.get_release_by_id(release_uuid, tenant_id=tenant_id)
    if release_obj:
        ensure_release_access(request, release_obj)
    xml_bytes, latest_path = _load_ern_xml(release_uuid, release_obj)
    ern_xml = xml_bytes.decode("utf-8")

    parsed_path = _save_parsed_ern(release_uuid=release_uuid, tenant_id=tenant_id, xml_bytes=xml_bytes)
    report = validate_with_workbench(ern_xml, profile="AudioAlbum", version="4.3")

    pre_validation = _read_pre_validation(store, release_uuid)

    status = "validated"
    if report.get("status") == "error":
        report.update({
            "pre_validation": pre_validation,
            "ern_generated": latest_path.exists(),
            "parsed_json_path": parsed_path,
        })
        if pre_validation.get("valid"):
            status = "external_unavailable"
            report["status"] = status
        else:
            status = "failed"
        
        if release_obj:
            release_obj.validation["ddex_status"] = status
            if parsed_path:
                release_obj.validation["parsed_json_path"] = parsed_path
            history = release_obj.validation.get("history") or []
            history.append({
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "validator": "external",
                "type": "DDEX",
                "status": "passed" if status == "external_unavailable" else "failed",
                "errors": report.get("ddex_errors") or report.get("errors") or [],
                "source": report.get("validator_source", "unknown"),
            })
            release_obj.validation["history"] = history
            _set_release_status(
                release_obj,
                tenant_id=tenant_id,
                status="VALIDATED" if status == "external_unavailable" else "CREATED",
            )

        # Persist auditable validation run
        try:
            xml_bytes = ern_xml.encode("utf-8")
            run = ValidationRun.create(
                release_id=release_uuid,
                validator="external",
                validator_version=str(report.get("validator_source") or "workbench"),
                validation_type="DDEX",
                profile="AudioAlbum",
                status="passed" if status == "external_unavailable" else "failed",
                errors=[
                    ValidationError(code="DDEX", message=str(e), location=None)
                    for e in (report.get("ddex_errors") or report.get("errors") or [])
                ],
                xml_path=str(latest_path) if latest_path.exists() else "generated",
                xml_hash=ValidationHistoryService.build_xml_hash(xml_bytes),
            )
            ValidationHistoryService.save_run(run, tenant_id=tenant_id)
        except Exception:
            pass
            
        return report

    errors = map_ddex_errors(report)
    status = "validated" if not errors else "failed"
    
    if release_obj:
        release_obj.validation["ddex_status"] = status
        if parsed_path:
            release_obj.validation["parsed_json_path"] = parsed_path
        history = release_obj.validation.get("history") or []
        history.append({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "validator": "external",
            "type": "DDEX",
            "status": "passed" if status == "validated" else "failed",
            "errors": errors,
            "source": report.get("validator_source", "unknown"),
        })
        release_obj.validation["history"] = history
        _set_release_status(
            release_obj,
            tenant_id=tenant_id,
            status="VALIDATED" if status == "validated" else "CREATED",
        )

    # Persist auditable validation run
    try:
        xml_bytes = ern_xml.encode("utf-8")
        run = ValidationRun.create(
            release_id=release_uuid,
            validator="external",
            validator_version=str(report.get("validator_source") or "workbench"),
            validation_type="DDEX",
            profile="AudioAlbum",
            status="passed" if status == "validated" else "failed",
            errors=[
                ValidationError(code=(e.get("code") or "DDEX"), message=(e.get("message") or str(e)), location=e.get("location"))
                if isinstance(e, dict)
                else ValidationError(code="DDEX", message=str(e), location=None)
                for e in (errors or [])
            ],
            xml_path=str(latest_path) if latest_path.exists() else "generated",
            xml_hash=ValidationHistoryService.build_xml_hash(xml_bytes),
        )
        ValidationHistoryService.save_run(run, tenant_id=tenant_id)
    except Exception:
        pass

    return {
        "status": status,
        "ddex_errors": errors,
        "pre_validation": pre_validation,
        "ern_generated": latest_path.exists(),
        "validator_source": report.get("validator_source", "unknown"),
        "parsed_json_path": parsed_path,
    }


@router.get("/admin/queue")
def admin_validation_queue(
    request: Request,
    state: str = Query("all", pattern="^(all|pending|approved|rejected)$"),
):
    require_admin(request)
    tenant_id = request.state.tenant_id
    releases = CatalogService.get_releases(tenant_id=tenant_id)
    rows = []
    for release in releases:
        review_state = _manual_validation_state(release)
        if state == "pending" and review_state not in {"pending"}:
            continue
        if state == "approved" and review_state not in {"approved", "approved_auto"}:
            continue
        if state == "rejected" and review_state not in {"rejected"}:
            continue

        artist_name = None
        if getattr(release, "artist_id", None):
            artist = CatalogService.get_artist_by_id(release.artist_id, tenant_id=tenant_id)
            artist_name = artist.name if artist else None

        validation = release.validation or {}
        manual = validation.get("manual_review") or {}
        history = validation.get("history") or []
        last_validation_at = history[-1].get("timestamp") if history else None

        rows.append(
            {
                "release_id": str(release.id),
                "title": release.title or "Untitled",
                "artist_name": artist_name or "Unknown",
                "release_status": release.status,
                "delivery_status": (release.delivery or {}).get("status"),
                "ddex_status": validation.get("ddex_status"),
                "manual_state": review_state,
                "manual_reason": manual.get("reason"),
                "manual_actor": manual.get("actor"),
                "manual_updated_at": manual.get("updated_at"),
                "last_validation_at": last_validation_at,
                "upc": release.upc,
            }
        )

    rows.sort(key=lambda row: row.get("last_validation_at") or "", reverse=True)
    return {"items": rows, "total": len(rows), "filter": state}


@router.post("/admin/{release_id}/approve")
def admin_approve_release_validation(
    release_id: str,
    payload: ManualValidationDecisionRequest,
    request: Request,
):
    require_admin(request)
    tenant_id = request.state.tenant_id
    rid = (release_id or "").strip()
    try:
        release_uuid = UUID(rid)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid release_id (expected UUID)")

    release_obj = CatalogService.get_release_by_id(release_uuid, tenant_id=tenant_id)
    if not release_obj:
        raise HTTPException(status_code=404, detail="Release not found")

    actor = (payload.actor or "").strip() or request.headers.get("X-Admin-User") or "admin"
    reason = (payload.reason or "").strip() or "Manual approval from Validation Center"
    now = datetime.utcnow().isoformat() + "Z"

    release_obj.validation["manual_review"] = {
        "status": "approved",
        "reason": reason,
        "actor": actor,
        "updated_at": now,
    }
    release_obj.validation["ddex_status"] = "validated"
    _append_manual_validation_history(
        release_obj,
        status="passed",
        actor=actor,
        reason=reason,
    )
    _set_release_status(release_obj, tenant_id=tenant_id, status="VALIDATED")

    return {
        "status": "approved",
        "release_id": rid,
        "reason": reason,
        "actor": actor,
        "updated_at": now,
    }


@router.post("/admin/{release_id}/reject")
def admin_reject_release_validation(
    release_id: str,
    payload: ManualValidationDecisionRequest,
    request: Request,
):
    require_admin(request)
    tenant_id = request.state.tenant_id
    rid = (release_id or "").strip()
    try:
        release_uuid = UUID(rid)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid release_id (expected UUID)")

    release_obj = CatalogService.get_release_by_id(release_uuid, tenant_id=tenant_id)
    if not release_obj:
        raise HTTPException(status_code=404, detail="Release not found")

    actor = (payload.actor or "").strip() or request.headers.get("X-Admin-User") or "admin"
    reason = (payload.reason or "").strip() or "Manual rejection from Validation Center"
    now = datetime.utcnow().isoformat() + "Z"

    release_obj.validation["manual_review"] = {
        "status": "rejected",
        "reason": reason,
        "actor": actor,
        "updated_at": now,
    }
    release_obj.validation["ddex_status"] = "failed"
    if not getattr(release_obj, "delivery", None):
        release_obj.delivery = {}
    release_obj.delivery["status"] = "not_delivered"
    _append_manual_validation_history(
        release_obj,
        status="failed",
        actor=actor,
        reason=reason,
    )
    _set_release_status(release_obj, tenant_id=tenant_id, status="CREATED")

    return {
        "status": "rejected",
        "release_id": rid,
        "reason": reason,
        "actor": actor,
        "updated_at": now,
    }


@router.post("/admin/{release_id}/revalidate")
def admin_revalidate_release(release_id: str, request: Request):
    require_admin(request)
    result = validate_ddex(release_id, request)

    tenant_id = request.state.tenant_id
    try:
        release_uuid = UUID(release_id)
    except Exception:
        return result
    release_obj = CatalogService.get_release_by_id(release_uuid, tenant_id=tenant_id)
    if release_obj:
        manual_review = (release_obj.validation or {}).get("manual_review") or {}
        manual_status = (manual_review.get("status") or "").strip().lower()
        if manual_status in {"approved", "rejected"}:
            release_obj.validation["manual_review"] = {
                "status": "pending",
                "reason": "Manual decision reset after revalidation",
                "actor": request.headers.get("X-Admin-User") or "admin",
                "updated_at": datetime.utcnow().isoformat() + "Z",
            }
            CatalogService.save_release(release_obj, tenant_id=tenant_id)

    return result


@router.post("/run/{release_id}")
def run_local_validation(release_id: UUID, request: Request):
    """
    Ejecuta validación local (XSD + Schematron placeholder) contra el ERN más reciente
    y persiste un ValidationRun auditable en disco.
    """
    tenant_id = request.state.tenant_id
    store = ErnStore()
    latest_dir = store.base / str(release_id) / "latest"
    xml_path = latest_dir / "ern.xml"
    meta_path = latest_dir / "meta.json"

    if not xml_path.exists():
        raise HTTPException(status_code=400, detail="ERN not generated yet for this release")

    xml_bytes = xml_path.read_bytes()
    _save_parsed_ern(release_uuid=release_id, tenant_id=tenant_id, xml_bytes=xml_bytes)

    # Load meta context (best-effort)
    version = "4.3"
    profile = "AudioAlbum"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            version = meta.get("ern_version") or version
            profile = meta.get("profile") or profile
        except Exception:
            pass

    results = post_build_validate(xml_bytes, version, profile)
    xsd_ok = bool(results.get("xsd", {}).get("valid", True))
    sch_ok = bool(results.get("schematron", {}).get("valid", True))
    ok = xsd_ok and sch_ok

    errors: list[ValidationError] = []
    for err in (results.get("xsd", {}).get("errors") or []):
        errors.append(ValidationError(code="XSD", message=str(err), location=None))
    for err in (results.get("schematron", {}).get("errors") or []):
        errors.append(ValidationError(code="Schematron", message=str(err), location=None))

    run = ValidationRun.create(
        release_id=release_id,
        validator="local",
        validator_version=f"ERN-{version}",
        validation_type="XSD+Schematron",
        profile=str(profile),
        status="passed" if ok else "failed",
        errors=errors,
        xml_path=str(xml_path),
        xml_hash=ValidationHistoryService.build_xml_hash(xml_bytes),
    )
    ValidationHistoryService.save_run(run, tenant_id=tenant_id)

    # Derive and persist current status on release for backwards compatibility
    release_obj = CatalogService.get_release_by_id(release_id, tenant_id=tenant_id)
    if release_obj:
        ensure_release_access(request, release_obj)
        release_obj.validation["ddex_status"] = "validated" if ok else "failed"
        _set_release_status(
            release_obj,
            tenant_id=tenant_id,
            status="VALIDATED" if ok else "CREATED",
        )

    return run.model_dump()


@router.get("/history/{release_id}")
def get_validation_history(release_id: UUID, request: Request):
    tenant_id = request.state.tenant_id
    release_obj = CatalogService.get_release_by_id(release_id, tenant_id=tenant_id)
    if release_obj:
        ensure_release_access(request, release_obj)
    return ValidationHistoryService.get_history(release_id, tenant_id=tenant_id)


@router.get("/ern/{release_id}/parsed")
def get_parsed_ern(release_id: str, request: Request):
    tenant_id = request.state.tenant_id
    try:
        rid = UUID(release_id)
        release_obj = CatalogService.get_release_by_id(rid, tenant_id=tenant_id)
        if release_obj:
            ensure_release_access(request, release_obj)
    except Exception:
        pass
    parsed_path = tenant_path(tenant_id, "validation", release_id, "parsed-latest.json")
    if parsed_path.exists():
        return json.loads(parsed_path.read_text(encoding="utf-8"))

    xml_path = ErnStore().base / release_id / "latest" / "ern.xml"
    if not xml_path.exists():
        raise HTTPException(status_code=404, detail="ERN not found")

    parsed = parse_xml_to_json(xml_path.read_bytes())
    persist_parsed_release(release_id=release_id, tenant_id=tenant_id, parsed_payload=parsed)
    return parsed

@router.post("/generate-ern")
def generate_ern(payload: dict, request: Request):
    from app.services.profile_validator import validate_profile
    from app.services.post_build_validator import post_build_validate
    from app.config.ddex import ERNProfile
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Generating ERN for payload: {payload.get('release_id')}")
        tenant_id = request.state.tenant_id
        ern = payload.get("ern", {})
        profile_str = ern.get("profile", "AudioAlbum")
        logger.info(f"Profile: {profile_str}")
        profile = ERNProfile(profile_str)
        
        logger.info("Validating profile...")
        validate_profile(profile, payload)

        # Sincronizar datos con el Catálogo
        logger.info("Syncing with Catalog...")
        payload["tenant_id"] = tenant_id
        release_id = (payload.get("release_id") or "").strip()
        if release_id:
            try:
                release_uuid = UUID(release_id)
                release_obj = CatalogService.get_release_by_id(release_uuid, tenant_id=tenant_id)
                if release_obj:
                    ensure_release_access(request, release_obj)
            except Exception:
                pass
        sync_release_db(payload)

        logger.info("Parsing payload with ErnJsonParser...")
        parser = ErnJsonParser()
        graph = parser.parse(payload)
        
        logger.info("Building XML with ErnBuilder...")
        builder = ErnBuilder()
        unsigned_xml = builder.build(graph)
        context = graph["context"]

        signing = sign_ern_xml(unsigned_xml)
        xml = signing.signed_xml if signing.applied else unsigned_xml

        # Post-build validation
        logger.info("Running post-build validation...")
        validation_results = post_build_validate(xml, context.version, context.profile)
        
        store = ErnStore()
        release_id = (payload.get("release_id") or "unknown").strip()
        logger.info(f"Saving ERN for release {release_id}...")
        meta = store.save(
            release_id,
            xml,
            context,
            validation_results=validation_results,
            extra_meta={
                "signing": {
                    "enabled": bool(signing.applied),
                    "signature_algorithm": signing.signature_algorithm,
                    "digest_algorithm": signing.digest_algorithm,
                    "key_path": signing.key_path,
                    "cert_path": signing.cert_path,
                    "message": signing.message,
                }
            },
        )
        parsed_payload = parse_xml_to_json(xml)
        parsed_path = persist_parsed_release(release_id=release_id, tenant_id=tenant_id, parsed_payload=parsed_payload)

        # Append validation history entry (audit)
        try:
            try:
                release_uuid = UUID(release_id)
            except Exception:
                release_uuid = None

            release_obj = CatalogService.get_release_by_id(release_uuid, tenant_id=tenant_id) if release_uuid else None
            if release_obj:
                history = release_obj.validation.get("history") or []
                history.append({
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "validator": "local",
                    "type": "ERN_GENERATED",
                    "status": "passed",
                    "errors": [],
                    "signed": signing.applied,
                })
                release_obj.validation["history"] = history
                release_obj.validation["signed"] = signing.applied
                release_obj.validation["signature_algorithm"] = signing.signature_algorithm
                release_obj.status = "SIGNED" if signing.applied else "CREATED"
                CatalogService.save_release(release_obj, tenant_id=tenant_id)
        except Exception:
            pass

        status = "generated"
        if not all(r.get("valid", True) for r in validation_results.values() if isinstance(r, dict)):
            status = "validation_failed"
            logger.warning(f"Validation failed for release {release_id}")

        return {
            "status": status,
            "meta": meta,
            "xml": xml.decode("utf-8"),
            "validation": validation_results,
            "parsed_json": parsed_payload,
            "parsed_json_path": parsed_path,
            "signing": {
                "applied": signing.applied,
                "signature_algorithm": signing.signature_algorithm,
                "digest_algorithm": signing.digest_algorithm,
                "message": signing.message,
            },
        }
    except XMLSigningError as e:
        logger.error(f"XML signing error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"XML signing error: {str(e)}")
    except Exception as e:
        logger.error(f"Error in generate_ern: {str(e)}", exc_info=True)
        raise e

@router.get("/ern/{release_id}/xml")
def get_ern_xml(release_id: str, request: Request):
    tenant_id = request.state.tenant_id
    try:
        rid = UUID(release_id)
        release_obj = CatalogService.get_release_by_id(rid, tenant_id=tenant_id)
        if release_obj:
            ensure_release_access(request, release_obj)
    except Exception:
        pass
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
def preview_ern(payload: dict, request: Request):
    try:
        # Sincronizar datos con RELEASES_DB
        logger.info(f"Previewing ERN for payload: {payload.get('release_id')}")
        tenant_id = request.state.tenant_id
        payload["tenant_id"] = tenant_id
        release_id = (payload.get("release_id") or "").strip()
        if release_id:
            try:
                release_uuid = UUID(release_id)
                release_obj = CatalogService.get_release_by_id(release_uuid, tenant_id=tenant_id)
                if release_obj:
                    ensure_release_access(request, release_obj)
            except Exception:
                pass
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
