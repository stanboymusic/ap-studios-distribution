from unittest.mock import patch, AsyncMock
from app.services import notification_service as ns

def test_notify_welcome_sin_smtp():
    with patch("app.services.email_service.ENABLED", False):
        with patch("app.services.email_service.send_email", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = False
            ns.notify_welcome("test@test.com", "Test Artist")

def test_render_welcome_template():
    from app.services.email_service import render_template
    html = render_template("welcome.html", {"artist_name": "Stan Boy", "email": "stan@test.com"})
    assert "Stan Boy" in html
    assert "AP Studios" in html

def test_render_royalties_template():
    from app.services.email_service import render_template
    html = render_template("royalties_available.html", {
        "artist_name": "Test", "period": "2026-01", "streams": "1,000",
        "gross_amount": "5.00", "net_amount": "4.25", "commission_amount": "0.75",
        "available_balance": "4.25", "top_dsp": "Spotify"
    })
    assert "2026-01" in html
    assert "4.25" in html

def test_fmt_date_helpers():
    from app.services.notification_service import _fmt_date
    assert "2026" in _fmt_date("2026-03-28T12:00:00Z")
    assert _fmt_date(None) == "—"
