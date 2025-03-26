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
            per_page: Optional[int] = None,
            status: Optional[str] = None,
            search_term: Optional[str] = None,
    ) -> Dict:
        """Get a list of all credit cards associated with your account.

        Args:
            page (Optional[int]): The page number for pagination (1-based)
            per_page (Optional[int]): Number of items per page
            status (Optional[str]): Filter cards by status (e.g., "ACTIVE", "CANCELLED")
            search_term (Optional[str]): Filter cards by search term (e.g., "Marketing")

        Returns:
            Dict: A dictionary containing:
                - creditCards: List of creditCard objects
                - pagination: Dictionary containing the following pagination stats:
                    - page: Current page number
                    - pageItemCount: Number of items per page
                    - totalItems: Total number of credit cards across all pages
                    - numberOfPages: Total number of pages

        Raises:
            httpx.HTTPError: If the request fails
        """

        params = {
            "page": page,
            "count": per_page,
            "statuses": status,
            "search": search_term,
        }
        params = {k: v for k, v in params.items() if v is not None}

        return await self._request(method="get", params=params)
