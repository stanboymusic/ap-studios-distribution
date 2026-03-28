import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def unique_email():
    return f"{uuid.uuid4().hex[:8]}@artist.io"


def test_register_artista_publico():
    """Un artista se puede registrar desde la API pública."""
    resp = client.post(
        "/api/auth/register",
        json={
            "email": unique_email(),
            "password": "secure123",
            "role": "artist",
            "tenant_id": "default",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["role"] == "artist"


def test_register_admin_bloqueado():
    """No se puede crear un admin desde la API pública."""
    resp = client.post(
        "/api/auth/register",
        json={
            "email": unique_email(),
            "password": "secure123",
            "role": "admin",
            "tenant_id": "default",
        },
    )
    assert resp.status_code == 403
    assert "admin" in resp.json()["detail"].lower()


def test_register_email_duplicado():
    """No se puede registrar el mismo email dos veces."""
    email = unique_email()
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "pass1234",
            "role": "artist",
            "tenant_id": "default",
        },
    )
    resp = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "otropass",
            "role": "artist",
            "tenant_id": "default",
        },
    )
    assert resp.status_code == 409


def test_register_auto_login():
    """El registro devuelve tokens válidos para auto-login."""
    resp = client.post(
        "/api/auth/register",
        json={
            "email": unique_email(),
            "password": "pass1234",
            "role": "artist",
            "tenant_id": "default",
        },
    )
    token = resp.json()["access_token"]
    me = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}", "X-Tenant-Id": "default"},
    )
    assert me.status_code == 200
    assert me.json()["role"] == "artist"


def test_register_staff_permitido():
    """El rol staff sí se puede registrar públicamente."""
    resp = client.post(
        "/api/auth/register",
        json={
            "email": unique_email(),
            "password": "pass1234",
            "role": "staff",
            "tenant_id": "default",
        },
    )
    assert resp.status_code == 200
