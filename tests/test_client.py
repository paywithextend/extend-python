import os
from datetime import datetime, timedelta
from typing import Any

import httpx
import pytest
from dotenv import load_dotenv

from extend import VirtualCard, Transaction, validations, ExtendClient

load_dotenv()


@pytest.fixture(scope="session")
def extend():
    # Initialize the API client
    return ExtendClient(os.getenv("EXTEND_API_KEY"), os.getenv("EXTEND_API_SECRET"))


@pytest.fixture
def mock_virtual_card() -> VirtualCard:
    return {
        "id": "vc_123",
        "displayName": "Test Card",
        "status": "ACTIVE",
        "balanceCents": 1000,
        "spentCents": 0,
        "limitCents": 1000,
        "last4": "1234",
        "expires": "2024-12",
        "validFrom": "2024-01-01T00:00:00.000Z",
        "validTo": "2024-12-31T23:59:59.999Z"
    }


@pytest.fixture
def mock_transaction() -> Transaction:
    return {
        "id": "txn_123",
        "merchantName": "Test Merchant",
        "status": "CLEARED",
        "type": "AUTH",
        "virtualCardId": "vc_123",
        "authedAt": "2024-01-01T12:00:00.000Z",
        "clearedAt": "2024-01-02T12:00:00.000Z",
        "authBillingAmountCents": 1000,
        "clearingBillingAmountCents": 1000,
        "mcc": "5812",
        "notes": "Test transaction"
    }


# Test validation methods
def test_validate_card_creation_data():
    # Test valid data
    valid_data = validations.validate_card_creation_data(
        credit_card_id="card123",
        display_name="Test Card",
        balance_cents=1000
    )
    assert valid_data["creditCardId"] == "card123"
    assert valid_data["displayName"] == "Test Card"
    assert valid_data["balanceCents"] == 1000

    # Test invalid balance
    with pytest.raises(ValueError, match="Balance must be greater than 0"):
        validations.validate_card_creation_data(
            credit_card_id="card123",
            display_name="Test Card",
            balance_cents=0
        )

    # Test invalid email
    with pytest.raises(ValueError, match="Invalid email format"):
        validations.validate_card_creation_data(
            credit_card_id="card123",
            display_name="Test Card",
            balance_cents=1000,
            recipient_email="invalid-email"
        )

    # Test valid dates
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    valid_data = validations.validate_card_creation_data(
        credit_card_id="card123",
        display_name="Test Card",
        balance_cents=1000,
        valid_from=tomorrow,
        valid_to=next_week
    )
    assert "validFrom" in valid_data
    assert "validTo" in valid_data


def test_validate_recurrence_data():
    # Test valid daily recurrence
    valid_data = validations.validate_recurrence_data(
        balance_cents=1000,
        period="DAILY",
        interval=1,
        terminator="NONE"
    )
    assert isinstance(valid_data, dict)
    assert valid_data["balanceCents"] == 1000
    assert valid_data["period"] == "DAILY"
    assert valid_data["interval"] == 1
    assert valid_data["terminator"] == "NONE"

    # Test valid weekly recurrence
    valid_data = validations.validate_recurrence_data(
        balance_cents=1000,
        period="WEEKLY",
        interval=1,
        terminator="NONE",
        by_week_day=1
    )
    assert valid_data["byWeekDay"] == 1

    # Test invalid period
    with pytest.raises(ValueError, match="Period must be one of"):
        validations.validate_recurrence_data(
            balance_cents=1000,
            period="INVALID",
            interval=1,
            terminator="NONE"
        )

    # Test missing required fields for weekly
    with pytest.raises(ValueError, match="byWeekDay is required for WEEKLY period"):
        validations.validate_recurrence_data(
            balance_cents=1000,
            period="WEEKLY",
            interval=1,
            terminator="NONE"
        )


# Test API methods with mocked responses
@pytest.mark.asyncio
async def test_create_virtual_card(extend, mocker, mock_virtual_card):
    mock_response: Any = {
        "virtualCard": mock_virtual_card
    }

    mocker.patch.object(extend._api_client, 'post', return_value=mock_response)

    response = await extend.virtual_cards.create_virtual_card(
        credit_card_id="card123",
        display_name="Test Card",
        balance_cents=1000
    )

    assert response["virtualCard"]["id"] == "vc_123"
    assert response["virtualCard"]["displayName"] == "Test Card"


@pytest.mark.asyncio
async def test_get_virtual_cards(extend, mocker, mock_virtual_card):
    mock_response = {"virtualCards": [mock_virtual_card, mock_virtual_card]}

    # Create a simple async mock that returns the response
    async def mock_get(*args, **kwargs):
        return mock_response

    # Patch the get method with our async function
    mocker.patch.object(extend._api_client, 'get', new=mock_get)

    # The get_virtual_cards method needs to await the get call
    response = await extend.virtual_cards.get_virtual_cards()
    assert len(response["virtualCards"]) == 2


def test_validate_card_data():
    # Test valid data
    data = validations.validate_card_data(
        credit_card_id="card123",
        display_name="Test Card",
        balance_cents=1000
    )
    assert data["creditCardId"] == "card123"
    assert data["displayName"] == "Test Card"
    assert data["balanceCents"] == 1000

    # Test invalid balance
    with pytest.raises(ValueError, match="Balance must be greater than 0"):
        validations.validate_card_data(
            credit_card_id="card123",
            display_name="Test Card",
            balance_cents=0
        )


# Additional API method tests
@pytest.mark.asyncio
async def test_update_virtual_card(extend, mocker, mock_virtual_card):
    mock_response: Any = {
        "virtualCard": mock_virtual_card
    }

    mocker.patch.object(extend._api_client, 'put', return_value=mock_response)

    response = await extend.virtual_cards.update_virtual_card(
        card_id="vc_123",
        display_name="Updated Card",
        balance_cents=2000
    )

    assert response["virtualCard"]["id"] == "vc_123"


@pytest.mark.asyncio
async def test_cancel_and_close_virtual_card(extend, mocker, mock_virtual_card):
    # Setup mock responses
    cancelled_card = dict(mock_virtual_card)
    cancelled_card["status"] = "CANCELLED"
    mock_cancel_response = {
        "virtualCard": cancelled_card
    }

    closed_card = dict(mock_virtual_card)
    closed_card["status"] = "CLOSED"
    mock_close_response = {
        "virtualCard": closed_card
    }

    # Mock the put method directly
    mocker.patch.object(
        extend._api_client,
        'put',
        return_value=mock_cancel_response
    )

    # Test cancel
    response = await extend.virtual_cards.cancel_virtual_card("vc_123")
    assert response["virtualCard"]["status"] == "CANCELLED"

    # Update mock for close
    mocker.patch.object(
        extend._api_client,
        'put',
        return_value=mock_close_response
    )

    # Test close
    response = await extend.virtual_cards.close_virtual_card("vc_123")
    assert response["virtualCard"]["status"] == "CLOSED"


@pytest.mark.asyncio
async def test_get_transactions(extend, mocker, mock_transaction):
    mock_response: Any = {
        "transactions": [mock_transaction, mock_transaction]
    }

    mocker.patch.object(extend._api_client, 'get', return_value=mock_response)

    response = await extend.transactions.get_transactions()
    assert len(response["transactions"]) == 2


# Additional recurrence validation tests
def test_validate_recurrence_data_monthly(extend):
    # Test valid monthly recurrence
    valid_data = validations.validate_recurrence_data(
        balance_cents=1000,
        period="MONTHLY",
        interval=1,
        terminator="NONE",
        by_month_day=15
    )
    assert valid_data["byMonthDay"] == 15

    # Test invalid month day
    with pytest.raises(ValueError, match="byMonthDay must be between 1 and 31"):
        validations.validate_recurrence_data(
            balance_cents=1000,
            period="MONTHLY",
            interval=1,
            terminator="NONE",
            by_month_day=32
        )

    # Test invalid month day (29th in February)
    with pytest.raises(ValueError, match="Choose a day between 1 and 28"):
        validations.validate_recurrence_data(
            balance_cents=1000,
            period="MONTHLY",
            interval=1,
            terminator="NONE",
            by_month_day=31
        )


def test_validate_recurrence_data_yearly():
    # Test valid yearly recurrence
    valid_data = validations.validate_recurrence_data(
        balance_cents=1000,
        period="YEARLY",
        interval=1,
        terminator="NONE",
        by_year_day=100
    )
    assert valid_data["byYearDay"] == 100

    # Test invalid year day
    with pytest.raises(ValueError, match="byYearDay must be between 1 and 365"):
        validations.validate_recurrence_data(
            balance_cents=1000,
            period="YEARLY",
            interval=1,
            terminator="NONE",
            by_year_day=366
        )


def test_validate_recurrence_terminator():
    # Test COUNT terminator
    valid_data = validations.validate_recurrence_data(
        balance_cents=1000,
        period="DAILY",
        interval=1,
        terminator="COUNT",
        count=5
    )
    assert valid_data["count"] == 5

    # Test DATE terminator
    next_month = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    valid_data = validations.validate_recurrence_data(
        balance_cents=1000,
        period="DAILY",
        interval=1,
        terminator="DATE",
        until=next_month
    )
    assert "until" in valid_data

    # Test missing count for COUNT terminator
    with pytest.raises(ValueError, match="Count is required"):
        validations.validate_recurrence_data(
            balance_cents=1000,
            period="DAILY",
            interval=1,
            terminator="COUNT"
        )

    # Test missing until for DATE terminator
    with pytest.raises(ValueError, match="Until date is required"):
        validations.validate_recurrence_data(
            balance_cents=1000,
            period="DAILY",
            interval=1,
            terminator="DATE"
        )


# Test HTTP error handling
@pytest.mark.asyncio
async def test_http_error_handling(extend, mocker):
    # Test 400 error
    error_response = mocker.Mock()
    error_response.status_code = 400

    async def mock_error_get(*args, **kwargs):
        raise httpx.HTTPStatusError(
            "Bad Request",
            request=mocker.Mock(),
            response=error_response
        )

    mocker.patch.object(extend._api_client, 'get', side_effect=mock_error_get)

    with pytest.raises(httpx.HTTPStatusError):
        await extend.virtual_cards.get_virtual_cards()

    # Test network error
    async def mock_network_get(*args, **kwargs):
        raise httpx.NetworkError("Connection failed")

    mocker.patch.object(extend._api_client, 'get', side_effect=mock_network_get)

    with pytest.raises(httpx.NetworkError):
        await extend.virtual_cards.get_virtual_cards()


@pytest.mark.asyncio
async def test_update_transaction_expense_data_success(extend, mocker, mock_transaction):
    mock_response = {
        "transaction": {
            **mock_transaction,
            "supplier": {"name": "Acme Inc", "id": "sup_123"},
            "customer": {"name": "Client A", "id": "cust_456"},
            "expenseCategories": [
                {"categoryCode": "TRAVEL", "labelCode": "TAXI"}
            ]
        }
    }

    mocker.patch.object(
        extend._api_client,
        'patch',
        return_value=mock_response
    )

    response = await extend.transactions.update_transaction_expense_data(
        transaction_id=mock_transaction["id"],
        data={
            "supplier": {"name": "Acme Inc", "id": "sup_123"},
            "customer": {"name": "Client A", "id": "cust_456"},
            "expenseCategories": [{"categoryCode": "TRAVEL", "labelCode": "TAXI"}]
        }
    )

    assert response["transaction"]["supplier"]["name"] == "Acme Inc"
    assert response["transaction"]["customer"]["id"] == "cust_456"
    assert response["transaction"]["expenseCategories"][0]["categoryCode"] == "TRAVEL"


@pytest.mark.asyncio
async def test_update_transaction_expense_data_partial_fields(extend, mocker, mock_transaction):
    mock_response = {
        "transaction": {
            **mock_transaction,
            "supplier": {"name": "Partial Supplier", "id": "sup_partial"}
        }
    }

    mocker.patch.object(
        extend._api_client,
        'patch',
        return_value=mock_response
    )

    response = await extend.transactions.update_transaction_expense_data(
        transaction_id=mock_transaction["id"],
        data={
            "supplier": {"name": "Partial Supplier", "id": "sup_partial"},
        }
    )

    assert response["transaction"]["supplier"]["name"] == "Partial Supplier"
    assert "customer" not in response["transaction"] or response["transaction"]["customer"] is None


@pytest.mark.asyncio
async def test_update_transaction_expense_data_error_handling(extend, mocker, mock_transaction):
    error_response = mocker.Mock()
    error_response.status_code = 400

    async def mock_error_patch(*args, **kwargs):
        raise httpx.HTTPStatusError(
            message="Bad Request",
            request=mocker.Mock(),
            response=error_response
        )

    mocker.patch.object(extend._api_client, 'patch', side_effect=mock_error_patch)

    with pytest.raises(httpx.HTTPStatusError):
        await extend.transactions.update_transaction_expense_data(
            transaction_id=mock_transaction["id"],
            data={"supplier": {"name": "Invalid", "id": None}}
        )


@pytest.mark.asyncio
async def test_get_expense_categories(extend, mocker):
    mock_response: Any = {
        "expenseCategories": [
            {"id": "cat_1", "name": "Category 1"},
            {"id": "cat_2", "name": "Category 2"}
        ]
    }

    mocker.patch.object(extend._api_client, 'get', return_value=mock_response)

    response = await extend.expense_data.get_expense_categories(active=True, required=False, search="cat")
    assert len(response["expenseCategories"]) == 2
    assert response["expenseCategories"][0]["name"] == "Category 1"


@pytest.mark.asyncio
async def test_get_expense_category(extend, mocker):
    mock_response: Any = {
        "id": "cat_123",
        "name": "Test Category"
    }

    mocker.patch.object(extend._api_client, 'get', return_value=mock_response)

    response = await extend.expense_data.get_expense_category("cat_123")
    assert response["id"] == "cat_123"
    assert response["name"] == "Test Category"


@pytest.mark.asyncio
async def test_get_expense_category_labels(extend, mocker):
    mock_response: Any = {
        "expenseLabels": [
            {"id": "lbl_1", "name": "Label 1"},
            {"id": "lbl_2", "name": "Label 2"}
        ],
        "pagination": {"page": 1, "pageItemCount": 2}
    }

    mocker.patch.object(extend._api_client, 'get', return_value=mock_response)

    response = await extend.expense_data.get_expense_category_labels(
        category_id="cat_123",
        page=1,
        per_page=10,
        active=True,
        search="Label"
    )

    assert "expenseLabels" in response
    assert len(response["expenseLabels"]) == 2
    assert response["expenseLabels"][0]["name"] == "Label 1"


@pytest.mark.asyncio
async def test_create_expense_category(extend, mocker):
    mock_response: Any = {
        "id": "cat_new",
        "name": "New Category"
    }

    mocker.patch.object(extend._api_client, 'post', return_value=mock_response)

    response = await extend.expense_data.create_expense_category(
        name="New Category",
        code="NEWCODE",
        required=True,
        active=True,
        free_text_allowed=True,
        integrator_enabled=True,
        integrator_field_number=42
    )

    assert response["id"] == "cat_new"
    assert response["name"] == "New Category"


@pytest.mark.asyncio
async def test_create_expense_category_label(extend, mocker):
    mock_response: Any = {
        "id": "label_new",
        "name": "New Label"
    }

    mocker.patch.object(extend._api_client, 'post', return_value=mock_response)

    response = await extend.expense_data.create_expense_category_label(
        category_id="cat_123",
        name="New Label",
        code="LBL123",
        active=True
    )

    assert response["id"] == "label_new"
    assert response["name"] == "New Label"


@pytest.mark.asyncio
async def test_update_expense_category(extend, mocker):
    mock_response: Any = {
        "id": "cat_123",
        "name": "Updated Category",
        "active": False
    }

    mocker.patch.object(extend._api_client, 'patch', return_value=mock_response)

    response = await extend.expense_data.update_expense_category(
        category_id="cat_123",
        name="Updated Category",
        active=False
    )

    assert response["name"] == "Updated Category"
    assert response["active"] is False


@pytest.mark.asyncio
async def test_update_expense_category_label(extend, mocker):
    mock_response: Any = {
        "id": "lbl_123",
        "name": "Updated Label",
        "active": True
    }

    mocker.patch.object(extend._api_client, 'patch', return_value=mock_response)

    response = await extend.expense_data.update_expense_category_label(
        category_id="cat_123",
        label_id="lbl_123",
        name="Updated Label",
        active=True
    )

    assert response["name"] == "Updated Label"
    assert response["active"] is True
