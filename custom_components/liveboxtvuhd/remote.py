"""Remote control support for Android TV Remote."""
from __future__ import annotations

from homeassistant.components.media_player.const import (
    MediaType
)
from .client import LiveboxTvUhdClient
import requests
import asyncio
from collections.abc import Iterable
from typing import Any, final
import homeassistant.util.dt as dt_util
import time

from homeassistant.components.remote import (
    ATTR_ACTIVITY,
    ATTR_DELAY_SECS,
    ATTR_HOLD_SECS,
    ATTR_NUM_REPEATS,
    DEFAULT_DELAY_SECS,
    DEFAULT_HOLD_SECS,
    DEFAULT_NUM_REPEATS,
    RemoteEntity,
    RemoteEntityFeature,
    PLATFORM_SCHEMA, ATTR_ACTIVITY_LIST, ATTR_CURRENT_ACTIVITY
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_SCAN_INTERVAL, STATE_PLAYING, STATE_PAUSED, STATE_ON, STATE_OFF
)
from .const import (
    SCAN_INTERVAL,
    MIN_TIME_BETWEEN_SCANS,
    MIN_TIME_BETWEEN_FORCED_SCANS,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_COUNTRY,
    CONF_COUNTRY
)
import homeassistant.helpers.config_validation as cv

from .client import LiveboxTvUhdClient
import requests
import voluptuous as vol

import logging

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_COUNTRY, default=DEFAULT_COUNTRY): vol.In(["france", "poland"]),
        vol.Optional(CONF_SCAN_INTERVAL, default=SCAN_INTERVAL): cv.time_period,
    }, extra=vol.ALLOW_EXTRA
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Orange Livebox TV UHD platform."""
    host = config.get(CONF_HOST)
    port = config.get(CONF_PORT)
    name = config.get(CONF_NAME)
    country = config.get(CONF_COUNTRY)
    livebox_devices = []

    try:
        device = LiveboxTvUhdRemote(host, port, name, country)
        livebox_devices.append(device)
    except OSError:
        _LOGGER.error(
            "Failed to connect to Livebox TV UHD at %s:%s. "
            "Please check your configuration",
            host,
            port,
        )
    async_add_entities(livebox_devices, True)

# async def async_setup_entry(
#     hass: HomeAssistant,
#     config_entry: ConfigEntry,
#     async_add_entities: AddEntitiesCallback,
# ) -> None:
#     """Set up the Android TV remote entity based on a config entry."""
#     api: AndroidTVRemote = hass.data[DOMAIN][config_entry.entry_id]
#     async_add_entities([AndroidTVRemoteEntity(api, config_entry)])


class LiveboxTvUhdRemote(RemoteEntity):
    """Android TV Remote Entity."""

    _attr_supported_features = RemoteEntityFeature.ACTIVITY

    def __init__(self, host, port, name, country):
        """Initialize the Livebox TV UHD device."""

        self._client = LiveboxTvUhdClient(host, port, country)
        # Assume that the appliance is not muted
        self._muted = False
        self._name = name
        self._current_source = None
        self._state = None
        self._channel_list = {}
        self._current_channel = None
        self._current_show = None
        self._media_duration = None
        self._media_position = None
        self._media_image_url = None
        self._media_last_updated = None
        self._media_series_title = None
        self._media_season = None
        self._media_episode = None
        self._media_type = MediaType.CHANNEL

    async def async_update(self):
        """Retrieve the latest data."""
        try:
            await self.hass.async_add_executor_job(self.refresh_livebox_data)
            self._state = self.refresh_state()
            self._attr_is_on = self._state is not None
            self._media_type = self._client.media_type
            self.refresh_channel_list()
            channel = self._client.channel_name
            _LOGGER.debug(channel)
            if channel is not None:
                self._current_channel = channel
                self._current_show = self._client.show_title
                self._media_duration = self._client.show_duration
                self._media_image_url = self._client.show_img
                self._media_position =  self._client.show_position
                self._media_last_updated = dt_util.utcnow()
                if self._media_type == MediaType.TVSHOW:
                    self._media_series_title = self._client.show_series_title
                    self._media_season = self._client.show_season
                    self._media_episode = self._client.show_episode
                else:
                    self._media_series_title = None
                    self._media_season = None
                    self._media_episode = None
        except requests.ConnectionError as ce:
            self._state = None
            _LOGGER.error(
                "Failed to connect to Livebox TV UHD at %s:%s. "
                "Please check your configuration.yaml. (%s)",
                self._client.hostname,
                self._client.port,
                ce,
            )

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state is not None

    @property
    def current_activity(self) -> str | None:
        """Return the current activity (channel)."""
        return self._current_channel

    @property
    def activity_list(self) -> list[str] | None:
        """Return the list of channels."""
        return [self._channel_list[c] for c in sorted(self._channel_list.keys())]

    @final
    @property
    def state_attributes(self) -> dict[str, Any] | None:
        """Return optional state attributes."""
        if RemoteEntityFeature.ACTIVITY not in self.supported_features_compat:
            return None
        return {
            ATTR_ACTIVITY_LIST: self.activity_list,
            ATTR_CURRENT_ACTIVITY: self.current_activity,
            "power_status": self.state
        }

    def refresh_channel_list(self):
        """Refresh the list of available channels."""
        new_channel_list = {}
        # update channels
        for channel in self._client.get_channels():
            new_channel_list[int(channel["index"])] = channel["name"]
        self._channel_list = new_channel_list

    def refresh_livebox_data(self):
        info = self._client.info

    def refresh_state(self):
        """Refresh the current media state."""
        state = self._client.media_state
        if state == "PLAY":
            return STATE_PLAYING
        if state == "PAUSE":
            return STATE_PAUSED
        return STATE_ON if self._client.is_on else STATE_OFF

    def turn_off(self):
        """Turn off media player."""
        self._state = STATE_OFF
        self._attr_is_on = False
        self._client.turn_off()

    def turn_on(self, activity: str = None, **kwargs):
        """Turn on the media player."""
        self._state = STATE_ON
        self._attr_is_on = True
        self._client.turn_on()
        if activity is not None:
            self._client.set_channel_by_name(activity)
        else:
            activity = kwargs.get(ATTR_ACTIVITY, "")
            if activity is not None:
                self._client.set_channel_by_name(activity)

    def toggle(self, activity: str = None, **kwargs):
        """Toggle a device."""
        if self._state == STATE_ON:
            self.turn_on(activity, **kwargs)
        else:
            self.turn_off()

    def send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send commands to one device."""
        num_repeats = kwargs.get(ATTR_NUM_REPEATS, DEFAULT_NUM_REPEATS)
        delay_secs = kwargs.get(ATTR_DELAY_SECS, DEFAULT_DELAY_SECS)
        hold_secs = kwargs.get(ATTR_HOLD_SECS, DEFAULT_HOLD_SECS)

        _LOGGER.debug("async_send_command %s %d repeats %d delay", ''.join(list(command)), num_repeats, delay_secs)

        for _ in range(num_repeats):
            for single_command in command:
                _LOGGER.debug("Remote command %", single_command)
                if hold_secs > 0:
                    self._client.press_key(single_command, mode=1)
                    time.sleep(hold_secs)
                    self._client.press_key(single_command, mode=2)
                else:
                    self._client.press_key(single_command)
                time.sleep(delay_secs)