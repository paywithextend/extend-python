from typing import Dict, Optional

from extend.client import APIClient
from .resource import Resource
from ..models import CreditCardStatus


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
            sort_direction: Optional[str] = None,
    ) -> Dict:
        """Get a list of all credit cards associated with your account.

        Args:
            page (Optional[int]): The page number for pagination (1-based)
            per_page (Optional[int]): Number of items per page
            status (Optional[str]): Filter cards by status (e.g., "ACTIVE", "CANCELLED")
            search_term (Optional[str]): Filter cards by search term (e.g., "Marketing")
            sort_direction (Optional[str]): Direction to sort (ASC or DESC)

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

        if status and not CreditCardStatus.is_valid(status.upper()):
            raise ValueError(f"{status} is not a valid status")

        params = {
            "page": page,
            "count": per_page,
            "statuses": status.upper() if status else None,
            "search": search_term,
            "sortDirection": sort_direction,
        }

        return await self._request(method="get", params=params)

    async def get_credit_card_detail(
            self,
            card_id: str
    ) -> Dict:
        """Get detailed information about a specific credit card.

        Args:
            card_id (str): The unique identifier of the credit card

        Returns:
            Dict: A dictionary containing the credit card details:

        Raises:
            httpx.HTTPError: If the request fails
        """

        return await self._request(method="get", path=f"/{card_id}")
