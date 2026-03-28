from fastapi import APIRouter, HTTPException, Request
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import date, datetime
import os
import tempfile
import shutil
from uuid import UUID
from app.models.dsr import SaleEvent, RevenueLineItem, Statement
from app.services.revenue_engine import calculate_payouts, build_statement
from app.services.rights_store import RightsStore
from app.services.dsr_store import DsrStore
from app.services.analytics_store import AnalyticsEvent, AnalyticsStore
from app.services.dsrf_validator import dsrf_validator
from app.services.dsr_parser import parse_dsrf_file, DSRFParseError
from app.services.dsr_history_store import DSRHistoryStore
from app.automation.engine import AutomationEngine
from app.automation.events import AutomationEvent
from app.services.royalty_engine import process_dsr_report
import logging

router = APIRouter(prefix="/dsr", tags=["DSR"])

def _tenant_id(request: Request) -> str:
    return getattr(request.state, "tenant_id", None) or "default"


def _parse_date(value: Any) -> Optional[date]:
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except Exception:
        return None


def _ingest_sales_report_payload(sales: List[Dict], tenant_id: str) -> dict:
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
            period_end=s["period_end"],
        )
        new_events.append(event)

        applicable_shares = []
        for config in rights_configs:
            if str(config.release_id) == event.release_ref:
                if config.scope == "release" and not event.track_ref:
                    applicable_shares = config.shares
                    break
                if config.scope == "track" and event.track_ref and str(config.track_id) == event.track_ref:
                    applicable_shares = config.shares
                    break

        if not applicable_shares:
            for config in rights_configs:
                if str(config.release_id) == event.release_ref and config.scope == "release":
                    applicable_shares = config.shares
                    break

        if applicable_shares:
            try:
                items = calculate_payouts(event, applicable_shares)
                new_line_items.extend(items)
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
            except ValueError:
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
        "line_items_generated": len(new_line_items),
    }


def _ingest_dsrf_records(records: List[Dict[str, Any]], tenant_id: str) -> None:
    for record in records:
        revenue = Decimal(str(record.get("revenue") or "0"))
        currency = record.get("currency") or "USD"
        dsp = record.get("dsp_name") or "unknown"
        territory = record.get("territory") or "unknown"
        release_id = record.get("upc")
        track_id = record.get("isrc")

        AnalyticsStore.append_event(
            AnalyticsEvent.create(
                event_type="revenue",
                dsp=dsp,
                territory=territory,
                amount=revenue,
                currency=currency,
                release_id=release_id,
                track_id=track_id,
                artist_id=None,
            ),
            tenant_id=tenant_id,
        )

        day = _parse_date(record.get("period_end")) or date.today()
        try:
            AnalyticsStore.add_daily_revenue(
                day=day,
                dsp=dsp,
                territory=territory,
                amount=revenue,
                currency=currency,
                tenant_id=tenant_id,
            )
        except Exception:
            pass

@router.post("/ingest")
async def ingest_sales_report(request: Request):
    """
    Ingesta:
    - JSON normalizado (lista de items) para ledger/payouts.
    - Archivo DSRF TSV (multipart/form-data, campo "file") para analytics.
    """
    tenant_id = _tenant_id(request)
    content_type = (request.headers.get("content-type") or "").lower()

    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        file = form.get("file")
        if not file:
            raise HTTPException(status_code=400, detail="Missing file in form-data")

        tmp_path = None
        try:
            suffix = os.path.splitext(getattr(file, "filename", "") or "report.tsv")[1] or ".tsv"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode="wb") as tmp:
                shutil.copyfileobj(file.file, tmp)
                tmp_path = tmp.name

            validation = dsrf_validator.validate(tmp_path)
            if not validation["valid"]:
                DSRHistoryStore.record(
                    tenant_id=tenant_id,
                    filename=getattr(file, "filename", None),
                    status="rejected",
                    dsrf_version=validation.get("version"),
                    errors=validation.get("errors"),
                    warnings=validation.get("warnings"),
                    row_count=validation.get("row_count"),
                )
                raise HTTPException(
                    status_code=422,
                    detail={
                        "message": "DSRF file failed validation",
                        "dsrf_version": validation.get("version"),
                        "errors": validation.get("errors"),
                        "warnings": validation.get("warnings"),
                    },
                )

            parsed = parse_dsrf_file(tmp_path, version=validation.get("version") or "unknown")
            _ingest_dsrf_records(parsed["records"], tenant_id=tenant_id)
            DSRHistoryStore.record(
                tenant_id=tenant_id,
                filename=getattr(file, "filename", None),
                status="accepted",
                dsrf_version=validation.get("version"),
                warnings=validation.get("warnings"),
                summary=parsed.get("summary"),
                row_count=parsed.get("raw_row_count"),
            )

            response_data = {
                "status": "ok",
                "dsrf_version": validation.get("version"),
                "filename": getattr(file, "filename", None),
                "rows_processed": len(parsed["records"]),
                "raw_row_count": parsed["raw_row_count"],
                "summary": parsed["summary"],
                "warnings": validation.get("warnings"),
            }

            try:
                summary = parsed.get("summary") or {}
                parsed_dsr = {
                    "dsr_id": getattr(file, "filename", None) or "dsrf-upload",
                    "dsp": summary.get("dsp_name") or "unknown_dsp",
                    "period": summary.get("period_end") or summary.get("period_start") or "",
                    "currency": summary.get("currency") or "USD",
                    "records": parsed.get("records") or [],
                }
                royalty_summary = process_dsr_report(
                    dsr_data=parsed_dsr,
                    tenant_id=tenant_id,
                )
                response_data["royalty_summary"] = royalty_summary
            except Exception as exc:
                logging.getLogger(__name__).warning(
                    f"Royalty processing failed for DSR: {exc}"
                )
                response_data["royalty_summary"] = {"error": str(exc)}

            return response_data
        except HTTPException:
            raise
        except DSRFParseError as exc:
            raise HTTPException(status_code=422, detail={"message": f"Parse error: {exc}"}) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail={"message": f"Internal error during DSR ingestion: {exc}"},
            ) from exc
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

    sales = await request.json()
    if not isinstance(sales, list):
        raise HTTPException(status_code=400, detail="Expected JSON list of sales items")
    return _ingest_sales_report_payload(sales, tenant_id)

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
