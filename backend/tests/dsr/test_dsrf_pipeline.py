import os
import tempfile


SAMPLE_DSRF_10 = """HEAD\t1.0\tSpotify\t2026-01-01\t2026-01-31\tUSD
SY01\t859000000012\tUSXX12345678\t15000\t200\t42.50\tUSD\tUS
AS01\tUSXX12345678\tMy Song Title\t15000\t42.50\tUSD\tUS
FOOT\t2
"""

SAMPLE_DSRF_INVALID = """HEAD\t1.0\tSpotify\t2026-01-01\t2026-01-31
SY01\tnot-a-upc\t\t-999\tabc\t\t
"""


def write_temp(content: str) -> str:
    handle = tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False, encoding="utf-8")
    handle.write(content)
    handle.close()
    return handle.name


def test_detectar_version_dsrf_10():
    from app.services.dsrf_validator import DSRFValidator

    v = DSRFValidator()
    path = write_temp(SAMPLE_DSRF_10)
    try:
        assert v.detect_version(path) == "1.0"
    finally:
        os.unlink(path)


def test_validar_dsrf_valido():
    from app.services.dsrf_validator import dsrf_validator

    path = write_temp(SAMPLE_DSRF_10)
    try:
        result = dsrf_validator.validate(path)
        assert result["valid"] is True
        assert result["version"] == "1.0"
    finally:
        os.unlink(path)


def test_parsear_dsrf_retorna_registros():
    from app.services.dsr_parser import parse_dsrf_file

    path = write_temp(SAMPLE_DSRF_10)
    try:
        parsed = parse_dsrf_file(path, version="1.0")
        assert len(parsed["records"]) == 2
        assert parsed["summary"]["dsp_name"] == "Spotify"
        assert parsed["summary"]["period_start"] == "2026-01-01"
    finally:
        os.unlink(path)


def test_parsear_sy01_campos():
    from app.services.dsr_parser import parse_dsrf_file

    path = write_temp(SAMPLE_DSRF_10)
    try:
        parsed = parse_dsrf_file(path, version="1.0")
        sy01 = next(r for r in parsed["records"] if r["record_type"] == "SY01")
        assert sy01["upc"] == "859000000012"
        assert sy01["streams"] == 15000
        assert sy01["revenue"] == 42.50
    finally:
        os.unlink(path)


def test_archivo_invalido_sin_head():
    from app.services.dsrf_validator import dsrf_validator

    path = write_temp("SY01\t123\t456\n")
    try:
        result = dsrf_validator.validate(path)
        assert result["valid"] is False
        assert len(result["errors"]) > 0
    finally:
        os.unlink(path)
