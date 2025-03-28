import os
import uuid
from datetime import datetime, timedelta

import pytest
from dotenv import load_dotenv

from extend import ExtendClient

load_dotenv()

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
def extend():
    """Create a real API client for integration testing"""
    api_key = os.getenv("EXTEND_API_KEY")
    api_secret = os.getenv("EXTEND_API_SECRET")
    return ExtendClient(api_key, api_secret)


@pytest.fixture(scope="session")
def test_recipient():
    """Get the test recipient email"""
    return os.getenv("EXTEND_TEST_RECIPIENT")


@pytest.fixture(scope="session")
def test_cardholder():
    """Get the test cardholder email"""
    return os.getenv("EXTEND_TEST_CARDHOLDER")


@pytest.fixture(scope="session")
async def test_credit_card(extend):
    """Get the first active credit card for testing"""
    response = await extend.credit_cards.get_credit_cards(status="ACTIVE")
    assert response.get("creditCards"), "No credit cards available for testing"
    return response["creditCards"][0]


@pytest.mark.integration
class TestVirtualCards:
    """Integration tests for virtual card operations"""

    @pytest.mark.asyncio
    async def test_virtual_card_lifecycle(self, extend, test_credit_card, test_recipient, test_cardholder):
        """Test creating, retrieving, updating, and canceling a virtual card"""
        # Calculate valid_to date (3 months from today)
        valid_to = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%dT23:59:59.999Z")

        # Create a simple virtual card without recurrence
        response = await extend.virtual_cards.create_virtual_card(
            credit_card_id=test_credit_card["id"],
            display_name="Integration Test Card",
            balance_cents=100,
            notes="Created by integration test",
            recurs=False,  # Explicitly set to false for non-recurring card
            recipient=test_recipient,
            cardholder=test_cardholder,
            valid_to=valid_to
        )

        card = response["virtualCard"]
        assert card["status"] == "ACTIVE"
        assert card["displayName"] == "Integration Test Card"
        assert card["balanceCents"] == 100
        assert card["recurs"] is False
        assert card["notes"] == "Created by integration test"

        # Store card ID for subsequent tests
        card_id = card["id"]

        # Get the card details
        get_response = await extend.virtual_cards.get_virtual_card_detail(card_id)
        assert get_response["virtualCard"]["id"] == card_id

        # Update the card
        update_response = await extend.virtual_cards.update_virtual_card(
            card_id=card_id,
            display_name="Updated Test Card",
            notes="Updated by integration test",
            balance_cents=200
        )

        updated_card = update_response["virtualCard"]
        assert updated_card["status"] == "ACTIVE"
        assert updated_card["displayName"] == "Updated Test Card"
        assert updated_card["balanceCents"] == 200
        assert updated_card["notes"] == "Updated by integration test"

        # Cancel the card
        cancel_response = await extend.virtual_cards.cancel_virtual_card(card_id)
        assert cancel_response["virtualCard"]["status"] == "CANCELLED"

        # Close the card (cleanup)
        close_response = await extend.virtual_cards.close_virtual_card(card_id)
        assert close_response["virtualCard"]["status"] == "CLOSED"

    @pytest.mark.asyncio
    async def test_list_virtual_cards(self, extend):
        """Test listing virtual cards with various filters"""

        # List all cards
        response = await extend.virtual_cards.get_virtual_cards()
        assert "virtualCards" in response

        # List with pagination
        response = await extend.virtual_cards.get_virtual_cards(
            page=1,
            per_page=10
        )
        assert len(response["virtualCards"]) <= 10

        # List with status filter
        response = await extend.virtual_cards.get_virtual_cards(
            status="CLOSED"
        )
        for card in response["virtualCards"]:
            assert card["status"] == "CLOSED"


@pytest.mark.integration
class TestTransactions:
    """Integration tests for transaction operations"""

    @pytest.mark.asyncio
    async def test_list_transactions(self, extend):
        """Test listing transactions with various filters"""
        # Get transactions
        response = await extend.transactions.get_transactions()

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
    async def test_create_recurring_card(self, extend, test_credit_card, test_recipient, test_cardholder):
        """Test creating a daily recurring card"""
        next_month = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%dT23:59:59.999Z")

        # Create a daily recurring card
        response = await extend.virtual_cards.create_virtual_card(
            credit_card_id=test_credit_card["id"],
            display_name="Daily Recurring Test Card",
            balance_cents=100,
            notes="Created by integration test",
            recurs=True,
            recipient=test_recipient,
            cardholder=test_cardholder,
            recurrence={
                "balance_cents": 100,
                "period": "DAILY",
                "interval": 1,
                "terminator": "DATE",
                "until": next_month
            }
        )

        card = response["virtualCard"]
        assert card["status"] == "ACTIVE"
        assert card["displayName"] == "Daily Recurring Test Card"
        assert card["balanceCents"] == 100
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
        cancel_response = await extend.virtual_cards.cancel_virtual_card(card_id)
        assert cancel_response["virtualCard"]["status"] == "CANCELLED"

        close_response = await extend.virtual_cards.close_virtual_card(card_id)
        assert close_response["virtualCard"]["status"] == "CLOSED"


@pytest.mark.integration
class TestExpenseData:
    """Integration tests for expense category and label operations"""

    @pytest.mark.asyncio
    async def test_create_update_category_and_label(self, extend):
        # Create a new expense category
        u = uuid.uuid4()
        name = f"Integration Test Category {u}"
        code = f"INTEG-CAT-{u}"
        category_resp = await extend.expense_data.create_expense_category(
            name=name,
            code=code,
            required=True,
            active=True,
            free_text_allowed=False,
        )

        category_id = category_resp["id"]
        assert category_resp["name"] == name
        assert category_resp["code"] == code

        # re-fetch newly created expense category
        category = await extend.expense_data.get_expense_category(category_id)
        assert category_resp["name"] == name
        assert category_resp["code"] == code

        # Update the category
        updated_name = f"Updated Integration Category {u}"
        updated_category = await extend.expense_data.update_expense_category(
            category_id=category_id,
            name=updated_name,
            active=False
        )

        assert updated_category["name"] == updated_name
        assert updated_category["active"] is False

        # Create a label under the category
        u1 = uuid.uuid4()
        label_name_one = f"Integration Label {u1}"
        label_code_one = f"INTEG-LABEL-{u1}"
        u2 = uuid.uuid4()
        label_name_two = f"Integration Label {u2}"
        label_code_two = f"INTEG-LABEL-{u2}"

        label_resp_one = await extend.expense_data.create_expense_category_label(
            category_id=category_id,
            name=label_name_one,
            code=label_code_one,
            active=True
        )

        label_resp_two = await extend.expense_data.create_expense_category_label(
            category_id=category_id,
            name=label_name_two,
            code=label_code_two,
            active=True
        )

        label_id = label_resp_one["id"]
        assert label_resp_one["name"] == label_name_one
        assert label_resp_one["code"] == label_code_one

        # Update the label
        updated_label = await extend.expense_data.update_expense_category_label(
            category_id=category_id,
            label_id=label_id,
            name=f"Updated Label Name {u1}",
            active=False
        )

        assert updated_label["name"] == f"Updated Label Name {u1}"
        assert updated_label["active"] is False

    @pytest.mark.asyncio
    async def test_get_expense_categories_and_labels(self, extend):
        # List categories
        categories = await extend.expense_data.get_expense_categories(active=True)
        assert isinstance(categories, dict)
        assert "expenseCategories" in categories

        # If categories exist, fetch one and its labels
        if categories["expenseCategories"]:
            cat_id = categories["expenseCategories"][0]["id"]

            # Get single category
            category = await extend.expense_data.get_expense_category(cat_id)
            assert category["id"] == cat_id

            # List labels
            labels = await extend.expense_data.get_expense_category_labels(
                category_id=cat_id,
                page=1,
                per_page=10
            )
            assert isinstance(labels, dict)
            assert "expenseLabels" in labels


def test_environment_variables():
    """Test that required environment variables are set"""
    assert os.getenv("EXTEND_API_KEY"), "EXTEND_API_KEY environment variable is required"
    assert os.getenv("EXTEND_API_SECRET"), "EXTEND_API_SECRET environment variable is required"
