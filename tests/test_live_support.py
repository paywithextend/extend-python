"""Exercise failure cleanup offline; never contacts the live API."""
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from tests.live_support import LiveRun, wait_for_automatch


@pytest.mark.asyncio
async def test_all_cleanup_runs_after_assertion_and_cleanup_failure(tmp_path):
    order = []

    async def cleanup(name):
        order.append(name)
        if name == "second":
            raise RuntimeError("cleanup failed")

    run = LiveRun(None, {"environment": "stage"}, tmp_path)
    with pytest.raises(RuntimeError, match="cleanup failed"):
        async with run:
            run.cleanup("fixture", "one", cleanup, "first")
            run.cleanup("fixture", "two", cleanup, "second")
            raise AssertionError("test failed after resource creation")
    assert order == ["second", "first"]
    records = json.loads(run.journal.read_text())["resources"]
    assert [r["cleanup"] for r in records] == ["complete", "failed"]
    assert run.journal.stat().st_mode & 0o777 == 0o600


@pytest.mark.asyncio
async def test_successful_cleanup_is_recorded(tmp_path):
    cleanup = AsyncMock()
    async with LiveRun(None, {"environment": "stage"}, tmp_path) as run:
        run.cleanup("receipt", "ra_test", cleanup, "ra_test")
    cleanup.assert_awaited_once_with("ra_test")
    assert json.loads(run.journal.read_text())["resources"][0]["cleanup"] == "complete"


@pytest.mark.asyncio
@pytest.mark.parametrize("status,transaction", [("ERROR", "txn_test"), ("SUCCESS", "txn_other")])
async def test_automatch_requires_success_and_expected_transaction(status, transaction):
    sdk = SimpleNamespace(receipt_capture=SimpleNamespace(get_automatch_status=AsyncMock(
        return_value={"id": "job_test", "tasks": [{"receiptAttachmentId": "ra_test", "status": status,
                                                  "transactionId": transaction}]}
    )))
    with pytest.raises(AssertionError):
        await wait_for_automatch(sdk, "job_test", "ra_test", "txn_test")


@pytest.mark.asyncio
async def test_pending_automatch_times_out():
    sdk = SimpleNamespace(receipt_capture=SimpleNamespace(get_automatch_status=AsyncMock(
        return_value={"id": "job_test", "tasks": []}
    )))
    with pytest.raises(TimeoutError):
        await wait_for_automatch(sdk, "job_test", "ra_test", "txn_test", timeout=0.01)


@pytest.mark.asyncio
async def test_automatch_success():
    result = {"id": "job_test", "tasks": [{"receiptAttachmentId": "ra_test", "status": "SUCCESS",
                                          "transactionId": "txn_test"}]}
    sdk = SimpleNamespace(receipt_capture=SimpleNamespace(get_automatch_status=AsyncMock(return_value=result)))
    assert await wait_for_automatch(sdk, "job_test", "ra_test", "txn_test") == result


@pytest.mark.asyncio
@pytest.mark.parametrize("active", [True, False])
async def test_deactivation_verifies_server_result(tmp_path, active):
    sdk = SimpleNamespace(expense_data=SimpleNamespace(
        update_expense_category=AsyncMock(return_value={"active": active}),
        update_expense_category_label=AsyncMock(return_value={"active": active}),
    ))
    run = LiveRun(sdk, {"environment": "stage"}, tmp_path)
    for operation, args in [(run.deactivate_category, ("cat_test",)),
                            (run.deactivate_label, ("cat_test", "label_test"))]:
        if active:
            with pytest.raises(AssertionError):
                await operation(*args)
        else:
            await operation(*args)
