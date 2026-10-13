import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    """Cada test usa su propio storage temporal: no toca datos reales ni se contaminan entre sí."""
    import app.core.paths as paths

    monkeypatch.setattr(paths, "STORAGE_DIR", tmp_path / "storage")

    from app.core import ratelimit
    from app.middleware.auth import invalidate_user_cache
    from app.services.tenant_service import TenantService

    ratelimit._events.clear()
    invalidate_user_cache()
    TenantService.ensure_default_tenant()
    yield
    ratelimit._events.clear()
    invalidate_user_cache()
