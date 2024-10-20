"""Support for interface with an Orange Livebox TV UHD appliance."""
from datetime import timedelta
import logging

from .client import LiveboxTvUhdClient
import requests
import voluptuous as vol

from homeassistant.components.media_player import PLATFORM_SCHEMA, MediaPlayerEntity
from homeassistant.components.media_player.const import (
    MediaPlayerEntityFeature,
    MediaType
)

from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    STATE_OFF,
    STATE_ON,
    STATE_PAUSED,
    STATE_PLAYING,
)
import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
from .const import (
    SCAN_INTERVAL,
    MIN_TIME_BETWEEN_SCANS,
    MIN_TIME_BETWEEN_FORCED_SCANS,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_COUNTRY,
    CONF_COUNTRY
)


_LOGGER = logging.getLogger(__name__)


SUPPORT_LIVEBOXUHD = (
    MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.SELECT_SOURCE
    | MediaPlayerEntityFeature.PLAY
)


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
        device = LiveboxTvUhdDevice(host, port, name, country)
        livebox_devices.append(device)
    except OSError:
        _LOGGER.error(
            "Failed to connect to Livebox TV UHD at %s:%s. "
            "Please check your configuration",
            host,
            port,
        )
    async_add_entities(livebox_devices, True)


class LiveboxTvUhdDevice(MediaPlayerEntity):
    """Representation of an Orange Livebox TV UHD."""

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
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        return self._muted

    @property
    def source(self):
        """Return the current input source."""
        return self._current_channel

    @property
    def source_list(self):
        """List of available input sources."""
        # Sort channels by tvIndex
        return [self._channel_list[c] for c in sorted(self._channel_list.keys())]

    @property
    def media_content_type(self):
        """Content type of current playing media."""
        return self._client.media_type

    @property
    def media_image_url(self):
        """Image url of current playing media."""
        return self._media_image_url

    @property
    def media_title(self):
        """Title of current playing media."""
        if self._current_channel:
            if self._current_show:
                return f"{self._current_channel} - {self._current_show}"
            return self._current_channel

    @property
    def media_series_title(self):
        """Title of series of current playing media, TV show only."""
        return self._media_series_title

    @property
    def media_season(self):
        """Season of current playing media, TV show only."""
        return self._media_season

    @property
    def media_episode(self):
        """Episode of current playing media, TV show only."""
        return self._media_episode

    @property
    def media_duration(self):
        """Duration of current playing media in seconds."""
        return self._media_duration

    @property
    def media_position(self):
        """Position of current playing media in seconds."""
        return self._media_position

    @property
    def media_position_updated_at(self):
        """When was the position of the current playing media valid.

        Returns value from homeassistant.util.dt.utcnow().
        """
        return self._media_last_updated

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return SUPPORT_LIVEBOXUHD

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
        self._client.turn_off()

    def turn_on(self):
        """Turn on the media player."""
        self._state = STATE_ON
        self._client.turn_on()

    def volume_up(self):
        """Volume up the media player."""
        self._client.volume_up()

    def volume_down(self):
        """Volume down media player."""
        self._client.volume_down()

    def mute_volume(self, mute):
        """Send mute command."""
        self._muted = mute
        self._client.mute()

    def media_play_pause(self):
        """Simulate play pause media player."""
        self._client.play_pause()

    def select_source(self, source):
        """Select input source."""
        self._current_source = source
        self._client.channel_name = source

    def media_play(self):
        """Send play command."""
        self._state = STATE_PLAYING
        self._client.play()

    def media_pause(self):
        """Send media pause command to media player."""
        self._state = STATE_PAUSED
        self._client.pause()

    def media_next_track(self):
        """Send next track command."""
        self._client.channel_up()

    def media_previous_track(self):
        """Send the previous track command."""
        self._client.channel_down()