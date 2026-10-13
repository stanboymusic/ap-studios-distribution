"""Flujo completo como lo hace el wizard: registro -> artista -> release -> audio -> portada -> ERN."""
from __future__ import annotations

import io
import math
import struct
import uuid
import wave

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from tests.helpers import auth, make_user

client = TestClient(app)


def _wav_bytes(seconds=4, rate=44100):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(rate)
        frames = b"".join(
            struct.pack("<hh", int(12000 * math.sin(2 * math.pi * 440 * i / rate)),
                        int(12000 * math.sin(2 * math.pi * 660 * i / rate)))
            for i in range(rate * seconds))
        w.writeframes(frames)
    return buf.getvalue()


def _cover():
    b = io.BytesIO()
    Image.new("RGB", (3000, 3000), (90, 20, 40)).save(b, "JPEG")
    return b.getvalue()


def test_flujo_completo_artista():
    # 1. registro real (como la pantalla de registro)
    email = f"{uuid.uuid4().hex[:8]}@mail.io"
    reg = client.post("/api/auth/register", json={"email": email, "password": "password-123", "role": "artist", "tenant_id": "default"})
    assert reg.status_code == 200, reg.text
    tok = reg.json()["access_token"]
    H = auth(tok)

    # 2. contrato
    assert client.post("/api/contracts/accept", json={"accepted": True}, headers=H).status_code in (200, 201)

    # 3. artista + release
    artist = client.post("/api/artists/", json={"name": "Stan boy", "type": "Person"}, headers=H)
    assert artist.status_code == 200, artist.text
    rel = client.post("/api/releases/", json={
        "title": "Primer sencillo", "release_type": "Single", "language": "es",
        "territories": ["Worldwide"], "artist_id": artist.json()["id"]}, headers=H)
    assert rel.status_code in (200, 201), rel.text
    rid = rel.json()["id"]

    # 4. audio (WAV real) — igual que StepTracks
    tr = client.post("/api/tracks/", data={"release_id": rid, "title": "Intro", "track_number": "1", "explicit": "false"},
                     files={"audio": ("intro.wav", _wav_bytes(), "audio/wav")}, headers=H)
    assert tr.status_code == 200, tr.text
    body = tr.json()
    assert body.get("isrc"), "el track debe recibir un ISRC"
    assert "file_path" not in body and body.get("file_name", "").endswith(".wav")

    # 5. portada
    cov = client.post("/api/assets/cover", files={"cover": ("c.jpg", _cover(), "image/jpeg")}, headers=H)
    assert cov.status_code == 200, cov.text
    up = client.put(f"/api/releases/{rid}", json={"artwork_id": cov.json()["id"]}, headers=H)
    assert up.status_code == 200, up.text

    # 6. el release guardado conserva TODO (persistencia)
    saved = client.get(f"/api/releases/{rid}", headers=H).json()
    assert saved["title"] == "Primer sencillo"
    assert len(saved.get("tracks") or []) == 1
    assert saved.get("artwork_id") == cov.json()["id"]
    assert saved["tracks"][0].get("isrc") == body["isrc"]
    print("RELEASE GUARDADO:", {k: saved.get(k) for k in ("upc", "status", "artist_id")})


def test_ern_usa_los_identificadores_reales_del_catalogo():
    """El XML que se envía a las plataformas NO puede llevar los valores de relleno del frontend."""
    uid, tok = make_user("artist")
    H = auth(tok)
    client.post("/api/contracts/accept", json={"accepted": True}, headers=H)
    art = client.post("/api/artists/", json={"name": "Stan boy", "type": "Person"}, headers=H).json()["id"]
    rid = client.post("/api/releases/", json={"title": "Single", "release_type": "Single", "language": "es",
                                              "territories": ["Worldwide"], "artist_id": art}, headers=H).json()["id"]
    tr = client.post("/api/tracks/", data={"release_id": rid, "title": "Intro", "track_number": "1", "explicit": "false"},
                     files={"audio": ("intro.wav", _wav_bytes(), "audio/wav")}, headers=H).json()
    real_isrc = tr["isrc"]
    real_upc = client.get(f"/api/releases/{rid}", headers=H).json()["upc"]

    # Payload tal cual lo arma frontend/src/utils/ernPayload.ts (con sus valores de relleno)
    payload = {
        "release_id": rid,
        "ern": {"version": "4.3", "profile": "AudioAlbum", "message_id": "msg-1",
                "sender": {"party_id": "PA-DPIDA-202402050E-4", "name": "AP Studios"},
                "recipient": {"party_id": "DPID-RECIPIENT", "name": "Recipient DSP"}},
        "parties": {"party-artist": {"display_name": "Stan boy", "country": "US", "primary_language": "es", "is_rights_holder": True},
                    "party-sender": {"display_name": "AP Studios", "party_id": "PA-DPIDA-202402050E-4", "role": "RightsController"}},
        "resources": {"resource-track-0": {"title": "Intro", "isrc": "US-ABC-00", "duration_seconds": 4, "type": "SoundRecording",
                                           "artists": ["party-artist"], "file": "x.wav", "track_id": tr["track_id"]}},
        "releases": {"release-main": {"title": "Single", "release_type": "Single", "artist": "party-artist",
                                      "parental_advisory": "None", "genres": {"primary": "Pop"},
                                      "release_date": "2026-01-01", "upc": "1234567890123",
                                      "tracks": ["resource-track-0"]}},
        "deals": {"deal-main": {"release": "release-main", "territories": ["Worldwide"], "startDate": "2026-01-01",
                                "commercialModels": [{"model": "SubscriptionModel", "use_type": "Stream"}]}},
    }
    r = client.post("/api/validation/generate-ern", json=payload, headers=H)
    print("generate-ern:", r.status_code, (r.text[:300] if r.status_code != 200 else "ok"))
    assert r.status_code == 200, r.text
    xml = r.json()["xml"]
    print("UPC real:", real_upc, "| ISRC real:", real_isrc)
    print("XML contiene UPC placeholder:", "1234567890123" in xml, "| contiene UPC real:", real_upc in xml)
    print("XML contiene ISRC placeholder:", "US-ABC-00" in xml or "USABC00" in xml, "| ISRC real:", real_isrc.replace("-", "") in xml.replace("-", ""))
    assert "1234567890123" not in xml, "UPC de relleno llegó al XML"
    assert real_upc in xml
    assert real_isrc.replace("-", "") in xml.replace("-", "")


def test_aprobacion_admin_y_paquete_de_entrega():
    uid, tok = make_user("artist")
    H = auth(tok)
    _, admin_tok = make_user("admin")
    A = auth(admin_tok)
    client.post("/api/contracts/accept", json={"accepted": True}, headers=H)
    art = client.post("/api/artists/", json={"name": "Stan boy", "type": "Person"}, headers=H).json()["id"]
    rid = client.post("/api/releases/", json={"title": "Single", "release_type": "Single", "language": "es",
                                              "territories": ["Worldwide"], "artist_id": art}, headers=H).json()["id"]
    tr = client.post("/api/tracks/", data={"release_id": rid, "title": "Intro", "track_number": "1", "explicit": "false"},
                     files={"audio": ("intro.wav", _wav_bytes(), "audio/wav")}, headers=H).json()
    cov = client.post("/api/assets/cover", files={"cover": ("c.jpg", _cover(), "image/jpeg")}, headers=H).json()
    client.put(f"/api/releases/{rid}", json={"artwork_id": cov["id"]}, headers=H)

    payload = {
        "release_id": rid,
        "ern": {"version": "4.3", "profile": "AudioAlbum", "message_id": "msg-1",
                "sender": {"party_id": "PA-DPIDA-202402050E-4", "name": "AP Studios"},
                "recipient": {"party_id": "DPID-RECIPIENT", "name": "Recipient DSP"}},
        "parties": {"party-artist": {"display_name": "Stan boy", "country": "US", "primary_language": "es"},
                    "party-sender": {"display_name": "AP Studios", "party_id": "PA-DPIDA-202402050E-4", "role": "RightsController"}},
        "resources": {"resource-track-0": {"title": "Intro", "isrc": tr["isrc"], "duration_seconds": 4, "type": "SoundRecording",
                                           "artists": ["party-artist"], "file": tr["file_name"]}},
        "releases": {"release-main": {"title": "Single", "release_type": "Single", "artist": "party-artist",
                                      "parental_advisory": "None", "genres": {"primary": "Pop"},
                                      "release_date": "2026-01-01", "upc": "1234567890123", "tracks": ["resource-track-0"]}},
        "deals": {"deal-main": {"release": "release-main", "territories": ["Worldwide"], "startDate": "2026-01-01",
                                "commercialModels": [{"model": "SubscriptionModel", "use_type": "Stream"}]}},
    }
    assert client.post("/api/validation/generate-ern", json=payload, headers=H).status_code == 200

    q = client.get("/api/validation/admin/queue", headers=A)
    print("admin queue:", q.status_code, str(q.json())[:200])
    ap = client.post(f"/api/validation/admin/{rid}/approve", json={}, headers=A)
    print("approve:", ap.status_code, ap.text[:300])
    ex = client.post(f"/api/delivery/{rid}/export", headers=A)
    print("export:", ex.status_code, ex.text[:400])
    assert ex.status_code == 200
    import zipfile
    names = zipfile.ZipFile(ex.json()["path"]).namelist()
    print("ZIP:", names)
    assert any(n.lower().endswith(".xml") for n in names), "falta el ERN"
    assert any(n.startswith("audio/") for n in names), "falta el audio"
    assert any("cover" in n.lower() or n.lower().endswith((".jpg", ".png")) for n in names), "falta la portada"
    # el artista NO puede lanzar entregas
    assert client.post(f"/api/delivery/{rid}/export", headers=H).status_code == 403
