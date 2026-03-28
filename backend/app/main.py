from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from app.api import artists, releases, tracks, validation, assets, delivery, rights, dsr, catalog, sandbox, dsp, tenants, mwn, fingerprint, mead, ern_import, auth, notifications
from app.api import mwn_notifications
from app.api import analytics
from app.api import automation
from app.api.admin_users import router as admin_users_router
from app.api.contracts import router as contracts_router
from app.api.contracts import admin_router as admin_contracts_router
from app.api.royalties import router as royalties_router
from app.api.admin_royalties import router as admin_royalties_router
import logging
from app.core.paths import storage_path
from app.middleware.tenant import TenantContextMiddleware
from app.middleware.auth import AuthContextMiddleware
from app.services.tenant_service import TenantService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AP Studios Distribution API v2")
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
    """
    Make `X-Tenant-Id` discoverable in Swagger UI via an Authorize button.
    The runtime enforcement still happens in TenantContextMiddleware.
    """
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version="2.0.0",
        description="Multi-tenant API. Most /api endpoints require X-Tenant-Id.",
        routes=app.routes,
    )

    schema.setdefault("components", {}).setdefault("securitySchemes", {})
    schema["components"]["securitySchemes"]["TenantIdHeader"] = {
        "type": "apiKey",
        "in": "header",
        "name": "X-Tenant-Id",
        "description": "Tenant context (e.g. default, labelx).",
    }

    # Apply globally so Swagger sends it automatically after Authorize.
    schema["security"] = [{"TenantIdHeader": []}]

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:5174", 
        "http://localhost:5200", 
        "http://localhost:5201",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5200",
        "http://127.0.0.1:5201"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {str(exc)}", exc_info=True)
    response = JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"},
    )
    # Ensure CORS headers are added to the error response
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    return response

app.mount("/assets", StaticFiles(directory=str(storage_path("assets"))), name="assets")

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
print("including delivery router")
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
