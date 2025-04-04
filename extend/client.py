import base64
from typing import Optional, Dict, Any

import httpx

from .config import API_HOST, API_VERSION


class APIClient:
    """Client for interacting with the Extend API.

    Args:
        api_key (str): Your Extend API key
        api_secret (str): Your Extend API secret
        
    Example:
        ```python
        client = ExtendAPI(api_key="your_key", api_secret="your_secret")
        cards = await client.get_virtual_cards()
        ```
    """

    _shared_instance: Optional["APIClient"] = None

    def __init__(self, api_key: str, api_secret: str):
        """Initialize the Extend API client.
        
        Args:
            api_key (str): Your Extend API key
            api_secret (str): Your Extend API secret
        """
        auth_value = base64.b64encode(f"{api_key}:{api_secret}".encode()).decode()
        self.headers = {
            "x-extend-api-key": api_key,
            "Authorization": f"Basic {auth_value}",
            "Accept": API_VERSION
        }

    @classmethod
    def shared_instance(cls, api_key: Optional[str] = None, api_secret: Optional[str] = None) -> "APIClient":
        """
        Returns a singleton instance of APIClient. On first call, you must provide both
        api_key and api_secret. Subsequent calls return the same instance.
        """
        if cls._shared_instance is None:
            if api_key is None or api_secret is None:
                raise ValueError("API key and API secret must be provided on the first call to global_instance.")
            cls._global_instance = cls(api_key, api_secret)
        return cls._global_instance

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
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.build_full_url(url),
                headers=self.headers,
                params=params,
                timeout=httpx.Timeout(30)
            )
            response.raise_for_status()
            return response.json()

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
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.build_full_url(url),
                headers=self.headers,
                json=data,
                timeout=httpx.Timeout(30)
            )
            response.raise_for_status()
            return response.json()

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
        async with httpx.AsyncClient() as client:
            response = await client.put(
                self.build_full_url(url),
                headers=self.headers,
                json=data,
                timeout=httpx.Timeout(30)
            )
            response.raise_for_status()
            return response.json()

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
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                self.build_full_url(url),
                headers=self.headers,
                json=data,
                timeout=httpx.Timeout(30)
            )
            response.raise_for_status()
            return response.json()

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
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.build_full_url(url),
                headers=self.headers,
                data=data,
                files=files,
                timeout=httpx.Timeout(30)
            )
            response.raise_for_status()
            return response.json()

    def build_full_url(self, url: Optional[str]):
        return f"https://{API_HOST}{url or ''}"
