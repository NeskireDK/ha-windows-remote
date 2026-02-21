"""API client for the Windows Remote service."""

from __future__ import annotations

import logging

import aiohttp

_LOGGER = logging.getLogger(__name__)


class WindowsRemoteClient:
    """Async HTTP client for the Windows Remote REST API."""

    def __init__(
        self,
        host: str,
        port: int,
        api_key: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the API client."""
        self._base_url = f"http://{host}:{port}"
        self._headers = {"X-Api-Key": api_key}
        self._session = session

    async def get_health(self) -> dict:
        """Poll the health endpoint. Returns the JSON response."""
        try:
            async with self._session.get(
                f"{self._base_url}/health",
                headers=self._headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 401:
                    raise InvalidAuthError("Invalid API key")
                resp.raise_for_status()
                return await resp.json()
        except aiohttp.ClientConnectorError as err:
            raise CannotConnectError(
                f"Cannot connect to {self._base_url}"
            ) from err

    async def sleep(self) -> None:
        """Send the sleep command to the Windows PC."""
        try:
            async with self._session.post(
                f"{self._base_url}/sleep",
                headers=self._headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 401:
                    raise InvalidAuthError("Invalid API key")
                resp.raise_for_status()
        except aiohttp.ClientConnectorError as err:
            raise CannotConnectError(
                f"Cannot connect to {self._base_url}"
            ) from err

    async def test_connection(self) -> bool:
        """Test the connection to the Windows Remote service."""
        await self.get_health()
        return True


class CannotConnectError(Exception):
    """Error raised when the client cannot connect."""


class InvalidAuthError(Exception):
    """Error raised when the API key is invalid."""
