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


# ── Entregas y regalías ──────────────────────────────────────────
# (Estas funciones se importaban desde delivery.py, admin_royalties.py y royalty_engine.py
#  pero no existían: la API entera fallaba con ImportError al arrancar.)

def notify_release_delivered(
    email: str,
    artist_name: str,
    release_title: str,
    release_type: str = "Single",
    upc: Optional[str] = None,
    release_date=None,
    territories: str = "Worldwide",
):
    release_type = getattr(release_type, "value", release_type)
    _fire(send_template_email(
        to_email=email,
        subject=f"Tu lanzamiento «{release_title}» fue enviado a las plataformas 🚀",
        template_name="release_delivered.html",
        context={
            "artist_name": artist_name or email.split("@")[0],
            "release_title": release_title,
            "release_type": str(release_type),
            "upc": upc or "Pendiente",
            "release_date": str(release_date) if release_date else "Por confirmar",
            "territories": territories or "Worldwide",
        },
    ))


def notify_payout_created(
    email: str,
    artist_name: str,
    amount: float,
    currency: str,
    method: str,
    note: Optional[str] = None,
):
    _fire(send_template_email(
        to_email=email,
        subject="Solicitud de pago registrada",
        template_name="payout_created.html",
        context={
            "artist_name": artist_name or email.split("@")[0],
            "amount": f"{float(amount):,.2f}",
            "currency": currency,
            "method": method or "",
            "note": note or "",
        },
    ))


def notify_payout_processed(
    email: str,
    artist_name: str,
    amount: float,
    currency: str,
    method: str,
    reference: Optional[str] = None,
    paid_at: Optional[str] = None,
):
    _fire(send_template_email(
        to_email=email,
        subject="Tu pago fue procesado ✓",
        template_name="payout_processed.html",
        context={
            "artist_name": artist_name or email.split("@")[0],
            "amount": f"{float(amount):,.2f}",
            "currency": currency,
            "method": method or "",
            "reference": reference or "—",
            "paid_at": _fmt_date(paid_at),
        },
    ))


def notify_royalties_available(
    email: str,
    artist_name: str,
    period: str,
    streams: int,
    gross_amount: float,
    net_amount: float,
    commission_amount: float,
    available_balance: float,
    top_dsp: str = "Spotify",
):
    _fire(send_template_email(
        to_email=email,
        subject=f"Nuevas regalías disponibles ({period})",
        template_name="royalties_available.html",
        context={
            "artist_name": artist_name or email.split("@")[0],
            "period": period,
            "streams": f"{int(streams):,}",
            "gross_amount": f"{float(gross_amount):,.2f}",
            "net_amount": f"{float(net_amount):,.2f}",
            "commission_amount": f"{float(commission_amount):,.2f}",
            "available_balance": f"{float(available_balance):,.2f}",
            "top_dsp": top_dsp or "Spotify",
        },
    ))
