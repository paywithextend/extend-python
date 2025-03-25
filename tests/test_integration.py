import pytest
import os
from datetime import datetime, timedelta
from extend_api import ExtendAPI

# Skip all tests if environment variables are not set
pytestmark = pytest.mark.skipif(
    not all([
        os.getenv("EXTEND_API_KEY"),
        os.getenv("EXTEND_API_SECRET"),
        os.getenv("EXTEND_TEST_RECIPIENT"),
        os.getenv("EXTEND_TEST_CARDHOLDER")
    ]),
    reason="Integration tests require EXTEND_API_KEY, EXTEND_API_SECRET, EXTEND_TEST_RECIPIENT, and EXTEND_TEST_CARDHOLDER environment variables"
)

@pytest.fixture(scope="session")
def api_client():
    """Create a real API client for integration testing"""
    api_key = os.getenv("EXTEND_API_KEY")
    api_secret = os.getenv("EXTEND_API_SECRET")
    return ExtendAPI(api_key, api_secret)

@pytest.fixture(scope="session")
def test_recipient():
    """Get the test recipient email"""
    return os.getenv("EXTEND_TEST_RECIPIENT")

@pytest.fixture(scope="session")
def test_cardholder():
    """Get the test cardholder email"""
    return os.getenv("EXTEND_TEST_CARDHOLDER")

@pytest.fixture(scope="session")
async def test_credit_card(api_client):
    """Get the first available credit card for testing"""
    response = await api_client.get_credit_cards()
    assert response.get("creditCards"), "No credit cards available for testing"
    return response["creditCards"][0]

@pytest.mark.integration
class TestVirtualCards:
    """Integration tests for virtual card operations"""
    
    @pytest.mark.asyncio
    async def test_virtual_card_lifecycle(self, api_client, test_credit_card, test_recipient, test_cardholder):
        """Test creating, retrieving, updating, and canceling a virtual card"""
        # Calculate valid_to date (3 months from today)
        valid_to = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%dT23:59:59.999Z")
        
        # Create a simple virtual card without recurrence
        response = await api_client.create_virtual_card(
            creditCardId=test_credit_card["id"],
            displayName="Integration Test Card",
            balanceCents=5000,
            notes="Created by integration test",
            recurs=False,  # Explicitly set to false for non-recurring card
            recipient=test_recipient,
            cardholder=test_cardholder,
            validTo=valid_to
        )
        
        card = response["virtualCard"]
        assert card["status"] == "ACTIVE"
        assert card["displayName"] == "Integration Test Card"
        assert card["balanceCents"] == 5000
        assert card["recurs"] is False
        assert card["notes"] == "Created by integration test"
        
        # Store card ID for subsequent tests
        card_id = card["id"]
        
        # Get the card details
        get_response = await api_client.get_virtual_card(card_id)
        assert get_response["virtualCard"]["id"] == card_id
        
        
        # Update the card
        update_response = await api_client.update_virtual_card(
            cardId=card_id,
            displayName="Updated Test Card",
            notes="Updated by integration test",
            balanceCents=6000  # Increase the balance
        )
        
        updated_card = update_response["virtualCard"]
        assert updated_card["status"] == "ACTIVE"
        assert updated_card["displayName"] == "Updated Test Card"
        assert updated_card["balanceCents"] == 6000
        assert updated_card["notes"] == "Updated by integration test"
        
        # Cancel the card
        cancel_response = await api_client.cancel_virtual_card(card_id)
        assert cancel_response["virtualCard"]["status"] == "CANCELLED"
        
        # Close the card (cleanup)
        close_response = await api_client.close_virtual_card(card_id)
        assert close_response["virtualCard"]["status"] == "CLOSED"

    @pytest.mark.asyncio
    async def test_list_virtual_cards(self, api_client):
        """Test listing virtual cards with various filters"""
        
        # List all cards
        response = await api_client.get_virtual_cards()
        assert "virtualCards" in response
        
        # List with pagination
        response = await api_client.get_virtual_cards(
            page=1,
            page_size=10
        )
        assert len(response["virtualCards"]) <= 10
        
        # List with status filter
        response = await api_client.get_virtual_cards(
            status="CLOSED"
        )
        for card in response["virtualCards"]:
            assert card["status"] == "CLOSED"

@pytest.mark.integration
class TestTransactions:
    """Integration tests for transaction operations"""
    
    @pytest.mark.asyncio
    async def test_list_transactions(self, api_client):
        """Test listing transactions with various filters"""
        # Get transactions
        response = await api_client.get_transactions()
        
        # Verify response structure
        assert isinstance(response, dict), "Response should be a dictionary"
        assert "transactions" in response, "Response should contain 'transactions' key"
        assert isinstance(response["transactions"], list), "Transactions should be a list"
        
        # If there are transactions, verify their structure
        if response["transactions"]:
            transaction = response["transactions"][0]
            required_fields = ["id", "status", "virtualCardId", "merchantName", "type", "authBillingAmountCents"]
            for field in required_fields:
                assert field in transaction, f"Transaction should contain '{field}' field"

@pytest.mark.integration
class TestRecurringCards:
    """Integration tests for recurring virtual cards"""
    
    @pytest.mark.asyncio
    async def test_create_recurring_card(self, api_client, test_credit_card, test_recipient, test_cardholder):
        """Test creating a daily recurring card"""
        next_month = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%dT23:59:59.999Z")
        
        # Create a daily recurring card
        response = await api_client.create_virtual_card(
            creditCardId=test_credit_card["id"],
            displayName="Daily Recurring Test Card",
            balanceCents=1000,
            notes="Created by integration test",
            recurs=True,
            recipient=test_recipient,
            cardholder=test_cardholder,
            recurrence={
                "balanceCents": 1000,
                "period": "DAILY",
                "interval": 1,
                "terminator": "DATE",
                "until": next_month
            }
        )
        
        card = response["virtualCard"]
        assert card["status"] == "ACTIVE"
        assert card["displayName"] == "Daily Recurring Test Card"
        assert card["balanceCents"] == 1000
        assert card["recurs"] is True
        assert card["recurrence"]["period"] == "DAILY"
        assert card["recurrence"]["interval"] == 1
        assert card["recurrence"]["terminator"] == "DATE"
        # Normalize timezone format before comparison
        expected_date = next_month.replace("Z", "+0000")
        assert card["recurrence"]["until"] == expected_date
        
        # Store card ID for cleanup
        card_id = card["id"]
        
        # Clean up by cancelling and closing
        cancel_response = await api_client.cancel_virtual_card(card_id)
        assert cancel_response["virtualCard"]["status"] == "CANCELLED"
        
        close_response = await api_client.close_virtual_card(card_id)
        assert close_response["virtualCard"]["status"] == "CLOSED"

def test_environment_variables():
    """Test that required environment variables are set"""
    assert os.getenv("EXTEND_API_KEY"), "EXTEND_API_KEY environment variable is required"
    assert os.getenv("EXTEND_API_SECRET"), "EXTEND_API_SECRET environment variable is required"