"""DataUpdateCoordinator for the Windows Remote integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CannotConnectError, InvalidAuthError, WindowsRemoteClient
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class WindowsRemoteCoordinator(DataUpdateCoordinator[bool]):
    """Coordinator that polls the Windows Remote health endpoint."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: WindowsRemoteClient,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client

    async def _async_update_data(self) -> bool:
        """Fetch data from the health endpoint.

        Returns True if the PC is online, False otherwise.
        """
        try:
            await self.client.get_health()
        except CannotConnectError:
            return False
        except InvalidAuthError as err:
            raise UpdateFailed("Invalid API key") from err
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Unexpected error polling health: %s", err)
            return False
        return True
