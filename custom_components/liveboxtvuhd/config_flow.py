"""Config flow for Orange Livebox TV UHD."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .client import LiveboxTvUhdClient
from .const import (
    CONF_COUNTRY,
    DEFAULT_COUNTRY,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DOMAIN,
)

COUNTRY_OPTIONS = [
    SelectOptionDict(value="france", label="France"),
    SelectOptionDict(value="caraibe", label="Cara\u00efbes"),
    SelectOptionDict(value="poland", label="Polska"),
]

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Optional(CONF_COUNTRY, default=DEFAULT_COUNTRY): SelectSelector(
            SelectSelectorConfig(
                options=COUNTRY_OPTIONS,
                mode=SelectSelectorMode.DROPDOWN,
            )
        ),
    }
)


class LiveboxTvUhdConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Orange Livebox TV UHD."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the user step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input.get(CONF_PORT, DEFAULT_PORT)

            # Deduplicate by host:port
            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()

            # Test connection
            session = async_get_clientsession(self.hass)
            client = LiveboxTvUhdClient(
                session,
                hostname=host,
                port=port,
                country=user_input.get(CONF_COUNTRY, DEFAULT_COUNTRY),
            )
            if await client.async_test_connection():
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, DEFAULT_NAME),
                    data=user_input,
                )
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_import(
        self, import_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle import from YAML configuration."""
        return await self.async_step_user(import_data)
