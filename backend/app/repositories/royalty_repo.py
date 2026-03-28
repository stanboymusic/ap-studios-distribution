"""
File-based royalty repository.
Storage layout:
  backend/storage/royalties/{tenant_id}/statements.json
  backend/storage/royalties/{tenant_id}/payouts.json
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from app.core.paths import storage_path
from app.models.royalty import RoyaltyStatement, Payout


# ── Internal helpers ─────────────────────────────────────────────

def _file(tenant_id: str, name: str) -> Path:
    path = storage_path("royalties", tenant_id)
    path.mkdir(parents=True, exist_ok=True)
    return path / f"{name}.json"


def _load(tenant_id: str, name: str) -> list[dict]:
    f = _file(tenant_id, name)
    if not f.exists():
        return []
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(tenant_id: str, name: str, data: list[dict]) -> None:
    _file(tenant_id, name).write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


# ── Statements ───────────────────────────────────────────────────

def save_statement(stmt: RoyaltyStatement) -> RoyaltyStatement:
    stmts = _load(stmt.tenant_id, "statements")
    stmts = [s for s in stmts if s.get("id") != stmt.id]
    stmts.append(stmt.to_dict())
    _save(stmt.tenant_id, "statements", stmts)
    return stmt


def get_statements(
    tenant_id: str,
    user_id: Optional[str] = None,
    period: Optional[str] = None,
    dsp: Optional[str] = None,
) -> list[RoyaltyStatement]:
    raw = _load(tenant_id, "statements")
    results = []
    for s in raw:
        if user_id and s.get("user_id") != user_id:
            continue
        if period and s.get("period") != period:
            continue
        if dsp and s.get("dsp") != dsp:
            continue
        results.append(RoyaltyStatement.from_dict(s))
    return results


def statement_exists(dsr_id: str, isrc: str, period: str, tenant_id: str) -> bool:
    """Prevent duplicate processing of same DSR line."""
    for s in _load(tenant_id, "statements"):
        if (
            s.get("dsr_id") == dsr_id
            and s.get("isrc") == isrc
            and s.get("period") == period
        ):
            return True
    return False


# ── Payouts ──────────────────────────────────────────────────────

def save_payout(payout: Payout) -> Payout:
    payouts = _load(payout.tenant_id, "payouts")
    payouts = [p for p in payouts if p.get("id") != payout.id]
    payouts.append(payout.to_dict())
    _save(payout.tenant_id, "payouts", payouts)
    return payout


def get_payouts(
    tenant_id: str,
    user_id: Optional[str] = None,
    status: Optional[str] = None,
) -> list[Payout]:
    raw = _load(tenant_id, "payouts")
    results = []
    for p in raw:
        if user_id and p.get("user_id") != user_id:
            continue
        if status and p.get("status") != status:
            continue
        results.append(Payout.from_dict(p))
    return results


def get_payout_by_id(payout_id: str, tenant_id: str) -> Optional[Payout]:
    for p in _load(tenant_id, "payouts"):
        if p.get("id") == payout_id:
            return Payout.from_dict(p)
    return None


# ── Balance calculation ──────────────────────────────────────────

def get_balance(user_id: str, tenant_id: str) -> dict:
    """
    Calculate current balance for an artist.
    Balance = total net earnings - total paid out - pending payouts
    """
    statements = get_statements(tenant_id, user_id=user_id)
    payouts = get_payouts(tenant_id, user_id=user_id, status="paid")

    total_gross = sum(s.gross_amount for s in statements)
    total_commission = sum(s.commission_amount for s in statements)
    total_net_earned = sum(s.net_amount for s in statements)
    total_paid = sum(p.amount for p in payouts)
    pending_payout = sum(
        p.amount
        for p in get_payouts(tenant_id, user_id=user_id, status="pending")
    )

    available_balance = round(total_net_earned - total_paid - pending_payout, 2)

    return {
        "user_id": user_id,
        "total_gross_earned": round(total_gross, 2),
        "total_commission_paid": round(total_commission, 2),
        "total_net_earned": round(total_net_earned, 2),
        "total_paid_out": round(total_paid, 2),
        "pending_payout": round(pending_payout, 2),
        "available_balance": available_balance,
        "currency": "USD",
        "statement_count": len(statements),
    }
