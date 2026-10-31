"""Origin-constrained asynchronous transport for Extend resources."""
from __future__ import annotations

import asyncio
import math
import re
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

from .auth import Authorization
from .config import API_HOSTS, resolve_environment

_PATH = re.compile(r"/[A-Za-z0-9_./~-]*\Z")
_RETRYABLE = {429, 502, 503, 504}


class ExtendAPIError(httpx.HTTPStatusError):
    """An HTTP failure with safe display text and inspectable response metadata."""

    def __init__(self, response: httpx.Response):
        self.status_code = response.status_code
        self.retry_after = response.headers.get("retry-after")
        candidate = response.headers.get("x-request-id", "")
        self.request_id = candidate if re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", candidate) else None
        super().__init__(
            f"Extend API returned HTTP {self.status_code}",
            request=response.request,
            response=response,
        )


class ExtendTransportError(httpx.TransportError):
    """An ambiguous transport failure; mutation callers must reconcile before retrying."""


class APIClient:
    """An explicit environment and a reusable transport bound to one auth provider.

    Injected HTTPX clients remain caller-owned. All requests disable HTTPX auth
    overrides, redirects and environment-proxy discovery for owned clients.
    """

    def __init__(
        self,
        auth: Authorization,
        *,
        environment: str | None = None,
        http_client: httpx.AsyncClient | None = None,
        timeout: float = 30,
        read_retries: int = 2,
        read_budget: float = 60,
    ):
        self.environment = resolve_environment(environment)
        self._host = API_HOSTS[self.environment]
        self._auth = auth
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be positive and finite")
        if not math.isfinite(read_budget) or read_budget <= 0:
            raise ValueError("read_budget must be positive and finite")
        if isinstance(read_retries, bool) or not isinstance(read_retries, int) or not 0 <= read_retries <= 5:
            raise ValueError("read_retries must be an integer between 0 and 5")
        self._timeout = timeout
        self._read_retries = read_retries
        self._read_budget = read_budget
        self._owned = http_client is None
        self._client = http_client or httpx.AsyncClient(trust_env=False, follow_redirects=False)
        self._closed = False

    @property
    def headers(self) -> dict[str, str]:
        """Return a fresh snapshot; token changes apply to the next request."""
        return dict(self._auth.get_auth_headers())

    @classmethod
    def shared_instance(cls, auth: Authorization, **kwargs) -> APIClient:
        """Compatibility factory; never share credentials between callers."""
        return cls(auth, **kwargs)

    async def __aenter__(self) -> APIClient:
        if self._closed:
            raise RuntimeError("Extend client is closed")
        return self

    async def __aexit__(self, *exc_info) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if not self._closed:
            self._closed = True
            if self._owned:
                await self._client.aclose()

    def build_full_url(self, url: str | None) -> str:
        """Accept only unambiguous relative endpoint paths, with separate query params."""
        path = "/" if url is None else url
        if not isinstance(path, str) or not _PATH.fullmatch(path):
            raise ValueError("Endpoint must be an unencoded, slash-prefixed relative path")
        if "//" in path or any(segment in {".", ".."} for segment in path.split("/")):
            raise ValueError("Endpoint contains an ambiguous path segment")
        parsed = httpx.URL(f"https://{self._host}{path}")
        if (parsed.scheme, parsed.host, parsed.port) != ("https", self._host, None):
            raise ValueError("Endpoint origin does not match the configured Extend origin")
        return str(parsed)

    async def get(self, url: str, params: dict | None = None) -> Any:
        return await self._send_request("GET", url, params=params)

    async def post(self, url: str, data: dict) -> Any:
        return await self._send_request("POST", url, json=data)

    async def put(self, url: str, data: dict) -> Any:
        return await self._send_request("PUT", url, json=data)

    async def patch(self, url: str, data: dict) -> Any:
        return await self._send_request("PATCH", url, json=data)

    async def post_multipart(
        self, url: str, data: dict | None = None, files: dict | None = None
    ) -> Any:
        return await self._send_request("POST", url, data=data, files=files)

    @staticmethod
    def _retry_delay(value: str | None, attempt: int) -> float:
        if value is not None:
            try:
                delay = float(value)
            except ValueError:
                try:
                    dt = parsedate_to_datetime(value)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    delay = (dt - datetime.now(timezone.utc)).total_seconds()
                except (ValueError, TypeError, OverflowError):
                    delay = 0.25 * 2**attempt
            if math.isfinite(delay):
                return max(0, delay)
        return 0.25 * 2**attempt

    async def _send_request(self, method: str, url: str, **kwargs) -> Any:
        if self._closed:
            raise RuntimeError("Extend client is closed")
        full_url = self.build_full_url(url)  # Before reading any credentials.
        safe_read = method == "GET"
        attempts = self._read_retries + 1 if safe_read else 1
        budget = self._read_budget if safe_read else self._timeout
        deadline = time.monotonic() + budget
        try:
            async with asyncio.timeout(budget):
                for attempt in range(attempts):
                    request = httpx.Request(
                        method, full_url, headers=self.headers, **kwargs,
                        extensions={"timeout": httpx.Timeout(self._timeout).as_dict()},
                    )
                    try:
                        response = await self._client.send(
                            request, auth=None, follow_redirects=False
                        )
                    except httpx.TransportError as exc:
                        if attempt + 1 == attempts:
                            raise ExtendTransportError("Extend request failed; reconcile any write before retrying") from exc
                        delay = self._retry_delay(None, attempt)
                    else:
                        if response.is_success:
                            if not response.content:
                                return None
                            try:
                                return response.json()
                            except ValueError as exc:
                                raise ExtendTransportError("Extend returned an invalid JSON response") from exc
                        error = ExtendAPIError(response)
                        if response.status_code not in _RETRYABLE or attempt + 1 == attempts:
                            raise error
                        delay = self._retry_delay(error.retry_after, attempt)
                        if delay >= deadline - time.monotonic():
                            raise error
                    if delay >= deadline - time.monotonic():
                        raise ExtendTransportError("Extend read retry budget exhausted")
                    await asyncio.sleep(delay)
        except TimeoutError as exc:
            raise ExtendTransportError("Extend request time budget exceeded; reconcile any write before retrying") from exc
