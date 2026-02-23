"""Media player platform for the PC Remote integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from wakeonlan import send_magic_packet

from .api import CannotConnectError, PcRemoteClient
from .const import CONF_MAC_ADDRESS, DOMAIN, build_device_info
from .coordinator import PcRemoteCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the media player platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: PcRemoteCoordinator = data["coordinator"]
    client: PcRemoteClient = data["client"]
    async_add_entities([PcRemoteSteamPlayer(coordinator, client, entry)])


class PcRemoteSteamPlayer(
    CoordinatorEntity[PcRemoteCoordinator], MediaPlayerEntity
):
    """Media player entity for Steam game control."""

    _attr_has_entity_name = True
    _attr_translation_key = "steam"
    _attr_icon = "mdi:steam"
    _attr_supported_features = (
        MediaPlayerEntityFeature.SELECT_SOURCE
        | MediaPlayerEntityFeature.STOP
    )

    def __init__(
        self,
        coordinator: PcRemoteCoordinator,
        client: PcRemoteClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the media player entity."""
        super().__init__(coordinator)
        self._client = client
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_steam"
        self._wake_target: dict | None = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info from latest coordinator data."""
        return build_device_info(
            self._entry,
            machine_name=self.coordinator.data.machine_name,
            sw_version=self.coordinator.data.service_version,
        )

    @property
    def available(self) -> bool:
        """Always available — source list is shown even when PC is offline."""
        return super().available

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the media player."""
        if self._wake_target is not None:
            return MediaPlayerState.BUFFERING
        if not self.coordinator.data.online:
            return MediaPlayerState.OFF
        if self.coordinator.data.steam_running:
            return MediaPlayerState.PLAYING
        return MediaPlayerState.IDLE

    @property
    def media_title(self) -> str | None:
        """Return the title of the currently playing game."""
        target = self._wake_target or self.coordinator.data.steam_running
        return target.get("name") if target else None

    @property
    def source(self) -> str | None:
        """Return the current game as the source."""
        target = self._wake_target or self.coordinator.data.steam_running
        return target.get("name") if target else None

    @property
    def source_list(self) -> list[str]:
        """Return the list of recently played games."""
        return [g.get("name", "") for g in self.coordinator.data.steam_games]

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        target = self._wake_target or self.coordinator.data.steam_running
        return {"app_id": target.get("appId")} if target else None

    async def async_select_source(self, source: str) -> None:
        """Launch the selected game."""
        for game in self.coordinator.data.steam_games:
            if game.get("name") == source:
                app_id = game.get("appId")
                if app_id is None:
                    return
                if not self.coordinator.data.online:
                    self._wake_target = {"appId": app_id, "name": source}
                    self.async_write_ha_state()
                    self.hass.async_create_task(self._wake_and_play(app_id, source))
                    return
                await self._client.steam_run(app_id)
                self.coordinator.data.steam_running = {"appId": app_id, "name": source}
                self.async_write_ha_state()
                return
        _LOGGER.warning("Steam game not found in list: %s", source)

    async def async_media_stop(self) -> None:
        """Stop the currently running game."""
        if not self.coordinator.data.online:
            return
        await self._client.steam_stop()
        # Optimistic update
        self.coordinator.data.steam_running = None
        self.async_write_ha_state()

    async def _wake_and_play(self, app_id: int, source: str) -> None:
        """Wake the PC via WoL, then launch the game when Steam is ready."""
        mac = self._entry.data.get(CONF_MAC_ADDRESS)
        if mac:
            try:
                await self.hass.async_add_executor_job(send_magic_packet, mac)
            except (ValueError, OSError) as err:
                _LOGGER.error("Failed to send WoL packet: %s", err)

        # Poll /api/health until service responds (max 3 minutes, every 5s)
        online = False
        for _ in range(36):
            await asyncio.sleep(5)
            try:
                await self._client.get_health()
                online = True
                break
            except CannotConnectError:
                continue

        if not online:
            _LOGGER.warning("Wake-and-play: PC did not come online within timeout")
            self._wake_target = None
            self.async_write_ha_state()
            return

        # Retry launch — Steam/tray may not be ready immediately after boot
        # steam_run() returns 200 silently if tray is down, so we verify via steam_running
        launched = False
        for attempt in range(4):
            if attempt > 0:
                await asyncio.sleep(15)
            try:
                await self._client.steam_run(app_id)
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Wake-and-play steam_run attempt %d: %s", attempt + 1, err)
            await asyncio.sleep(10)
            try:
                running = await self._client.get_steam_running()
                if running and running.get("appId") == app_id:
                    launched = True
                    break
            except Exception:  # noqa: BLE001
                pass

        if not launched:
            _LOGGER.warning("Wake-and-play: game did not launch after 4 attempts")

        self._wake_target = None
        if launched:
            self.coordinator.data.steam_running = {"appId": app_id, "name": source}
        await self.coordinator.async_request_refresh()
