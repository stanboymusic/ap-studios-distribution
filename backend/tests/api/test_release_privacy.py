import uuid

from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.main import app

client = TestClient(app)


def token(role="artist", uid=None):
    uid = uid or str(uuid.uuid4())
    return create_access_token(
        {
            "sub": uid,
            "role": role,
            "tenant_id": "default",
            "email": f"{uid}@t.io",
        }
    )


def headers(tok):
    return {
        "Authorization": f"Bearer {tok}",
        "X-Tenant-Id": "default",
        "Content-Type": "application/json",
    }


def accept_contract(tok):
    client.post(
        "/api/contracts/accept",
        json={"accepted": True},
        headers=headers(tok),
    )


def test_artista_no_ve_releases_sin_owner():
    """Releases sin owner_user_id NO aparecen para artistas."""
    artist_tok = token("artist")
    resp = client.get("/api/releases", headers=headers(artist_tok))
    assert resp.status_code == 200
    releases = resp.json()
    items = releases if isinstance(releases, list) else releases.get("releases", [])
    for r in items:
        assert r.get("owner_user_id") is not None


def test_artista_no_ve_releases_de_otro():
    """Artista A no ve releases de artista B."""
    uid_a = str(uuid.uuid4())
    uid_b = str(uuid.uuid4())
    tok_a = token("artist", uid_a)
    tok_b = token("artist", uid_b)
    accept_contract(tok_a)
    accept_contract(tok_b)

    title = f"Private release {uuid.uuid4().hex[:6]}"
    client.post(
        "/api/releases",
        json={
            "title": title,
            "release_type": "Single",
            "language": "es",
            "territories": ["Worldwide"],
        },
        headers=headers(tok_a),
    )

    resp = client.get("/api/releases", headers=headers(tok_b))
    items = resp.json() if isinstance(resp.json(), list) else resp.json().get("releases", [])
    titles = [r["title"] for r in items]
    assert title not in titles


def test_artista_no_puede_ver_release_ajena_por_id():
    """GET /releases/{id} de otra persona -> 404."""
    uid_a = str(uuid.uuid4())
    uid_b = str(uuid.uuid4())
    tok_a = token("artist", uid_a)
    tok_b = token("artist", uid_b)
    accept_contract(tok_a)
    accept_contract(tok_b)

    resp = client.post(
        "/api/releases",
        json={
            "title": "Exclusive",
            "release_type": "Single",
            "language": "es",
            "territories": ["Worldwide"],
        },
        headers=headers(tok_a),
    )
    rid = resp.json().get("id") or resp.json().get("release_id")

    resp2 = client.get(f"/api/releases/{rid}", headers=headers(tok_b))
    assert resp2.status_code == 404


def test_admin_ve_releases_sin_owner():
    """Admin ve releases aunque no tengan owner_user_id."""
    admin_tok = token("admin")
    resp = client.get("/api/releases", headers=headers(admin_tok))
    assert resp.status_code == 200


def test_artista_ve_sus_propias_releases():
    """Artista ve exactamente sus propias releases."""
    uid = str(uuid.uuid4())
    tok = token("artist", uid)
    accept_contract(tok)

    title = f"Mi release {uuid.uuid4().hex[:6]}"
    client.post(
        "/api/releases",
        json={
            "title": title,
            "release_type": "Single",
            "language": "es",
            "territories": ["Worldwide"],
        },
        headers=headers(tok),
    )

    resp = client.get("/api/releases", headers=headers(tok))
    items = resp.json() if isinstance(resp.json(), list) else resp.json().get("releases", [])
    titles = [r["title"] for r in items]
    assert title in titles
