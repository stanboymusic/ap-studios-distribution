"""
Royalty endpoints for artists.
Artists see their own earnings, statements, and payout history.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Query
from typing import Optional

from app.repositories import royalty_repo

router = APIRouter(prefix="/royalties", tags=["Royalties"])


def _require_auth(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if not user_id or user_id.endswith(":anonymous"):
        raise HTTPException(status_code=401, detail="Authentication required")
    return user_id


def _get_tenant(request: Request) -> str:
    return getattr(request.state, "tenant_id", None) or request.headers.get(
        "X-Tenant-Id", "default"
    )


@router.get("/balance")
def get_my_balance(request: Request):
    """Get current balance for authenticated artist."""
    user_id = _require_auth(request)
    tenant_id = _get_tenant(request)
    return royalty_repo.get_balance(user_id, tenant_id)


@router.get("/statements")
def get_my_statements(
    request: Request,
    period: Optional[str] = Query(None, description="Filter by period YYYY-MM"),
    dsp: Optional[str] = Query(None, description="Filter by DSP"),
):
    """Get royalty statements for authenticated artist."""
    user_id = _require_auth(request)
    tenant_id = _get_tenant(request)

    statements = royalty_repo.get_statements(
        tenant_id, user_id=user_id, period=period, dsp=dsp
    )

    # Group by period for easier frontend rendering
    by_period: dict[str, dict] = {}
    for s in statements:
        p = s.period
        if p not in by_period:
            by_period[p] = {
                "period": p,
                "total_streams": 0,
                "total_gross": 0.0,
                "total_commission": 0.0,
                "total_net": 0.0,
                "dsps": [],
                "statements": [],
            }
        by_period[p]["total_streams"] += s.streams
        by_period[p]["total_gross"] = round(
            by_period[p]["total_gross"] + s.gross_amount, 6
        )
        by_period[p]["total_commission"] = round(
            by_period[p]["total_commission"] + s.commission_amount, 6
        )
        by_period[p]["total_net"] = round(
            by_period[p]["total_net"] + s.net_amount, 6
        )
        if s.dsp not in by_period[p]["dsps"]:
            by_period[p]["dsps"].append(s.dsp)
        by_period[p]["statements"].append(s.to_dict())

    periods_sorted = sorted(
        by_period.values(), key=lambda x: x["period"], reverse=True
    )

    return {
        "total_statements": len(statements),
        "periods": periods_sorted,
    }


@router.get("/payouts")
def get_my_payouts(request: Request):
    """Get payout history for authenticated artist."""
    user_id = _require_auth(request)
    tenant_id = _get_tenant(request)

    payouts = royalty_repo.get_payouts(tenant_id, user_id=user_id)
    return {
        "total": len(payouts),
        "payouts": [
            p.to_dict()
            for p in sorted(payouts, key=lambda x: x.created_at, reverse=True)
        ],
    }
