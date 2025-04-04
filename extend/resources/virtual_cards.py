from typing import Optional, Dict

from extend.client import APIClient
from extend.models import CardCreationRequest, VirtualCardStatus
from extend.validations import validate_card_creation_data, validate_card_update_data
from .resource import Resource


class VirtualCards(Resource):
    @property
    def _base_url(self) -> str:
        return "/virtualcards"

    def __init__(self, api_client: APIClient):
        super().__init__(api_client)

    async def get_virtual_cards(
            self,
            page: Optional[int] = None,
            per_page: Optional[int] = None,
            status: Optional[str] = None,
            recipient: Optional[str] = None,
            search_term: Optional[str] = None,
            sort_field: Optional[str] = None,
            sort_direction: Optional[str] = None,
    ) -> Dict:
        """Get a list of virtual cards with optional filtering and pagination.

        Args:
            page (Optional[int]): The page number for pagination (1-based)
            per_page (Optional[int]): Number of items per page
            status (Optional[str]): Filter cards by status (e.g., "ACTIVE", "CANCELLED", "PENDING", "EXPIRED", "CLOSED", "CONSUMED")
            recipient (Optional[str]): Filter cards by recipient id (e.g., "u_1234")
            search_term (Optional[str]): Filter cards by search term (e.g., "Marketing")
            sort_field (Optional[str]): Field to sort by "createdAt", "updatedAt", "balanceCents", "displayName", "type", or "status"
            sort_direction (Optional[str]): Direction to sort (ASC or DESC)

        Returns:
            Dict: A dictionary containing:
                - virtualCards: List of VirtualCard objects
                - pagination: Dictionary containing the following pagination stats:
                    - page: Current page number
                    - pageItemCount: Number of items per page
                    - totalItems: Total number of virtual cards across all pages
                    - numberOfPages: Total number of pages

        Raises:
            httpx.HTTPError: If the request fails
        """

        if status and not VirtualCardStatus.is_valid(status.upper()):
            raise ValueError(f"{status} is not a valid status")

        params = {
            "page": page,
            "count": per_page,
            "statuses": status.upper() if status else None,
            "recipient": recipient,
            "search": search_term,
            "sortField": sort_field,
            "sortDirection": sort_direction,
        }

        return await self._request(method="get", params=params)

    async def get_virtual_card_detail(self, card_id: str) -> Dict:
        """Get detailed information about a specific virtual card.

        Args:
            card_id (str): The unique identifier of the virtual card

        Returns:
            Dict: A dictionary containing the virtual card details

        Raises:
            httpx.HTTPError: If the request fails or card not found
        """
        return await self._request(method="get", path=f"/{card_id}")

    async def create_virtual_card(
            self,
            credit_card_id: str,
            display_name: str,
            balance_cents: int,
            notes: Optional[str] = None,
            recurs: Optional[bool] = None,
            recurrence: Optional[Dict] = None,
            recipient: Optional[str] = None,
            cardholder: Optional[str] = None,
            valid_to: Optional[str] = None,
    ) -> Dict:
        """Create a new virtual card.

        Args:
            credit_card_id (str): ID of the parent credit card
            display_name (str): Name to display for the virtual card
            balance_cents (int): Initial balance in cents
            notes (Optional[str]): Additional notes about the card
            recurs (Optional[bool]): Whether this is a recurring card
            recurrence (Optional[Dict]): Recurrence configuration if recurs is True
            recipient (Optional[str]): Email of the card recipient
            cardholder (Optional[str]): Email of the cardholder
            valid_to (Optional[str]): Expiration date in YYYY-MM-DD format

        Returns:
            Dict: The created virtual card details

        Raises:
            ValueError: If required fields are missing or invalid
            httpx.HTTPError: If the request fails

        Example:
            ```python
            card = await client.create_virtual_card(
                credit_card_id="cc_123",
                display_name="Marketing Card",
                balance_cents=10000,  # $100.00
                recipient="marketing@company.com",
                valid_to="2024-12-31"
            )
            ```
        """
        # Use the helper validation method for basic card data
        card_data: CardCreationRequest = validate_card_creation_data(
            credit_card_id=credit_card_id,
            display_name=display_name,
            balance_cents=balance_cents,
            recipient_email=recipient,
            valid_to=valid_to,
            notes=notes,
            recurs=recurs,
            recurrence=recurrence
        )

        # Add cardholder if provided
        if cardholder:
            card_data["cardholder"] = cardholder

        # Set recurs flag if provided
        if recurs is not None:
            card_data["recurs"] = recurs

        print(f"Creating virtual card with data: {card_data}")  # Debug log
        return await self._request(method="post", params=card_data)

    async def update_virtual_card(
            self,
            card_id: str,
            display_name: str,
            balance_cents: int,
            notes: Optional[str] = None,
            valid_from: Optional[str] = None,
            valid_to: Optional[str] = None
    ) -> Dict:
        """Update an existing virtual card.

        Args:
            card_id (str): ID of the virtual card to update.
            balance_cents (int): New balance in cents.
            display_name (Optional[str]): New display name.
            notes (Optional[str]): New notes.
            valid_from (Optional[str]): New start date in YYYY-MM-DD format.
            valid_to (Optional[str]): New expiration date in YYYY-MM-DD format.

        Returns:
            Dict: The updated virtual card details.

        Raises:
            ValueError: If date formats are invalid or validTo is before validFrom.
            httpx.HTTPError: If the request fails or card not found.

        Example:
            ```python
            updated = await client.update_virtual_card(
                card_id="vc_123",
                balance_cents=5000,  # $50.00
                display_name="Updated Name",
                valid_to="2024-12-31"
            )
            ```
        """
        update_data = validate_card_update_data(
            balance_cents=balance_cents,
            display_name=display_name,
            notes=notes,
            valid_from=valid_from,
            valid_to=valid_to
        )

        return await self._request("put", f"/{card_id}", update_data)

    async def cancel_virtual_card(self, card_id: str) -> Dict:
        """Cancel a virtual card, preventing further transactions.

        Args:
            card_id (str): ID of the virtual card to cancel

        Returns:
            Dict: The updated virtual card details

        Raises:
            httpx.HTTPError: If the request fails or card not found
        """
        return await self._request("put", f"/{card_id}/cancel")

    async def close_virtual_card(self, card_id: str) -> Dict:
        """Permanently close a virtual card.

        This action cannot be undone. The card will be permanently disabled
        and cannot be reactivated.

        Args:
            card_id (str): ID of the virtual card to close

        Returns:
            Dict: The updated virtual card details

        Raises:
            httpx.HTTPError: If the request fails or card not found
        """
        return await self._request("put", f"/{card_id}/close")
