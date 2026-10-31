"""Opt-in checks of SDK contracts against explicitly provisioned test resources."""
import struct
import zlib
from datetime import datetime, timedelta, timezone
from io import BytesIO

import pytest

from tests.live_support import wait_for_automatch

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


def png():
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", 100, 100, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress((b"\x00" + b"\xff" * 300) * 100))
            + chunk(b"IEND", b""))


async def test_fixture_reads(live):
    sdk, cfg = live.sdk, live.config
    card = await sdk.credit_cards.get_credit_card_detail(cfg["credit_card_id"])
    assert card["creditCard"]["id"] == cfg["credit_card_id"]
    transaction = await sdk.transactions.get_transaction(cfg["transaction_id"])
    assert transaction["id"] == cfg["transaction_id"]
    categories = await sdk.expense_data.get_expense_categories(active=True)
    assert isinstance(categories["expenseCategories"], list)


@pytest.mark.parametrize("missing", [True, False])
async def test_transaction_receipt_filter(live, missing):
    response = await live.sdk.transactions.get_transactions(
        credit_card_id=live.config["credit_card_id"], receipt_missing=missing, page=1, per_page=10
    )
    rows = response["report"]["transactions"]
    assert len(rows) <= 10
    assert all((row["attachmentsCount"] == 0) == missing for row in rows)


async def test_transaction_filters_and_pagination(live):
    sdk, cfg = live.sdk, live.config
    detail = await sdk.transactions.get_transaction(cfg["transaction_id"])
    response = await sdk.transactions.get_transactions(
        virtual_card_id=detail["virtualCardId"], statuses=[detail["status"]],
        page=1, per_page=1, sort_field="-date",
    )
    rows = response["report"]["transactions"]
    assert len(rows) == 1
    assert rows[0]["virtualCardId"] == detail["virtualCardId"]
    assert rows[0]["status"] == detail["status"]
    count = await sdk.transactions.count_transactions(
        virtual_card_id=detail["virtualCardId"], statuses=[detail["status"]]
    )
    assert count["count"] >= 1
    second = await sdk.transactions.get_transactions(
        virtual_card_id=detail["virtualCardId"], statuses=[detail["status"]],
        page=2, per_page=1, sort_field="-date",
    )
    assert len(second["report"]["transactions"]) <= 1
    if second["report"]["transactions"]:
        assert second["report"]["transactions"][0]["id"] != rows[0]["id"]


@pytest.mark.parametrize("recurring", [False, True])
async def test_virtual_card_lifecycle(writes, recurring):
    run = writes
    until = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(timespec="milliseconds")
    response = await run.sdk.virtual_cards.create_virtual_card(
        credit_card_id=run.config["credit_card_id"], display_name=run.name,
        balance_cents=100, recipient=run.config["recipient"], cardholder=run.config["cardholder"],
        recurs=recurring, valid_to=None if recurring else until,
        recurrence={"balance_cents": 100, "period": "DAILY", "interval": 1,
                    "terminator": "DATE", "until": until} if recurring else None,
    )
    card = response["virtualCard"]
    run.cleanup("virtual_card", card["id"], run.close_card, card["id"])
    assert card["status"] == "ACTIVE"
    assert card["recurs"] is recurring
    assert card["displayName"] == run.name
    changed = await run.sdk.virtual_cards.update_virtual_card(card["id"], display_name=run.name, notes="SDK test", balance_cents=200)
    assert changed["virtualCard"]["balanceCents"] == 200
    assert changed["virtualCard"]["notes"] == "SDK test"
    cancelled = await run.sdk.virtual_cards.cancel_virtual_card(card["id"])
    assert cancelled["virtualCard"]["status"] == "CANCELLED"
    # Closing and verifying CLOSED happens in teardown even after assertion failures.


async def test_expense_category_label_and_transaction(writes):
    run, sdk = writes, writes.sdk
    txid = run.config["transaction_id"]
    category = await sdk.expense_data.create_expense_category(
        name=run.name, code=run.name, required=False, active=True, free_text_allowed=False
    )
    catid = category["id"]
    run.cleanup("category", catid, sdk.expense_data.update_expense_category, catid, active=False)
    assert (await sdk.expense_data.get_expense_category(catid))["name"] == run.name
    label = await sdk.expense_data.create_expense_category_label(catid, name=run.name, code=run.name, active=True)
    labelid = label["id"]
    run.cleanup("label", labelid, sdk.expense_data.update_expense_category_label, catid, labelid, active=False)
    labels = await sdk.expense_data.get_expense_category_labels(catid)
    assert any(label["id"] == labelid and label["name"] == run.name for label in labels["expenseLabels"])
    # PATCH affects only this newly created category. Clear it before deactivating it;
    # never replace or restore unrelated categories belonging to other tests/users.
    async def clear():
        await sdk.transactions.update_transaction_expense_data(
            txid, {"expenseDetails": [{"categoryId": catid, "labelId": None}]}
        )
        result = await sdk.transactions.get_transaction(txid)
        assert not any(d["categoryId"] == catid and d.get("labelId") for d in result.get("expenseDetails", []))
    run.cleanup("transaction_category", txid + "/" + catid, clear)
    result = await sdk.transactions.update_transaction_expense_data(
        txid, {"expenseDetails": [{"categoryId": catid, "labelId": labelid}]}
    )
    assert any(d["categoryId"] == catid and d["labelId"] == labelid for d in result["expenseDetails"])


async def test_receipt_upload(receipt_cleanup, writes):
    run = writes
    with BytesIO(png()) as stream:
        result = await run.sdk.receipt_attachments.create_receipt_attachment(
            stream, transaction_id=run.config["transaction_id"],
            filename=run.name + ".png", content_type="image/png",
        )
    run.cleanup("receipt", result["id"], run.delete_receipt, result["id"])
    assert result["contentType"] == "image/png"
    assert result["transactionId"] == run.config["transaction_id"]
    assert result["urls"]


async def test_automatch_completion(writes, request, receipt_cleanup):
    if not request.config.getoption("--live-automatch"):
        pytest.skip("Requires --live-automatch and a synthetic receipt that matches the fixture transaction")
    run = writes
    receipt = (run.directory / run.config["matching_receipt_file"]).resolve()
    assert receipt.is_relative_to(run.directory)
    with receipt.open("rb") as stream:
        result = await run.sdk.receipt_attachments.create_receipt_attachment(stream)
    run.cleanup("receipt", result["id"], run.delete_receipt, result["id"])
    job = await run.sdk.receipt_capture.automatch_receipts([result["id"]])
    await wait_for_automatch(run.sdk, job["id"], result["id"], run.config["transaction_id"])


async def test_receipt_reminder(live, request):
    if not request.config.getoption("--live-reminders"):
        pytest.skip("Reminders require --live-reminders and a dedicated recipient fixture")
    txid = live.config["reminder_transaction_id"]
    transaction = await live.sdk.transactions.get_transaction(txid)
    assert transaction["recipientEmail"].casefold() == live.config["reminder_recipient"].casefold()
    assert transaction["receiptRequired"] is True
    assert transaction["attachmentsCount"] == 0
    # A 429 is a failure, not evidence that a reminder was sent. Delivery is a separate service concern.
    assert await live.sdk.transactions.send_receipt_reminder(txid) is None
