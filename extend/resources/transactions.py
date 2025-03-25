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
            from_date: Optional[str] = None,
            to_date: Optional[str] = None,
            page: Optional[int] = None,
            page_size: Optional[int] = None,
    ) -> Dict:
        """Get a list of transactions with optional filtering and pagination.

        Args:
            from_date (Optional[str]): Start date in YYYY-MM-DD format
            to_date (Optional[str]): End date in YYYY-MM-DD format
            page (Optional[int]): The page number for pagination (1-based)
            page_size (Optional[int]): Number of items per page

        Returns:
            Dict: A dictionary containing:
                - transactions: List of Transaction objects
                - total: Total number of transactions
                - page: Current page number
                - pageSize: Number of items per page

        Raises:
            httpx.HTTPError: If the request fails
        """
        params = {}
        if from_date:
            params["fromDate"] = from_date
        if to_date:
            params["toDate"] = to_date
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["count"] = page_size

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
