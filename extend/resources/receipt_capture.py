from typing import Dict, List, Any

from extend.client import APIClient
from .resource import Resource


class ReceiptCapture(Resource):
    @property
    def _base_url(self) -> str:
        return "/receiptcapture"

    def __init__(self, api_client: APIClient):
        super().__init__(api_client)

    async def automatch_receipts(
            self,
            receipt_attachment_ids: List[str],
    ) -> Dict[str, Any]:
        """
        Initiates an asynchronous bulk receipt automatch job.

        This method triggers an asynchronous job on the server that processes the provided receipt
        attachment IDs. The operation is non-blocking: it immediately returns a job ID and preliminary
        details, while the matching process is performed in the background.

        The server returns a response conforming to the BulkReceiptAutomatchResponse structure, which includes:
          - id (str): The bulk automatch job ID.
          - tasks (List[Dict]): A list of tasks representing individual automatch operations. Each task includes:
              - id (str): Task ID.
              - status (str): Task status.
              - receiptAttachmentId (str): Receipt attachment ID.
              - transactionId (Optional[str]): Matched transaction ID (if available).
              - attachmentsCount (Optional[int]): Number of attachments on the matched transaction.

        Args:
            receipt_attachment_ids (List[str]): A list of receipt attachment IDs to be automatched.

        Returns:
            Dict[str, Any]: A dictionary representing the Bulk Receipt Automatch Response, including the job ID.

        Raises:
            httpx.HTTPError: If the request fails.
        """
        payload = {"receiptAttachmentIds": receipt_attachment_ids}

        return await self._request(
            method="post",
            path="/automatch",
            params=payload,
        )

    async def get_automatch_status(
            self,
            job_id: str,
    ) -> Dict[str, Any]:
        """
        Retrieves the status of a bulk receipt capture automatch job.

        This method calls a GET endpoint with the provided job ID to fetch the current status of the
        asynchronous automatch job. The response conforms to the BulkReceiptAutomatchResponse structure and includes:
          - id (str): The job ID.
          - tasks (List[Dict]): A list of automatch task views containing details such as task ID, status,
            receipt attachment ID, the matched transaction ID (if available), and the number of attachments
            on the transaction.

        Args:
            job_id (str): The ID of the automatch job whose status is to be retrieved.

        Returns:
            Dict[str, Any]: A dictionary representing the current Bulk Receipt Automatch Response.

        Raises:
            httpx.HTTPError: If the request fails.
        """
        return await self._request(
            method="get",
            path=f"/{job_id}/status",
        )
