from typing import Optional, Dict

from extend.client import APIClient
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
            virtual_card_id: Optional[str] = None,
            min_amount_cents: Optional[int] = None,
            max_amount_cents: Optional[int] = None,
            search_term: Optional[str] = None,
    ) -> Dict:
        """Get a list of transactions with optional filtering and pagination.

        Args:
            page (Optional[int]): The page number for pagination (1-based)
            per_page (Optional[int]): Number of items per page
            from_date (Optional[str]): Start date in YYYY-MM-DD format
            to_date (Optional[str]): End date in YYYY-MM-DD format
            virtual_card_id (str): Filter by specific virtual card
            min_amount_cents (int): Minimum clearing amount in cents
            max_amount_cents (int): Maximum clearing amount in cents
            search_term (Optional[str]): Filter cards by search term (e.g., "Marketing")

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

        params = {
            "page": page,
            "count": per_page,
            "fromDate": from_date,
            "toDate": to_date,
            "virtualCardId": virtual_card_id,
            "minClearingBillingCents": min_amount_cents,
            "maxClearingBillingCents": max_amount_cents,
            "search": search_term,
        }
        params = {k: v for k, v in params.items() if v is not None}

        return await self._request(method="get", params=params)

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
