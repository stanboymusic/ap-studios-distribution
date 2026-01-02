from fastapi import APIRouter, UploadFile, File, HTTPException
from PIL import Image
from io import BytesIO

router = APIRouter(prefix="/assets", tags=["Assets"])


@router.post("/cover")
async def upload_cover(cover: UploadFile = File(...)):
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

    # Save the file
    import os
    os.makedirs("storage/assets", exist_ok=True)
    file_path = f"storage/assets/cover_{cover.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(image_bytes)

    return {
        "status": "ok",
        "width": width,
        "height": height,
        "format": format,
        "file_path": file_path
    }