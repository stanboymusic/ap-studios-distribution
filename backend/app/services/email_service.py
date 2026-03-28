"""
Async email service for AP Studios.
Uses aiosmtplib for non-blocking SMTP delivery.
Falls back gracefully if SMTP is not configured.
"""
from __future__ import annotations

import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

import aiosmtplib
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_NAME = os.getenv("SMTP_FROM_NAME", "AP Studios")
FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5200")
ENABLED = bool(SMTP_USER and SMTP_PASSWORD)

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates" / "email"
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

_jinja_env: Optional[Environment] = None


def _get_jinja() -> Environment:
    global _jinja_env
    if _jinja_env is None:
        _jinja_env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(["html"]),
        )
    return _jinja_env


def render_template(template_name: str, context: dict) -> str:
    """Render a Jinja2 HTML email template."""
    base_context = {
        "frontend_url": FRONTEND_URL,
        "brand_name": "AP Studios",
        "brand_tagline": "Music Distribution Platform",
        "brand_color": "#6B1A2E",
        "brand_color_light": "#A8385A",
        "support_email": FROM_EMAIL,
    }
    ctx = {**base_context, **context}
    template = _get_jinja().get_template(template_name)
    return template.render(**ctx)


async def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
) -> bool:
    """
    Send an HTML email via SMTP async.
    Returns True if sent, False if failed or not configured.
    """
    if not ENABLED:
        logger.info("[email] SMTP not configured — would send to %s: %s", to_email, subject)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg["To"] = to_email

    if text_body:
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            start_tls=True,
        )
        logger.info("[email] Sent '%s' to %s", subject, to_email)
        return True
    except Exception as exc:
        logger.error("[email] Failed to send '%s' to %s: %s", subject, to_email, exc)
        return False


async def send_template_email(
    to_email: str,
    subject: str,
    template_name: str,
    context: dict,
) -> bool:
    """Render template and send."""
    try:
        html = render_template(template_name, context)
    except Exception as exc:
        logger.error("[email] Template render failed (%s): %s", template_name, exc)
        return False
    return await send_email(to_email, subject, html)
