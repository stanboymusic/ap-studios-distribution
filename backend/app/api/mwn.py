from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.delivery import receive_mwn as receive_delivery_mwn

router = APIRouter(prefix="/mwn", tags=["MWN"])


@router.post("/receive")
async def receive_mwn(request: Request):
    # Reuse the existing delivery MWN pipeline to keep one source of truth.
    return await receive_delivery_mwn(request)
