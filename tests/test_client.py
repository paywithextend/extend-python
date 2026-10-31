"""Response and authentication behavior using only synthetic HTTP responses."""
import base64

import httpx
import pytest

from extend import ExtendClient
from extend.auth import BasicAuth
from extend.client import ExtendAPIError


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [400, 401, 403, 404, 409, 422, 500])
async def test_error_response_is_inspectable_without_disclosing_body(status):
    calls = []
    def respond(request):
        calls.append(request)
        return httpx.Response(status, json={"private": "synthetic-sensitive-value"})
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as transport:
        async with ExtendClient(BasicAuth("key", "secret"), environment="stage", http_client=transport) as sdk:
            with pytest.raises(ExtendAPIError) as exc:
                await sdk.transactions.get_transaction("txn_test")
    assert exc.value.status_code == status
    assert exc.value.response.json() == {"private": "synthetic-sensitive-value"}
    assert "synthetic-sensitive-value" not in str(exc.value)
    assert len(calls) == 1
    assert calls[0].headers["authorization"] == "Basic " + base64.b64encode(b"key:secret").decode()
    assert calls[0].headers["x-extend-api-key"] == "key"


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [200, 204])
async def test_empty_success_response(status):
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(status))) as transport:
        async with ExtendClient(BasicAuth("key", "secret"), environment="stage", http_client=transport) as sdk:
            assert await sdk.transactions.send_receipt_reminder("txn_test") is None


@pytest.mark.asyncio
async def test_delete_is_origin_constrained_and_not_retried():
    calls = []
    def respond(request):
        calls.append(request)
        return httpx.Response(503)
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as transport:
        async with ExtendClient(BasicAuth("key", "secret"), environment="stage", http_client=transport) as sdk:
            with pytest.raises(ValueError):
                await sdk.api_client.delete("https://other.invalid/x")
            assert not calls
            with pytest.raises(ExtendAPIError):
                await sdk.api_client.delete("/receiptattachments/ra_test")
    assert len(calls) == 1
    assert calls[0].method == "DELETE"
    assert calls[0].url.path == "/receiptattachments/ra_test"


@pytest.mark.asyncio
async def test_offline_guard_rejects_real_http():
    async with httpx.AsyncClient(trust_env=False) as transport:
        with pytest.raises(AssertionError, match="Real HTTP is disabled"):
            await transport.get("https://should-never-resolve.invalid")
