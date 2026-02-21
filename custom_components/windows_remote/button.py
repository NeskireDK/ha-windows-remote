"""Button platform for the Windows Remote integration."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import WindowsRemoteClient
from .const import CONF_HOST, DOMAIN
from .coordinator import WindowsRemoteCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: WindowsRemoteCoordinator = data["coordinator"]
    client: WindowsRemoteClient = data["client"]
    async_add_entities([WindowsRemoteSleepButton(coordinator, client, entry)])


class WindowsRemoteSleepButton(
    CoordinatorEntity[WindowsRemoteCoordinator], ButtonEntity
):
    """Button that puts the Windows PC to sleep."""

    _attr_has_entity_name = True
    _attr_name = "Sleep"

    def __init__(
        self,
        coordinator: WindowsRemoteCoordinator,
        client: WindowsRemoteClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._client = client
        self._attr_unique_id = f"{entry.entry_id}_sleep"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Windows Remote ({entry.data[CONF_HOST]})",
            "manufacturer": "Windows Remote",
            "model": "PC",
            "configuration_url": f"http://{entry.data[CONF_HOST]}:{entry.data['port']}",
        }

    async def async_press(self) -> None:
        """Send the sleep command."""
        await self._client.sleep()
