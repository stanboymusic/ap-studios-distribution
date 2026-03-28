import uuid

from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.main import app

client = TestClient(app)


def admin_token() -> str:
    return create_access_token(
        {
            "sub": "admin-test-001",
            "role": "admin",
            "tenant_id": "default",
            "email": "admin@apstudios.io",
        }
    )


def artist_token(user_id: str = None) -> str:
    uid = user_id or str(uuid.uuid4())
    return create_access_token(
        {
            "sub": uid,
            "role": "artist",
            "tenant_id": "default",
            "email": f"{uid}@artist.io",
        }
    )


def admin_headers() -> dict:
    return {
        "Authorization": f"Bearer {admin_token()}",
        "X-Tenant-Id": "default",
        "Content-Type": "application/json",
    }


def accept_contract(token: str) -> None:
    client.post(
        "/api/contracts/accept",
        json={"accepted": True},
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant-Id": "default",
            "Content-Type": "application/json",
        },
    )


def test_list_users_requiere_admin():
    """GET /admin/users requiere rol admin."""
    resp = client.get(
        "/api/admin/users",
        headers={
            "Authorization": f"Bearer {artist_token()}",
            "X-Tenant-Id": "default",
        },
    )
    assert resp.status_code == 403


def test_list_users_como_admin():
    """Admin puede listar usuarios."""
    resp = client.get("/api/admin/users", headers=admin_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert "users" in data
    assert "total" in data


def test_get_user_no_existe():
    """GET /admin/users/{id} con ID inexistente -> 404."""
    resp = client.get(
        f"/api/admin/users/{uuid.uuid4()}",
        headers=admin_headers(),
    )
    assert resp.status_code == 404


def test_patch_user_desactivar():
    """Admin puede desactivar una cuenta de artista."""
    email = f"{uuid.uuid4().hex[:8]}@test.io"
    reg = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "pass1234",
            "role": "artist",
            "tenant_id": "default",
        },
    )
    assert reg.status_code == 200
    user_id = reg.json()["user"]["id"]

    resp = client.patch(
        f"/api/admin/users/{user_id}",
        json={"is_active": False},
        headers=admin_headers(),
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


def test_patch_user_reactivar():
    """Admin puede reactivar una cuenta desactivada."""
    email = f"{uuid.uuid4().hex[:8]}@test.io"
    reg = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "pass1234",
            "role": "artist",
            "tenant_id": "default",
        },
    )
    user_id = reg.json()["user"]["id"]

    client.patch(
        f"/api/admin/users/{user_id}",
        json={"is_active": False},
        headers=admin_headers(),
    )

    resp = client.patch(
        f"/api/admin/users/{user_id}",
        json={"is_active": True},
        headers=admin_headers(),
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is True


def test_patch_user_no_puede_asignar_admin():
    """No se puede asignar rol admin via API."""
    email = f"{uuid.uuid4().hex[:8]}@test.io"
    reg = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "pass1234",
            "role": "artist",
            "tenant_id": "default",
        },
    )
    user_id = reg.json()["user"]["id"]

    resp = client.patch(
        f"/api/admin/users/{user_id}",
        json={"role": "admin"},
        headers=admin_headers(),
    )
    assert resp.status_code == 403


def test_get_user_releases():
    """Admin puede ver releases de un usuario."""
    email = f"{uuid.uuid4().hex[:8]}@test.io"
    reg = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "pass1234",
            "role": "artist",
            "tenant_id": "default",
        },
    )
    user_id = reg.json()["user"]["id"]
    token = reg.json()["access_token"]
    accept_contract(token)

    client.post(
        "/api/releases",
        json={
            "title": "Test Release Admin View",
            "release_type": "Single",
            "language": "es",
            "territories": ["Worldwide"],
        },
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant-Id": "default",
            "Content-Type": "application/json",
        },
    )

    resp = client.get(
        f"/api/admin/users/{user_id}/releases",
        headers=admin_headers(),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "releases" in data
    assert data["total"] >= 1


def test_login_desactivado_retorna_403():
    """Usuario desactivado no puede hacer login."""
    email = f"{uuid.uuid4().hex[:8]}@test.io"
    reg = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "pass1234",
            "role": "artist",
            "tenant_id": "default",
        },
    )
    user_id = reg.json()["user"]["id"]

    client.patch(
        f"/api/admin/users/{user_id}",
        json={"is_active": False},
        headers=admin_headers(),
    )

    resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": "pass1234", "tenant_id": "default"},
    )
    assert resp.status_code == 403
