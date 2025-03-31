from extend.resources.virtual_cards import VirtualCards
from .client import APIClient
from .resources.credit_cards import CreditCards
from .resources.expense_data import ExpenseData
from .resources.receipt_attachments import ReceiptAttachments
from .resources.transactions import Transactions


class ExtendClient:
    """Wrapper around Extend API

    Args:
        api_key (str): Your Extend API key
        api_secret (str): Your Extend API secret

    Example:
        ```python
        extend = ExtendClient(api_key="your_key", api_secret="your_secret")
        cards = await extend.get_virtual_cards()
        ```
    """

    def __init__(self, api_key: str, api_secret: str):
        """Initialize the Extend Client.

        Args:
            api_key (str): Your Extend API key
            api_secret (str): Your Extend API secret
        """
        self._api_client = APIClient(api_key=api_key, api_secret=api_secret)
        self.credit_cards = CreditCards(self._api_client)
        self.virtual_cards = VirtualCards(self._api_client)
        self.transactions = Transactions(self._api_client)
        self.expense_data = ExpenseData(self._api_client)
        self.receipt_attachments = ReceiptAttachments(self._api_client)
