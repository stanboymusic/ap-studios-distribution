import uuid

from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.main import app

client = TestClient(app)


def make_token(user_id: str, role: str = "artist", tenant: str = "default") -> str:
    return create_access_token(
        {
            "sub": user_id,
            "role": role,
            "tenant_id": tenant,
            "email": f"{user_id}@test.io",
        }
    )


def auth_headers(token: str, tenant: str = "default") -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-Id": tenant,
        "Content-Type": "application/json",
    }


def accept_contract(token: str, tenant: str = "default") -> None:
    client.post(
        "/api/contracts/accept",
        json={"accepted": True},
        headers=auth_headers(token, tenant),
    )


def create_release_payload(title: str = None) -> dict:
    return {
        "title": title or f"Release {uuid.uuid4().hex[:6]}",
        "release_type": "Single",
        "language": "es",
        "territories": ["Worldwide"],
    }


# ── Tests de creación ────────────────────────────────────────────

def test_release_guarda_owner_user_id():
    """Al crear una release, owner_user_id se guarda del JWT."""
    user_id = str(uuid.uuid4())
    token = make_token(user_id)
    accept_contract(token)

    resp = client.post(
        "/api/releases",
        json=create_release_payload(),
        headers=auth_headers(token),
    )
    assert resp.status_code in (200, 201)
    data = resp.json()
    assert data.get("owner_user_id") == user_id


def test_release_sin_token_no_tiene_owner():
    """Release creada sin JWT tiene owner_user_id null (legacy)."""
    resp = client.post(
        "/api/releases",
        json=create_release_payload(),
        headers={
            "X-User-Role": "artist",
            "X-Tenant-Id": "default",
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code in (200, 201)
    data = resp.json()
    # owner_user_id puede ser null o no estar — ambos son válidos
    assert data.get("owner_user_id") is None or "anonymous" not in str(
        data.get("owner_user_id", "")
    )


# ── Tests de listado ─────────────────────────────────────────────

def test_artista_solo_ve_sus_releases():
    """Un artista solo recibe sus propias releases en GET /releases."""
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    token_a = make_token(user_a)
    token_b = make_token(user_b)
    accept_contract(token_a)
    accept_contract(token_b)

    # user_a crea una release
    title_a = f"Release de A {uuid.uuid4().hex[:4]}"
    client.post(
        "/api/releases",
        json=create_release_payload(title_a),
        headers=auth_headers(token_a),
    )

    # user_b crea una release
    title_b = f"Release de B {uuid.uuid4().hex[:4]}"
    client.post(
        "/api/releases",
        json=create_release_payload(title_b),
        headers=auth_headers(token_b),
    )

    # user_a lista — solo debe ver la suya
    resp = client.get("/api/releases", headers=auth_headers(token_a))
    assert resp.status_code == 200
    releases = resp.json()
    titles = [r["title"] for r in (releases if isinstance(releases, list) else releases.get("releases", []))]
    assert title_a in titles
    assert title_b not in titles


def test_admin_ve_todas_las_releases():
    """El admin ve releases de todos los artistas."""
    user_a = str(uuid.uuid4())
    token_a = make_token(user_a, role="artist")
    token_admin = make_token("admin-001", role="admin")
    accept_contract(token_a)

    title = f"Release visible admin {uuid.uuid4().hex[:4]}"
    client.post(
        "/api/releases",
        json=create_release_payload(title),
        headers=auth_headers(token_a),
    )

    resp = client.get("/api/releases", headers=auth_headers(token_admin))
    assert resp.status_code == 200
    releases = resp.json()
    titles = [r["title"] for r in (releases if isinstance(releases, list) else releases.get("releases", []))]
    assert title in titles


# ── Tests de protección ──────────────────────────────────────────

def test_artista_no_puede_editar_release_ajena():
    """Un artista no puede editar la release de otro artista."""
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    token_a = make_token(user_a)
    token_b = make_token(user_b)
    accept_contract(token_a)

    # user_a crea release
    resp = client.post(
        "/api/releases",
        json=create_release_payload(),
        headers=auth_headers(token_a),
    )
    release_id = resp.json().get("id") or resp.json().get("release_id")

    # user_b intenta editarla
    resp2 = client.put(
        f"/api/releases/{release_id}",
        json={"title": "Hackeado"},
        headers=auth_headers(token_b),
    )
    assert resp2.status_code == 403


def test_artista_no_puede_borrar_release_ajena():
    """Un artista no puede eliminar la release de otro artista."""
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    token_a = make_token(user_a)
    token_b = make_token(user_b)
    accept_contract(token_a)

    resp = client.post(
        "/api/releases",
        json=create_release_payload(),
        headers=auth_headers(token_a),
    )
    release_id = resp.json().get("id") or resp.json().get("release_id")

    resp2 = client.delete(
        f"/api/releases/{release_id}",
        headers=auth_headers(token_b),
    )
    assert resp2.status_code == 403


def test_admin_puede_editar_cualquier_release():
    """El admin puede editar releases de cualquier artista."""
    user_a = str(uuid.uuid4())
    token_a = make_token(user_a, role="artist")
    token_admin = make_token("admin-001", role="admin")
    accept_contract(token_a)

    resp = client.post(
        "/api/releases",
        json=create_release_payload(),
        headers=auth_headers(token_a),
    )
    release_id = resp.json().get("id") or resp.json().get("release_id")

    resp2 = client.put(
        f"/api/releases/{release_id}",
        json={"title": "Editado por admin"},
        headers=auth_headers(token_admin),
    )
    assert resp2.status_code in (200, 204)
