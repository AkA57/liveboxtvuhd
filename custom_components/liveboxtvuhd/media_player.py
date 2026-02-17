"""Support for Orange Livebox TV UHD media player."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.components.media_player import (
    PLATFORM_SCHEMA as MEDIA_PLAYER_PLATFORM_SCHEMA,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
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
import homeassistant.util.dt as dt_util
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

# Deprecated YAML platform schema (triggers import)
PLATFORM_SCHEMA = MEDIA_PLAYER_PLATFORM_SCHEMA.extend(
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
    """Set up via YAML platform (deprecated, triggers config flow import)."""
    _LOGGER.warning(
        "Configuration of %s media_player via platform YAML is deprecated. "
        "Please use the UI or move config under 'liveboxtvuhd:' key",
        DOMAIN,
    )
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "import"},
            data={
                CONF_HOST: config[CONF_HOST],
                CONF_PORT: config.get(CONF_PORT, DEFAULT_PORT),
                CONF_NAME: config.get(CONF_NAME, DEFAULT_NAME),
                CONF_COUNTRY: config.get(CONF_COUNTRY, DEFAULT_COUNTRY),
            },
        )
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the media player from a config entry."""
    coordinator: LiveboxTvUhdCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([LiveboxTvUhdMediaPlayer(coordinator, entry)])


class LiveboxTvUhdMediaPlayer(
    CoordinatorEntity[LiveboxTvUhdCoordinator], MediaPlayerEntity
):
    """Representation of an Orange Livebox TV UHD media player."""

    _attr_has_entity_name = True
    _attr_name = "Media Player"
    _attr_supported_features = SUPPORT_LIVEBOXUHD

    def __init__(
        self, coordinator: LiveboxTvUhdCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._attr_muted = False
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
    def state(self) -> str | None:
        if self._data is None:
            return None
        if self._data.media_state == "PLAY":
            return STATE_PLAYING
        if self._data.media_state == "PAUSE":
            return STATE_PAUSED
        return STATE_ON if self._data.is_on else STATE_OFF

    @property
    def is_volume_muted(self) -> bool:
        return self._attr_muted

    @property
    def source(self) -> str | None:
        if self._data:
            return self._data.channel_name
        return None

    @property
    def source_list(self) -> list[str]:
        if self._data and self._data.channel_list:
            return [self._data.channel_list[k] for k in sorted(self._data.channel_list)]
        return []

    @property
    def media_content_type(self) -> str | None:
        return self._data.media_type if self._data else None

    @property
    def media_image_url(self) -> str | None:
        return self._data.show_img if self._data else None

    @property
    def media_title(self) -> str | None:
        if self._data and self._data.channel_name:
            if self._data.show_title:
                return f"{self._data.channel_name} - {self._data.show_title}"
            return self._data.channel_name
        return None

    @property
    def media_series_title(self) -> str | None:
        return self._data.show_series_title if self._data else None

    @property
    def media_season(self) -> int | None:
        return self._data.show_season if self._data else None

    @property
    def media_episode(self) -> int | None:
        return self._data.show_episode if self._data else None

    @property
    def media_duration(self) -> int | None:
        return self._data.show_duration if self._data else None

    @property
    def media_position(self) -> int | None:
        return self._data.show_position if self._data else None

    @property
    def media_position_updated_at(self):
        """Return when the position was last updated."""
        if self._data and self._data.show_position > 0:
            return dt_util.utcnow()
        return None

    async def async_turn_on(self) -> None:
        await self.coordinator.client.async_turn_on()
        await self.coordinator.async_refresh()

    async def async_turn_off(self) -> None:
        await self.coordinator.client.async_turn_off()
        await self.coordinator.async_refresh()

    async def async_volume_up(self) -> None:
        await self.coordinator.client.async_volume_up()
        await self.coordinator.async_refresh()

    async def async_volume_down(self) -> None:
        await self.coordinator.client.async_volume_down()
        await self.coordinator.async_refresh()

    async def async_mute_volume(self, mute: bool) -> None:
        self._attr_muted = mute
        await self.coordinator.client.async_mute()
        await self.coordinator.async_refresh()

    async def async_media_play_pause(self) -> None:
        await self.coordinator.client.async_play_pause()
        await self.coordinator.async_refresh()

    async def async_media_play(self) -> None:
        await self.coordinator.client.async_play()
        await self.coordinator.async_refresh()

    async def async_media_pause(self) -> None:
        await self.coordinator.client.async_pause()
        await self.coordinator.async_refresh()

    async def async_media_next_track(self) -> None:
        await self.coordinator.client.async_channel_up()
        await self.coordinator.async_refresh()

    async def async_media_previous_track(self) -> None:
        await self.coordinator.client.async_channel_down()
        await self.coordinator.async_refresh()

    async def async_select_source(self, source: str) -> None:
        await self.coordinator.client.async_set_channel_by_name(source)
        await self.coordinator.async_refresh()
