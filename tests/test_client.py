import pytest
from datetime import datetime, timedelta
from extend_api import ExtendAPI, VirtualCard, Transaction, RecurrenceConfig, ApiResponse
import httpx
import os

@pytest.fixture(scope="session")
def api_client():
    # Initialize the API client
    return ExtendAPI(os.getenv("EXTEND_API_KEY"), os.getenv("EXTEND_API_SECRET"))

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
def test_validate_card_creation_data(api_client):
    # Test valid data
    valid_data = api_client._validate_card_creation_data(
        creditCardId="card123",
        displayName="Test Card",
        balanceCents=1000
    )
    assert valid_data["creditCardId"] == "card123"
    assert valid_data["displayName"] == "Test Card"
    assert valid_data["balanceCents"] == 1000

    # Test invalid balance
    with pytest.raises(ValueError, match="Balance must be greater than 0"):
        api_client._validate_card_creation_data(
            creditCardId="card123",
            displayName="Test Card",
            balanceCents=0
        )

    # Test invalid email
    with pytest.raises(ValueError, match="Invalid email format"):
        api_client._validate_card_creation_data(
            creditCardId="card123",
            displayName="Test Card",
            balanceCents=1000,
            recipientEmail="invalid-email"
        )

    # Test valid dates
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    valid_data = api_client._validate_card_creation_data(
        creditCardId="card123",
        displayName="Test Card",
        balanceCents=1000,
        validFrom=tomorrow,
        validTo=next_week
    )
    assert "validFrom" in valid_data
    assert "validTo" in valid_data

def test_validate_recurrence_data(api_client):
    # Test valid daily recurrence
    valid_data = api_client._validate_recurrence_data(
        balanceCents=1000,
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
    valid_data = api_client._validate_recurrence_data(
        balanceCents=1000,
        period="WEEKLY",
        interval=1,
        terminator="NONE",
        byWeekDay=1
    )
    assert valid_data["byWeekDay"] == 1

    # Test invalid period
    with pytest.raises(ValueError, match="Period must be one of"):
        api_client._validate_recurrence_data(
            balanceCents=1000,
            period="INVALID",
            interval=1,
            terminator="NONE"
        )

    # Test missing required fields for weekly
    with pytest.raises(ValueError, match="byWeekDay is required for WEEKLY period"):
        api_client._validate_recurrence_data(
            balanceCents=1000,
            period="WEEKLY",
            interval=1,
            terminator="NONE"
        )

# Test API methods with mocked responses
@pytest.mark.asyncio
async def test_create_virtual_card(api_client, mocker, mock_virtual_card):
    mock_response: ApiResponse = {
        "virtualCard": mock_virtual_card
    }
    
    mocker.patch.object(api_client, 'post', return_value=mock_response)

    response = await api_client.create_virtual_card(
        creditCardId="card123",
        displayName="Test Card",
        balanceCents=1000
    )
    
    assert response["virtualCard"]["id"] == "vc_123"
    assert response["virtualCard"]["displayName"] == "Test Card"

@pytest.mark.asyncio
async def test_get_virtual_cards(api_client, mocker, mock_virtual_card):
    mock_response = {"virtualCards": [mock_virtual_card, mock_virtual_card]}
    
    # Create a simple async mock that returns the response
    async def mock_get(*args, **kwargs):
        return mock_response
    
    # Patch the get method with our async function
    mocker.patch.object(api_client, 'get', new=mock_get)
    
    # The get_virtual_cards method needs to await the get call
    response = await api_client.get_virtual_cards()
    assert len(response["virtualCards"]) == 2

# Test formatting helpers
def test_format_virtual_card_details(api_client, mock_virtual_card):
    mock_response: ApiResponse = {
        "virtualCard": mock_virtual_card
    }
    
    formatted = api_client.format_virtual_card_details(mock_response)
    assert "Test Card" in formatted
    assert "ACTIVE" in formatted
    assert "$10.00" in formatted  # 1000 cents = $10.00

def test_validate_card_data():
    # Test valid data
    data = ExtendAPI.validate_card_data(
        creditCardId="card123",
        displayName="Test Card",
        balanceCents=1000
    )
    assert data["creditCardId"] == "card123"
    assert data["displayName"] == "Test Card"
    assert data["balanceCents"] == 1000

    # Test invalid balance
    with pytest.raises(ValueError, match="Balance must be greater than 0"):
        ExtendAPI.validate_card_data(
            creditCardId="card123",
            displayName="Test Card",
            balanceCents=0
        )

# Additional API method tests
@pytest.mark.asyncio
async def test_update_virtual_card(api_client, mocker, mock_virtual_card):
    mock_response: ApiResponse = {
        "virtualCard": mock_virtual_card
    }
    
    mocker.patch.object(api_client, 'put', return_value=mock_response)

    response = await api_client.update_virtual_card(
        cardId="vc_123",
        displayName="Updated Card",
        balanceCents=2000
    )
    
    assert response["virtualCard"]["id"] == "vc_123"

@pytest.mark.asyncio
async def test_cancel_and_close_virtual_card(api_client, mocker, mock_virtual_card):
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
        api_client, 
        'put', 
        return_value=mock_cancel_response
    )

    # Test cancel
    response = await api_client.cancel_virtual_card("vc_123")
    assert response["virtualCard"]["status"] == "CANCELLED"

    # Update mock for close
    mocker.patch.object(
        api_client, 
        'put', 
        return_value=mock_close_response
    )

    # Test close
    response = await api_client.close_virtual_card("vc_123")
    assert response["virtualCard"]["status"] == "CLOSED"

@pytest.mark.asyncio
async def test_get_transactions(api_client, mocker, mock_transaction):
    mock_response: ApiResponse = {
        "transactions": [mock_transaction, mock_transaction]
    }
    
    mocker.patch.object(api_client, 'get', return_value=mock_response)

    response = await api_client.get_transactions()
    assert len(response["transactions"]) == 2

# Additional recurrence validation tests
def test_validate_recurrence_data_monthly(api_client):
    # Test valid monthly recurrence
    valid_data = api_client._validate_recurrence_data(
        balanceCents=1000,
        period="MONTHLY",
        interval=1,
        terminator="NONE",
        byMonthDay=15
    )
    assert valid_data["byMonthDay"] == 15

    # Test invalid month day
    with pytest.raises(ValueError, match="byMonthDay must be between 1 and 31"):
        api_client._validate_recurrence_data(
            balanceCents=1000,
            period="MONTHLY",
            interval=1,
            terminator="NONE",
            byMonthDay=32
        )

    # Test invalid month day (29th in February)
    with pytest.raises(ValueError, match="Choose a day between 1 and 28"):
        api_client._validate_recurrence_data(
            balanceCents=1000,
            period="MONTHLY",
            interval=1,
            terminator="NONE",
            byMonthDay=31
        )

def test_validate_recurrence_data_yearly(api_client):
    # Test valid yearly recurrence
    valid_data = api_client._validate_recurrence_data(
        balanceCents=1000,
        period="YEARLY",
        interval=1,
        terminator="NONE",
        byYearDay=100
    )
    assert valid_data["byYearDay"] == 100

    # Test invalid year day
    with pytest.raises(ValueError, match="byYearDay must be between 1 and 365"):
        api_client._validate_recurrence_data(
            balanceCents=1000,
            period="YEARLY",
            interval=1,
            terminator="NONE",
            byYearDay=366
        )

def test_validate_recurrence_terminator(api_client):
    # Test COUNT terminator
    valid_data = api_client._validate_recurrence_data(
        balanceCents=1000,
        period="DAILY",
        interval=1,
        terminator="COUNT",
        count=5
    )
    assert valid_data["count"] == 5

    # Test DATE terminator
    next_month = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    valid_data = api_client._validate_recurrence_data(
        balanceCents=1000,
        period="DAILY",
        interval=1,
        terminator="DATE",
        until=next_month
    )
    assert "until" in valid_data

    # Test missing count for COUNT terminator
    with pytest.raises(ValueError, match="Count is required"):
        api_client._validate_recurrence_data(
            balanceCents=1000,
            period="DAILY",
            interval=1,
            terminator="COUNT"
        )

    # Test missing until for DATE terminator
    with pytest.raises(ValueError, match="Until date is required"):
        api_client._validate_recurrence_data(
            balanceCents=1000,
            period="DAILY",
            interval=1,
            terminator="DATE"
        )

# Test transaction formatting
def test_format_transaction_details(api_client, mock_transaction):
    mock_response: ApiResponse = {
        "transaction": mock_transaction
    }
    
    formatted = api_client.format_transaction_details(mock_response)
    assert "Test Merchant" in formatted
    assert "CLEARED" in formatted
    assert "$10.00" in formatted

# Test HTTP error handling
@pytest.mark.asyncio
async def test_http_error_handling(api_client, mocker):
    # Test 400 error
    error_response = mocker.Mock()
    error_response.status_code = 400
    
    async def mock_error_get(*args, **kwargs):
        raise httpx.HTTPStatusError(
            "Bad Request",
            request=mocker.Mock(),
            response=error_response
        )
    
    mocker.patch.object(api_client, 'get', side_effect=mock_error_get)
    
    with pytest.raises(httpx.HTTPStatusError):
        await api_client.get_virtual_cards()

    # Test network error
    async def mock_network_get(*args, **kwargs):
        raise httpx.NetworkError("Connection failed")
    
    mocker.patch.object(api_client, 'get', side_effect=mock_network_get)
    
    with pytest.raises(httpx.NetworkError):
        await api_client.get_virtual_cards()
