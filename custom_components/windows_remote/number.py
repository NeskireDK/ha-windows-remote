"""Number platform for the Windows Remote integration."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import WindowsRemoteClient
from .const import CONF_HOST, DOMAIN
from .coordinator import WindowsRemoteCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the number platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: WindowsRemoteCoordinator = data["coordinator"]
    client: WindowsRemoteClient = data["client"]
    async_add_entities([WindowsRemoteVolumeNumber(coordinator, client, entry)])


class WindowsRemoteVolumeNumber(
    CoordinatorEntity[WindowsRemoteCoordinator], NumberEntity
):
    """Number entity for controlling the system volume."""

    _attr_has_entity_name = True
    _attr_name = "Volume"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1

    def __init__(
        self,
        coordinator: WindowsRemoteCoordinator,
        client: WindowsRemoteClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._client = client
        self._attr_unique_id = f"{entry.entry_id}_volume"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Windows Remote ({entry.data[CONF_HOST]})",
            "manufacturer": "Windows Remote",
            "model": "PC",
            "configuration_url": f"http://{entry.data[CONF_HOST]}:{entry.data['port']}",
        }

    @property
    def native_value(self) -> float | None:
        """Return the current volume level."""
        return self.coordinator.data.volume

    async def async_set_native_value(self, value: float) -> None:
        """Set the volume level."""
        await self._client.set_volume(int(value))
        await self.coordinator.async_request_refresh()
