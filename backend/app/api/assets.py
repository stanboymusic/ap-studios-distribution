from __future__ import annotations

import re
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from PIL import Image

from app.core.auth import ensure_authenticated, is_admin
from app.core.paths import storage_path
from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/assets", tags=["Assets"])

MAX_COVER_BYTES = 25 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 60_000_000  # defensa contra "decompression bombs"

_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def _clean_uuid(value: str) -> str:
    """Solo UUID completos (sin comodines ni prefijos): evita enumerar/adivinar archivos."""
    v = (value or "").strip()
    if v.upper().startswith("TRK-"):
        v = v[4:]
    if not _UUID_RE.match(v):
        raise HTTPException(status_code=404, detail="Not found")
    return v.lower()


def _owns_release_with(request: Request, tenant_id: str, predicate) -> bool:
    uid = ensure_authenticated(request)
    for r in CatalogService.get_releases(tenant_id=tenant_id):
        if (getattr(r, "owner_user_id", None) or "") == uid and predicate(r):
            return True
    return False


@router.get("/artwork/{artwork_id}")
def get_artwork(artwork_id: str, request: Request):
    tenant_id = request.state.tenant_id
    aid = _clean_uuid(artwork_id)
    asset = CatalogService.get_asset_by_id(aid, tenant_id=tenant_id)
    if not asset or asset.get("type") != "artwork":
        raise HTTPException(status_code=404, detail="Artwork not found")

    uid = ensure_authenticated(request)
    allowed = (
        is_admin(request)
        or (asset.get("owner_user_id") or "") == uid
        # portadas anteriores a esta versión (sin owner): vale si el release es tuyo
        or _owns_release_with(request, tenant_id, lambda r: str(getattr(r, "artwork_id", "") or "").lower() == aid)
    )
    if not allowed:
        raise HTTPException(status_code=404, detail="Artwork not found")

    path = Path(asset.get("path") or "")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Artwork not found")
    return FileResponse(str(path))


@router.get("/audio/{track_id}")
def get_audio(track_id: str, request: Request):
    tenant_id = request.state.tenant_id
    tid = _clean_uuid(track_id)
    asset = CatalogService.get_asset_by_id(tid, tenant_id=tenant_id)
    if not asset or asset.get("type") != "audio":
        raise HTTPException(status_code=404, detail="Audio not found")

    def _has_track(r) -> bool:
        for t in getattr(r, "tracks", None) or []:
            if isinstance(t, dict) and str(t.get("track_id") or "").replace("TRK-", "").lower() == tid:
                return True
        return False

    uid = ensure_authenticated(request)
    allowed = (
        is_admin(request)
        or (asset.get("owner_user_id") or "") == uid
        or _owns_release_with(request, tenant_id, _has_track)
    )
    if not allowed:
        raise HTTPException(status_code=404, detail="Audio not found")

    path = Path(asset.get("path") or "")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio not found")
    return FileResponse(str(path))


@router.post("/cover")
async def upload_cover(request: Request, cover: UploadFile = File(...)):
    uid = ensure_authenticated(request)
    tenant_id = request.state.tenant_id

    image_bytes = await cover.read(MAX_COVER_BYTES + 1)
    if len(image_bytes) > MAX_COVER_BYTES:
        raise HTTPException(status_code=413, detail="Cover file too large (max 25 MB)")

    try:
        img = Image.open(BytesIO(image_bytes))
        width, height = img.size
        format = img.format
        mode = img.mode
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")

    if format not in ["JPEG", "PNG"]:
        raise HTTPException(status_code=400, detail="Cover must be JPG or PNG")

    if width < 1400 or height < 1400:
        raise HTTPException(status_code=400, detail="Cover resolution too low")

    if mode != "RGB":
        raise HTTPException(status_code=400, detail="Cover must be RGB")

    asset_id = str(uuid.uuid4())
    directory = storage_path("assets")
    directory.mkdir(parents=True, exist_ok=True)
    extension = "jpg" if format == "JPEG" else "png"
    file_path = directory / f"cover_{asset_id}.{extension}"

    with open(file_path, "wb") as buffer:
        buffer.write(image_bytes)

    asset_data = {
        "id": asset_id,
        "type": "artwork",
        "path": str(file_path),
        "width": width,
        "height": height,
        "format": format,
        "owner_user_id": uid,
        "created_at": datetime.utcnow().isoformat(),
    }
    CatalogService.save_asset(asset_data, tenant_id=tenant_id)

    # Sin "file_path": no se expone la ruta interna del servidor.
    return {
        "status": "ok",
        "id": asset_id,
        "width": width,
        "height": height,
        "format": format,
    }
