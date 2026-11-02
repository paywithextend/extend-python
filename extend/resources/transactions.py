from typing import Dict, Optional, Sequence

from extend.client import APIClient

from ..filters import transaction_query
from ..validations import pagination, resource_id
from .resource import Resource


class Transactions(Resource):
    @property
    def _base_url(self) -> str:
        return "/transactions"

    def __init__(self, api_client: APIClient):
        super().__init__(api_client)

    async def get_transactions(
            self,
            page: Optional[int] = None,
            per_page: Optional[int] = None,
            from_date: Optional[str] = None,
            to_date: Optional[str] = None,
            status: Optional[Sequence[str]] = None,
            virtual_card_id: Optional[str] = None,
            min_amount_cents: Optional[int] = None,
            max_amount_cents: Optional[int] = None,
            receipt_missing: Optional[bool] = None,
            search_term: Optional[str] = None,
            sort_field: Optional[str] = None,
            missing_expense_categories: Optional[bool] = None,
            *,
            statuses: Optional[Sequence[str]] = None,
            receipt_statuses: Optional[Sequence[str]] = None,
            expense_category_statuses: Optional[Sequence[str]] = None,
            credit_card_id: Optional[str] = None,
            date_type: str = "Transaction",
    ) -> Dict:
        """Get a list of transactions with optional filtering and pagination.

        Args:
            page (Optional[int]): The page number for pagination (1-based)
            per_page (Optional[int]): Number of items per page
            from_date (Optional[str]): Start date in YYYY-MM-DD format
            to_date (Optional[str]): End date in YYYY-MM-DD format
            status (Optional[Sequence[str]]): Filter transactions by one or more statuses (e.g., "PENDING", "CLEARED", "DECLINED", "NO_MATCH", "AVS_PASS", "AVS_FAIL", "AUTH_REVERSAL").
            virtual_card_id (str): Filter by specific virtual card
            min_amount_cents (int): Minimum clearing amount in cents
            max_amount_cents (int): Maximum clearing amount in cents
            search_term (Optional[str]): Filter transactions by search term (e.g., "Subscription")
            receipt_missing (Optional[bool]): Filter transactions by missing receipts
            sort_field (Optional[str]): Field to sort by, with optional direction
                                    Use "recipientName", "merchantName", "amount", "date" for ASC
                                    Use "-recipientName", "-merchantName", "-amount", "-date" for DESC
            missing_expense_categories (Optional[bool]): Filter transactions that are missing required expense categories

        Returns:
            Dict: The report envelope with page, perPage, count and transactions.
                A full page's count is a continuation sentinel, not an exact total.
                Use count_transactions for an explicit exact count.

        Raises:
            httpx.HTTPError: If the request fails
        """

        pagination(page, per_page, first_page=1)
        params = transaction_query(
            from_date=from_date, to_date=to_date, status=status, statuses=statuses,
            virtual_card_id=virtual_card_id, credit_card_id=credit_card_id,
            min_amount_cents=min_amount_cents, max_amount_cents=max_amount_cents,
            receipt_missing=receipt_missing, receipt_statuses=receipt_statuses,
            missing_expense_categories=missing_expense_categories,
            expense_category_statuses=expense_category_statuses,
            search_term=search_term, sort_field=sort_field, date_type=date_type,
        )
        params.update(page=page, perPage=per_page)
        return await self._request("get", params=params, base_url_override="/reports/transactions/v2")

    async def count_transactions(self, **filters) -> Dict:
        """Return {count: int} using the same filters as get_transactions, without pagination."""
        return await self._request(
            "get", params=transaction_query(**filters), base_url_override="/reports/transactions/count"
        )

    async def get_transaction(self, transaction_id: str) -> Dict:
        """Get detailed information about a specific transaction.

        Args:
            transaction_id (str): The unique identifier of the transaction

        Returns:
            Dict: A dictionary containing the transaction details

        Raises:
            httpx.HTTPError: If the request fails or transaction not found
        """
        return await self._request(method="get", path=f"/{resource_id(transaction_id)}")

    async def update_transaction_expense_data(self, transaction_id: str, data: Dict) -> Dict:
        """Update the expense data for a specific transaction.

        Args:
            transaction_id (str): The unique identifier of the transaction
            data (Dict): A dictionary representing the expense data to update, should match
                         the schema:
                         {
                             "expenseDetails": [
                                 {
                                     "categoryId": "ec_1234",
                                     "labelId": "ecl_1234"
                                 }
                             ],
                         }

        Returns:
            Dict: A dictionary containing the updated transaction details

        Raises:
            httpx.HTTPError: If the request fails or the transaction is not found
        """
        return await self._request(
            method="patch",
            path=f"/{resource_id(transaction_id)}/expensedata",
            params=data
        )

    async def send_receipt_reminder(self, transaction_id: str) -> None:
        """Send a transaction-specific receipt reminder.

        Args:
            transaction_id (str): The unique identifier of the transaction.

        Returns:
            None

        Raises:
            httpx.HTTPError: If the request fails.
        """
        return await self._request(
            method="post",
            path=f"/{resource_id(transaction_id)}/receiptreminder"
        )
