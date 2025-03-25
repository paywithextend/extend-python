from typing import Dict, Optional

from extend.client import APIClient
from .resource import Resource


class CreditCards(Resource):
    @property
    def _base_url(self) -> str:
        return "/creditcards"

    def __init__(self, api_client: APIClient):
        super().__init__(api_client)

    async def get_credit_cards(
            self,
            page: Optional[int] = None,
            page_size: Optional[int] = None,
            status: Optional[str] = None,
    ) -> Dict:
        """Get a list of all credit cards associated with your account.

        Args:
            page (Optional[int]): The page number for pagination (1-based)
            page_size (Optional[int]): Number of items per page
            status (Optional[str]): Filter cards by status (e.g., "ACTIVE", "CANCELLED")

        Returns:
            Dict: A dictionary containing the list of credit cards and pagination info

        Raises:
            httpx.HTTPError: If the request fails
        """

        params = {}
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["count"] = page_size
        if status:
            params["statuses"] = status

        return await self._request(method="get", params=params)
