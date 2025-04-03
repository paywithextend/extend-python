import os
import uuid
from datetime import datetime, timedelta
from io import BytesIO

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

    @pytest.mark.asyncio
    async def test_list_virtual_cards_with_sorting(self, extend):
        """Test listing virtual cards with various sorting options"""

        # Test sorting by display name ascending
        asc_response = await extend.virtual_cards.get_virtual_cards(
            sort_field="displayName",
            sort_direction="ASC",
            per_page=50  # Ensure we get enough cards to compare
        )

        # Test sorting by display name descending
        desc_response = await extend.virtual_cards.get_virtual_cards(
            sort_field="displayName",
            sort_direction="DESC",
            per_page=50  # Ensure we get enough cards to compare
        )

        # Verify responses contain cards
        assert "virtualCards" in asc_response
        assert "virtualCards" in desc_response

        # If sufficient cards exist, just verify the orders are different
        # rather than trying to implement our own sorting logic
        if len(asc_response["virtualCards"]) > 1 and len(desc_response["virtualCards"]) > 1:
            asc_ids = [card["id"] for card in asc_response["virtualCards"]]
            desc_ids = [card["id"] for card in desc_response["virtualCards"]]

            # Verify the orders are different for different sort directions
            assert asc_ids != desc_ids, "ASC and DESC sorting should produce different results"

        # Test other sort fields
        for field in ["createdAt", "updatedAt", "balanceCents", "status", "type"]:
            # Test both directions for each field
            for direction in ["ASC", "DESC"]:
                response = await extend.virtual_cards.get_virtual_cards(
                    sort_field=field,
                    sort_direction=direction
                )
                assert "virtualCards" in response, f"Sorting by {field} {direction} should return virtual cards"


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
        assert "transactions" in response["report"], "Response should contain 'report' key"
        assert isinstance(response["report"]["transactions"], list), "Transactions should be a list"

        # If there are transactions, verify their structure
        if response["report"] and response["report"]['transactions']:
            transactions = response["report"]['transactions']
            transaction = transactions[0]
            required_fields = ["id", "status", "virtualCardId", "merchantName", "type", "authBillingAmountCents"]
            for field in required_fields:
                assert field in transaction, f"Transaction should contain '{field}' field"

    @pytest.mark.asyncio
    async def test_list_transactions_with_sorting(self, extend):
        """Test listing transactions with various sorting options"""

        # Define sort fields - positive for ASC, negative (prefixed with -) for DESC
        sort_fields = [
            "recipientName", "-recipientName",
            "merchantName", "-merchantName",
            "amount", "-amount",
            "date", "-date"
        ]

        # Test each sort field
        for sort_field in sort_fields:
            # Get transactions with this sort
            response = await extend.transactions.get_transactions(
                sort_field=sort_field,
                per_page=10
            )

            # Verify response contains transactions and basic structure
            assert isinstance(response, dict), f"Response for sort {sort_field} should be a dictionary"
            assert "report" in response, f"Response for sort {sort_field} should contain 'report' key"
            assert "transactions" in response["report"], f"Report should contain 'transactions' key"

            # If we have enough data, test opposite sort direction for comparison
            if len(response["report"]["transactions"]) > 1:
                # Determine the field name and opposite sort field
                is_desc = sort_field.startswith("-")
                field_name = sort_field[1:] if is_desc else sort_field
                opposite_sort = field_name if is_desc else f"-{field_name}"

                # Get transactions with opposite sort
                opposite_response = await extend.transactions.get_transactions(
                    sort_field=opposite_sort,
                    per_page=10
                )

                # Get IDs in both sort orders for comparison
                sorted_ids = [tx["id"] for tx in response["report"]["transactions"]]
                opposite_sorted_ids = [tx["id"] for tx in opposite_response["report"]["transactions"]]

                # If we have the same set of transactions in both responses,
                # verify that different sort directions produce different orders
                if set(sorted_ids) == set(opposite_sorted_ids) and len(sorted_ids) > 1:
                    assert sorted_ids != opposite_sorted_ids, (
                        f"Different sort directions for {field_name} should produce different results"
                    )


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


@pytest.mark.integration
class TestTransactionExpenseData:
    """Integration tests for updating transaction expense data using a specific expense category and label"""

    @pytest.mark.asyncio
    async def test_update_transaction_expense_data_with_specific_category_and_label(self, extend):
        """Test updating the expense data for a transaction using a specific expense category and label."""
        # Create a new expense category for testing
        u = uuid.uuid4()
        category_name = f"Integration Test Category {u}"
        category_code = f"INTEG-CAT-{u}"
        category_resp = await extend.expense_data.create_expense_category(
            name=category_name,
            code=category_code,
            required=True,
            active=True,
            free_text_allowed=False,
        )
        category_id = category_resp["id"]
        assert category_resp["name"] == category_name
        assert category_resp["code"] == category_code

        # Create a label under the category
        u1 = uuid.uuid4()
        label_name = f"Integration Label {u1}"
        label_code = f"INTEG-LABEL-{u1}"
        label_resp = await extend.expense_data.create_expense_category_label(
            category_id=category_id,
            name=label_name,
            code=label_code,
            active=True
        )
        label_id = label_resp["id"]
        assert label_resp["name"] == label_name
        assert label_resp["code"] == label_code

        # Retrieve at least one transaction to update expense data
        transactions_response = await extend.transactions.get_transactions(per_page=1)
        assert "report" in transactions_response, "Response should include 'report'"
        assert "transactions" in transactions_response["report"], "Response should include 'transactions'"
        assert transactions_response["report"]["transactions"], "No transactions available for testing expense data update"
        transaction = transactions_response["report"]["transactions"][0]
        transaction_id = transaction["id"]

        # Prepare the expense data payload with the specific category and label
        update_payload = {
            "expenseDetails": [
                {
                    "categoryId": category_id,
                    "labelId": label_id
                }
            ]
        }

        # Call the update_transaction_expense_data method
        response = await extend.transactions.update_transaction_expense_data(transaction_id, update_payload)

        # Verify the response contains the transaction id and expected expense details
        assert "id" in response, "Response should include the transaction id"
        assert "expenseDetails" in response, "Response should include expenseDetails"
        assert len(response["expenseDetails"]) == 1, "Response should contain exactly one expense detail"
        assert response["expenseDetails"][0]["categoryId"] == category_id, "Category ID should match"
        assert response["expenseDetails"][0]["labelId"] == label_id, "Label ID should match"


@pytest.mark.integration
class TestReceiptAttachments:
    """Integration tests for receipt attachment operations"""

    @pytest.mark.asyncio
    async def test_create_receipt_attachment(self, extend):
        """Test creating a receipt attachment via multipart upload."""
        # Create a dummy PNG file in memory
        # This is a minimal PNG header plus extra bytes to simulate file content.
        png_header = b'\x89PNG\r\n\x1a\n'
        dummy_content = png_header + b'\x00' * 100
        file_obj = BytesIO(dummy_content)
        # Optionally set a name attribute for file identification in the upload
        file_obj.name = f"test_receipt_{uuid.uuid4()}.png"

        # Retrieve a valid transaction id from existing transactions
        transactions_response = await extend.transactions.get_transactions(page=0, per_page=1)
        assert transactions_response["report"][
            "transactions"], "No transactions available for testing receipt attachment"
        transaction_id = transactions_response["report"]["transactions"][0]["id"]

        # Call the receipt attachment upload method
        response = await extend.receipt_attachments.create_receipt_attachment(
            transaction_id=transaction_id,
            file=file_obj
        )

        # Assert that the response contains expected keys
        assert "id" in response, "Receipt attachment should have an id"
        assert "urls" in response, "Receipt attachment should include urls"
        assert "contentType" in response, "Receipt attachment should include a content type"
        assert response["contentType"] == "image/png", "Content type should be 'image/png'"


def test_environment_variables():
    """Test that required environment variables are set"""
    assert os.getenv("EXTEND_API_KEY"), "EXTEND_API_KEY environment variable is required"
    assert os.getenv("EXTEND_API_SECRET"), "EXTEND_API_SECRET environment variable is required"
