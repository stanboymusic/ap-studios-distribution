import pytest
import httpx
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_reintenta_en_timeout():
    call_count = 0

    async def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise httpx.TimeoutException("timeout", request=None)
        return httpx.Response(200, json={"status": "valid", "issues": []})

    with patch("httpx.AsyncClient.post", side_effect=mock_post):
        from app.services.ern_validator_api_client import validate_with_ern_validator_api

        result = await validate_with_ern_validator_api(b"<ern>...</ern>")
        assert result["status"] == "validated"
        assert call_count == 3


@pytest.mark.asyncio
async def test_no_reintenta_en_error_http_400():
    call_count = 0

    async def mock_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return httpx.Response(400, json={"status": "failed", "issues": ["bad xml"]})

    with patch("httpx.AsyncClient.post", side_effect=mock_post):
        from app.services.ern_validator_api_client import validate_with_ern_validator_api

        result = await validate_with_ern_validator_api(b"<ern>bad</ern>")
        assert result["status"] == "failed"
        assert call_count == 1


@pytest.mark.asyncio
async def test_circuit_breaker_se_abre_tras_fallos():
    from app.services.ern_validator_api_client import (
        _circuit_breaker,
        ExternalValidatorUnavailable,
        validate_with_ern_validator_api,
    )

    _circuit_breaker.failure_count = 0
    _circuit_breaker.state = "CLOSED"
    _circuit_breaker.last_failure_time = None

    async def always_fail(*args, **kwargs):
        raise httpx.ConnectError("refused", request=None)

    with patch("httpx.AsyncClient.post", side_effect=always_fail):
        for _ in range(5):
            try:
                await validate_with_ern_validator_api(b"<ern/>")
            except ExternalValidatorUnavailable:
                pass

    assert _circuit_breaker.state == "OPEN"

    with pytest.raises(ExternalValidatorUnavailable) as exc:
        await validate_with_ern_validator_api(b"<ern/>")
    assert "circuit breaker" in str(exc.value).lower()


def test_wrapper_sincrono_funciona():
    mock_result = {"status": "valid", "issues": []}

    with patch(
        "app.services.ern_validator_api_client.validate_with_ern_validator_api",
        new=AsyncMock(return_value=mock_result),
    ):
        from app.services.ern_validator_api_client import (
            validate_with_ern_validator_api_sync,
        )

        result = validate_with_ern_validator_api_sync(b"<ern/>")
        assert result["status"] == "valid"
