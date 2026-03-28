import uuid

from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.main import app

client = TestClient(app)


def artist_token(uid=None):
    uid = uid or str(uuid.uuid4())
    return uid, create_access_token(
        {
            "sub": uid,
            "role": "artist",
            "tenant_id": "default",
            "email": f"{uid}@t.io",
        }
    )


def admin_token():
    return create_access_token(
        {
            "sub": "admin-001",
            "role": "admin",
            "tenant_id": "default",
            "email": "admin@apstudios.io",
        }
    )


def headers(tok):
    return {
        "Authorization": f"Bearer {tok}",
        "X-Tenant-Id": "default",
        "Content-Type": "application/json",
    }


def test_artista_sin_contrato_no_puede_crear_release():
    """Artista sin contrato → 403 al crear release."""
    uid, tok = artist_token()
    resp = client.post(
        "/api/releases",
        json={
            "title": "Release sin contrato",
            "release_type": "Single",
            "language": "es",
            "territories": ["Worldwide"],
        },
        headers=headers(tok),
    )
    assert resp.status_code == 403
    assert "terms" in resp.json()["detail"].lower()


def test_artista_acepta_contrato():
    """Artista puede aceptar el contrato."""
    uid, tok = artist_token()
    resp = client.post(
        "/api/contracts/accept",
        json={"accepted": True},
        headers=headers(tok),
    )
    assert resp.status_code == 200
    assert resp.json()["has_accepted"] is True


def test_contrato_rejected_si_accepted_false():
    """accepted=false debe retornar 400."""
    uid, tok = artist_token()
    resp = client.post(
        "/api/contracts/accept",
        json={"accepted": False},
        headers=headers(tok),
    )
    assert resp.status_code == 400


def test_artista_con_contrato_puede_crear_release():
    """Artista con contrato firmado puede crear release."""
    uid, tok = artist_token()

    # Firmar contrato
    client.post(
        "/api/contracts/accept",
        json={"accepted": True},
        headers=headers(tok),
    )

    # Crear release
    resp = client.post(
        "/api/releases",
        json={
            "title": "Release con contrato",
            "release_type": "Single",
            "language": "es",
            "territories": ["Worldwide"],
        },
        headers=headers(tok),
    )
    assert resp.status_code in (200, 201)


def test_get_my_contract_sin_firmar():
    """GET /contracts/me sin contrato → has_accepted=false."""
    uid, tok = artist_token()
    resp = client.get("/api/contracts/me", headers=headers(tok))
    assert resp.status_code == 200
    assert resp.json()["has_accepted"] is False


def test_get_my_contract_firmado():
    """GET /contracts/me después de firmar → has_accepted=true."""
    uid, tok = artist_token()
    client.post(
        "/api/contracts/accept",
        json={"accepted": True},
        headers=headers(tok),
    )
    resp = client.get("/api/contracts/me", headers=headers(tok))
    assert resp.status_code == 200
    assert resp.json()["has_accepted"] is True


def test_admin_lista_contratos():
    """Admin puede ver todos los contratos."""
    tok = admin_token()
    resp = client.get("/api/admin/contracts", headers=headers(tok))
    assert resp.status_code == 200
    assert "contracts" in resp.json()


def test_artista_no_puede_ver_admin_contracts():
    """Artista no puede acceder a /admin/contracts."""
    uid, tok = artist_token()
    resp = client.get("/api/admin/contracts", headers=headers(tok))
    assert resp.status_code == 403


def test_admin_no_necesita_contrato_para_releases():
    """Admin puede crear releases sin contrato."""
    tok = admin_token()
    resp = client.post(
        "/api/releases",
        json={
            "title": "Admin release sin contrato",
            "release_type": "Single",
            "language": "es",
            "territories": ["Worldwide"],
        },
        headers=headers(tok),
    )
    # Admin no es bloqueado por falta de contrato
    assert resp.status_code in (200, 201)
