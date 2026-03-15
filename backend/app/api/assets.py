from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse
from PIL import Image
from io import BytesIO
import os
from uuid import UUID
from datetime import datetime
from app.core.paths import storage_path

router = APIRouter(prefix="/assets", tags=["Assets"])

@router.get("/artwork/{artwork_id}")
def get_artwork(artwork_id: str):
    # Simplified: search for file starting with artwork_id in storage/assets
    # In a real app, we'd have a database or catalog entry mapping ID to path
    directory = storage_path("assets")
    if not directory.exists():
        raise HTTPException(status_code=404, detail="Assets directory not found")
    
    for filename in os.listdir(directory):
        if filename.startswith(f"cover_{artwork_id}") or filename.startswith(artwork_id):
            return FileResponse(str(directory / filename))
    
    raise HTTPException(status_code=404, detail="Artwork not found")

@router.get("/audio/{track_id}")
def get_audio(track_id: str):
    directory = storage_path("audio")
    if not directory.exists():
        raise HTTPException(status_code=404, detail="Audio directory not found")
    
    for filename in os.listdir(directory):
        if filename.startswith(track_id):
            return FileResponse(str(directory / filename))
    
    raise HTTPException(status_code=404, detail="Audio not found")

from app.services.catalog_service import CatalogService
import uuid

@router.post("/cover")
async def upload_cover(request: Request, cover: UploadFile = File(...)):
    print("DEBUG: upload_cover called")
    image_bytes = await cover.read()

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

    # Save the file with a UUID
    asset_id = str(uuid.uuid4())
    directory = storage_path("assets")
    directory.mkdir(parents=True, exist_ok=True)
    extension = "jpg" if format == "JPEG" else "png"
    file_path = directory / f"cover_{asset_id}.{extension}"
    
    with open(file_path, "wb") as buffer:
        buffer.write(image_bytes)

    # Save metadata to catalog
    asset_data = {
        "id": asset_id,
        "type": "artwork",
        "path": str(file_path),
        "width": width,
        "height": height,
        "format": format,
        "created_at": datetime.utcnow().isoformat()
    }
    tenant_id = request.state.tenant_id
    CatalogService.save_asset(asset_data, tenant_id=tenant_id)

    return {
        "status": "ok",
        "id": asset_id,
        "width": width,
        "height": height,
        "format": format,
        "file_path": str(file_path)
    }
