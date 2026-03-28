"""
Admin royalty management.
Admin sees all earnings, creates payouts, marks them as paid.
"""
from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

from app.repositories import royalty_repo
from app.repositories import user_repository as user_repo
from app.models.royalty import Payout
from app.services.notification_service import notify_payout_created, notify_payout_processed

router = APIRouter(prefix="/admin/royalties", tags=["Admin - Royalties"])


def _require_admin(request: Request):
    if getattr(request.state, "user_role", "artist") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")


def _get_tenant(request: Request) -> str:
    return getattr(request.state, "tenant_id", None) or request.headers.get(
        "X-Tenant-Id", "default"
    )


# ── Schemas ──────────────────────────────────────────────────────

class CreatePayoutRequest(BaseModel):
    user_id: str
    amount: float
    currency: str = "USD"
    method: str = "zelle"  # zelle | paypal | transferencia | binance | otro
    note: Optional[str] = None
    period_from: Optional[str] = None
    period_to: Optional[str] = None
    statement_ids: Optional[list[str]] = None


class MarkPaidRequest(BaseModel):
    reference: str  # confirmation number
    note: Optional[str] = None


# ── Overview ─────────────────────────────────────────────────────

@router.get("/overview")
def get_overview(request: Request):
    """
    Global royalty overview for admin.
    Shows total earnings, AP Studios revenue, and pending payouts.
    """
    _require_admin(request)
    tenant_id = _get_tenant(request)

    all_statements = royalty_repo.get_statements(tenant_id)
    all_payouts = royalty_repo.get_payouts(tenant_id)

    total_gross = sum(s.gross_amount for s in all_statements)
    total_commission = sum(s.commission_amount for s in all_statements)
    total_net_artists = sum(s.net_amount for s in all_statements)
    total_paid = sum(p.amount for p in all_payouts if p.status == "paid")
    total_pending = sum(p.amount for p in all_payouts if p.status == "pending")

    # Per-artist breakdown
    artist_balances = {}
    for s in all_statements:
        uid = s.user_id
        if uid not in artist_balances:
            user = user_repo.get_by_id(uid, tenant_id)
            artist_balances[uid] = {
                "user_id": uid,
                "email": user.email if user else "unknown",
                "total_gross": 0.0,
                "total_net": 0.0,
                "total_streams": 0,
            }
        artist_balances[uid]["total_gross"] = round(
            artist_balances[uid]["total_gross"] + s.gross_amount, 2
        )
        artist_balances[uid]["total_net"] = round(
            artist_balances[uid]["total_net"] + s.net_amount, 2
        )
        artist_balances[uid]["total_streams"] += s.streams

    # Add payout info per artist
    for p in all_payouts:
        if p.user_id in artist_balances and p.status == "paid":
            artist_balances[p.user_id]["total_net"] = round(
                artist_balances[p.user_id]["total_net"] - p.amount, 2
            )

    return {
        "ap_studios_revenue_usd": round(total_commission, 2),
        "total_gross_from_dsps_usd": round(total_gross, 2),
        "total_net_owed_to_artists_usd": round(total_net_artists, 2),
        "total_paid_out_usd": round(total_paid, 2),
        "total_pending_payouts_usd": round(total_pending, 2),
        "available_to_pay_usd": round(
            total_net_artists - total_paid - total_pending, 2
        ),
        "artist_count": len(artist_balances),
        "statement_count": len(all_statements),
        "artists": sorted(
            artist_balances.values(), key=lambda x: x["total_net"], reverse=True
        ),
    }


@router.get("/artist/{user_id}")
def get_artist_royalties(user_id: str, request: Request):
    """Full royalty detail for a specific artist. Admin only."""
    _require_admin(request)
    tenant_id = _get_tenant(request)

    balance = royalty_repo.get_balance(user_id, tenant_id)
    statements = royalty_repo.get_statements(tenant_id, user_id=user_id)
    payouts = royalty_repo.get_payouts(tenant_id, user_id=user_id)

    user = user_repo.get_by_id(user_id, tenant_id)

    return {
        "user_id": user_id,
        "email": user.email if user else "unknown",
        "balance": balance,
        "statements": [
            s.to_dict()
            for s in sorted(statements, key=lambda x: x.period, reverse=True)
        ],
        "payouts": [
            p.to_dict()
            for p in sorted(payouts, key=lambda x: x.created_at, reverse=True)
        ],
    }


# ── Payouts ──────────────────────────────────────────────────────

@router.get("/payouts")
def list_all_payouts(request: Request):
    """List all payouts across all artists. Admin only."""
    _require_admin(request)
    tenant_id = _get_tenant(request)

    payouts = royalty_repo.get_payouts(tenant_id)
    enriched = []
    for p in sorted(payouts, key=lambda x: x.created_at, reverse=True):
        user = user_repo.get_by_id(p.user_id, tenant_id)
        d = p.to_dict()
        d["email"] = user.email if user else "unknown"
        enriched.append(d)

    pending_total = sum(p.amount for p in payouts if p.status == "pending")
    paid_total = sum(p.amount for p in payouts if p.status == "paid")

    return {
        "total": len(payouts),
        "pending_total_usd": round(pending_total, 2),
        "paid_total_usd": round(paid_total, 2),
        "payouts": enriched,
    }


@router.post("/payouts")
def create_payout(body: CreatePayoutRequest, request: Request):
    """
    Create a pending payout for an artist.
    Admin registers this before making the actual transfer.
    """
    _require_admin(request)
    tenant_id = _get_tenant(request)
    caller_id = getattr(request.state, "user_id", "admin")

    if body.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    if body.method not in Payout.VALID_METHODS:
        raise HTTPException(status_code=400, detail="Invalid payout method")

    user = user_repo.get_by_id(body.user_id, tenant_id)
    if not user:
        raise HTTPException(status_code=404, detail="Artist not found")

    # Validate amount doesn't exceed available balance
    balance = royalty_repo.get_balance(body.user_id, tenant_id)
    if body.amount > balance["available_balance"]:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Amount ${body.amount} exceeds available balance "
                f"${balance['available_balance']}"
            ),
        )

    payout = Payout(
        user_id=body.user_id,
        tenant_id=tenant_id,
        amount=body.amount,
        currency=body.currency,
        method=body.method,
        status="pending",
        note=body.note,
        period_from=body.period_from,
        period_to=body.period_to,
        statement_ids=body.statement_ids or [],
        created_by=caller_id,
    )
    royalty_repo.save_payout(payout)

    notify_payout_created(
        email=user.email,
        artist_name=user.email.split("@")[0],
        amount=body.amount,
        currency=body.currency,
        method=body.method,
        note=body.note,
    )

    return {
        **payout.to_dict(),
        "artist_email": user.email,
        "message": (
            f"Payout of ${body.amount} created for {user.email}. "
            "Mark as paid after completing the transfer."
        ),
    }


@router.patch("/payouts/{payout_id}/mark-paid")
def mark_payout_paid(
    payout_id: str,
    body: MarkPaidRequest,
    request: Request,
):
    """
    Mark a payout as paid after completing the manual transfer.
    Requires the payment reference (confirmation number).
    """
    _require_admin(request)
    tenant_id = _get_tenant(request)

    payout = royalty_repo.get_payout_by_id(payout_id, tenant_id)
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")

    if payout.status == "paid":
        raise HTTPException(status_code=400, detail="Payout already marked as paid")

    payout.status = "paid"
    payout.reference = body.reference
    payout.paid_at = datetime.now(timezone.utc).isoformat()
    if body.note:
        payout.note = body.note

    royalty_repo.save_payout(payout)

    user = user_repo.get_by_id(payout.user_id, tenant_id)
    if user:
        notify_payout_processed(
            email=user.email,
            artist_name=user.email.split("@")[0],
            amount=payout.amount,
            currency=payout.currency,
            method=payout.method,
            reference=body.reference,
            paid_at=payout.paid_at or "",
        )

    return {
        **payout.to_dict(),
        "artist_email": user.email if user else "unknown",
        "message": "Payout marked as paid successfully.",
    }


@router.patch("/payouts/{payout_id}/mark-failed")
def mark_payout_failed(payout_id: str, request: Request):
    """Mark a payout as failed - returns amount to available balance."""
    _require_admin(request)
    tenant_id = _get_tenant(request)

    payout = royalty_repo.get_payout_by_id(payout_id, tenant_id)
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")

    payout.status = "failed"
    royalty_repo.save_payout(payout)
    return payout.to_dict()
