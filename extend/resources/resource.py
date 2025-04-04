from abc import abstractmethod
from typing import Optional, Any, Dict

from extend.client import APIClient


class Resource:
    _api_client: APIClient

    def __init__(self, api_client):
        self._api_client = api_client

    @property
    @abstractmethod
    def _base_url(self) -> str:
        """Subclasses must override this to provide the base URL."""
        pass

    async def _request(
            self,
            method: str,
            path: str = None,
            params: Optional[Dict] = None,
            data: Optional[Dict[str, Any]] = None,
            files: Optional[Dict[str, Any]] = None,
            base_url_override: Optional[str] = None,
    ) -> Any:
        if params is not None:
            params = {k: v for k, v in params.items() if v is not None}
        match method:
            case "get":
                return await self._api_client.get(self.build_full_path(path, base_url_override), params)
            case "post":
                return await self._api_client.post(self.build_full_path(path, base_url_override), params)
            case "put":
                return await self._api_client.put(self.build_full_path(path, base_url_override), params)
            case "patch":
                return await self._api_client.patch(self.build_full_path(path, base_url_override), params)
            case "post_multipart":
                return await self._api_client.post_multipart(
                    self.build_full_path(path, base_url_override),
                    data=data,
                    files=files
                )
            case _:
                raise ValueError(f"Unsupported HTTP method: {method}")

    def build_full_path(self, path, base_url_override):
        base = base_url_override if base_url_override is not None else self._base_url
        return f"{base}{path or ''}"
