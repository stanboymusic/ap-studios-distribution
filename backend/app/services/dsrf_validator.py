"""
DSRF validator using ddexnet/dsrf (if available).
Falls back to basic validation when the library is missing.
"""
from __future__ import annotations

import logging
from typing import Optional


logger = logging.getLogger(__name__)


try:
    import dsrf
    from dsrf import dsrf_report, dsrf_error
    DSRF_AVAILABLE = True
except ImportError:
    DSRF_AVAILABLE = False

if not DSRF_AVAILABLE:
    logger.warning(
        "ddexnet/dsrf not installed — DSRF validation using basic fallback. "
        "Install manually: pip install git+https://github.com/ddexnet/dsrf.git"
    )


class DSRFValidationError(Exception):
    """Raised when a DSRF file does not pass validation."""

    def __init__(self, errors: list[str], version: Optional[str] = None):
        self.errors = errors
        self.version = version
        super().__init__(f"DSRF validation failed ({len(errors)} errors)")


class DSRFValidator:
    """
    Validates DSRF TSV files (1.0/2.0).
    Detects version from HEAD line.
    """

    SUPPORTED_VERSIONS = ["1.0", "2.0"]

    def detect_version(self, file_path: str) -> str:
        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split("\t")
                    if parts[0] == "HEAD" and len(parts) > 1:
                        version = parts[1].strip()
                        return version if version in self.SUPPORTED_VERSIONS else "unknown"
        except Exception:
            pass
        return "unknown"

    def validate(self, file_path: str) -> dict:
        version = self.detect_version(file_path)
        errors: list[str] = []
        warnings: list[str] = []
        row_count = 0

        if not DSRF_AVAILABLE:
            warnings.append("ddexnet/dsrf library not available — using basic validation only")
            errors, row_count = self._basic_validate(file_path)
        else:
            try:
                report = dsrf_report.DsrfReport(file_path)
                report.validate()
                row_count = getattr(report, "row_count", 0) or 0
            except Exception as exc:
                if dsrf_error and isinstance(exc, dsrf_error.DsrfError):
                    errors.append(str(exc))
                else:
                    errors.append(f"Unexpected validation error: {exc}")

        return {
            "valid": len(errors) == 0,
            "version": version,
            "errors": errors,
            "warnings": warnings,
            "row_count": row_count,
        }

    def _basic_validate(self, file_path: str) -> tuple[list[str], int]:
        errors: list[str] = []
        row_count = 0
        required_record_types = {"HEAD", "SY01", "AS01", "FOOT"}
        found_types: set[str] = set()

        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                for i, line in enumerate(handle):
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split("\t")
                    if len(parts) < 2:
                        errors.append(
                            f"Line {i+1}: expected TSV with at least 2 columns, got {len(parts)}"
                        )
                        continue
                    found_types.add(parts[0])
                    row_count += 1

            missing = required_record_types - found_types
            if missing:
                errors.append(
                    f"Missing required DSRF record types: {', '.join(sorted(missing))}"
                )
        except UnicodeDecodeError:
            errors.append("File encoding error — DSRF files must be UTF-8")
        except Exception as exc:
            errors.append(f"Could not read file: {exc}")

        return errors, row_count


dsrf_validator = DSRFValidator()
