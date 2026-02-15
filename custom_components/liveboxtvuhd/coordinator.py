"""DataUpdateCoordinator for Orange Livebox TV UHD."""
from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import LiveboxStateData, LiveboxTvUhdClient
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class LiveboxTvUhdCoordinator(DataUpdateCoordinator[LiveboxStateData]):
    """Coordinator that polls the Livebox TV UHD."""

    def __init__(self, hass: HomeAssistant, client: LiveboxTvUhdClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> LiveboxStateData:
        try:
            return await self.client.async_update()
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Livebox: {err}") from err
