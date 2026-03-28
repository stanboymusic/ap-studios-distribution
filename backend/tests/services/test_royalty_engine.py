import uuid
from unittest.mock import patch, MagicMock

import pytest

from app.models.royalty import RoyaltyStatement, Payout, AP_STUDIOS_COMMISSION_PCT
from app.services.royalty_engine import _normalize_period, process_dsr_line

TENANT = "test-royalty-tenant"


def test_commission_es_15_porciento():
    assert AP_STUDIOS_COMMISSION_PCT == 15.0


def test_royalty_statement_calcula_comision():
    stmt = RoyaltyStatement(
        user_id="u1",
        tenant_id=TENANT,
        period="2026-01",
        dsp="spotify",
        release_id="r1",
        release_title="Test",
        isrc="USRC17607839",
        territory="US",
        streams=10000,
        gross_amount=30.00,
    )
    assert stmt.commission_amount == pytest.approx(4.50, abs=0.001)
    assert stmt.net_amount == pytest.approx(25.50, abs=0.001)
    assert stmt.commission_pct == 15.0


def test_royalty_statement_redondeo():
    stmt = RoyaltyStatement(
        user_id="u1",
        tenant_id=TENANT,
        period="2026-01",
        dsp="apple_music",
        release_id="r1",
        release_title="Test",
        isrc="USRC17607839",
        territory="US",
        streams=1234,
        gross_amount=7.33,
    )
    assert stmt.gross_amount + 0.0 == pytest.approx(7.33, abs=0.001)
    total = stmt.commission_amount + stmt.net_amount
    assert total == pytest.approx(stmt.gross_amount, abs=0.0001)


def test_normalize_period_yyyy_mm():
    assert _normalize_period("2026-01") == "2026-01"


def test_normalize_period_full_date():
    assert _normalize_period("2026-01-15") == "2026-01"


def test_normalize_period_empty():
    result = _normalize_period("")
    assert len(result) == 7  # YYYY-MM


def test_payout_to_dict_round_trip():
    p = Payout(
        user_id="u1",
        tenant_id=TENANT,
        amount=50.00,
        method="zelle",
    )
    restored = Payout.from_dict(p.to_dict())
    assert restored.amount == 50.00
    assert restored.method == "zelle"
    assert restored.status == "pending"


def test_process_dsr_line_sin_release_retorna_none():
    with patch(
        "app.services.royalty_engine._find_release_by_isrc",
        return_value=None,
    ):
        result = process_dsr_line(
            dsr_id="dsr-001",
            tenant_id=TENANT,
            isrc="USRC99999999",
            dsp="spotify",
            period="2026-01",
            territory="US",
            streams=1000,
            gross_amount=5.00,
        )
        assert result is None


def test_process_dsr_line_sin_owner_retorna_none():
    mock_release = MagicMock()
    mock_release.owner_user_id = None
    mock_release.id = str(uuid.uuid4())
    mock_release.title = "Test"
    with patch(
        "app.services.royalty_engine._find_release_by_isrc",
        return_value=mock_release,
    ):
        result = process_dsr_line(
            dsr_id="dsr-002",
            tenant_id=TENANT,
            isrc="USRC17607839",
            dsp="spotify",
            period="2026-01",
            territory="US",
            streams=1000,
            gross_amount=5.00,
        )
        assert result is None


def test_get_balance_sin_datos():
    from app.repositories.royalty_repo import get_balance

    balance = get_balance(str(uuid.uuid4()), "empty-tenant")
    assert balance["available_balance"] == 0.0
    assert balance["total_net_earned"] == 0.0


def test_balance_descuenta_pagos_realizados():
    from app.repositories import royalty_repo

    uid = str(uuid.uuid4())
    t = f"test-balance-{uuid.uuid4().hex[:6]}"

    # Create statement
    stmt = RoyaltyStatement(
        user_id=uid,
        tenant_id=t,
        period="2026-01",
        dsp="spotify",
        release_id="r1",
        release_title="T",
        isrc="USRC00000001",
        territory="US",
        streams=5000,
        gross_amount=20.00,
    )
    royalty_repo.save_statement(stmt)

    # Create paid payout
    payout = Payout(
        user_id=uid,
        tenant_id=t,
        amount=10.00,
        status="paid",
    )
    royalty_repo.save_payout(payout)

    balance = royalty_repo.get_balance(uid, t)
    # net = 20 * 0.85 = 17.00, paid = 10.00, available = 7.00
    assert balance["total_net_earned"] == pytest.approx(17.00, abs=0.01)
    assert balance["total_paid_out"] == pytest.approx(10.00, abs=0.01)
    assert balance["available_balance"] == pytest.approx(7.00, abs=0.01)
