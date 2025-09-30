from typing import Optional, Dict, Sequence, List

from extend.client import APIClient
from .resource import Resource
from ..models import TransactionStatus


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
            Dict: A dictionary containing:
                - transactions: List of Transaction objects
                - pagination: Dictionary containing the following pagination stats:
                    - page: Current page number
                    - pageItemCount: Number of items per page
                    - totalItems: Total items will be 1 more than pageItemCount if there is another page to fetch
                    - numberOfPages: Total number of pages

        Raises:
            httpx.HTTPError: If the request fails
        """

        normalized_statuses: Optional[List[str]] = None
        if status:
            status_values = [status] if isinstance(status, str) else list(status)
            normalized_statuses = []
            invalid_statuses = []
            for status_value in status_values:
                normalized_value = status_value.upper()
                if TransactionStatus.is_valid(normalized_value):
                    normalized_statuses.append(normalized_value)
                else:
                    invalid_statuses.append(status_value)
            if invalid_statuses:
                invalid_list = ", ".join(invalid_statuses)
                raise ValueError(f"{invalid_list} is not a valid status")
            if not normalized_statuses:
                normalized_statuses = None

        params = {
            "page": page,
            "perPage": per_page,
            "since": from_date,
            "until": to_date,
            "status": normalized_statuses,
            "virtualCardId": virtual_card_id,
            "minClearingBillingCents": min_amount_cents,
            "maxClearingBillingCents": max_amount_cents,
            "receiptMissing": receipt_missing,
            "receiptStatus": ["Missing"] if receipt_missing else None,
            "expenseCategoryStatuses": ["Missing"] if missing_expense_categories else None,
            "search": search_term,
            "sort": sort_field,
        }

        return await self._request(method="get", params=params, base_url_override='/reports/transactions/v2')

    async def get_transaction(self, transaction_id: str) -> Dict:
        """Get detailed information about a specific transaction.

        Args:
            transaction_id (str): The unique identifier of the transaction

        Returns:
            Dict: A dictionary containing the transaction details

        Raises:
            httpx.HTTPError: If the request fails or transaction not found
        """
        return await self._request(method="get", path=f"/{transaction_id}")

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
            path=f"/{transaction_id}/expensedata",
            params=data
        )

    async def send_receipt_reminder(self, transaction_id: str) -> Dict:
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
            path=f"/{transaction_id}/receiptreminder"
        )
