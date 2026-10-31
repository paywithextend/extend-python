"""Authorization providers. Secrets are only materialized when sending a request."""
import base64
from abc import ABC, abstractmethod

from .config import API_VERSION


class Authorization(ABC):
    @abstractmethod
    def get_auth_headers(self) -> dict[str, str]:
        """Return the current authorization headers."""


class BasicAuth(Authorization):
    def __init__(self, api_key: str, api_secret: str, api_version: str = API_VERSION):
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_version = api_version

    def get_auth_headers(self) -> dict[str, str]:
        encoded = base64.b64encode(f"{self.api_key}:{self.api_secret}".encode()).decode()
        return {
            "Authorization": f"Basic {encoded}",
            "x-extend-api-key": self.api_key,
            "Accept": self.api_version,
        }


class BearerAuth(Authorization):
    def __init__(self, jwt_token: str, api_version: str = API_VERSION):
        self.jwt_token = jwt_token
        self.api_version = api_version

    def get_auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.jwt_token}", "Accept": self.api_version}
