"""Synthetic contracts checked against endpoint implementations and consumer requests."""

import inspect
import io
import json
from pathlib import Path

import httpx
import pytest

from extend import ExtendClient
from extend.auth import BasicAuth
from extend.filters import transaction_query
from extend.validations import validate_card_creation_data, validate_card_update_data

CASES = json.loads(
    Path(__file__).with_name("fixtures").joinpath("endpoint_contracts.json").read_text()
)
pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["name"])
async def test_every_resource_wire_contract(case):
    seen = []
    stream = io.BytesIO(b"%PDF-1.7 synthetic")

    def respond(request):
        seen.append(request)
        assert request.method == case["method"]
        assert request.url.path == case["path"]
        assert dict(request.url.params) == case["query"]
        if case["body"] == "multipart":
            assert b'filename="synthetic.pdf"' in request.content
            assert b"application/pdf" in request.content
            assert b"transactionId" not in request.content
            assert b"%PDF-1.7 synthetic" in request.content
        else:
            assert (json.loads(request.content) if request.content else None) == case["body"]
        return (
            httpx.Response(200, json=case["response"])
            if case["response"] is not None
            else httpx.Response(200)
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as transport:
        async with ExtendClient(
            BasicAuth("synthetic", "secret"), environment="stage", http_client=transport
        ) as client:
            args = dict(case["arguments"])
            if case["body"] == "multipart":
                args.update(file=stream, filename="synthetic.pdf", content_type="application/pdf")
            result = await getattr(getattr(client, case["resource"]), case["name"])(**args)
    assert len(seen) == 1
    assert result == case["response"]
    assert not stream.closed


async def test_fixtures_cover_all_public_resource_operations():
    async with ExtendClient(BasicAuth("synthetic", "secret"), environment="stage") as client:
        expected = {
            (resource, name)
            for resource in {case["resource"] for case in CASES}
            for name, method in inspect.getmembers(
                getattr(client, resource), inspect.iscoroutinefunction
            )
            if not name.startswith("_")
        }
    assert {(case["resource"], case["name"]) for case in CASES} == expected


async def test_clear_date_filters_match_list_and_count():
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json={})

    filters = dict(
        from_date="2026-10-01",
        to_date="2026-10-31",
        date_type="Clear",
        statuses=["cleared", "pending"],
        sort_field="-dateClearedAt",
        receipt_missing=False,
        missing_expense_categories=False,
        min_amount_cents=0,
        credit_card_id="cc_1",
        virtual_card_id="vc_1",
    )
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as transport:
        async with ExtendClient(
            BasicAuth("synthetic", "secret"), environment="stage", http_client=transport
        ) as client:
            await client.transactions.get_transactions(page=1, per_page=50, **filters)
            await client.transactions.count_transactions(**filters)
    assert [
        (k, v) for k, v in requests[0].url.params.multi_items() if k not in {"page", "perPage"}
    ] == requests[1].url.params.multi_items()
    query = requests[0].url.params
    assert query.get_list("status") == ["CLEARED", "PENDING"]
    assert query["sinceClearedAt"] == "2026-10-01"
    assert query["untilClearedAt"] == "2026-10-31"
    assert "since" not in query and "until" not in query
    assert query["receiptStatus"] == "Attached"
    assert query["expenseCategoryStatuses"] == "Attached"
    assert query["minClearingBillingCents"] == "0"


@pytest.mark.parametrize("day", [28, 29, 30, 31])
async def test_camelcase_recurrence_supports_month_end(day):
    recurrence = dict(
        balanceCents=100,
        period="MONTHLY",
        interval=1,
        terminator="COUNT",
        count=12,
        byMonthDay=day,
        resetCount=False,
    )
    body = validate_card_creation_data("cc_1", "Synthetic", 100, recurs=True, recurrence=recurrence)
    assert body["recurrence"] == recurrence


@pytest.mark.parametrize("balance", [0, 99, 2_100_000_001, True, 100.5])
async def test_card_amount_limits_are_enforced(balance):
    with pytest.raises(ValueError):
        validate_card_creation_data("cc_1", "Synthetic", balance)
    with pytest.raises(ValueError):
        validate_card_update_data(balance, "Synthetic")


async def test_card_dates_notes_and_required_fields():
    result = validate_card_update_data(
        100, "Synthetic", notes="", valid_from="2027-01-01", valid_to="2027-01-01T20:00:00-05:00"
    )
    assert result["notes"] == ""
    assert result["validFrom"] == "2027-01-01"
    assert result["validTo"] == "2027-01-01T20:00:00-05:00"
    assert validate_card_update_data(100, "Synthetic", notes="x" * 501)["notes"] == "x" * 501
    for value in ["2027-02-31", "2027-01-01Tgarbage", "2027-01-01T10:00:00", ""]:
        with pytest.raises(ValueError):
            validate_card_update_data(100, "Synthetic", valid_to=value)
    for name in [None, " ", "x" * 256]:
        with pytest.raises(ValueError):
            validate_card_update_data(100, name)


@pytest.mark.parametrize(
    "recurrence",
    [
        {
            "balanceCents": 100,
            "period": "DAILY",
            "interval": 1,
            "terminator": "NONE",
            "byWeekDay": 0,
        },
        {
            "balanceCents": 100,
            "period": "YEARLY",
            "interval": 2,
            "terminator": "NONE",
            "byYearDay": 1,
        },
        {"balanceCents": 100, "period": "DAILY", "interval": 1, "terminator": "NONE", "count": 1},
        {
            "balanceCents": 100,
            "balance_cents": 100,
            "period": "DAILY",
            "interval": 1,
            "terminator": "NONE",
        },
    ],
)
async def test_invalid_recurrences_are_not_silently_rewritten(recurrence):
    with pytest.raises(ValueError):
        validate_card_creation_data("cc_1", "Synthetic", 100, recurs=True, recurrence=recurrence)


@pytest.mark.parametrize("bad_id", ["a/b", "../other", "a?x", "a%2fb", "", "a\\b"])
async def test_resource_ids_fail_before_authentication(bad_id):
    class NeverAuth:
        def get_auth_headers(self):
            pytest.fail("Credentials accessed before ID validation")

    async with ExtendClient(NeverAuth(), environment="stage") as client:
        for resource, operation, key in [
            ("credit_cards", "get_credit_card_detail", "card_id"),
            ("virtual_cards", "close_virtual_card", "card_id"),
            ("transactions", "get_transaction", "transaction_id"),
            ("expense_data", "get_expense_category", "category_id"),
            ("organizations", "get_expense_policy", "organization_id"),
            ("users", "get_user_details", "user_id"),
            ("receipt_capture", "get_automatch_status", "job_id"),
        ]:
            with pytest.raises(ValueError):
                await getattr(getattr(client, resource), operation)(**{key: bad_id})


async def test_nested_null_clears_label_and_false_updates_survive():
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(
            200,
            json={"id": "t_1", "clearingBillingAmountCents": None, "authBillingCurrency": "CAD"},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as transport:
        async with ExtendClient(
            BasicAuth("synthetic", "secret"), environment="stage", http_client=transport
        ) as client:
            body = {"expenseDetails": [{"categoryId": "ec_1", "labelId": None}]}
            result = await client.transactions.update_transaction_expense_data("t_1", body)
            await client.expense_data.update_expense_category("ec_1", active=False, required=False, required_for_transactions=True, required_for_virtual_cards=False)
            await client.expense_data.get_expense_categories(
                transaction_id="t_1", active=True, required_for_transactions=False
            )
    assert json.loads(requests[0].content) == body
    assert result["authBillingCurrency"] == "CAD" and result["clearingBillingAmountCents"] is None
    assert json.loads(requests[1].content) == {"active": False, "required": False, "requiredForTransactions": True, "requiredForVirtualCards": False}
    assert requests[2].url.params["transactionId"] == "t_1"
    assert requests[2].url.params["requiredForTransactions"] == "false"


async def test_new_card_statuses_are_serialized():
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json={})

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as transport:
        async with ExtendClient(
            BasicAuth("synthetic", "secret"), environment="stage", http_client=transport
        ) as client:
            await client.virtual_cards.get_virtual_cards(status="rejected")
            await client.credit_cards.get_credit_cards(status="needs_verification")
            await client.credit_cards.get_credit_cards(status="not_applicable")
    assert requests[0].url.params["statuses"] == "REJECTED"
    assert requests[1].url.params["status"] == "NEEDS_VERIFICATION"
    assert requests[2].url.params["status"] == "NOT_APPLICABLE"


@pytest.mark.parametrize(
    "filters",
    [
        {"statuses": []},
        {"from_date": "2026-02-31"},
        {"date_type": "Wrong"},
        {"min_amount_cents": True},
        {"status": "CLEARED", "statuses": ["PENDING"]},
        {"receipt_missing": False, "receipt_statuses": ["Missing"]},
    ],
)
async def test_invalid_transaction_filters_fail(filters):
    with pytest.raises(ValueError):
        transaction_query(**filters)
