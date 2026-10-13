"""
Pruebas de seguridad: autenticación, aislamiento entre cuentas/tenants y persistencia.
Cada test documenta un hueco real que existía antes del endurecimiento.
"""
from __future__ import annotations

import io
import json
import threading
import uuid

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.filelock import StorageCorruptionError, atomic_write_json, read_json, update_json
from app.core.security import create_access_token
from app.main import app
from tests.helpers import auth, make_user

client = TestClient(app)


def _accept_contract(token):
    r = client.post("/api/contracts/accept", json={"accepted": True}, headers=auth(token))
    assert r.status_code in (200, 201), r.text


def _artist():
    uid, tok = make_user("artist")
    _accept_contract(tok)
    return uid, tok


def _release(tok, title="Mi release"):
    r = client.post(
        "/api/releases",
        json={"title": title, "release_type": "Single", "language": "es", "territories": ["Worldwide"]},
        headers=auth(tok),
    )
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _cover_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (1500, 1500), (120, 10, 40)).save(buf, "JPEG")
    return buf.getvalue()


# ───────────────────────── Autenticación ─────────────────────────

@pytest.mark.parametrize("method,path", [
    ("get", "/api/releases"),
    ("get", "/api/artists"),
    ("get", "/api/tenants"),
    ("post", "/api/tenants"),
    ("post", "/api/dsr/ingest"),
    ("get", "/api/rights/configurations"),
    ("get", "/api/assets/artwork/" + str(uuid.uuid4())),
])
def test_sin_token_es_401(method, path):
    assert getattr(client, method)(path).status_code == 401


def test_headers_de_rol_falsificados_no_funcionan():
    r = client.get("/api/tenants", headers={"X-User-Role": "admin", "X-User-Id": "x"})
    assert r.status_code == 401


def test_header_de_rol_no_eleva_un_token_de_artista():
    _, tok = make_user("artist")
    r = client.get("/api/tenants", headers={**auth(tok), "X-User-Role": "admin"})
    assert r.status_code == 403


def test_token_invalido_o_refresh_como_access():
    assert client.get("/api/releases", headers={"Authorization": "Bearer basura"}).status_code == 401
    from app.core.security import create_refresh_token
    uid, _ = make_user("artist")
    refresh = create_refresh_token({"sub": uid, "role": "artist", "tenant_id": "default"})
    assert client.get("/api/releases", headers={"Authorization": f"Bearer {refresh}"}).status_code == 401


def test_usuario_desactivado_pierde_acceso_aunque_su_token_siga_vigente():
    from app.repositories import user_repository as user_repo
    from app.middleware.auth import invalidate_user_cache
    uid, tok = make_user("artist")
    assert client.get("/api/releases", headers=auth(tok)).status_code == 200
    user_repo.update(uid, {"is_active": False}, "default")
    invalidate_user_cache(uid)
    assert client.get("/api/releases", headers=auth(tok)).status_code == 401


def test_rol_degradado_surte_efecto_con_token_viejo():
    """Un admin degradado no conserva privilegios por tener un token antiguo con role=admin."""
    from app.repositories import user_repository as user_repo
    from app.middleware.auth import invalidate_user_cache
    uid, tok = make_user("admin")
    assert client.get("/api/tenants", headers=auth(tok)).status_code == 200
    user_repo.update(uid, {"role": "artist"}, "default")
    invalidate_user_cache(uid)
    assert client.get("/api/tenants", headers=auth(tok)).status_code == 403


# ───────────────────────── Registro ─────────────────────────

@pytest.mark.parametrize("role", ["admin", "staff"])
def test_registro_publico_no_crea_admin_ni_staff(role):
    r = client.post("/api/auth/register", json={
        "email": f"{uuid.uuid4().hex[:8]}@x.io", "password": "password-123", "role": role, "tenant_id": "default"})
    assert r.status_code == 403


def test_registro_tenant_inexistente_o_malicioso():
    for tid in ["no-existe", "../../etc", "a/b", ""]:
        r = client.post("/api/auth/register", json={
            "email": f"{uuid.uuid4().hex[:8]}@x.io", "password": "password-123", "role": "artist", "tenant_id": tid or "x y"})
        assert r.status_code == 400, tid


def test_registro_password_corta():
    r = client.post("/api/auth/register", json={
        "email": "a@x.io", "password": "123", "role": "artist", "tenant_id": "default"})
    assert r.status_code == 422


def test_login_con_demasiados_intentos_se_bloquea():
    email = f"{uuid.uuid4().hex[:8]}@x.io"
    client.post("/api/auth/register", json={"email": email, "password": "password-123", "role": "artist", "tenant_id": "default"})
    codes = [client.post("/api/auth/login", json={"email": email, "password": "mala", "tenant_id": "default"}).status_code
             for _ in range(7)]
    assert codes[:5] == [401] * 5
    assert 429 in codes[5:]


# ───────────────────────── Tenants ─────────────────────────

def test_header_tenant_distinto_al_del_token_se_rechaza():
    _, tok = make_user("artist")
    assert client.get("/api/releases", headers={**auth(tok), "X-Tenant-Id": "otro"}).status_code == 403


def test_path_traversal_por_header_tenant():
    _, tok = make_user("artist")
    r = client.get("/api/releases", headers={**auth(tok), "X-Tenant-Id": "../../../tmp"})
    assert r.status_code == 403


def test_aislamiento_entre_tenants():
    from app.services.tenant_service import TenantService
    TenantService.create_tenant("label-b", "Label B")
    uid_a, tok_a = make_user("artist", "default")
    _accept_contract(tok_a)
    rid = _release(tok_a)
    _, tok_b = make_user("artist", "label-b")
    r = client.get(f"/api/releases/{rid}", headers=auth(tok_b, "label-b"))
    assert r.status_code == 404
    assert client.get("/api/releases", headers=auth(tok_b, "label-b")).json() == []


def test_artista_no_puede_crear_ni_listar_tenants():
    _, tok = make_user("artist")
    assert client.post("/api/tenants", json={"id": "nuevo", "name": "N"}, headers=auth(tok)).status_code == 403
    assert client.get("/api/tenants", headers=auth(tok)).status_code == 403


# ───────────────────────── Rutas solo admin ─────────────────────────

@pytest.mark.parametrize("method,path", [
    ("post", "/api/dsr/ingest"),           # inyectar ventas falsas = inflar regalías
    ("post", "/api/mwn/receive"),
    ("post", "/api/delivery/sftp"),
    ("get", "/api/analytics/overview"),
    ("post", "/api/catalog/identifiers"),
    ("get", "/api/admin/users"),
    ("post", "/api/ern/import"),
])
def test_artista_no_accede_a_rutas_de_admin(method, path):
    _, tok = make_user("artist")
    assert getattr(client, method)(path, headers=auth(tok)).status_code == 403


def test_token_de_servicio_del_worker_funciona_en_rutas_admin():
    """El worker de Celery se autentica con un JWT de servicio (antes llamaba sin credenciales y recibía 403)."""
    from workers.delivery_worker import _service_headers
    r = client.get("/api/tenants", headers=_service_headers("default"))
    assert r.status_code == 200


# ───────────────────────── Aislamiento entre artistas ─────────────────────────

def test_artista_no_ve_artistas_de_otros():
    _, tok_a = _artist()
    _, tok_b = _artist()
    r = client.post("/api/artists", json={"name": "Stan Boy", "type": "Person"}, headers=auth(tok_a))
    assert r.status_code == 200
    assert client.get("/api/artists", headers=auth(tok_b)).json() == []
    # y B crea "el mismo nombre": obtiene SU perfil, no el de A
    r2 = client.post("/api/artists", json={"name": "Stan Boy", "type": "Person"}, headers=auth(tok_b))
    assert r2.json()["id"] != r.json()["id"]


def test_no_se_puede_crear_release_con_artista_ajeno():
    _, tok_a = _artist()
    _, tok_b = _artist()
    art_a = client.post("/api/artists", json={"name": "A", "type": "Person"}, headers=auth(tok_a)).json()["id"]
    r = client.post("/api/releases", json={
        "title": "robo", "release_type": "Single", "language": "es", "territories": ["Worldwide"], "artist_id": art_a},
        headers=auth(tok_b))
    assert r.status_code == 400


def test_release_ajena_get_put_delete():
    _, tok_a = _artist()
    _, tok_b = _artist()
    rid = _release(tok_a)
    assert client.get(f"/api/releases/{rid}", headers=auth(tok_b)).status_code == 404
    assert client.put(f"/api/releases/{rid}", json={"title": "hack"}, headers=auth(tok_b)).status_code == 403
    assert client.delete(f"/api/releases/{rid}", headers=auth(tok_b)).status_code == 403
    assert client.get(f"/api/releases/{rid}", headers=auth(tok_a)).json()["title"] == "Mi release"


def test_respuesta_de_release_no_expone_rutas_del_servidor():
    _, tok = _artist()
    data = client.get(f"/api/releases/{_release(tok)}", headers=auth(tok)).json()
    assert "track_file" not in data


def test_portada_solo_la_ve_su_dueno_y_admin():
    _, tok_a = _artist()
    _, tok_b = _artist()
    _, tok_admin = make_user("admin")
    up = client.post("/api/assets/cover", files={"cover": ("c.jpg", _cover_bytes(), "image/jpeg")}, headers=auth(tok_a))
    assert up.status_code == 200, up.text
    assert "file_path" not in up.json()          # no filtra rutas internas
    aid = up.json()["id"]
    assert client.get(f"/api/assets/artwork/{aid}", headers=auth(tok_a)).status_code == 200
    assert client.get(f"/api/assets/artwork/{aid}", headers=auth(tok_admin)).status_code == 200
    assert client.get(f"/api/assets/artwork/{aid}", headers=auth(tok_b)).status_code == 404


def test_no_se_pueden_adivinar_archivos_por_prefijo():
    _, tok = _artist()
    for guess in ["c", "cover_", "..", "%2e%2e", "a"]:
        assert client.get(f"/api/assets/artwork/{guess}", headers=auth(tok)).status_code == 404
        assert client.get(f"/api/assets/audio/{guess}", headers=auth(tok)).status_code == 404


def test_artwork_ajeno_no_se_puede_asignar_a_mi_release():
    _, tok_a = _artist()
    _, tok_b = _artist()
    aid = client.post("/api/assets/cover", files={"cover": ("c.jpg", _cover_bytes(), "image/jpeg")}, headers=auth(tok_a)).json()["id"]
    rid = _release(tok_b)
    r = client.put(f"/api/releases/{rid}", json={"artwork_id": aid}, headers=auth(tok_b))
    assert r.status_code == 400


def test_storage_ya_no_se_sirve_publicamente():
    assert client.get("/assets/").status_code == 404
    assert client.get("/assets/cover_x.jpg").status_code == 404


def test_derechos_ajenos():
    _, tok_a = _artist()
    _, tok_b = _artist()
    rid = _release(tok_a)
    payload = {"scope": "RELEASE", "release_id": rid, "shares": [{
        "party_reference": "P1", "rights_type": "MasterRights", "usage_types": ["Stream"], "territories": ["Worldwide"],
        "share_percentage": 100, "valid_from": "2026-01-01"}]}
    assert client.post("/api/rights/configurations", json=payload, headers=auth(tok_b)).status_code in (403, 404)
    assert client.get("/api/rights/configurations", headers=auth(tok_b)).json() == []


def test_validacion_y_ern_de_release_ajena():
    _, tok_a = _artist()
    _, tok_b = _artist()
    rid = _release(tok_a)
    for path in (f"/api/validation/ern/{rid}/xml", f"/api/validation/ern/{rid}/parsed", f"/api/validation/results/{rid}"):
        assert client.get(path, headers=auth(tok_b)).status_code in (403, 404), path
    gen = client.post("/api/validation/generate-ern", json={"release_id": rid, "ern": {"profile": "AudioAlbum"}}, headers=auth(tok_b))
    assert gen.status_code in (403, 404)


def test_release_id_con_path_traversal_en_validacion():
    _, tok = _artist()
    for bad in ["..%2F..%2Fetc", "not-a-uuid"]:
        assert client.get(f"/api/validation/ern/{bad}/xml", headers=auth(tok)).status_code in (400, 404)


def test_artista_no_puede_firmar_ern():
    _, tok = _artist()
    assert client.post(f"/api/validation/sign/{uuid.uuid4()}", headers=auth(tok)).status_code == 403


def test_subida_de_audio_rechaza_extension_peligrosa():
    _, tok = _artist()
    rid = _release(tok)
    r = client.post("/api/tracks/upload", data={"release_id": rid, "title": "t"},
                    files={"audio": ("evil.html", b"<script>1</script>", "text/html")}, headers=auth(tok))
    assert r.status_code in (400, 404, 422)


def test_errores_internos_no_filtran_detalles(monkeypatch):
    from app.services.catalog_service import CatalogService
    _, tok = _artist()

    def boom(*a, **k):
        raise RuntimeError("SECRETO /home/user/db_password=123")

    monkeypatch.setattr(CatalogService, "get_releases", staticmethod(boom))
    c = TestClient(app, raise_server_exceptions=False)
    r = c.get("/api/releases", headers=auth(tok))
    assert r.status_code == 500
    assert "SECRETO" not in r.text and "error_id" in r.json()


def test_cors_no_refleja_origenes_arbitrarios():
    r = client.options("/api/releases", headers={
        "Origin": "https://evil.example", "Access-Control-Request-Method": "GET"})
    assert r.headers.get("access-control-allow-origin") != "https://evil.example"


# ───────────────────────── Persistencia ─────────────────────────

def test_escritura_atomica_y_lectura(tmp_path):
    f = tmp_path / "x.json"
    atomic_write_json(f, [{"a": 1}])
    assert read_json(f, list) == [{"a": 1}]
    assert not list(tmp_path.glob("*.tmp"))


def test_json_corrupto_no_se_convierte_en_lista_vacia(tmp_path):
    f = tmp_path / "x.json"
    f.write_text("[{\"a\": 1}", encoding="utf-8")        # truncado
    with pytest.raises(StorageCorruptionError):
        read_json(f, list)
    assert list(tmp_path.glob("x.json.corrupt-*"))        # quedó copia de cuarentena


def test_json_corrupto_se_recupera_desde_bak(tmp_path):
    f = tmp_path / "x.json"
    atomic_write_json(f, [{"a": 1}])
    atomic_write_json(f, [{"a": 1}, {"a": 2}])            # genera .bak con la versión previa
    f.write_text("{{{", encoding="utf-8")
    assert read_json(f, list) == [{"a": 1}]


def test_escrituras_concurrentes_no_pierden_datos(tmp_path):
    f = tmp_path / "x.json"
    atomic_write_json(f, [])

    def worker(i):
        for j in range(20):
            update_json(f, lambda d, v=(i, j): d.append(v))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert len(read_json(f, list)) == 8 * 20


def test_catalogo_concurrente_no_pierde_releases():
    from app.services.catalog_service import CatalogService
    from app.models.release import ReleaseDraft

    def worker(n):
        for _ in range(5):
            r = ReleaseDraft()
            r.title = f"t{n}"
            CatalogService.save_release(r, tenant_id="default")

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(6)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert len(CatalogService.get_releases(tenant_id="default")) == 30


def test_alta_de_usuarios_duplicados_concurrente():
    from app.repositories import user_repository as user_repo
    from app.models.user import User
    results = []

    def worker():
        try:
            user_repo.create(User(email="dup@x.io", hashed_password="h", role="artist", tenant_id="default"))
            results.append("ok")
        except user_repo.DuplicateEmailError:
            results.append("dup")

    ts = [threading.Thread(target=worker) for _ in range(6)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert results.count("ok") == 1
