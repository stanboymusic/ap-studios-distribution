from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from app.schemas.release import ReleaseCreate, ReleaseResponse, ReleaseUpdate
from app.models.release import ReleaseDraft
from app.services.catalog_service import CatalogService
from app.catalog.catalog_service import create_release as create_catalog_release
from app.catalog.identifier_service import claim_manual_isrc, claim_manual_upc, create_isrc
from uuid import UUID
from typing import List
from mutagen import File as MutagenFile
import shutil
from app.core.paths import storage_path
from app.fingerprinting.fingerprint_service import process_audio_fingerprint
from app.core.auth import ensure_release_access
from app.repositories import catalog_repository
from app.repositories import contract_repository as contract_repo

router = APIRouter(prefix="/releases", tags=["Releases"])

@router.post("/", response_model=ReleaseResponse)
def create_release(data: ReleaseCreate, request: Request):
    user_id = getattr(request.state, "user_id", None)
    user_role = getattr(request.state, "user_role", "artist")
    tenant_id = getattr(request.state, "tenant_id", "default")

    # Admin no necesita contrato
    # Artistas sin contrato no pueden crear releases
    if user_role != "admin" and user_id and not user_id.endswith(":anonymous"):
        if not contract_repo.has_accepted(user_id, tenant_id):
            raise HTTPException(
                status_code=403,
                detail="You must accept the AP Studios distribution terms "
                       "before creating releases. Go to /artist/contract.",
            )

    print("DEBUG: create_release called with data:", data.dict())

    if data.artist_id and not CatalogService.get_artist_by_id(data.artist_id, tenant_id=tenant_id):
        raise HTTPException(status_code=400, detail="artist_id does not exist")

    release = ReleaseDraft()
    release.title = data.title
    release.release_type = data.release_type
    release.original_release_date = data.original_release_date
    release.language = data.language
    release.territories = data.territories
    release.artist_id = data.artist_id
    # Extraer user_id del JWT (seteado por AuthContextMiddleware)
    owner_user_id = getattr(request.state, "user_id", None)
    # No guardar el anonymous placeholder
    if owner_user_id and owner_user_id.endswith(":anonymous"):
        owner_user_id = None
    release.owner_user_id = owner_user_id
    try:
        release_identity = create_catalog_release(
            title=data.title,
            artist_id=str(data.artist_id) if data.artist_id else None,
            tenant_id=tenant_id,
        )
        release.upc = release_identity["upc"]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unable to allocate UPC: {exc}") from exc

    CatalogService.save_release(release, tenant_id=tenant_id)

    return ReleaseResponse(
        id=release.id,
        release_id=release.id,
        title=release.title,
        type=release.release_type.value if hasattr(release.release_type, "value") else str(release.release_type),
        status=release.status,
        owner_user_id=release.owner_user_id,
    )

@router.get("/", response_model=List[ReleaseResponse])
def list_releases(request: Request):
    tenant_id = request.state.tenant_id
    releases = CatalogService.get_releases(tenant_id=tenant_id)
    user_id = getattr(request.state, "user_id", None)
    user_role = getattr(request.state, "user_role", "artist")
    if user_role != "admin":
        if user_id and not user_id.endswith(":anonymous"):
            releases = [
                r
                for r in releases
                if getattr(r, "owner_user_id", None) == user_id
            ]
        else:
            releases = []
    artists = CatalogService.get_artists(tenant_id=tenant_id)
    artist_map = {a.id: a.name for a in artists}
    
    print("DEBUG: list_releases called, returning", len(releases), "releases")
    return [
        ReleaseResponse(
            id=r.id,
            release_id=r.id,
            title=r.title or "Untitled",
            type=r.release_type.value if hasattr(r.release_type, "value") else str(r.release_type),
            status=r.status,
            owner_user_id=getattr(r, "owner_user_id", None),
            artist_name=artist_map.get(r.artist_id) if r.artist_id else "Unknown"
        )
        for r in releases
    ]

@router.get("/{release_id}")
def get_release(release_id: UUID, request: Request):
    tenant_id = request.state.tenant_id
    user_id = getattr(request.state, "user_id", None)
    user_role = getattr(request.state, "user_role", "artist")

    release = CatalogService.get_release_by_id(release_id, tenant_id=tenant_id)
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")

    if user_role != "admin":
        release_owner = getattr(release, "owner_user_id", None)
        if release_owner != user_id:
            raise HTTPException(status_code=404, detail="Release not found")

    return release.to_dict()

@router.put("/{release_id}")
def update_release(release_id: UUID, payload: ReleaseUpdate, request: Request):
    tenant_id = request.state.tenant_id
    owner_user_id = getattr(request.state, "user_id", None)
    user_role = getattr(request.state, "user_role", "artist")

    existing = CatalogService.get_release_by_id(release_id, tenant_id=tenant_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Release not found")

    # Admin puede editar cualquier release
    # Artista solo puede editar las suyas
    if user_role != "admin":
        if owner_user_id and existing.owner_user_id:
            if existing.owner_user_id != owner_user_id:
                raise HTTPException(
                    status_code=403,
                    detail="You can only edit your own releases",
                )

    release = existing
    if payload.upc:
        candidate_upc = (payload.upc or "").strip()
        if candidate_upc and candidate_upc != (release.upc or "").strip():
            try:
                release.upc = claim_manual_upc(
                    candidate_upc,
                    tenant_id=tenant_id,
                    source=f"release:{release.id}",
                )
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
    if payload.original_release_date:
        release.original_release_date = payload.original_release_date
    if payload.artwork_id:
        release.artwork_id = payload.artwork_id
    if payload.artist_id:
        release.artist_id = payload.artist_id
    
    CatalogService.save_release(release, tenant_id=tenant_id)
    return release.to_dict()

@router.delete("/{release_id}")
def delete_release(release_id: UUID, request: Request):
    tenant_id = request.state.tenant_id
    owner_user_id = getattr(request.state, "user_id", None)
    user_role = getattr(request.state, "user_role", "artist")

    existing = CatalogService.get_release_by_id(release_id, tenant_id=tenant_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Release not found")

    if user_role != "admin":
        if owner_user_id and existing.owner_user_id:
            if existing.owner_user_id != owner_user_id:
                raise HTTPException(
                    status_code=403,
                    detail="You can only delete your own releases",
                )

    deleted = catalog_repository.delete_release(tenant_id, str(release_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Release not found")
    return {"status": "deleted"}

@router.post("/{release_id}/audio")
def upload_audio(
    release_id: UUID,
    request: Request,
    file: UploadFile = File(...),
    isrc: str = None
):
    tenant_id = request.state.tenant_id
    release = CatalogService.get_release_by_id(release_id, tenant_id=tenant_id)
    if release:
        ensure_release_access(request, release)
        # Validar extensión
        if not file.filename.lower().endswith((".wav", ".flac")):
            raise HTTPException(
                status_code=400,
                detail="Only WAV or FLAC files are allowed"
            )

        # Ensure storage dir exists
        directory = storage_path("audio")
        directory.mkdir(parents=True, exist_ok=True)

        # Guardar archivo
        file_path = directory / f"{release.id}_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Leer duración
        audio = MutagenFile(str(file_path))
        if audio is None or not audio.info:
            raise HTTPException(
                status_code=400,
                detail="Unable to read audio file"
            )

        duration_seconds = int(audio.info.length)

        try:
            fingerprint_result = process_audio_fingerprint(
                source_id=str(release.id),
                source_type="release_audio",
                file_path=str(file_path),
                asset_path=str(file_path),
                tenant_id=tenant_id,
                ignore_same_source=True,
            )
        except RuntimeError as exc:
            try:
                file_path.unlink(missing_ok=True)
            except Exception:
                pass
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        if fingerprint_result["duplicate"]:
            try:
                file_path.unlink(missing_ok=True)
            except Exception:
                pass
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Duplicate audio detected",
                    "duplicate_of": fingerprint_result["track_id"],
                    "similarity": fingerprint_result["similarity"],
                    "source_type": fingerprint_result["source_type"],
                },
            )

        # Guardar metadata
        release.track_file = str(file_path)
        current_isrc = (release.isrc or "").strip() if getattr(release, "isrc", None) else ""
        requested_isrc = (isrc or "").strip()
        if requested_isrc:
            if requested_isrc != current_isrc:
                try:
                    release.isrc = claim_manual_isrc(
                        requested_isrc,
                        tenant_id=tenant_id,
                        source=f"release:{release.id}:audio",
                    )
                except ValueError as exc:
                    raise HTTPException(status_code=400, detail=str(exc)) from exc
            else:
                release.isrc = current_isrc
        elif not current_isrc:
            release.isrc = create_isrc(
                tenant_id=tenant_id,
                source=f"release:{release.id}:audio",
            )
        else:
            release.isrc = current_isrc
        release.duration = duration_seconds
        
        CatalogService.save_release(release, tenant_id=tenant_id)

        return {
            "message": "Audio uploaded successfully",
            "duration": duration_seconds,
            "file": file.filename,
            "fingerprint": {
                "id": fingerprint_result["fingerprint_id"],
                "hash": fingerprint_result["fingerprint"],
            },
        }

    raise HTTPException(status_code=404, detail="Release not found")
