import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
from typing_extensions import TypedDict
import asyncio
from .models import (
    VirtualCard, 
    Transaction, 
    RecurrenceConfig, 
    CardCreationRequest, 
    CardUpdateRequest,
    ApiResponse
)

class ExtendAPI:
    """Client for interacting with the Extend API.
    
    This client provides a high-level interface to the Extend API, handling authentication,
    request formatting, and response parsing. It supports all major operations including
    virtual card management and transaction tracking.
    
    Args:
        api_key (str): Your Extend API key
        api_secret (str): Your Extend API secret
        
    Example:
        ```python
        client = ExtendAPI(api_key="your_key", api_secret="your_secret")
        cards = await client.get_virtual_cards()
        ```
    """
    BASE_URL = "https://apiv2.paywithextend.com"
    API_VERSION = "application/vnd.paywithextend.v2021-03-12+json"
    
    def __init__(self, api_key: str, api_secret: str):
        """Initialize the Extend API client.
        
        Args:
            api_key (str): Your Extend API key
            api_secret (str): Your Extend API secret
        """
        self.headers = {
            "x-extend-api-key": api_key,
            "Authorization": f"Basic {api_secret}",
            "Accept": self.API_VERSION
        }
    
    # ----------------------------------------
    # HTTP Methods
    # ----------------------------------------
    async def get(self, url: str, params: Optional[Dict] = None) -> ApiResponse:
        """Make a GET request to the Extend API.
        
        Args:
            url (str): The API endpoint path (e.g., "virtualcards")
            params (Optional[Dict]): Query parameters to include in the request
            
        Returns:
            ApiResponse: The parsed JSON response from the API
            
        Raises:
            httpx.HTTPError: If the request fails
            ValueError: If the response is not valid JSON
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/{url}",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()

    async def post(self, url: str, data: Dict) -> ApiResponse:
        """Make a POST request to the Extend API.
        
        Args:
            url (str): The API endpoint path (e.g., "virtualcards")
            data (Dict): The JSON payload to send in the request body
            
        Returns:
            ApiResponse: The parsed JSON response from the API
            
        Raises:
            httpx.HTTPError: If the request fails
            ValueError: If the response is not valid JSON
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/{url}",
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
        
    async def put(self, url: str, data: Dict) -> ApiResponse:
        """Make a PUT request to the Extend API.
        
        Args:
            url (str): The API endpoint path (e.g., "virtualcards/{card_id}")
            data (Dict): The JSON payload to send in the request body
            
        Returns:
            ApiResponse: The parsed JSON response from the API
            
        Raises:
            httpx.HTTPError: If the request fails
            ValueError: If the response is not valid JSON
        """
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.BASE_URL}/{url}",
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            return response.json()

    # ----------------------------------------
    # Virtual Card Operations
    # ----------------------------------------
    async def get_credit_cards(self) -> Dict:
        """Get a list of all credit cards associated with your account.
        
        Returns:
            Dict: A dictionary containing the list of credit cards and pagination info
            
        Raises:
            httpx.HTTPError: If the request fails
        """
        return await self.get("creditcards")

    async def get_virtual_cards(
        self,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        status: Optional[str] = None,
    ) -> Dict:
        """Get a list of virtual cards with optional filtering and pagination.
        
        Args:
            page (Optional[int]): The page number for pagination (1-based)
            page_size (Optional[int]): Number of items per page
            status (Optional[str]): Filter cards by status (e.g., "ACTIVE", "CANCELLED")
            
        Returns:
            Dict: A dictionary containing:
                - virtualCards: List of VirtualCard objects
                - total: Total number of cards
                - page: Current page number
                - pageSize: Number of items per page
                
        Raises:
            httpx.HTTPError: If the request fails
        """
        params = {}
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["pageSize"] = page_size
        if status:
            params["status"] = status
        
        return await self.get("virtualcards", params=params)

    async def get_virtual_card(self, card_id: str) -> Dict:
        """Get detailed information about a specific virtual card.
        
        Args:
            card_id (str): The unique identifier of the virtual card
            
        Returns:
            Dict: A dictionary containing the virtual card details
            
        Raises:
            httpx.HTTPError: If the request fails or card not found
        """
        return await self.get(f"virtualcards/{card_id}")

    async def create_virtual_card(
        self,
        creditCardId: str,
        displayName: str,
        balanceCents: int,
        notes: Optional[str] = None,
        recurs: Optional[bool] = None,
        recurrence: Optional[Dict] = None,
        recipient: Optional[str] = None,
        cardholder: Optional[str] = None,
        validTo: Optional[str] = None,
    ) -> Dict:
        """Create a new virtual card.
        
        Args:
            creditCardId (str): ID of the parent credit card
            displayName (str): Name to display for the virtual card
            balanceCents (int): Initial balance in cents
            notes (Optional[str]): Additional notes about the card
            recurs (Optional[bool]): Whether this is a recurring card
            recurrence (Optional[Dict]): Recurrence configuration if recurs is True
            recipient (Optional[str]): Email of the card recipient
            cardholder (Optional[str]): Email of the cardholder
            validTo (Optional[str]): Expiration date in YYYY-MM-DD format
            
        Returns:
            Dict: The created virtual card details
            
        Raises:
            ValueError: If required fields are missing or invalid
            httpx.HTTPError: If the request fails
            
        Example:
            ```python
            card = await client.create_virtual_card(
                creditCardId="cc_123",
                displayName="Marketing Card",
                balanceCents=10000,  # $100.00
                recipient="marketing@company.com",
                validTo="2024-12-31"
            )
            ```
        """
        # Use the helper validation method for basic card data
        card_data = self._validate_card_creation_data(
            creditCardId=creditCardId,
            displayName=displayName,
            balanceCents=balanceCents,
            recipientEmail=recipient,
            validTo=validTo,
            notes=notes,
            recurrence=recurrence
        )
        
        # Add cardholder if provided
        if cardholder:
            card_data["cardholder"] = cardholder
            
        # Set recurs flag if provided
        if recurs is not None:
            card_data["recurs"] = recurs
            
        # Handle recurrence config if provided
        if recurrence:
            # Use the helper validation method for recurrence
            card_data["recurrence"] = self._validate_recurrence_data(**recurrence)

        print(f"Creating virtual card with data: {card_data}")  # Debug log
        return await self.post("virtualcards", card_data)
    
    async def update_virtual_card(
        self,
        cardId: str,
        balanceCents: int,
        displayName: Optional[str] = None,
        notes: Optional[str] = None,
        validFrom: Optional[str] = None,
        validTo: Optional[str] = None
    ) -> Dict:
        """Update an existing virtual card.
        
        Args:
            cardId (str): ID of the virtual card to update
            balanceCents (int): New balance in cents
            displayName (Optional[str]): New display name
            notes (Optional[str]): New notes
            validFrom (Optional[str]): New start date in YYYY-MM-DD format
            validTo (Optional[str]): New expiration date in YYYY-MM-DD format
            
        Returns:
            Dict: The updated virtual card details
            
        Raises:
            ValueError: If date formats are invalid or validTo is before validFrom
            httpx.HTTPError: If the request fails or card not found
            
        Example:
            ```python
            updated = await client.update_virtual_card(
                cardId="vc_123",
                balanceCents=5000,  # $50.00
                displayName="Updated Name",
                validTo="2024-12-31"
            )
            ```
        """
        update_data = {
            "balanceCents": balanceCents
        }
        
        if displayName:
            update_data["displayName"] = displayName
            
        if notes:
            update_data["notes"] = notes
            
        if validFrom:
            try:
                datetime.strptime(validFrom, "%Y-%m-%d")
                update_data["validFrom"] = f"{validFrom}T00:00:00.000Z"
            except ValueError:
                raise ValueError("validFrom must be in YYYY-MM-DD format")
                
        if validTo:
            try:
                # Handle both simple date format and ISO format with time
                if "T" in validTo:
                    valid_to_date = datetime.strptime(validTo.split("T")[0], "%Y-%m-%d")
                else:
                    valid_to_date = datetime.strptime(validTo, "%Y-%m-%d")
                
                if validFrom:
                    if "T" in validFrom:
                        valid_from_date = datetime.strptime(validFrom.split("T")[0], "%Y-%m-%d")
                    else:
                        valid_from_date = datetime.strptime(validFrom, "%Y-%m-%d")
                    if valid_to_date.date() <= valid_from_date.date():
                        raise ValueError("validTo must be after validFrom")
                update_data["validTo"] = validTo if "T" in validTo else f"{validTo}T23:59:59.999Z"
            except ValueError as e:
                if "strptime" in str(e):
                    raise ValueError("validTo must be in YYYY-MM-DD format or ISO format with time")
                raise

        return await self.put(f"virtualcards/{cardId}", update_data)
    
    async def cancel_virtual_card(self, card_id: str) -> Dict:
        """Cancel a virtual card, preventing further transactions.
        
        Args:
            card_id (str): ID of the virtual card to cancel
            
        Returns:
            Dict: The updated virtual card details
            
        Raises:
            httpx.HTTPError: If the request fails or card not found
        """
        return await self.put(f"virtualcards/{card_id}/cancel", {})

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
        return await self.put(f"virtualcards/{card_id}/close", {})

    # ----------------------------------------
    # Transaction Operations 
    # ----------------------------------------
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
            params["pageSize"] = page_size
        
        return await self.get("transactions", params=params)

    async def get_transaction(self, transaction_id: str) -> Dict:
        """Get detailed information about a specific transaction.
        
        Args:
            transaction_id (str): The unique identifier of the transaction
            
        Returns:
            Dict: A dictionary containing the transaction details
            
        Raises:
            httpx.HTTPError: If the request fails or transaction not found
        """
        return await self.get(f"transactions/{transaction_id}")

    # ----------------------------------------
    # Validation Helper Functions
    # ----------------------------------------
    def _validate_card_creation_data(
        self,
        creditCardId: str,
        displayName: str,
        balanceCents: int,
        recipientEmail: Optional[str] = None,
        validFrom: Optional[str] = None,
        validTo: Optional[str] = None,
        notes: Optional[str] = None,
        recurrence: Optional[Dict] = None
    ) -> CardCreationRequest:
        """Validate and format card creation data.
        
        Args:
            creditCardId (str): ID of the parent credit card
            displayName (str): Name to display for the virtual card
            balanceCents (int): Initial balance in cents
            recipientEmail (Optional[str]): Email of the card recipient
            validFrom (Optional[str]): Start date in YYYY-MM-DD format
            validTo (Optional[str]): Expiration date in YYYY-MM-DD format
            notes (Optional[str]): Additional notes about the card
            recurrence (Optional[Dict]): Recurrence configuration
            
        Returns:
            CardCreationRequest: Validated and formatted card creation data
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Validate required fields
        if not creditCardId:
            raise ValueError("Credit card ID is required")
        
        if balanceCents <= 0:
            raise ValueError("Balance must be greater than 0")
        
        if not displayName:
            raise ValueError("Display name is required")
        
        data = {
            "creditCardId": creditCardId,
            "displayName": displayName,
            "balanceCents": balanceCents
        }
        
        if recipientEmail:
            # Basic email format validation
            if not '@' in recipientEmail or not '.' in recipientEmail:
                raise ValueError("Invalid email format")
            data["recipient"] = recipientEmail
        
        if validFrom:
            try:
                # Validate date format and ensure it's not in the past
                valid_from_date = datetime.strptime(validFrom, "%Y-%m-%d")
                if valid_from_date.date() < datetime.now().date():
                    raise ValueError("validFrom date cannot be in the past")
                data["validFrom"] = f"{validFrom}T00:00:00.000Z"
            except ValueError as e:
                if "strptime" in str(e):
                    raise ValueError("validFrom must be in YYYY-MM-DD format")
                raise
            
        if validTo:
            try:
                # Handle both simple date format and ISO format with time
                if "T" in validTo:
                    valid_to_date = datetime.strptime(validTo.split("T")[0], "%Y-%m-%d")
                else:
                    valid_to_date = datetime.strptime(validTo, "%Y-%m-%d")
                
                if validFrom:
                    if "T" in validFrom:
                        valid_from_date = datetime.strptime(validFrom.split("T")[0], "%Y-%m-%d")
                    else:
                        valid_from_date = datetime.strptime(validFrom, "%Y-%m-%d")
                    if valid_to_date.date() <= valid_from_date.date():
                        raise ValueError("validTo must be after validFrom")
                data["validTo"] = validTo if "T" in validTo else f"{validTo}T23:59:59.999Z"
            except ValueError as e:
                if "strptime" in str(e):
                    raise ValueError("validTo must be in YYYY-MM-DD format or ISO format with time")
                raise
            
        if notes:
            if len(notes) > 500:  # Add reasonable max length
                raise ValueError("Notes must be less than 500 characters")
            data["notes"] = notes
        
        # Handle recurrence configuration if provided
        if recurrence:
            data["recurs"] = True
            data["recurrence"] = self._validate_recurrence_data(**recurrence)
        
        return data

    def _validate_recurrence_data(
        self,
        balanceCents: int,
        period: str,
        interval: int,
        terminator: str,
        count: Optional[int] = None,
        until: Optional[str] = None,
        byWeekDay: Optional[int] = None,
        byMonthDay: Optional[int] = None,
        byYearDay: Optional[int] = None
    ) -> RecurrenceConfig:
        """Validate and format recurrence configuration data.
        
        Args:
            balanceCents (int): Balance for each recurring card
            period (str): Recurrence period ("DAILY", "WEEKLY", "MONTHLY", "YEARLY")
            interval (int): Number of periods between recurrences
            terminator (str): How to end the recurrence ("NONE", "COUNT", "DATE", "COUNT_OR_DATE")
            count (Optional[int]): Number of recurrences if terminator is "COUNT"
            until (Optional[str]): End date in YYYY-MM-DD format if terminator is "DATE"
            byWeekDay (Optional[int]): Day of week (0-6) for weekly recurrence
            byMonthDay (Optional[int]): Day of month (1-31) for monthly recurrence
            byYearDay (Optional[int]): Day of year (1-366) for yearly recurrence
            
        Returns:
            RecurrenceConfig: Validated and formatted recurrence configuration
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Validate basic required fields
        valid_periods = ["DAILY", "WEEKLY", "MONTHLY", "YEARLY"]
        valid_terminators = ["NONE", "COUNT", "DATE", "COUNT_OR_DATE"]
        
        if balanceCents <= 0:
            raise ValueError("Recurrence balanceCents must be greater than 0")
            
        if period not in valid_periods:
            raise ValueError(f"Period must be one of: {', '.join(valid_periods)}")
            
        if terminator not in valid_terminators:
            raise ValueError(f"Terminator must be one of: {', '.join(valid_terminators)}")
            
        if interval <= 0:
            raise ValueError("Interval must be greater than 0")
                
        data = {
            "balanceCents": balanceCents,
            "period": period,
            "interval": interval,
            "terminator": terminator
        }
        
        # Validate terminator-specific fields
        if terminator in ["COUNT", "COUNT_OR_DATE"]:
            if count is None:
                raise ValueError("Count is required for COUNT or COUNT_OR_DATE terminator")
            if count <= 0:
                raise ValueError("Count must be greater than 0")
            data["count"] = count
                
        if terminator in ["DATE", "COUNT_OR_DATE"]:
            if not until:
                raise ValueError("Until date is required for DATE or COUNT_OR_DATE terminator")
            try:
                # Handle both simple date format and ISO format with time
                if "T" in until:
                    until_date = datetime.strptime(until.split("T")[0], "%Y-%m-%d")
                else:
                    until_date = datetime.strptime(until, "%Y-%m-%d")
                
                if until_date.date() <= datetime.now().date():
                    raise ValueError("Until date must be in the future")
                data["until"] = until if "T" in until else f"{until}T23:59:59.999Z"
            except ValueError as e:
                if "strptime" in str(e):
                    raise ValueError("Until date must be in YYYY-MM-DD format or ISO format with time")
                raise
                    
        # Validate period-specific fields
        if period == "WEEKLY":
            if byWeekDay is None:
                raise ValueError("byWeekDay is required for WEEKLY period")
            if not 0 <= byWeekDay <= 6:
                raise ValueError("byWeekDay must be between 0 and 6 (Monday to Sunday)")
            data["byWeekDay"] = byWeekDay
                
        elif period == "MONTHLY":
            if byMonthDay is None:
                raise ValueError("byMonthDay is required for MONTHLY period")
            if not 1 <= byMonthDay <= 31:
                raise ValueError("byMonthDay must be between 1 and 31")
            # Additional validation for invalid dates like February 31
            if byMonthDay > 28:
                # Check if this day exists in all months
                for month in range(1, 13):
                    try:
                        datetime(2024, month, byMonthDay)  # Use leap year for February
                    except ValueError:
                        raise ValueError(
                            f"byMonthDay {byMonthDay} is invalid as it doesn't exist in all months. "
                            "Choose a day between 1 and 28 for consistent monthly recurrence."
                        )
            data["byMonthDay"] = byMonthDay
                
        elif period == "YEARLY":
            if byYearDay is None:
                raise ValueError("byYearDay is required for YEARLY period")
            if not 1 <= byYearDay <= 365:
                raise ValueError("byYearDay must be between 1 and 365")
            # Check if it's a valid day (not February 29 on non-leap years)
            try:
                # Convert day of year to date using a non-leap year
                datetime(2023, 1, 1) + timedelta(days=byYearDay - 1)
            except ValueError:
                raise ValueError(
                    f"byYearDay {byYearDay} is invalid as it doesn't exist in non-leap years. "
                    "Choose a different day for consistent yearly recurrence."
                )
            data["byYearDay"] = byYearDay
        
        # DAILY period doesn't require additional parameters
        elif period == "DAILY":
            if any([byWeekDay, byMonthDay, byYearDay]):
                raise ValueError("DAILY period should not include byWeekDay, byMonthDay, or byYearDay")
                    
        return data
    

    # ----------------------------------------
    # Formatting Helper Functions
    # ----------------------------------------
    @staticmethod
    def format_virtual_cards_list(response: Dict) -> str:
        """Format the virtual cards list response"""
        cards = response.get("virtualCards", [])
        if not cards:
            return "No virtual cards found."
        
        result = "Virtual Cards:\n\n"
        for card in cards:
            result += (
                f"- ID: {card['id']}\n"
                f"  Name: {card['displayName']}\n"
                f"  Status: {card['status']}\n"
                f"  Balance: ${card['balanceCents']/100:.2f}\n"
                f"  Expires: {card['expires']}\n\n"
            )
        return result

    @staticmethod
    def format_virtual_card_details(response: ApiResponse) -> str:
        """Format the detailed virtual card response"""
        card = response.get("virtualCard", {})
        if not card:
            return "Virtual card not found."
        
        return (
            f"Virtual Card Details:\n\n"
            f"ID: {card['id']}\n"
            f"Name: {card['displayName']}\n"
            f"Status: {card['status']}\n"
            f"Balance: ${card['balanceCents']/100:.2f}\n"
            f"Spent: ${card['spentCents']/100:.2f}\n"
            f"Limit: ${card['limitCents']/100:.2f}\n"
            f"Last 4: {card['last4']}\n"
            f"Expires: {card['expires']}\n"
            f"Valid From: {card['validFrom']}\n"
            f"Valid To: {card['validTo']}\n"
            f"Recipient: {card.get('recipientId', 'N/A')}\n"
            f"Notes: {card.get('notes', 'N/A')}\n"
        )
        
    @staticmethod
    def format_transactions_list(response: Dict) -> str:
        """Format the transactions list response"""
        transactions = response.get("transactions", [])
        if not transactions:
            return "No transactions found."
        
        result = "Recent Transactions:\n\n"
        for txn in transactions:
            amount = txn.get('clearingBillingAmountCents', txn.get('authBillingAmountCents', 0))
            result += (
                f"- ID: {txn['id']}\n"
                f"  Merchant: {txn.get('merchantName', 'N/A')}\n"
                f"  Amount: ${amount/100:.2f}\n"
                f"  Status: {txn['status']}\n"
                f"  Date: {txn.get('clearedAt', txn.get('authedAt', 'N/A'))}\n\n"
            )
        return result

    @staticmethod
    def format_transaction_details(response: ApiResponse) -> str:
        """Format the detailed transaction response"""
        txn = response.get("transaction", {})
        if not txn:
            return "Transaction not found."
        
        amount = txn.get('clearingBillingAmountCents', txn.get('authBillingAmountCents', 0))
        return (
            f"Transaction Details:\n\n"
            f"ID: {txn['id']}\n"
            f"Merchant: {txn.get('merchantName', 'N/A')}\n"
            f"Amount: ${amount/100:.2f}\n"
            f"Status: {txn['status']}\n"
            f"Type: {txn['type']}\n"
            f"Card: {txn.get('virtualCardId', 'N/A')}\n"
            f"Authorization Date: {txn.get('authedAt', 'N/A')}\n"
            f"Clearing Date: {txn.get('clearedAt', 'N/A')}\n"
            f"MCC: {txn.get('mcc', 'N/A')}\n"
            f"Notes: {txn.get('notes', 'N/A')}\n"
        )

    @staticmethod
    def validate_card_data(creditCardId: str, displayName: str, balanceCents: int, **kwargs) -> dict:
        """Validate card creation data."""
        if not balanceCents or balanceCents <= 0:
            raise ValueError("Balance must be greater than 0")
        
        data = {
            "creditCardId": creditCardId,
            "displayName": displayName,
            "balanceCents": balanceCents
        }

        # Add any additional valid kwargs to the data
        for key, value in kwargs.items():
            if value is not None:
                data[key] = value

        return data

