"""
RoyaltyEngine: processes DSR data into RoyaltyStatements.

Flow:
  DSR parsed lines
    -> match ISRC to release -> get owner_user_id
    -> apply 15% AP Studios commission
    -> save RoyaltyStatement
    -> return summary
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from app.models.royalty import RoyaltyStatement, AP_STUDIOS_COMMISSION_PCT
from app.repositories import royalty_repo
from app.services.catalog_service import CatalogService
from app.repositories import user_repository as user_repo
from app.services.notification_service import notify_royalties_available

logger = logging.getLogger(__name__)


def _normalize_period(period_str: str) -> str:
    """
    Normalize period to YYYY-MM format.
    Accepts: "2026-01", "January 2026", "2026-01-01", etc.
    """
    if not period_str:
        return datetime.utcnow().strftime("%Y-%m")
    period_str = str(period_str).strip()
    # Already YYYY-MM
    if len(period_str) >= 7 and period_str[4] == "-":
        return period_str[:7]
    # Try parsing full date
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(period_str, fmt).strftime("%Y-%m")
        except ValueError:
            continue
    return period_str[:7] if len(period_str) >= 7 else period_str


def _find_release_by_isrc(isrc: str, tenant_id: str) -> Optional[object]:
    """Find a release that contains a track with this ISRC."""
    if not isrc:
        return None
    try:
        releases = CatalogService.get_releases(tenant_id=tenant_id)
        for release in releases:
            tracks = getattr(release, "tracks", []) or []
            for track in tracks:
                track_isrc = (
                    track.get("isrc") if isinstance(track, dict) else getattr(track, "isrc", None)
                )
                if (
                    track_isrc
                    and track_isrc.replace("-", "").upper()
                    == isrc.replace("-", "").upper()
                ):
                    return release
            # Also check release-level ISRC (singles)
            release_isrc = getattr(release, "isrc", None)
            if (
                release_isrc
                and release_isrc.replace("-", "").upper()
                == isrc.replace("-", "").upper()
            ):
                return release
    except Exception as exc:
        logger.warning(f"ISRC lookup failed for {isrc}: {exc}")
    return None


def process_dsr_line(
    *,
    dsr_id: str,
    tenant_id: str,
    isrc: str,
    dsp: str,
    period: str,
    territory: str,
    streams: int,
    gross_amount: float,
    currency: str = "USD",
) -> Optional[RoyaltyStatement]:
    """
    Process a single DSR line into a RoyaltyStatement.
    Returns None if the ISRC cannot be matched to a release.
    Skips duplicate DSR lines silently.
    """
    period_normalized = _normalize_period(period)

    # Deduplication check
    if royalty_repo.statement_exists(dsr_id, isrc, period_normalized, tenant_id):
        logger.debug(f"Skipping duplicate DSR line: {dsr_id}/{isrc}/{period_normalized}")
        return None

    # Match ISRC -> release -> owner
    release = _find_release_by_isrc(isrc, tenant_id)
    if not release:
        logger.warning(
            f"No release found for ISRC {isrc} "
            f"(DSR: {dsr_id}, period: {period_normalized})"
        )
        return None

    owner_user_id = getattr(release, "owner_user_id", None)
    if not owner_user_id:
        logger.warning(
            f"Release {release.id} has no owner_user_id - "
            f"skipping royalty for ISRC {isrc}"
        )
        return None

    release_id = str(getattr(release, "id", "") or getattr(release, "release_id", ""))
    release_title = getattr(release, "title", "Unknown Release")

    dsp_value = str(dsp or "unknown_dsp").lower().replace(" ", "_")

    stmt = RoyaltyStatement(
        user_id=owner_user_id,
        tenant_id=tenant_id,
        period=period_normalized,
        dsp=dsp_value,
        release_id=release_id,
        release_title=release_title,
        isrc=isrc,
        territory=territory or "Worldwide",
        streams=streams,
        gross_amount=gross_amount,
        commission_pct=AP_STUDIOS_COMMISSION_PCT,
        currency=currency,
        dsr_id=dsr_id,
    )

    royalty_repo.save_statement(stmt)
    logger.info(
        f"RoyaltyStatement created: {stmt.id} | "
        f"Artist: {owner_user_id} | "
        f"Net: ${stmt.net_amount} {currency} | "
        f"ISRC: {isrc} | DSP: {dsp_value} | Period: {period_normalized}"
    )
    return stmt


def process_dsr_report(dsr_data: dict, tenant_id: str) -> dict:
    """
    Process a full parsed DSR report.
    dsr_data: output from dsr_parser.py

    Returns summary:
      {
        processed: int,
        skipped_duplicate: int,
        skipped_no_match: int,
        total_net_usd: float,
        statements: [RoyaltyStatement]
      }
    """
    dsr_id = dsr_data.get("dsr_id") or dsr_data.get("id", "unknown")
    dsp = dsr_data.get("dsp") or dsr_data.get("sender", "unknown_dsp")
    period = dsr_data.get("period") or dsr_data.get("usage_period", "")
    currency = dsr_data.get("currency", "USD")

    lines = dsr_data.get("lines") or dsr_data.get("records") or []

    processed = []
    skipped_dup = 0
    skipped_no_match = 0

    for line in lines:
        isrc = (line.get("isrc") or "").strip()
        if not isrc:
            skipped_no_match += 1
            continue

        territory = line.get("territory") or line.get("country") or "Worldwide"
        streams = int(line.get("streams") or line.get("quantity") or 0)
        gross = float(
            line.get("gross_amount")
            or line.get("amount")
            or line.get("royalty_amount")
            or line.get("revenue")
            or 0.0
        )
        line_period = (
            line.get("period")
            or line.get("period_end")
            or line.get("period_start")
            or period
        )

        stmt = process_dsr_line(
            dsr_id=dsr_id,
            tenant_id=tenant_id,
            isrc=isrc,
            dsp=dsp,
            period=line_period,
            territory=territory,
            streams=streams,
            gross_amount=gross,
            currency=currency,
        )

        if stmt is None:
            # Could be duplicate or no match - check which
            if royalty_repo.statement_exists(
                dsr_id, isrc, _normalize_period(line_period), tenant_id
            ):
                skipped_dup += 1
            else:
                skipped_no_match += 1
        else:
            processed.append(stmt)

    total_net = sum(s.net_amount for s in processed)
    total_gross = sum(s.gross_amount for s in processed)
    ap_commission = sum(s.commission_amount for s in processed)

    if processed:
        users = {s.user_id for s in processed if getattr(s, "user_id", None)}
        for uid in users:
            try:
                user = user_repo.get_by_id(uid, tenant_id)
                if not user:
                    continue
                artist_stmts = [st for st in processed if st.user_id == uid]
                balance = royalty_repo.get_balance(uid, tenant_id)
                notify_royalties_available(
                    email=user.email,
                    artist_name=user.email.split("@")[0],
                    period=period or "N/A",
                    streams=sum(st.streams for st in artist_stmts),
                    gross_amount=sum(st.gross_amount for st in artist_stmts),
                    net_amount=sum(st.net_amount for st in artist_stmts),
                    commission_amount=sum(st.commission_amount for st in artist_stmts),
                    available_balance=balance.get("available_balance", 0.0),
                    top_dsp=dsp or "Spotify",
                )
            except Exception as exc:
                logger.warning("Failed to notify royalties for user %s: %s", uid, exc)

    return {
        "dsr_id": dsr_id,
        "dsp": dsp,
        "period": period,
        "processed": len(processed),
        "skipped_duplicate": skipped_dup,
        "skipped_no_match": skipped_no_match,
        "total_gross_usd": round(total_gross, 2),
        "ap_studios_commission_usd": round(ap_commission, 2),
        "total_net_artists_usd": round(total_net, 2),
        "statements": [s.to_dict() for s in processed],
    }
