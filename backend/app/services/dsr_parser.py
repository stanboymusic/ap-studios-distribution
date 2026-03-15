"""
DSRF TSV parser -> normalized records for analytics ingestion.
Supports DSRF 1.0 / 2.0 at a basic level.
"""
from __future__ import annotations

from typing import Optional
import csv


class DSRFParseError(Exception):
    pass


def parse_dsrf_file(file_path: str, version: str = "unknown") -> dict:
    records: list[dict] = []
    summary = {
        "dsp_name": None,
        "period_start": None,
        "period_end": None,
        "currency": None,
        "dsrf_version": version,
    }
    raw_row_count = 0

    try:
        with open(file_path, "r", encoding="utf-8") as handle:
            reader = csv.reader(handle, delimiter="\t")
            for row in reader:
                if not row:
                    continue
                raw_row_count += 1
                record_type = row[0].strip() if row else ""

                if record_type == "HEAD":
                    summary["dsp_name"] = _safe_get(row, 2)
                    summary["period_start"] = _safe_get(row, 3)
                    summary["period_end"] = _safe_get(row, 4)

                elif record_type == "SY01":
                    record = {
                        "record_type": "SY01",
                        "upc": _safe_get(row, 1),
                        "isrc": _safe_get(row, 2),
                        "streams": _safe_int(row, 3),
                        "downloads": _safe_int(row, 4),
                        "revenue": _safe_float(row, 5),
                        "currency": _safe_get(row, 6),
                        "territory": _safe_get(row, 7),
                        "period_start": summary.get("period_start"),
                        "period_end": summary.get("period_end"),
                        "dsp_name": summary.get("dsp_name"),
                    }
                    summary["currency"] = record["currency"] or summary.get("currency")
                    records.append(record)

                elif record_type == "AS01":
                    record = {
                        "record_type": "AS01",
                        "isrc": _safe_get(row, 1),
                        "title": _safe_get(row, 2),
                        "streams": _safe_int(row, 3),
                        "revenue": _safe_float(row, 4),
                        "currency": _safe_get(row, 5),
                        "territory": _safe_get(row, 6),
                        "period_start": summary.get("period_start"),
                        "period_end": summary.get("period_end"),
                        "dsp_name": summary.get("dsp_name"),
                    }
                    records.append(record)
    except UnicodeDecodeError as exc:
        raise DSRFParseError("File encoding error — expected UTF-8") from exc
    except Exception as exc:
        raise DSRFParseError(f"Unable to parse DSRF file: {exc}") from exc

    if not raw_row_count:
        raise DSRFParseError("Empty DSRF file")

    return {
        "records": records,
        "summary": summary,
        "raw_row_count": raw_row_count,
    }


def _safe_get(row: list, index: int) -> Optional[str]:
    try:
        val = row[index].strip()
        return val if val else None
    except IndexError:
        return None


def _safe_int(row: list, index: int) -> int:
    try:
        return int(row[index].strip())
    except (IndexError, ValueError):
        return 0


def _safe_float(row: list, index: int) -> float:
    try:
        return float(row[index].strip())
    except (IndexError, ValueError):
        return 0.0
