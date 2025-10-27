from typing import Optional, Dict, Any

import httpx

from .auth import Authorization
from .config import API_HOST


class APIClient:
    """Client for interacting with the Extend API.

    Args:
        auth (Authorization): Authorization strategy that yields request headers.
        
    Example:
        ```python
        from extend.auth import BasicAuth

        client = APIClient(auth=BasicAuth("your_key", "your_secret"))
        cards = await client.get_virtual_cards()
        ```
    """

    _shared_instance: Optional["APIClient"] = None

    def __init__(self, auth: Authorization):
        """Initialize the Extend API client.

        Args:
            auth (Authorization): Authorization strategy to use for requests.
        """
        headers = dict(auth.get_auth_headers())

        self._auth = auth
        self.headers = headers

    @classmethod
    def shared_instance(cls, auth: Authorization) -> "APIClient":
        """Returns a singleton instance of APIClient using the provided authorization."""
        if cls._shared_instance is None:
            cls._shared_instance = cls(auth=auth)
        return cls._shared_instance

    # ----------------------------------------
    # HTTP Methods
    # ----------------------------------------

    async def get(self, url: str, params: Optional[Dict] = None) -> Any:
        """Make a GET request to the Extend API.
        
        Args:
            url (str): The API endpoint path (e.g., "/virtualcards")
            params (Optional[Dict]): Query parameters to include in the request
            
        Returns:
            The JSON response from the API
            
        Raises:
            httpx.HTTPError: If the request fails
            ValueError: If the response is not valid JSON
        """
        return await self._send_request("GET", url, params=params)

    async def post(self, url: str, data: Dict) -> Any:
        """Make a POST request to the Extend API.
        
        Args:
            url (str): The API endpoint path (e.g., "/virtualcards")
            data (Dict): The JSON payload to send in the request body
            
        Returns:
            The JSON response from the API
            
        Raises:
            httpx.HTTPError: If the request fails
            ValueError: If the response is not valid JSON
        """
        return await self._send_request("POST", url, json=data)

    async def put(self, url: str, data: Dict) -> Any:
        """Make a PUT request to the Extend API.
        
        Args:
            url (str): The API endpoint path (e.g., "/virtualcards/{card_id}")
            data (Dict): The JSON payload to send in the request body
            
        Returns:
            The JSON response from the API
            
        Raises:
            httpx.HTTPError: If the request fails
            ValueError: If the response is not valid JSON
        """
        return await self._send_request("PUT", url, json=data)

    async def patch(self, url: str, data: Dict) -> Any:
        """Make a PATCH request to the Extend API.

        Args:
            url (str): The API endpoint path (e.g., "/virtualcards/{card_id}")
            data (Dict): The JSON payload to send in the request body

        Returns:
            The JSON response from the API

        Raises:
            httpx.HTTPError: If the request fails
            ValueError: If the response is not valid JSON
        """
        return await self._send_request("PATCH", url, json=data)

    async def post_multipart(
            self,
            url: str,
            data: Optional[Dict[str, Any]] = None,
            files: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Make a POST request with multipart/form-data payload.

        This method is designed to support file uploads along with optional form data.

        Args:
            url (str): The API endpoint path (e.g., "/receiptattachments")
            data (Optional[Dict[str, Any]]): Optional form fields to include in the request.
            files (Optional[Dict[str, Any]]): Files to be uploaded. For example,
                {"file": file_obj} where file_obj is an open file in binary mode.

        Returns:
            The JSON response from the API.

        Raises:
            httpx.HTTPError: If the request fails.
            ValueError: If the response is not valid JSON.
        """
        # When sending multipart data, we pass `data` (for non-file fields)
        # and `files` (for file uploads) separately.
        return await self._send_request("POST", url, data=data, files=files)

    def build_full_url(self, url: Optional[str]):
        return f"https://{API_HOST}{url or ''}"

    async def _send_request(
            self,
            method: str,
            url: str,
            *,
            params: Optional[Dict] = None,
            json: Optional[Dict] = None,
            data: Optional[Dict] = None,
            files: Optional[Dict] = None
    ) -> Any:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method.upper(),
                url=self.build_full_url(url),
                headers=self.headers,
                params=params,
                json=json,
                data=data,
                files=files,
                timeout=httpx.Timeout(30)
            )
            response.raise_for_status()

            if response.content:
                return response.json()
            return None
