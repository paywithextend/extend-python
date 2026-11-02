"""Focused transport regressions; all requests use synthetic data and MockTransport."""
import asyncio
import json
import os
import subprocess
import sys

import httpx
import pytest

from extend import ExtendClient
from extend.auth import BasicAuth, BearerAuth
from extend.client import APIClient, ExtendAPIError, ExtendTransportError


@pytest.mark.parametrize("path", [
    "https://audit.invalid/x", "//audit.invalid/x", ".audit.invalid/x",
    "@audit.invalid/x", "/\\audit.invalid/x", "/x?query=secret", "/x#fragment",
    "/%2f%2faudit.invalid", "/%252f", "/../x", "/x/./y", "/x//y",
    "/x\n", "/x\r", "/x\t", "/x\x00", "/é", "/a:b", "", "/a@b",
])
@pytest.mark.asyncio
async def test_invalid_paths_fail_before_credentials_or_network(path):
    class NeverAuth:
        def get_auth_headers(self):
            pytest.fail("Credentials read for invalid path")

    async with APIClient(NeverAuth(), environment="stage") as api:
        with pytest.raises(ValueError):
            await api.get(path)


@pytest.mark.asyncio
async def test_url_and_headers_refresh_without_redirects():
    seen = []

    def handle(request):
        seen.append(request)
        return httpx.Response(200, json={"ok": True})

    auth = BearerAuth("first-dummy")
    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as transport:
        async with APIClient(auth, environment="stage", http_client=transport) as api:
            await api.get("/transactions/txn_dummy", {"search": "a&b"})
            auth.jwt_token = "second-dummy"
            await api.get("/transactions/txn_dummy")
        assert not transport.is_closed
    assert [r.headers["authorization"] for r in seen] == ["Bearer first-dummy", "Bearer second-dummy"]
    assert seen[0].url.host == "apiv2-stage.paywithextend.com"
    assert seen[0].url.params["search"] == "a&b"


@pytest.mark.asyncio
async def test_redirect_never_receives_credentials():
    seen = []

    def handle(request):
        seen.append(request)
        return httpx.Response(302, headers={"location": "https://audit.invalid/steal"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle), follow_redirects=True) as transport:
        async with APIClient(BasicAuth("dummy", "secret"), environment="prod", http_client=transport) as api:
            with pytest.raises(ExtendAPIError) as error:
                await api.get("/creditcards")
    assert len(seen) == 1
    assert seen[0].url.host == "apiv2.paywithextend.com"
    assert error.value.status_code == 302


@pytest.mark.asyncio
async def test_owned_transport_lifecycle_and_factory_isolation():
    one = APIClient.shared_instance(BearerAuth("one"), environment="stage")
    two = APIClient.shared_instance(BearerAuth("two"), environment="prod")
    assert one is not two
    assert one.headers != two.headers
    await one.aclose()
    await one.aclose()
    assert one._client.is_closed
    with pytest.raises(RuntimeError, match="closed"):
        await one.get("/creditcards")
    await two.aclose()


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH"])
@pytest.mark.asyncio
async def test_mutations_are_never_retried(method):
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(503, headers={"retry-after": "0"}, json={"private": "do-not-log"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as transport:
        async with APIClient(BearerAuth("dummy"), environment="stage", http_client=transport) as api:
            with pytest.raises(ExtendAPIError) as error:
                await getattr(api, method.lower())("/virtualcards/vc_dummy", {})
    assert len(calls) == 1
    assert "do-not-log" not in str(error.value)
    assert error.value.retry_after == "0"


@pytest.mark.asyncio
async def test_bounded_read_retries_and_safe_error_metadata():
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(429, headers={"retry-after": "0", "x-request-id": "req_dummy"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as transport:
        async with APIClient(BearerAuth("dummy"), environment="stage", http_client=transport) as api:
            with pytest.raises(ExtendAPIError) as error:
                await api.get("/creditcards")
    assert len(calls) == 3
    assert error.value.status_code == 429
    assert error.value.request_id == "req_dummy"


@pytest.mark.asyncio
async def test_retry_after_larger_than_budget_is_not_shortened():
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(429, headers={"retry-after": "600"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as transport:
        async with APIClient(BearerAuth("dummy"), environment="stage", http_client=transport) as api:
            with pytest.raises(ExtendAPIError):
                await api.get("/creditcards")
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_timeout_and_cancellation_propagation():
    async def handle(request):
        await asyncio.sleep(10)
        return httpx.Response(200, json={})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as transport:
        async with APIClient(BearerAuth("dummy"), environment="stage", http_client=transport, read_budget=.01) as api:
            with pytest.raises(ExtendTransportError, match="budget"):
                await api.get("/creditcards")
            task = asyncio.create_task(api.get("/creditcards"))
            await asyncio.sleep(0)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task


@pytest.mark.asyncio
async def test_public_resource_routes_and_no_payload_print(capsys):
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(200, json={"virtualCard": {"id": "vc_dummy"}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as transport:
        async with ExtendClient(BasicAuth("dummy", "secret"), environment="stage", http_client=transport) as client:
            await client.virtual_cards.create_virtual_card(
                credit_card_id="cc_dummy", display_name="private-name", balance_cents=100,
                recipient="private@example.invalid", notes="private-note",
            )
            assert client.api_client.environment == "stage"
    assert calls[0].method == "POST"
    assert calls[0].url.path == "/virtualcards"
    assert "private" not in capsys.readouterr().out
    assert json.loads(calls[0].content)["notes"] == "private-note"


def test_environment_is_explicit_but_import_is_safe(monkeypatch, tmp_path):
    monkeypatch.delenv("ENV", raising=False)
    with pytest.raises(ValueError, match="environment"):
        APIClient(BearerAuth("dummy"))
    for environment in ["dev", "production", "", "STAGE"]:
        with pytest.raises(ValueError):
            APIClient(BearerAuth("dummy"), environment=environment)
    (tmp_path / ".env").write_text("ENV=prod\nEXTEND_API_KEY=do-not-read\n")
    env = {k: v for k, v in os.environ.items() if not k.startswith("EXTEND_") and k != "ENV"}
    result = subprocess.run(
        [sys.executable, "-c", "import extend,os,sys; assert 'dotenv' not in sys.modules; assert 'ENV' not in os.environ; assert 'EXTEND_API_KEY' not in os.environ"],
        cwd=tmp_path, env=env, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
