from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.api import artists, releases, tracks, validation, assets, delivery, rights, dsr, catalog, sandbox, dsp, tenants, mwn, fingerprint, mead, ern_import, auth
from app.api import mwn_notifications
from app.api import analytics
from app.api import automation
from app.api.admin_users import router as admin_users_router
from app.api.contracts import router as contracts_router
from app.api.contracts import admin_router as admin_contracts_router
from app.api.royalties import router as royalties_router
from app.api.admin_royalties import router as admin_royalties_router
from app.api import notifications
import logging
import os
import uuid
from app.core.paths import storage_path
from app.middleware.tenant import TenantContextMiddleware
from app.middleware.auth import AuthContextMiddleware
from app.services.tenant_service import TenantService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IS_PROD = (os.getenv("APP_ENV") or "").strip().lower() in {"prod", "production"}

# En producción no se exponen /docs ni /openapi.json (mapa completo de la API).
app = FastAPI(
    title="AP Studios Distribution API v2",
    docs_url=None if IS_PROD else "/docs",
    redoc_url=None if IS_PROD else "/redoc",
    openapi_url=None if IS_PROD else "/openapi.json",
)
TenantService.ensure_default_tenant()
try:
    from scripts.create_admin import create_admin_if_missing

    create_admin_if_missing()
except Exception as e:
    import logging

    logging.getLogger(__name__).warning(f"Admin seed failed: {e}")
try:
    from app.database.migrations import run_migrations

    run_migrations()
except Exception as e:
    import logging

    logging.getLogger(__name__).warning(f"DB migration skipped: {e}")
app.add_middleware(TenantContextMiddleware)
app.add_middleware(AuthContextMiddleware)


def custom_openapi():
    """Swagger: botón Authorize con Bearer JWT (el tenant sale del token)."""
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version="2.0.0",
        description="Multi-tenant API. Authenticate with a Bearer JWT from /api/auth/login.",
        routes=app.routes,
    )
    schema.setdefault("components", {}).setdefault("securitySchemes", {})
    schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi

_DEFAULT_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5200",
    "http://localhost:5201",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5200",
    "http://127.0.0.1:5201",
]
# Producción: AP_CORS_ORIGINS="https://app.apstudios.com,https://www.apstudios.com"
ALLOWED_ORIGINS = [
    o.strip() for o in (os.getenv("AP_CORS_ORIGINS") or "").split(",") if o.strip()
] or ([] if IS_PROD else _DEFAULT_ORIGINS)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Cache-Control", "no-store")
    if IS_PROD:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Tenant-Id"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # El detalle técnico va al log con un id; al cliente solo el id (nunca str(exc): filtra rutas/SQL/datos).
    error_id = uuid.uuid4().hex[:12]
    logger.error("Unhandled error [%s] %s %s: %s", error_id, request.method, request.url.path, exc, exc_info=True)
    response = JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error_id": error_id},
    )
    # CORS solo para orígenes de la lista blanca (antes se reflejaba cualquier Origin con credenciales).
    origin = request.headers.get("origin")
    if origin and origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Vary"] = "Origin"
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Solo método y ruta: la query string puede traer datos personales.
    logger.info("Request: %s %s", request.method, request.url.path)
    return await call_next(request)


# NOTA: se eliminó app.mount("/assets", StaticFiles(...)). Servía TODO el storage/assets sin
# autenticación. Las portadas/audios se sirven por /api/assets/* con control de propietario.


app.include_router(artists.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(admin_users_router, prefix="/api")
app.include_router(contracts_router, prefix="/api")
app.include_router(admin_contracts_router, prefix="/api")
app.include_router(royalties_router, prefix="/api")
app.include_router(admin_royalties_router, prefix="/api")
app.include_router(releases.router, prefix="/api")
app.include_router(tracks.router, prefix="/api")
app.include_router(assets.router, prefix="/api")
app.include_router(validation.router, prefix="/api")
app.include_router(catalog.router, prefix="/api")
app.include_router(sandbox.router, prefix="/api")
app.include_router(dsp.router, prefix="/api")
app.include_router(tenants.router, prefix="/api")
app.include_router(delivery.router, prefix="/api")
app.include_router(mwn.router, prefix="/api")
app.include_router(mead.router, prefix="/api")
app.include_router(mwn_notifications.router, prefix="/api")
app.include_router(ern_import.router, prefix="/api")
app.include_router(rights.router, prefix="/api")
app.include_router(dsr.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(automation.router, prefix="/api")
app.include_router(fingerprint.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")

@app.get("/")
def root():
    return {"status": "AP Studios Distribution API running"}
