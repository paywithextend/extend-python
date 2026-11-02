from typing import Dict, Optional

from extend.client import APIClient

from ..validations import pagination, resource_id
from .resource import Resource


class ExpenseData(Resource):
    @property
    def _base_url(self) -> str:
        return "/expensedata"

    def __init__(self, api_client: APIClient):
        super().__init__(api_client)

    async def get_expense_categories(
            self,
            active: Optional[bool] = None,
            required: Optional[bool] = None,
            search: Optional[str] = None,
            sort_field: Optional[str] = None,
            sort_direction: Optional[str] = None,
            *,
            transaction_id: Optional[str] = None,
            required_for_transactions: Optional[bool] = None,
            required_for_virtual_cards: Optional[bool] = None,
    ) -> Dict:
        """Get a list of expense categories.

        Args:
            active (Optional[bool]): Show only active categories
            required (Optional[bool]): Show only required categories
            search (Optional[str]): Full-text search query for filtering categories
            sort_field (Optional[str]): Field to sort by
            sort_direction (Optional[str]): Direction of sorting ("asc" or "desc")

        Returns:
            Dict: A dictionary containing:
                - expenseCategories: List of Expense Category objects

        Raises:
            httpx.HTTPError: If the request fails
        """

        params = {
            "active": active,
            "required": required,
            "transactionId": resource_id(transaction_id) if transaction_id is not None else None,
            "requiredForTransactions": required_for_transactions,
            "requiredForVirtualCards": required_for_virtual_cards,
            "search": search,
            "sortField": sort_field,
            "sortDirection": sort_direction,
        }

        return await self._request(method="get", path="/categories", params=params)

    async def get_expense_category(self, category_id: str) -> Dict:
        """Get detailed information about a specific expense category.

        Args:
            category_id (str): The unique identifier of the expense category

        Returns:
            Dict: A dictionary containing the expense category details

        Raises:
            httpx.HTTPError: If the request fails or transaction not found
        """
        return await self._request(method="get", path=f"/categories/{resource_id(category_id)}")

    async def get_expense_category_labels(
            self,
            category_id: str,
            page: Optional[int] = None,
            per_page: Optional[int] = None,
            active: Optional[bool] = None,
            search: Optional[str] = None,
            sort_field: Optional[str] = None,
            sort_direction: Optional[str] = None,
    ) -> Dict:
        """Get a paginated list of expense categories.

        Args:
            category_id (str): The unique identifier of the expense category
            page (Optional[int]): The page number for pagination (0-based)
            per_page (Optional[int]): Number of items per page
            active (Optional[bool]): Show only active labels
            search (Optional[str]): Full-text search query
            sort_field (Optional[str]): Field to sort by (e.g., activeLabelNameAsc, name)
            sort_direction (Optional[str]): Sort direction (asc, desc) for sortable fields

        Returns:
            Dict: A dictionary containing:
                - expenseLabels: List of Expense Category Label objects
                - pagination: Dictionary containing the following pagination stats:
                    - page: Current page number
                    - pageItemCount: Number of items per page
                    - totalItems: Total number expense category labels across all pages
                    - numberOfPages: Total number of pages

        Raises:
            httpx.HTTPError: If the request fails
        """

        pagination(page, per_page)
        params = {
            "page": page,
            "count": per_page,
            "active": active,
            "search": search,
            "sortField": sort_field,
            "sortDirection": sort_direction,
        }

        return await self._request(method="get", path=f"/categories/{resource_id(category_id)}/labels", params=params)

    async def create_expense_category(
            self,
            name: str,
            code: str,
            required: bool = False,
            active: Optional[bool] = None,
            free_text_allowed: Optional[bool] = None,
            *,
            required_for_transactions: Optional[bool] = None,
            required_for_virtual_cards: Optional[bool] = None,
    ) -> Dict:
        """Create an expense category.

        Args:
            name (str): User-facing name for this expense category
            code (str): Code for the expense category
            required (bool): Whether this field is required for all users
            active (Optional[bool]): Whether this category is active and available for input
            free_text_allowed (Optional[bool]): Whether free text input is allowed

        Returns:
            Dict: A dictionary containing the newly created expense category

        Raises:
            httpx.HTTPError: If the request fails or the transaction is not found
        """

        payload = {
            "name": name,
            "code": code,
            "required": required,
            "active": active,
            "freeTextAllowed": free_text_allowed,
            "requiredForTransactions": required_for_transactions,
            "requiredForVirtualCards": required_for_virtual_cards,
        }

        return await self._request(
            method="post",
            path='/categories',
            params=payload
        )

    async def create_expense_category_label(
            self,
            category_id: str,
            name: str,
            code: str,
            active: bool = True
    ) -> Dict:
        """Create an expense category.

        Args:
            category_id (str): The unique identifier of the expense category
            name (str): User-facing name for this expense category label
            code (str): Code for the expense category label
            active (bool): Whether the label is active and available for input

        Returns:
            Dict: A dictionary containing the newly created expense category label

        Raises:
            httpx.HTTPError: If the request fails or the transaction is not found
        """
        payload = {
            "name": name,
            "code": code,
            "active": active,
        }

        return await self._request(
            method="post",
            path=f"/categories/{resource_id(category_id)}/labels",
            params=payload
        )

    async def update_expense_category(
            self,
            category_id: str,
            name: Optional[str] = None,
            active: Optional[bool] = None,
            required: Optional[bool] = None,
            free_text_allowed: Optional[bool] = None,
            *,
            required_for_transactions: Optional[bool] = None,
            required_for_virtual_cards: Optional[bool] = None,
    ) -> Dict:
        """Update the an expense category.

        Args:
            category_id (str): The unique identifier of the expense category
            name (Optional[str]): User-facing name for this expense category
            active (Optional[bool]): Whether the category is active
            required (Optional[bool]): Whether this field is required for all users
            free_text_allowed (Optional[bool]): Whether free text input is allowed

        Returns:
            Dict: A dictionary containing the updated expense category details

        Raises:
            httpx.HTTPError: If the request fails or the transaction is not found
        """

        payload = {
            "name": name,
            "active": active,
            "required": required,
            "freeTextAllowed": free_text_allowed,
            "requiredForTransactions": required_for_transactions,
            "requiredForVirtualCards": required_for_virtual_cards,
        }

        return await self._request(
            method="patch",
            path=f"/categories/{resource_id(category_id)}",
            params=payload
        )

    async def update_expense_category_label(
            self,
            category_id: str,
            label_id: str,
            name: Optional[str] = None,
            active: Optional[bool] = None,
    ) -> Dict:
        """Update an expense category label.

        Args:
            category_id (str): The unique identifier of the expense category
            label_id (str): The unique identifier of the expense category label to update
            name (Optional[str]): User-facing name for the expense label
            active (Optional[bool]): Whether the label is active and available for input

        Returns:
            Dict: A dictionary containing the updated expense category details

        Raises:
            httpx.HTTPError: If the request fails or the transaction is not found
        """

        payload = {
            "name": name,
            "active": active,
        }

        return await self._request(
            method="patch",
            path=f"/categories/{resource_id(category_id)}/labels/{resource_id(label_id)}",
            params=payload
        )

    async def get_expense_category_label(self, category_id: str, label_id: str) -> Dict:
        """Return the flat expense-label object, scoped to its category."""
        return await self._request(
            "get", path=f"/categories/{resource_id(category_id)}/labels/{resource_id(label_id)}"
        )
