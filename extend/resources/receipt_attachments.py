from typing import IO, Dict, Optional

from extend.client import APIClient

from ..validations import resource_id
from .resource import Resource


class ReceiptAttachments(Resource):
    @property
    def _base_url(self) -> str:
        return "/receiptattachments"

    def __init__(self, api_client: APIClient):
        super().__init__(api_client)

    async def create_receipt_attachment(
            self,
            file: IO,
            transaction_id: Optional[str] = None,
            *,
            filename: Optional[str] = None,
            content_type: Optional[str] = None,
    ) -> Dict:
        """Create a receipt attachment for a transaction by uploading a file using multipart form data.

        The caller owns the open binary stream; the SDK does not close it or open paths.
        filename/content_type can preserve an already-verified upload snapshot.

        Args:
            file (IO): A file-like object opened in binary mode that contains the data
                       to be uploaded
            transaction_id (Optional[str]): The optional unique identifier of the transaction to attach the receipt to

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

        if content_type is not None and filename is None:
            raise ValueError("content_type requires filename")
        upload = (filename, file, content_type) if filename is not None else file
        return await self._request(
            method="post_multipart",
            data={"transactionId": resource_id(transaction_id)} if transaction_id is not None else None,
            files={"file": upload},
        )
