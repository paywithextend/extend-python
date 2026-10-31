"""Offline by default; live access requires an explicit configuration file."""
import json
import os
from pathlib import Path

import httpx
import pytest

from extend import ExtendClient
from extend.auth import BasicAuth
from tests.live_support import LiveRun


def pytest_addoption(parser):
    parser.addoption("--live-config", help="Private JSON fixture file (never auto-loaded)")
    parser.addoption("--live-writes", action="store_true", help="Enable reversible fixture writes")
    parser.addoption("--live-reminders", action="store_true", help="Send to the configured test recipient")
    parser.addoption("--live-automatch", action="store_true", help="Match the configured synthetic receipt")


@pytest.fixture(autouse=True)
def offline_network_guard(request, monkeypatch):
    if request.node.get_closest_marker("integration") and request.config.getoption("--live-config"):
        return

    def blocked(*args, **kwargs):
        raise AssertionError("Real HTTP is disabled in offline tests; use MockTransport")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", blocked)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", blocked)


@pytest.fixture
async def live(request):
    filename = request.config.getoption("--live-config")
    if not filename:
        pytest.skip("Live tests require --live-config; no credentials are read")
    path = Path(filename).resolve()
    config = json.loads(path.read_text())
    if config.get("dedicated_test_account") is not True:
        pytest.fail("Use a dedicated test account and set dedicated_test_account=true", pytrace=False)
    for name in ("environment", "credit_card_id", "transaction_id"):
        if not config.get(name):
            pytest.fail(f"Live config requires {name}", pytrace=False)
    key = os.environ.get("EXTEND_TEST_API_KEY")
    secret = os.environ.get("EXTEND_TEST_API_SECRET")
    if not key or not secret:
        pytest.fail("Set EXTEND_TEST_API_KEY and EXTEND_TEST_API_SECRET", pytrace=False)
    async with ExtendClient(BasicAuth(key, secret), environment=config["environment"]) as sdk:
        async with LiveRun(sdk, config, path.parent) as run:
            yield run


@pytest.fixture
async def writes(request, live):
    if not request.config.getoption("--live-writes"):
        pytest.skip("Writes require --live-writes")
    return live


@pytest.fixture
async def receipt_cleanup(writes):
    """Do not upload if this environment cannot delete test-owned receipts."""
    from extend.client import ExtendAPIError

    try:
        await writes.sdk.api_client.delete("/receiptattachments/ra_" + writes.name.replace("-", ""))
    except ExtendAPIError as exc:
        if exc.status_code == 403:
            pytest.skip("Receipt cleanup is unavailable on this API gateway; no upload performed")
        if exc.status_code != 404:
            raise
    else:
        pytest.fail("Cleanup preflight unexpectedly accepted a nonexistent receipt", pytrace=False)
