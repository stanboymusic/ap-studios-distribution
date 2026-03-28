import pytest
from unittest.mock import patch

from app.core.security import hash_password, verify_password, create_access_token, decode_token
from app.models.user import User
from app.repositories import user_repository as user_repo


TENANT = "test-auth-tenant"
EMAIL = "test@apstudios.io"
PASSWORD = "secure123"


def _make_user(tmp_path):
    user = User(
        email=EMAIL,
        hashed_password=hash_password(PASSWORD),
        role="artist",
        tenant_id=TENANT,
    )
    with patch("app.repositories.user_repository._users_file") as mock_f:
        mock_f.return_value = tmp_path / "users.json"
        tmp_path.mkdir(parents=True, exist_ok=True)
        user_repo.create(user)
    return user


def test_hash_and_verify():
    h = hash_password(PASSWORD)
    assert verify_password(PASSWORD, h)
    assert not verify_password("wrong", h)


def test_create_access_token_and_decode():
    payload = {"sub": "user-123", "role": "artist", "tenant_id": "default"}
    token = create_access_token(payload)
    decoded = decode_token(token)
    assert decoded["sub"] == "user-123"
    assert decoded["type"] == "access"


def test_decode_invalid_token_returns_none():
    assert decode_token("not.a.token") is None


def test_user_to_public_has_no_password():
    user = User(email="a@b.com", hashed_password="secret", role="artist", tenant_id="t1")
    public = user.to_public()
    assert "hashed_password" not in public
    assert public["email"] == "a@b.com"


def test_user_from_dict_round_trip():
    user = User(email="r@t.com", hashed_password="h", role="admin", tenant_id="t1")
    restored = User.from_dict(user.to_dict())
    assert restored.email == user.email
    assert restored.role == user.role


def test_register_endpoint():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    import uuid

    unique_email = f"{uuid.uuid4().hex[:8]}@test.io"
    resp = client.post(
        "/api/auth/register",
        headers={"X-Tenant-Id": "default"},
        json={
            "email": unique_email,
            "password": "test1234",
            "role": "artist",
            "tenant_id": "default",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_returns_tokens():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    import uuid

    email = f"{uuid.uuid4().hex[:8]}@test.io"
    client.post(
        "/api/auth/register",
        headers={"X-Tenant-Id": "default"},
        json={"email": email, "password": "pass123", "role": "artist", "tenant_id": "default"},
    )
    resp = client.post(
        "/api/auth/login",
        headers={"X-Tenant-Id": "default"},
        json={"email": email, "password": "pass123", "tenant_id": "default"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password_returns_401():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    resp = client.post(
        "/api/auth/login",
        headers={"X-Tenant-Id": "default"},
        json={"email": "noexiste@x.com", "password": "bad", "tenant_id": "default"},
    )
    assert resp.status_code == 401


def test_me_sin_token_returns_401():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    resp = client.get("/api/auth/me", headers={"X-Tenant-Id": "default"})
    assert resp.status_code == 401


def test_me_con_token_valido():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    import uuid

    email = f"{uuid.uuid4().hex[:8]}@test.io"
    reg = client.post(
        "/api/auth/register",
        headers={"X-Tenant-Id": "default"},
        json={"email": email, "password": "pass123", "role": "artist", "tenant_id": "default"},
    )
    token = reg.json()["access_token"]
    resp = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}", "X-Tenant-Id": "default"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == email
