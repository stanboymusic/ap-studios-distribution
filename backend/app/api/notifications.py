from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from app.services.email_service import send_template_email

router = APIRouter(prefix="/admin/notifications", tags=["Admin — Notifications"])

class TestEmailRequest(BaseModel):
    to_email: str
    template: str = "welcome"

@router.post("/test")
async def send_test_email(body: TestEmailRequest, request: Request):
    role = getattr(request.state, "user_role", "artist")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    templates = {
        "welcome": ("Bienvenido a AP Studios 🎵", "welcome.html", {"artist_name": "Test Artist", "email": body.to_email}),
    }

    if body.template not in templates:
        raise HTTPException(status_code=400, detail=f"Unknown template. Available: {list(templates.keys())}")

    subject, tmpl_name, ctx = templates[body.template]
    sent = await send_template_email(body.to_email, subject, tmpl_name, ctx)
    return {"sent": sent, "to": body.to_email, "template": body.template}

@router.get("/status")
def smtp_status(request: Request):
    role = getattr(request.state, "user_role", "artist")
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    from app.services.email_service import ENABLED, SMTP_HOST, SMTP_PORT, FROM_EMAIL
    return {
        "enabled": ENABLED,
        "smtp_host": SMTP_HOST,
        "smtp_port": SMTP_PORT,
        "from_email": FROM_EMAIL,
        "status": "configured" if ENABLED else "not configured",
    }
