from typing import Dict, IO

from extend.client import APIClient
from .resource import Resource


class ReceiptAttachments(Resource):
    @property
    def _base_url(self) -> str:
        return "/receiptattachments"

    def __init__(self, api_client: APIClient):
        super().__init__(api_client)

    async def create_receipt_attachment(
            self,
            transaction_id: str,
            file: IO,
    ) -> Dict:
        """Create a receipt attachment for a transaction by uploading a file using multipart form data.

        Args:
            transaction_id (str): The unique identifier of the transaction to attach the receipt to
            file (IO): A file-like object opened in binary mode that contains the data
                       to be uploaded

        Returns:
            Dict: A dictionary representing the receipt attachment, including:
                - id: Unique identifier of the receipt attachment.
                - transactionId: The associated transaction ID.
                - contentType: The MIME type of the uploaded file.
                - urls: A dictionary with URLs for the original image, main image, and thumbnail.
                - createdAt: Timestamp when the receipt attachment was created.
                - uploadType: A string describing the type of upload (e.g., "TRANSACTION", "VIRTUAL_CARD").

        Raises:
            httpx.HTTPError: If the request fails
        """

        return await self._request(
            method="post_multipart",
            data={"transactionId": transaction_id},
            files={"file": file})
