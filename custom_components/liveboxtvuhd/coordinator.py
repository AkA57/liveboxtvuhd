"""DataUpdateCoordinator for Orange Livebox TV UHD."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .client import LiveboxStateData, LiveboxTvUhdClient
from .const import CONF_MAC, DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class LiveboxTvUhdCoordinator(DataUpdateCoordinator[LiveboxStateData]):
    """Coordinator that polls the Livebox TV UHD."""

    def __init__(
        self, hass: HomeAssistant, client: LiveboxTvUhdClient, entry: ConfigEntry
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.client = client
        self._entry = entry

    async def _async_update_data(self) -> LiveboxStateData:
        try:
            data = await self.client.async_update()
        except Exception as err:
            _LOGGER.debug("Error communicating with Livebox: %s", err)
            # Return an "off" state instead of raising UpdateFailed,
            # so the entity shows as "off" rather than "unavailable".
            return LiveboxStateData(channel_list=self.client._build_channel_list())

        # Persist MAC address in config entry when first discovered
        if data.mac_address and CONF_MAC not in self._entry.data:
            self.hass.config_entries.async_update_entry(
                self._entry,
                data={**self._entry.data, CONF_MAC: data.mac_address},
            )

        return data
