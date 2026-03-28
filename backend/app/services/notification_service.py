from __future__ import annotations
import asyncio
import logging
import os
from datetime import datetime
from typing import Optional

from app.services.email_service import send_template_email

logger = logging.getLogger(__name__)
ADMIN_EMAIL = os.getenv("AP_ADMIN_EMAIL", "admin@apstudios.io")

def _fmt_date(iso_str: Optional[str]) -> str:
    if not iso_str:
        return "—"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y, %H:%M UTC")
    except Exception:
        return iso_str

def _fire(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(coro)
        else:
            asyncio.run(coro)
    except Exception as exc:
        logger.warning("[notifications] Failed to schedule: %s", exc)

def notify_welcome(email: str, artist_name: str):
    _fire(send_template_email(
        to_email=email,
        subject="Bienvenido a AP Studios 🎵",
        template_name="welcome.html",
        context={"artist_name": artist_name or email.split("@")[0], "email": email},
    ))

def notify_admin_new_artist(artist_email: str, registered_at: str, tenant_id: str, contract_signed: bool = False):
    _fire(send_template_email(
        to_email=ADMIN_EMAIL,
        subject=f"👤 Nuevo artista: {artist_email}",
        template_name="new_artist_admin.html",
        context={
            "artist_email": artist_email,
            "registered_at": _fmt_date(registered_at),
            "tenant_id": tenant_id,
            "contract_signed": contract_signed,
        },
    ))

def notify_contract_accepted(email: str, artist_name: str, version: str, accepted_at: str, ip_address: Optional[str]):
    _fire(send_template_email(
        to_email=email,
        subject="Contrato AP Studios firmado ✓",
        template_name="contract_accepted.html",
        context={
            "artist_name": artist_name or email.split("@")[0],
            "version": version,
            "accepted_at": _fmt_date(accepted_at),
            "ip_address": ip_address,
        },
    ))
