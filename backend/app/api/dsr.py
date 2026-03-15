from fastapi import APIRouter, HTTPException, Request
from typing import List, Dict
from decimal import Decimal
from datetime import date, datetime
from uuid import UUID
from app.models.dsr import SaleEvent, RevenueLineItem, Statement
from app.services.revenue_engine import calculate_payouts, build_statement
from app.services.rights_store import RightsStore
from app.services.dsr_store import DsrStore
from app.services.analytics_store import AnalyticsEvent, AnalyticsStore
from app.automation.engine import AutomationEngine
from app.automation.events import AutomationEvent

router = APIRouter(prefix="/dsr", tags=["DSR"])

def _tenant_id(request: Request) -> str:
    return getattr(request.state, "tenant_id", None) or "default"

@router.post("/ingest")
def ingest_sales_report(sales: List[Dict], request: Request):
    """
    Ingesta un reporte normalizado (lista de items) y genera ledger persistente.
    """
    tenant_id = _tenant_id(request)
    new_events = []
    new_line_items = []
    
    rights_configs = RightsStore.list_configurations(tenant_id)
    for s in sales:
        event = SaleEvent(
            dsp=s["dsp"],
            release_ref=str(s["release_ref"]).strip(),
            track_ref=str(s.get("track_ref")).strip() if s.get("track_ref") else None,
            usage_type=s["usage_type"],
            territory=s["territory"],
            quantity=s["quantity"],
            gross_amount=Decimal(str(s["gross_amount"])),
            currency=s["currency"],
            period_start=s["period_start"],
            period_end=s["period_end"]
        )
        new_events.append(event)
        
        # Resolve splits for this sale
        applicable_shares = []
        for config in rights_configs:
            if str(config.release_id) == event.release_ref:
                # Basic matching logic: check scope and track_id
                if config.scope == "release" and not event.track_ref:
                    applicable_shares = config.shares
                    break
                elif config.scope == "track" and event.track_ref and str(config.track_id) == event.track_ref:
                    applicable_shares = config.shares
                    break
        
        if not applicable_shares:
            # Fallback to any release-level config if specific track not found
            for config in rights_configs:
                if str(config.release_id) == event.release_ref and config.scope == "release":
                    applicable_shares = config.shares
                    break
        
        if applicable_shares:
            try:
                items = calculate_payouts(event, applicable_shares)
                new_line_items.extend(items)
                # Emit analytics for revenue (by line item)
                for li in items:
                    AnalyticsStore.append_event(
                        AnalyticsEvent.create(
                            event_type="revenue",
                            dsp=li.dsp,
                            territory=li.territory,
                            amount=li.amount,
                            currency=li.currency,
                            release_id=event.release_ref,
                            track_id=event.track_ref,
                            artist_id=None,
                        ),
                        tenant_id=tenant_id,
                    )
                    try:
                        AnalyticsStore.add_daily_revenue(
                            day=li.period_end if isinstance(li.period_end, date) else date.today(),
                            dsp=li.dsp,
                            territory=li.territory,
                            amount=li.amount,
                            currency=li.currency,
                            tenant_id=tenant_id,
                        )
                    except Exception:
                        pass
            except ValueError as e:
                # In real life: mark as unallocated
                pass
                 
    DsrStore.append_sales(new_events, tenant_id=tenant_id)
    DsrStore.append_line_items(new_line_items, tenant_id=tenant_id)
    try:
        AutomationEngine.process(
            AutomationEvent(
                type="dsr.ingested",
                tenant_id=tenant_id,
                payload={"events": len(new_events), "line_items": len(new_line_items)},
                severity="info",
            )
        )
    except Exception:
        pass

    return {
        "status": "processed",
        "events_ingested": len(new_events),
        "line_items_generated": len(new_line_items)
    }

@router.get("/statements/{party_reference}")
def get_party_statement(party_reference: str, request: Request):
    """
    Generates a statement for a specific party based on the ledger.
    """
    tenant_id = _tenant_id(request)
    rid = (party_reference or "").strip()
    party_items = [li for li in DsrStore.list_ledger(tenant_id) if li.party_reference == rid]
    
    if not party_items:
        raise HTTPException(status_code=404, detail="No revenue found for this party")
        
    return build_statement(rid, party_items)

@router.get("/ledger")
def get_ledger(request: Request):
    tenant_id = _tenant_id(request)
    return DsrStore.list_ledger(tenant_id)

@router.get("/balances")
def get_balances(request: Request):
    tenant_id = _tenant_id(request)
    ledger = DsrStore.list_ledger(tenant_id)
    balances: Dict[str, Decimal] = {}
    currency = "USD"
    for li in ledger:
        currency = li.currency or currency
        balances[li.party_reference] = balances.get(li.party_reference, Decimal("0")) + li.amount
    return {"currency": currency, "balances": {k: float(v) for k, v in sorted(balances.items())}}
