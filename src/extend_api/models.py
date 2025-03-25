from typing import TypedDict, Optional, Literal, Dict, Any, NotRequired
from datetime import datetime

class VirtualCard(TypedDict):
    """Type definition for Virtual Card data.
    
    Represents a virtual card in the Extend system. Virtual cards are single-use
    or recurring cards that can be created from a parent credit card.
    
    Fields:
        id (str): Unique identifier for the virtual card
        displayName (str): Name shown on the virtual card
        status (Literal['ACTIVE', 'CANCELLED', 'CLOSED']): Current status of the card
        balanceCents (int): Available balance in cents
        spentCents (int): Amount spent in cents
        limitCents (int): Spending limit in cents
        last4 (str): Last 4 digits of the card number
        expires (str): Card expiration date in ISO format
        validFrom (str): Card activation date in ISO format
        validTo (str): Card expiration date in ISO format
        recipientId (NotRequired[str]): ID of the card recipient
        notes (NotRequired[str]): Additional notes about the card
        recurrence (NotRequired['RecurrenceConfig']): Recurrence configuration if applicable
    """
    id: str
    displayName: str
    status: Literal['ACTIVE', 'CANCELLED', 'CLOSED']
    balanceCents: int
    spentCents: int
    limitCents: int
    last4: str
    expires: str
    validFrom: str
    validTo: str
    recipientId: NotRequired[str]
    notes: NotRequired[str]
    recurrence: NotRequired['RecurrenceConfig']

class Transaction(TypedDict):
    """Type definition for Transaction data.
    
    Represents a transaction made with a virtual card. Transactions can be either
    authorizations (pending) or clearings (completed).
    
    Fields:
        id (str): Unique identifier for the transaction
        merchantName (str): Name of the merchant where the transaction occurred
        status (Literal['PENDING', 'CLEARED', 'DECLINED']): Current status of the transaction
        type (Literal['AUTH', 'CLEARING']): Type of transaction (authorization or clearing)
        virtualCardId (str): ID of the virtual card used
        authedAt (NotRequired[str]): Authorization timestamp in ISO format
        clearedAt (NotRequired[str]): Clearing timestamp in ISO format
        authBillingAmountCents (int): Authorized amount in cents
        clearingBillingAmountCents (NotRequired[int]): Final cleared amount in cents
        mcc (NotRequired[str]): Merchant Category Code
        notes (NotRequired[str]): Additional notes about the transaction
    """
    id: str
    merchantName: str
    status: Literal['PENDING', 'CLEARED', 'DECLINED']
    type: Literal['AUTH', 'CLEARING']
    virtualCardId: str
    authedAt: NotRequired[str]
    clearedAt: NotRequired[str]
    authBillingAmountCents: int
    clearingBillingAmountCents: NotRequired[int]
    mcc: NotRequired[str]
    notes: NotRequired[str]

class RecurrenceConfig(TypedDict):
    """Type definition for Recurrence Configuration.
    
    Defines how a virtual card should recur, including timing and termination rules.
    
    Fields:
        balanceCents (int): Balance for each recurring card instance
        period (Literal['DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY']): Recurrence period
        interval (int): Number of periods between recurrences (e.g., 2 for bi-weekly)
        terminator (Literal['NONE', 'COUNT', 'DATE', 'COUNT_OR_DATE']): How to end recurrence
        count (NotRequired[int]): Number of recurrences if terminator is "COUNT"
        until (NotRequired[str]): End date in YYYY-MM-DD format if terminator is "DATE"
        byWeekDay (NotRequired[int]): Day of week (0-6) for weekly recurrence
        byMonthDay (NotRequired[int]): Day of month (1-31) for monthly recurrence
        byYearDay (NotRequired[int]): Day of year (1-366) for yearly recurrence
        
    Example:
        ```python
        config = {
            "balanceCents": 10000,  # $100.00
            "period": "MONTHLY",
            "interval": 1,
            "terminator": "COUNT",
            "count": 12,
            "byMonthDay": 1  # First day of each month
        }
        ```
    """
    balanceCents: int
    period: Literal['DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY']
    interval: int
    terminator: Literal['NONE', 'COUNT', 'DATE', 'COUNT_OR_DATE']
    count: NotRequired[int]
    until: NotRequired[str]
    byWeekDay: NotRequired[int]
    byMonthDay: NotRequired[int]
    byYearDay: NotRequired[int]

class CardCreationRequest(TypedDict):
    """Type definition for card creation request data.
    
    Defines the data structure required to create a new virtual card.
    
    Fields:
        creditCardId (str): ID of the parent credit card
        displayName (str): Name to display for the virtual card
        balanceCents (int): Initial balance in cents
        recipient (NotRequired[str]): Email of the card recipient
        validFrom (NotRequired[str]): Start date in YYYY-MM-DD format
        validTo (NotRequired[str]): Expiration date in YYYY-MM-DD format
        notes (NotRequired[str]): Additional notes about the card
        recurs (NotRequired[bool]): Whether this is a recurring card
        recurrence (NotRequired[RecurrenceConfig]): Recurrence configuration if recurs is True
        
    Example:
        ```python
        request = {
            "creditCardId": "cc_123",
            "displayName": "Marketing Card",
            "balanceCents": 10000,  # $100.00
            "recipient": "marketing@company.com",
            "validTo": "2024-12-31",
            "recurs": True,
            "recurrence": {
                "balanceCents": 10000,
                "period": "MONTHLY",
                "interval": 1,
                "terminator": "COUNT",
                "count": 12
            }
        }
        ```
    """
    creditCardId: str
    displayName: str
    balanceCents: int
    recipient: NotRequired[str]
    validFrom: NotRequired[str]
    validTo: NotRequired[str]
    notes: NotRequired[str]
    recurs: NotRequired[bool]
    recurrence: NotRequired[RecurrenceConfig]

class CardUpdateRequest(TypedDict):
    """Type definition for card update request data.
    
    Defines the data structure for updating an existing virtual card.
    All fields are optional, only specified fields will be updated.
    
    Fields:
        displayName (NotRequired[str]): New display name
        balanceCents (NotRequired[int]): New balance in cents
        validFrom (NotRequired[str]): New start date in YYYY-MM-DD format
        validTo (NotRequired[str]): New expiration date in YYYY-MM-DD format
        notes (NotRequired[str]): New notes
        
    Example:
        ```python
        update = {
            "displayName": "Updated Name",
            "balanceCents": 5000,  # $50.00
            "validTo": "2024-12-31"
        }
        ```
    """
    displayName: NotRequired[str]
    balanceCents: NotRequired[int]
    validFrom: NotRequired[str]
    validTo: NotRequired[str]
    notes: NotRequired[str]

class ApiResponse(TypedDict):
    """Type definition for API responses.
    
    Represents the structure of responses from the Extend API.
    The response will contain one of the following fields based on the endpoint.
    
    Fields:
        virtualCard (NotRequired[VirtualCard]): Single virtual card details
        virtualCards (NotRequired[list[VirtualCard]]): List of virtual cards
        transaction (NotRequired[Transaction]): Single transaction details
        transactions (NotRequired[list[Transaction]]): List of transactions
    """
    virtualCard: NotRequired[VirtualCard]
    virtualCards: NotRequired[list[VirtualCard]]
    transaction: NotRequired[Transaction]
    transactions: NotRequired[list[Transaction]]