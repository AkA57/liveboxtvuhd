"""Remote control support for Orange Livebox TV UHD."""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable
from typing import Any

import voluptuous as vol

from homeassistant.components.remote import (
    ATTR_ACTIVITY,
    ATTR_DELAY_SECS,
    ATTR_HOLD_SECS,
    ATTR_NUM_REPEATS,
    DEFAULT_DELAY_SECS,
    DEFAULT_HOLD_SECS,
    DEFAULT_NUM_REPEATS,
    PLATFORM_SCHEMA as REMOTE_PLATFORM_SCHEMA,
    RemoteEntity,
    RemoteEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    STATE_OFF,
    STATE_ON,
    STATE_PAUSED,
    STATE_PLAYING,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import homeassistant.helpers.config_validation as cv

from .client import LiveboxStateData
from .const import (
    CONF_COUNTRY,
    DEFAULT_COUNTRY,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DOMAIN,
)
from .coordinator import LiveboxTvUhdCoordinator

_LOGGER = logging.getLogger(__name__)

# Deprecated YAML platform schema (triggers import)
PLATFORM_SCHEMA = REMOTE_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_COUNTRY, default=DEFAULT_COUNTRY): vol.In(
            ["france", "poland", "caraibe"]
        ),
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up via YAML platform (deprecated, does not trigger a second import)."""
    _LOGGER.warning(
        "Configuration of %s remote via platform YAML is deprecated. "
        "Please use the UI or move config under 'liveboxtvuhd:' key",
        DOMAIN,
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the remote from a config entry."""
    coordinator: LiveboxTvUhdCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([LiveboxTvUhdRemote(coordinator, entry)])


class LiveboxTvUhdRemote(
    CoordinatorEntity[LiveboxTvUhdCoordinator], RemoteEntity
):
    """Orange Livebox TV UHD Remote Entity."""

    _attr_has_entity_name = True
    _attr_name = "Remote"
    _attr_supported_features = RemoteEntityFeature.ACTIVITY

    def __init__(
        self, coordinator: LiveboxTvUhdCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        mac = coordinator.client.mac_address
        if mac:
            self._attr_unique_id = mac
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, mac)},
                connections={("mac", mac)},
                name=entry.title,
                manufacturer="Orange",
                model="Livebox TV UHD",
            )
        else:
            self._attr_unique_id = entry.entry_id
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, entry.entry_id)},
                name=entry.title,
                manufacturer="Orange",
                model="Livebox TV UHD",
            )

    @property
    def _data(self) -> LiveboxStateData | None:
        return self.coordinator.data

    @property
    def is_on(self) -> bool:
        return self._data is not None and self._data.is_on

    @property
    def current_activity(self) -> str | None:
        return self._data.channel_name if self._data else None

    @property
    def activity_list(self) -> list[str] | None:
        if self._data and self._data.channel_list:
            return [self._data.channel_list[k] for k in sorted(self._data.channel_list)]
        return []

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return power status as extra attribute."""
        if self._data is None:
            return None
        state = self._data.media_state
        if state == "PLAY":
            power = STATE_PLAYING
        elif state == "PAUSE":
            power = STATE_PAUSED
        else:
            power = STATE_ON if self._data.is_on else STATE_OFF
        return {"power_status": power}

    async def async_turn_on(self, activity: str | None = None, **kwargs: Any) -> None:
        """Turn on the Livebox, optionally tuning to a channel."""
        if not self.is_on:
            await self.coordinator.client.async_turn_on()
        channel = activity or kwargs.get(ATTR_ACTIVITY)
        if channel:
            await self.coordinator.client.async_set_channel_by_name(channel)
        await self.coordinator.async_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.async_turn_off()
        await self.coordinator.async_refresh()

    async def async_toggle(self, activity: str | None = None, **kwargs: Any) -> None:
        """Toggle the device (fixed: was inverted in original code)."""
        if self.is_on:
            await self.async_turn_off()
        else:
            await self.async_turn_on(activity, **kwargs)

    async def async_send_command(
        self, command: Iterable[str], **kwargs: Any
    ) -> None:
        """Send commands to the Livebox."""
        num_repeats = kwargs.get(ATTR_NUM_REPEATS, DEFAULT_NUM_REPEATS)
        delay_secs = kwargs.get(ATTR_DELAY_SECS, DEFAULT_DELAY_SECS)
        hold_secs = kwargs.get(ATTR_HOLD_SECS, DEFAULT_HOLD_SECS)

        for _ in range(num_repeats):
            for single_command in command:
                _LOGGER.debug("Remote command: %s", single_command)
                if hold_secs > 0:
                    await self.coordinator.client.async_press_key(
                        single_command, mode=1
                    )
                    await asyncio.sleep(hold_secs)
                    await self.coordinator.client.async_press_key(
                        single_command, mode=2
                    )
                else:
                    await self.coordinator.client.async_press_key(single_command)
                await asyncio.sleep(delay_secs)
        await self.coordinator.async_refresh()
