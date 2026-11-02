from extend.resources.virtual_cards import VirtualCards

from .auth import Authorization
from .client import APIClient
from .resources.credit_cards import CreditCards
from .resources.expense_data import ExpenseData
from .resources.organizations import Organizations
from .resources.receipt_attachments import ReceiptAttachments
from .resources.receipt_capture import ReceiptCapture
from .resources.transactions import Transactions
from .resources.users import Users


class ExtendClient:
    """Wrapper around Extend API

    Args:
        auth (Authorization): Authorization instance shared with the internal API client.

    Example:
        ```python
        from extend.auth import BasicAuth

        extend = ExtendClient(auth=BasicAuth("your_key", "your_secret"))
        cards = await extend.virtual_cards.get_virtual_cards()
        ```
    """

    def __init__(self, auth: Authorization, *, environment: str | None = None, **transport_options):
        """Initialize the Extend Client.

        Args:
            auth (Authorization): Authorization strategy shared with the underlying API client.
        """
        self._api_client = APIClient(auth=auth, environment=environment, **transport_options)
        self.credit_cards = CreditCards(self._api_client)
        self.virtual_cards = VirtualCards(self._api_client)
        self.transactions = Transactions(self._api_client)
        self.expense_data = ExpenseData(self._api_client)
        self.receipt_attachments = ReceiptAttachments(self._api_client)
        self.receipt_capture = ReceiptCapture(self._api_client)
        self.organizations = Organizations(self._api_client)
        self.users = Users(self._api_client)

    @property
    def api_client(self) -> APIClient:
        """Public origin-validated transport for endpoints without a resource wrapper."""
        return self._api_client

    async def aclose(self) -> None:
        await self._api_client.aclose()

    async def __aenter__(self):
        await self._api_client.__aenter__()
        return self

    async def __aexit__(self, *exc_info):
        await self.aclose()
