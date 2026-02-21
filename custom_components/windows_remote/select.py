"""Select platform for the Windows Remote integration."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
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
    """Set up the select platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: WindowsRemoteCoordinator = data["coordinator"]
    client: WindowsRemoteClient = data["client"]
    async_add_entities([
        WindowsRemoteAudioOutputSelect(coordinator, client, entry),
        WindowsRemoteMonitorProfileSelect(coordinator, client, entry),
    ])


class WindowsRemoteAudioOutputSelect(
    CoordinatorEntity[WindowsRemoteCoordinator], SelectEntity
):
    """Select entity for choosing the active audio output device."""

    _attr_has_entity_name = True
    _attr_name = "Audio Output"

    def __init__(
        self,
        coordinator: WindowsRemoteCoordinator,
        client: WindowsRemoteClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._client = client
        self._attr_unique_id = f"{entry.entry_id}_audio_output"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Windows Remote ({entry.data[CONF_HOST]})",
            "manufacturer": "Windows Remote",
            "model": "PC",
            "configuration_url": f"http://{entry.data[CONF_HOST]}:{entry.data['port']}",
        }

    @property
    def options(self) -> list[str]:
        """Return the list of available audio output devices."""
        return [d["name"] for d in self.coordinator.data.audio_devices]

    @property
    def current_option(self) -> str | None:
        """Return the currently active audio output device."""
        return self.coordinator.data.current_audio_device

    async def async_select_option(self, option: str) -> None:
        """Set the audio output device."""
        await self._client.set_audio_device(option)
        await self.coordinator.async_request_refresh()


class WindowsRemoteMonitorProfileSelect(
    CoordinatorEntity[WindowsRemoteCoordinator], SelectEntity
):
    """Select entity for choosing a monitor profile."""

    _attr_has_entity_name = True
    _attr_name = "Monitor Profile"

    def __init__(
        self,
        coordinator: WindowsRemoteCoordinator,
        client: WindowsRemoteClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._client = client
        self._attr_unique_id = f"{entry.entry_id}_monitor_profile"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Windows Remote ({entry.data[CONF_HOST]})",
            "manufacturer": "Windows Remote",
            "model": "PC",
            "configuration_url": f"http://{entry.data[CONF_HOST]}:{entry.data['port']}",
        }

    @property
    def options(self) -> list[str]:
        """Return the list of available monitor profiles."""
        return self.coordinator.data.monitor_profiles

    @property
    def current_option(self) -> str | None:
        """Return the current option (not tracked)."""
        return None

    async def async_select_option(self, option: str) -> None:
        """Activate the selected monitor profile."""
        await self._client.set_monitor_profile(option)
        await self.coordinator.async_request_refresh()
