"""Client for Orange Livebox TV UHD."""
from __future__ import annotations

import asyncio
import calendar
import logging
from collections import OrderedDict
from dataclasses import dataclass, field

import aiohttp

import homeassistant.util.dt as dt_util
from homeassistant.components.media_player.const import MediaType
from homeassistant.helpers.device_registry import format_mac

from . import const_caraibes, const_france, const_poland
from .const import (
    KEYS,
    OPERATION_CHANNEL_CHANGE,
    OPERATION_INFORMATION,
    OPERATION_KEYPRESS,
)

COUNTRY_MODULES = {
    "france": const_france,
    "caraibe": const_caraibes,
    "poland": const_poland,
}

_LOGGER = logging.getLogger(__name__)


@dataclass
class LiveboxStateData:
    """Immutable snapshot of the Livebox state returned by async_update."""

    mac_address: str | None = None
    standby_state: str = "1"
    channel_id: str | None = None
    osd_context: str | None = None
    wol_support: str | None = None
    media_state: str | None = None
    media_type: str = MediaType.CHANNEL
    channel_name: str | None = None
    show_title: str | None = None
    show_series_title: str | None = None
    show_season: int | None = None
    show_episode: int | None = None
    show_definition: str | None = None
    show_img: str | None = None
    show_start_dt: int = 0
    show_duration: int = 0
    show_position: int = 0
    channel_list: dict[int, str] = field(default_factory=dict)

    @property
    def is_on(self) -> bool:
        return self.standby_state == "0"


class LiveboxTvUhdClient:
    """Async client for Orange Livebox TV UHD."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        hostname: str,
        port: int = 8080,
        country: str = "france",
        timeout: int = 3,
    ) -> None:
        self.session = session
        self.hostname = hostname
        self.port = port
        self.country = country
        self.timeout = aiohttp.ClientTimeout(total=timeout)

        # Load country-specific data
        mod = COUNTRY_MODULES[country]
        self.channels: list[dict] = mod.CHANNELS
        self.epg_url: str = mod.EPG_URL
        self.epg_mco: str = mod.EPG_MCO
        self.epg_user_agent: str = mod.EPG_USER_AGENT

        # Persistent state across updates
        self._mac_address: str | None = None
        self._last_channel_id: str | None = None
        self._display_con_err = True

        # Cached EPG data (only refreshed on channel/show change)
        self._cached_show_title: str | None = None
        self._cached_show_series_title: str | None = None
        self._cached_show_season: int | None = None
        self._cached_show_episode: int | None = None
        self._cached_show_definition: str | None = None
        self._cached_show_img: str | None = None
        self._cached_show_start_dt: int = 0
        self._cached_show_duration: int = 0
        self._cached_channel_name: str | None = None

        # Cached EPG program list for France/Caraïbes
        self._epg_programs: list | None = None
        self._epg_programs_channel_id: str | None = None

        # EPG response cache for Poland (avoid re-fetching full 24h guide)
        self._epg_cache: dict | None = None
        self._epg_cache_date: str | None = None

    @property
    def mac_address(self) -> str | None:
        return self._mac_address

    def _build_channel_list(self) -> dict[int, str]:
        """Build sorted channel list for source selection."""
        return {
            int(ch["index"]): f'{ch["index"]}. {ch["name"]}'
            for ch in self.channels
        }

    async def async_test_connection(self) -> bool:
        """Test if the Livebox is reachable. Used by config flow."""
        try:
            result = await self._async_rq_livebox(OPERATION_INFORMATION)
            return result is not None
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return False

    async def async_update(self) -> LiveboxStateData:
        """Poll the Livebox and return a state snapshot."""
        osd_context = None
        channel_id = None
        media_state = None
        standby_state = "1"
        wol_support = None

        data = await self._async_rq_livebox(OPERATION_INFORMATION)
        if data:
            self._display_con_err = False
            result = data.get("result", {}).get("data", {})
            if result:
                standby_state = result.get("activeStandbyState", "1")
                osd_context = result.get("osdContext")
                wol_support = result.get("wolSupport")
                if "macAddress" in result:
                    self._mac_address = format_mac(result["macAddress"])
                media_state = result.get("playedMediaState")
                channel_id = result.get("playedMediaId")

        # If a known channel is displayed
        if channel_id and self.get_channel_from_epg_id(channel_id):
            channel_changed = channel_id != self._last_channel_id
            show_expired = self._cached_show_position > self._cached_show_duration

            if channel_changed:
                self._last_channel_id = channel_id
                chan = self.get_channel_from_epg_id(channel_id)
                self._cached_channel_name = f'{chan["index"]}. {chan["name"]}'

            if channel_changed or show_expired:
                # Reset cached EPG show data
                self._cached_show_series_title = None
                self._cached_show_season = None
                self._cached_show_episode = None
                self._cached_show_title = None
                self._cached_show_img = None
                self._cached_show_start_dt = 0
                self._cached_show_duration = 0

                if self.country in ("france", "caraibe"):
                    # Try to find current show in cached programs
                    if not channel_changed and self._epg_programs and self._epg_programs_channel_id == channel_id:
                        self._apply_current_program_france()
                    # Fetch from API if channel changed or no match in cache
                    if self._cached_show_start_dt == 0:
                        epg_data = await self._async_rq_epg(channel_id)
                        self._parse_epg_france(epg_data, channel_id)
                elif self.country == "poland":
                    epg_data = await self._async_rq_epg(channel_id)
                    self._parse_epg_poland(epg_data, channel_id)

            # Update position
            show_position = 0
            if self._cached_show_start_dt > 0:
                d = dt_util.utcnow()
                show_position = calendar.timegm(d.utctimetuple()) - self._cached_show_start_dt

            media_type = MediaType.CHANNEL
            if self._cached_show_series_title is not None:
                media_type = MediaType.TVSHOW

            return LiveboxStateData(
                mac_address=self._mac_address,
                standby_state=standby_state,
                channel_id=channel_id,
                osd_context=osd_context,
                wol_support=wol_support,
                media_state=media_state,
                media_type=media_type,
                channel_name=self._cached_channel_name,
                show_title=self._cached_show_title,
                show_series_title=self._cached_show_series_title,
                show_season=self._cached_show_season,
                show_episode=self._cached_show_episode,
                show_definition=self._cached_show_definition,
                show_img=self._cached_show_img,
                show_start_dt=self._cached_show_start_dt,
                show_duration=self._cached_show_duration,
                show_position=show_position,
                channel_list=self._build_channel_list(),
            )

        # Unknown or no channel (HOMEPAGE, NETFLIX, etc.)
        return self._no_channel_state(
            standby_state=standby_state,
            osd_context=osd_context,
            wol_support=wol_support,
            media_state=media_state,
        )

    def _no_channel_state(
        self,
        standby_state: str,
        osd_context: str | None,
        wol_support: str | None,
        media_state: str | None,
    ) -> LiveboxStateData:
        """Build state when no known channel is displayed."""
        self._last_channel_id = None
        self._cached_show_start_dt = 0
        self._cached_show_duration = 0
        channel_name = osd_context.upper() if osd_context else None
        return LiveboxStateData(
            mac_address=self._mac_address,
            standby_state=standby_state,
            channel_id="-1",
            osd_context=osd_context,
            wol_support=wol_support,
            media_state=media_state,
            media_type=MediaType.CHANNEL,
            channel_name=channel_name,
            channel_list=self._build_channel_list(),
        )

    def _parse_epg_france(self, epg_data: dict | None, channel_id: str) -> None:
        """Parse EPG response for France/Caraïbes."""
        if epg_data is None or channel_id not in epg_data:
            return
        programs = epg_data[channel_id]
        if not programs:
            return

        # Cache the full program list
        self._epg_programs = programs
        self._epg_programs_channel_id = channel_id

        self._apply_current_program_france()

    def _apply_current_program_france(self) -> None:
        """Find and apply the program matching the current time."""
        if not self._epg_programs:
            return

        now_ts = calendar.timegm(dt_util.utcnow().utctimetuple())

        # Find the program that covers the current time
        prog = None
        for p in self._epg_programs:
            start = p.get("diffusionDate", 0)
            duration = p.get("duration", 0)
            if start <= now_ts < start + duration:
                prog = p
                break

        if prog is None:
            return

        if prog.get("programType") == "EPISODE":
            self._cached_show_series_title = prog.get("title")
            season = prog.get("season", {})
            self._cached_show_season = season.get("number")
            self._cached_show_episode = prog.get("episodeNumber", 0)
            serie = season.get("serie", {})
            self._cached_show_title = serie.get("title")
        else:
            self._cached_show_title = prog.get("title")

        self._cached_show_definition = prog.get("definition")
        self._cached_show_start_dt = prog.get("diffusionDate", 0)
        self._cached_show_duration = prog.get("duration", 0)

        covers = prog.get("covers") or []
        if len(covers) > 1:
            self._cached_show_img = covers[1].get("url")
        elif len(covers) > 0:
            self._cached_show_img = covers[0].get("url")

    def _parse_epg_poland(self, epg_data: dict | None, channel_id: str) -> None:
        """Parse EPG response for Poland."""
        if epg_data is None:
            return
        for epg in epg_data.get("guide", []):
            if channel_id not in epg.get("channelExtId", ""):
                continue
            for sch in epg.get("programs", []):
                d = dt_util.utcnow()
                now_ts = calendar.timegm(d.utctimetuple())
                start = sch.get("startTimeUtc", 0)
                end = sch.get("endTimeUtc", 0)
                if start <= now_ts <= end:
                    self._cached_show_start_dt = start
                    self._cached_show_duration = end - start
                   
                    serie_id = sch.get("seriesId")
                    if serie_id:
                        self._cached_show_series_title = sch.get("name")
                        self._cached_show_episode = sch.get("episodeNumber")
                    else:
                        self._cached_show_title = sch.get("name")

                    img_path = sch.get("image")
                    if img_path:
                        self._cached_show_img = f"https://tvgo.orange.pl/mnapi/gopher-2epgthumb/{img_path}"
                    return

    @property
    def _cached_show_position(self) -> int:
        """Compute current show position from cached start time."""
        if self._cached_show_start_dt > 0:
            d = dt_util.utcnow()
            return calendar.timegm(d.utctimetuple()) - self._cached_show_start_dt
        return 0

    # ── Control methods ──────────────────────────────────────────────

    async def async_turn_on(self) -> None:
        """Wake the Livebox from standby."""
        await self.async_press_key(key=KEYS["POWER"])
        await asyncio.sleep(2)
        await self.async_press_key(key=KEYS["OK"])

    async def async_turn_off(self) -> None:
        """Put the Livebox in standby."""
        await self.async_press_key(key=KEYS["POWER"])

    async def async_press_key(self, key: int | str, mode: int = 0) -> dict | None:
        """Send a key press to the Livebox.

        Modes: 0=press, 1=long press, 2=release.
        """
        if isinstance(key, str):
            if key not in KEYS:
                _LOGGER.error("Unknown key: %s", key)
                return None
            key = KEYS[key]
        return await self._async_rq_livebox(
            OPERATION_KEYPRESS,
            OrderedDict([("key", key), ("mode", mode)]),
        )

    async def async_volume_up(self) -> None:
        await self.async_press_key(key=KEYS["VOL+"])

    async def async_volume_down(self) -> None:
        await self.async_press_key(key=KEYS["VOL-"])

    async def async_mute(self) -> None:
        await self.async_press_key(key=KEYS["MUTE"])

    async def async_channel_up(self) -> None:
        await self.async_press_key(key=KEYS["CH+"])

    async def async_channel_down(self) -> None:
        await self.async_press_key(key=KEYS["CH-"])

    async def async_play_pause(self) -> None:
        await self.async_press_key(key=KEYS["PLAY/PAUSE"])

    async def async_play(self) -> None:
        """Send play if currently paused."""
        # Note: media_state isn't tracked here anymore; caller should check.
        await self.async_play_pause()

    async def async_pause(self) -> None:
        """Send pause if currently playing."""
        await self.async_play_pause()

    def get_channel_names(self) -> list[str]:
        return [ch["name"] for ch in self.channels]

    def get_channel_info(self, channel: str) -> dict | None:
        """Find channel info by name or index prefix (e.g. '1. TF1')."""
        channel_index = None
        if "." in channel:
            channel_index = channel.split(".")[0].strip()
        for chan in self.channels:
            if channel_index:
                if chan["index"] == channel_index:
                    return chan
            else:
                if chan["name"].lower() == channel.lower():
                    return chan
        return None

    def get_channel_from_epg_id(self, epg_id: str) -> dict | None:
        """Find a channel by its EPG ID."""
        res = [c for c in self.channels if c["epg_id"] == epg_id]
        return res[0] if res else None

    async def async_set_channel_by_name(self, channel: str) -> None:
        """Tune to a channel by name or display string."""
        info = self.get_channel_info(channel)
        if info:
            await self.async_set_channel_by_id(info["epg_id"])
        else:
            _LOGGER.warning("Channel not found: %s", channel)

    async def async_set_channel_by_id(self, epg_id: str) -> None:
        """Tune to a channel by EPG ID."""
        epg_id_str = str(epg_id).rjust(10, "*")
        chan = self.get_channel_from_epg_id(epg_id)
        name = chan["name"] if chan else "unknown"
        _LOGGER.debug("Tune to channel %s, epg_id %s", name, epg_id_str)
        await self._async_rq_livebox(
            OPERATION_CHANNEL_CHANGE,
            OrderedDict([("epg_id", epg_id_str), ("uui", "1")]),
        )

    # ── HTTP helpers ─────────────────────────────────────────────────

    async def _async_rq_livebox(
        self, operation: str, params: dict | None = None
    ) -> dict | None:
        """Send a command to the Livebox."""
        url = f"http://{self.hostname}:{self.port}/remoteControl/cmd"
        get_params: dict = {"operation": operation}
        if params:
            get_params.update(params)
        try:
            async with self.session.get(
                url, params=get_params, timeout=self.timeout
            ) as resp:
                resp.raise_for_status()
                return await resp.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            if self._display_con_err:
                self._display_con_err = False
                _LOGGER.error("Livebox request failed: %s", err)
            return None

    async def _async_rq_epg(self, channel_id: str) -> dict | None:
        """Fetch EPG data for a channel."""
        if channel_id in ("-1", None):
            return None

        if self.country in ("france", "caraibe"):
            get_params: dict = {
                "groupBy": "channel",
                "period": "current",
                "epgIds": channel_id,
                "mco": self.epg_mco,
            }
        elif self.country == "poland":
            from datetime import timedelta

            now = dt_util.utcnow()
            target_23h = now.replace(hour=23, minute=0, second=0, microsecond=0)
            if now < target_23h:
                target_23h = target_23h - timedelta(days=1)
            epg_date = str(calendar.timegm(target_23h.utctimetuple()))

            # Return cached EPG if same period
            if self._epg_cache is not None and self._epg_cache_date == epg_date:
                _LOGGER.debug("EPG cache HIT for date=%s", epg_date)
                return self._epg_cache

            _LOGGER.debug("EPG cache MISS, fetching for date=%s", epg_date)
            get_params = {"date": epg_date, "deviceCat": "otg"}
        else:
            return None

        try:
            headers = {"User-Agent": self.epg_user_agent}
            async with self.session.get(
                self.epg_url,
                headers=headers,
                params=get_params,
                timeout=self.timeout,
            ) as resp:
                resp.raise_for_status()
                data = await resp.json(content_type=None)
                # Cache full 24h EPG response for Poland
                if data and self.country == "poland":
                    self._epg_cache = data
                    self._epg_cache_date = epg_date
                    _LOGGER.debug("EPG cached for date=%s", epg_date)
                return data
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error("EPG request failed: %s", err)
            return None
