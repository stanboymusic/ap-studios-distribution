"""
ERN import endpoints (parse -> confirm).
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from pydantic import BaseModel

from app.services.ern_importer import ERNImporter, ERNParseError

router = APIRouter(prefix="/ern/import", tags=["ERN Import"])


def _tenant_id(request: Request) -> str:
    return getattr(request.state, "tenant_id", None) or "default"


def _decode_xml(content: bytes) -> str:
    if not content:
        raise HTTPException(status_code=400, detail="Empty ERN XML payload")
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return content.decode("latin-1")
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail="Could not decode XML (expected UTF-8 or Latin-1)",
            ) from exc


class ConfirmERNImportRequest(BaseModel):
    preview_id: str
    override_title: Optional[str] = None
    override_artist_name: Optional[str] = None
    override_release_date: Optional[str] = None
    override_label: Optional[str] = None
    override_genre: Optional[str] = None
    override_territory: Optional[str] = None
    force_new_upc: bool = False


@router.post("/parse")
async def parse_ern_import(request: Request, file: UploadFile | None = File(None)):
    tenant_id = _tenant_id(request)
    if file is not None:
        content = await file.read()
    else:
        content = await request.body()

    xml_content = _decode_xml(content)
    importer = ERNImporter()
    try:
        preview = importer.parse(xml_content, tenant_id)
    except ERNParseError as exc:
        raise HTTPException(status_code=422, detail={"message": str(exc)}) from exc

    preview.pop("original_xml", None)
    return preview


@router.post("/confirm")
def confirm_ern_import(body: ConfirmERNImportRequest, request: Request):
    tenant_id = _tenant_id(request)
    importer = ERNImporter()
    overrides = {
        "title": body.override_title,
        "artist_name": body.override_artist_name,
        "release_date": body.override_release_date,
        "label": body.override_label,
        "genre": body.override_genre,
        "territory": body.override_territory,
        "force_new_upc": body.force_new_upc,
    }
    try:
        result = importer.confirm(body.preview_id, overrides, tenant_id)
    except ERNParseError as exc:
        raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"message": str(exc)}) from exc

    return result


@router.delete("/cancel/{preview_id}")
def cancel_ern_import(preview_id: str, request: Request):
    tenant_id = _tenant_id(request)
    importer = ERNImporter()
    importer.delete_preview(preview_id, tenant_id)
    return {"status": "cancelled", "preview_id": preview_id}
