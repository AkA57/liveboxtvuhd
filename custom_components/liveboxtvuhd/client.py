#!/usr/bin/env python
# coding: utf-8
from collections import OrderedDict
import json
import logging
import requests
import time
import homeassistant.util.dt as dt_util
import calendar
import os

from fuzzywuzzy import process
from .const import CHANNELS
from .const import KEYS
from .const import (
    OPERATION_INFORMATION,
    OPERATION_CHANNEL_CHANGE,
    OPERATION_KEYPRESS,
    URL_EPG,
)
from homeassistant.components.media_player.const import (
    MEDIA_TYPE_CHANNEL,
    MEDIA_TYPE_TVSHOW,
)

_LOGGER = logging.getLogger(__name__)

class LiveboxTvUhdClient(object):
    def __init__(self, hostname, port=8080, timeout=3, refresh_frequency=60):
        from datetime import timedelta
        self.hostname = hostname
        self.port = port
        self.timeout = timeout
        self.refresh_frequency = timedelta(seconds=refresh_frequency)
        # data from livebox
        self._name = None
        self._standby_state = False
        self._channel_id = None
        self._osd_context = None
        self._wol_support = None
        self._media_state = None
        self._media_type = None
        self._show_series_title = None
        self._show_season = None
        self._show_episode = None
        # data from woopic.com
        self._channel_name = None
        self._show_title = None
        self._show_definition = None
        self._show_img = None
        self._show_start_dt = 0
        self._show_duration = 0
        self._show_position = 0
        self._last_channel_id = None
        self._cache_channel_img = {}

    def update(self):
        _LOGGER.debug("Refresh Orange API data")
        _data = self.rq_livebox(OPERATION_INFORMATION)["result"]["data"]

        if _data:
            self._standby_state = _data["activeStandbyState"]
            self._osd_context = _data["osdContext"] 
            self._wol_support = _data["wolSupport"]

            self._channel_id = None          
            self._media_state = "UNKNOW"
            if "playedMediaState" in _data:
                self._media_state = _data["playedMediaState"]

            if "playedMediaId" in _data:
                self._channel_id = _data["playedMediaId"]

        # If a channel is displayed
        if self._channel_id and self.get_channel_from_epg_id(self._channel_id):

            # We should update all information only if channel or show change
            if self._channel_id != self._last_channel_id or self._show_position > self._show_duration: 
                self._last_channel_id = self._channel_id
                self._channel_name = self.get_channel_from_epg_id(self._channel_id)["name"]

                # Reset everything
                self._show_series_title = None
                self._show_season = None
                self._show_episode = None
                self._show_title = None
                self._show_img = None
                self._show_position = 0
                self._show_start_dt = 0

                # Get EPG information
                _data2 =  self.rq_epg(self._channel_id)
                
                if _data2 != None and _data2[self._channel_id]:
                    # Show title depending of programType
                    if _data2[self._channel_id][0]["programType"] == "EPISODE":
                        self._media_type = MEDIA_TYPE_TVSHOW
                        self._show_series_title = _data2[self._channel_id][0]["title"]
                        self._show_season = _data2[self._channel_id][0]["season"]["number"]
                        self._show_episode = _data2[self._channel_id][0]["episodeNumber"]
                        self._show_title = _data2[self._channel_id][0]["season"]["serie"]["title"]
                    else:
                        self._media_type = MEDIA_TYPE_CHANNEL                    
                        self._show_title = _data2[self._channel_id][0]["title"]


                    self._show_definition = _data2[self._channel_id][0]["definition"]
                    self._show_start_dt = _data2[self._channel_id][0]["diffusionDate"]
                    self._show_duration = _data2[self._channel_id][0]["duration"]
                    if _data2[self._channel_id][0]["covers"]:
                        self._show_img = _data2[self._channel_id][0]["covers"][1]["url"]

            # update position if we have show information
            if self._show_start_dt > 0: 
                d = dt_util.utcnow()
                self._show_position = calendar.timegm(d.utctimetuple()) - self._show_start_dt
        else:
            # Unknow or no channel displayed. Should be HOMEPAGE, NETFLIX, WHATEVER...
            self._channel_id = -1
            self._last_channel_id = self._channel_id
            self._media_type = MEDIA_TYPE_CHANNEL
            self._channel_name = self._osd_context.upper()
            self._show_title = None
            self._show_season = None
            self._show_episode = None
            self._show_title = None
            self._show_definition = None
            self._show_img = None
            self._show_start_dt = 0
            self._show_duration = 0
            self._show_position = 0
        return _data
        

    
    @property 
    def name(self):
        return self._name

    @property 
    def standby_state(self):
        return self._standby_state == "0"

    @property
    def channel_id(self):
        return self._channel_id

    @property
    def osd_context(self):
        return self._osd_context

    @property
    def media_state(self):
        return self._media_state

    @property
    def media_type(self):
        return self._media_type

    @property
    def show_series_title(self):
        return self._show_series_title

    @property
    def show_season(self):
        return self._show_season

    @property
    def show_episode(self):
        return self._show_episode

    @property
    def wol_support(self):
        return self._wol_support == "0"

    @property
    def channel_name(self):
        return self._channel_name

    @channel_name.setter
    def channel_name(self, value):
        self.set_channel_by_name(value)
    
    @property
    def show_title(self):
        return self._show_title

    @property
    def show_definition(self):
        return self._show_definition

    @property
    def show_img(self):
        return self._show_img

    @property
    def show_start_dt(self):
        return self._show_start_dt

    @property
    def show_duration(self):
        return self._show_duration
    
    @property
    def show_position(self):
        return self._show_position

    @property
    def is_on(self):
        return self.standby_state

    @property
    def info(self):
        return self.update()

    # TODO
    @staticmethod
    def discover():
        pass

    def get_channels(self):
        return CHANNELS

    def turn_on(self):
        if not self.standby_state:
            self.press_key(key=KEYS["POWER"])
            time.sleep(2)
            self.press_key(key=KEYS["OK"])

    def turn_off(self):
        if self.standby_state:
            return self.press_key(key=KEYS["POWER"])

    def __get_key_name(self, key_id):
        for key_name, k_id in KEYS.items():
            if k_id == key_id:
                return key_name

    def press_key(self, key, mode=0):
        """
        modes:
            0 -> simple press
            1 -> long press
            2 -> release after long press
        """
        if isinstance(key, str):
            assert key in KEYS, "No such key: {}".format(key)
            key = KEYS[key]
        _LOGGER.info("Press key %s", self.__get_key_name(key))
        return self.rq_livebox(OPERATION_KEYPRESS, OrderedDict([("key", key), ("mode", mode)]))

    def volume_up(self):
        return self.press_key(key=KEYS["VOL+"])

    def volume_down(self):
        return self.press_key(key=KEYS["VOL-"])

    def mute(self):
        return self.press_key(key=KEYS["MUTE"])

    def channel_up(self):
        return self.press_key(key=KEYS["CH+"])

    def channel_down(self):
        return self.press_key(key=KEYS["CH-"])

    def play_pause(self):
        return self.press_key(key=KEYS["PLAY/PAUSE"])

    def play(self):
        if self.media_state == "PAUSE":
            return self.play_pause()
        _LOGGER.debug("Media is already playing.")

    def pause(self):
        if self.media_state == "PLAY":
            return self.play_pause()
        _LOGGER.debug("Media is already paused.")

    def get_channel_names(self, json_output=False):
        channels = [x["name"] for x in CHANNELS]
        return json.dumps(channels) if json_output else channels

    def get_channel_info(self, channel):
        # If the channel start with '#' search by channel number
        channel_index = None
        if channel.startswith("#"):
            channel_index = channel.split("#")[1]
        # Look for an exact match first
        for chan in CHANNELS:
            if channel_index:
                if chan["index"] == channel_index:
                    return chan
            else:
                if chan["name"].lower() == channel.lower():
                    return chan
        # Try fuzzy matching it that did not give any result
        chan = process.extractOne(channel, CHANNELS)[0]
        return chan

    def get_channel_id_from_name(self, channel):
        return self.get_channel_info(channel)["epg_id"]

    def get_channel_from_epg_id(self, epg_id):
        res = [c for c in CHANNELS if c["epg_id"] == epg_id]
        return res[0] if res else None

    def set_channel_by_id(self, epg_id):
        # The EPG ID needs to be 10 chars long, padded with '*' chars
        epg_id_str = str(epg_id).rjust(10, "*")
        _LOGGER.debug("Tune to channel %s, epg_id %s", self.get_channel_from_epg_id(epg_id)["name"], epg_id_str)
        return self.rq_livebox(OPERATION_CHANNEL_CHANGE, OrderedDict([("epg_id", epg_id_str), ("uui", "1")]))

    def set_channel_by_name(self, channel):
        epg_id = self.get_channel_id_from_name(channel)
        return self.set_channel_by_id(epg_id)

    def rq_livebox(self, operation, params=None):
        url = "http://{}:{}/remoteControl/cmd".format(self.hostname, self.port)
        get_params = OrderedDict({"operation": operation})
        _LOGGER.debug("Request Livebox operation %s", operation)
        if params:
            get_params.update(params)
        try:
            r = requests.get(url, params=get_params, timeout=self.timeout)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as err:
            raise SystemExit(err)
        except requests.exceptions.HTTPError as errh:
            raise SystemExit(errh)
        except requests.exceptions.ConnectionError as errc:
            raise SystemExit(errc)
        except requests.exceptions.Timeout as errt:
            raise SystemExit(errt)            

    def rq_epg(self, channel_id):
        get_params = OrderedDict({"groupBy": "channel", "period": "current", "epgIds": channel_id, "mco": "OFR"})
        _LOGGER.debug("Request EPG channel id %s", channel_id)
        try:
            r = requests.get(URL_EPG, params=get_params, timeout=self.timeout)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as err:
            pass
        except requests.exceptions.HTTPError as errh:
            pass
        except requests.exceptions.ConnectionError as errc:
            pass
        except requests.exceptions.Timeout as errt:
            pass




           
            
            

