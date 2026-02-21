"""Config flow for the Windows Remote integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CannotConnectError, InvalidAuthError, WindowsRemoteClient
from .const import CONF_API_KEY, CONF_HOST, CONF_PORT, DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_API_KEY): str,
    }
)


class WindowsRemoteConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Windows Remote."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._async_abort_entries_match(
                {CONF_HOST: user_input[CONF_HOST], CONF_PORT: user_input[CONF_PORT]}
            )

            session = async_get_clientsession(self.hass)
            client = WindowsRemoteClient(
                host=user_input[CONF_HOST],
                port=user_input[CONF_PORT],
                api_key=user_input[CONF_API_KEY],
                session=session,
            )

            try:
                await client.test_connection()
            except CannotConnectError:
                errors["base"] = "cannot_connect"
            except InvalidAuthError:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected exception during config flow")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"Windows Remote ({user_input[CONF_HOST]})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
