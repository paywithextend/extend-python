from extend.resources.virtual_cards import VirtualCards
from .auth import Authorization
from .client import APIClient
from .resources.credit_cards import CreditCards
from .resources.expense_data import ExpenseData
from .resources.receipt_attachments import ReceiptAttachments
from .resources.receipt_capture import ReceiptCapture
from .resources.transactions import Transactions


class ExtendClient:
    """Wrapper around Extend API

    Args:
        auth (Authorization): Authorization instance shared with the internal API client.

    Example:
        ```python
        from extend.auth import BasicAuth

        extend = ExtendClient(auth=BasicAuth("your_key", "your_secret"))
        cards = await extend.get_virtual_cards()
        ```
    """

    def __init__(self, auth: Authorization):
        """Initialize the Extend Client.

        Args:
            auth (Authorization): Authorization strategy shared with the underlying API client.
        """
        self._api_client = APIClient(auth=auth)
        self.credit_cards = CreditCards(self._api_client)
        self.virtual_cards = VirtualCards(self._api_client)
        self.transactions = Transactions(self._api_client)
        self.expense_data = ExpenseData(self._api_client)
        self.receipt_attachments = ReceiptAttachments(self._api_client)
        self.receipt_capture = ReceiptCapture(self._api_client)
