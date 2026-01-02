from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import artists, releases, tracks, validation, assets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AP Studios Distribution API")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url} Origin: {request.headers.get('origin')}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code} Headers: {dict(response.headers)}")
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5200", "http://localhost:5201"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/assets", StaticFiles(directory="storage/assets"), name="assets")

app.include_router(artists.router, prefix="/api")
app.include_router(releases.router, prefix="/api")
app.include_router(tracks.router, prefix="/api")
app.include_router(assets.router, prefix="/api")
app.include_router(validation.router, prefix="/api")

@app.get("/")
def root():
    return {"status": "AP Studios Distribution API running"}