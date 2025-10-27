import base64
from abc import ABC, abstractmethod
from typing import Dict

from .config import API_VERSION


class Authorization(ABC):
    @abstractmethod
    def get_auth_headers(self) -> Dict[str, str]:
        pass


class BasicAuth(Authorization):
    def __init__(self, api_key: str, api_secret: str, api_version: str = API_VERSION):
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_version = api_version

    def get_auth_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Basic {base64.b64encode(f"{self.api_key}:{self.api_secret}".encode()).decode()}",
            "x-extend-api-key": self.api_key,
            "Accept": self.api_version,
        }


class BearerAuth(Authorization):
    def __init__(self, jwt_token: str, api_version: str = API_VERSION):
        self.jwt_token = jwt_token
        self.api_version = api_version

    def get_auth_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.jwt_token}", "Accept": self.api_version}
