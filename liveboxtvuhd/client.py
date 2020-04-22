#!/usr/bin/env python
# coding: utf-8


from collections import OrderedDict
import json
import logging
import requests
import time
import homeassistant.util.dt as dt_util
import calendar

from fuzzywuzzy import process
from .const import CHANNELS
from .const import KEYS


_LOGGER = logging.getLogger(__name__)
OPERATION_INFORMATION = 10
OPERATION_CHANNEL_CHANGE = 9
OPERATION_KEYPRESS = 1
URL_EPG = 'https://rp-live-pc.woopic.com/live-webapp/v3/applications/PC/programs'



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
        self._media_state = None
        self._wol_support = None
        # data from woopic.com
        self._channel_name = None
        self._program_title = None
        self._program_definition = None
        self._program_img = None
        self._program_start_dt = 0
        self._program_duration = 0
        self._program_position = 0
        self._last_channel_id = None
        self._cache_channel_img = {}
        assert isinstance(self.info, dict), "Failed to retrive info from {}".format(self.hostname)        

    def update(self):
        _LOGGER.debug("Refresh Orange API data")
        url = "http://{}:{}/remoteControl/cmd".format(self.hostname, self.port)
        get_params = OrderedDict({"operation": OPERATION_INFORMATION})
        resp = requests.get(url, params=get_params, timeout=self.timeout)
        resp.raise_for_status()

        _data = resp.json()["result"]["data"]
        self._standby_state = _data["activeStandbyState"]
        self._osd_context = _data["osdContext"] 
        self._media_state = _data["playedMediaState"]
        self._wol_support = _data["wolSupport"]
        self._channel_id = _data["playedMediaId"]
        
        # If a channel is displayed
        if self._channel_id and self.channel_id != 'NA':

            # We should update all information only if channel or program change
            if self._channel_id != self._last_channel_id or self._program_position > self._program_duration:
                self._last_channel_id = self._channel_id
                self._channel_name = self.get_channel_from_epg_id(self._channel_id)["name"]

                # get information from EPG
                get_params = OrderedDict({"groupBy": "channel", "period": "current", "epgIds": self._channel_id, "mco": "OFR"})
                resp = requests.get(URL_EPG, params=get_params, timeout=self.timeout)
                resp.raise_for_status()
                _data2 =  resp.json()
                _LOGGER.debug(str(_data2))
                if _data2:
                    self._program_title = _data2[self._channel_id][0]["title"]
                    self._program_definition = _data2[self._channel_id][0]["definition"]
                    self._program_img = _data2[self._channel_id][0]["covers"][1]["url"]
                    self._program_start_dt = _data2[self._channel_id][0]["diffusionDate"]
                    self._program_duration = _data2[self._channel_id][0]["duration"]

            d = dt_util.utcnow()
            self._program_position = calendar.timegm(d.utctimetuple()) - self._program_start_dt
        else:
            # No channel displayed. Should be HOMEPAGE, NETFLIX, WHATEVER...
            self._channel_id = -1
            self._channel_name = self._osd_context.upper()
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
        self.update()
        return self._media_state
    
    @property
    def wol_support(self):
        return self._wol_support == "0"

    @property
    def channel_name(self):
        #self.update()
        return self._channel_name

    @channel_name.setter
    def channel_name(self, value):
        self.set_channel_by_name(value)
    
    @property
    def program_title(self):
        return self._program_title

    @property
    def program_definition(self):
        return self._program_definition

    @property
    def program_img(self):
        return self._program_img

    @property
    def program_start_dt(self):
        return self._program_start_dt

    @property
    def program_duration(self):
        return self._program_duration
    
    @property
    def program_position(self):
        return self._program_position

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
            time.sleep(0.8)
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
        return self.rq(OPERATION_KEYPRESS, OrderedDict([("key", key), ("mode", mode)]))

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
        _LOGGER.info("Tune to %s", self.get_channel_from_epg_id(epg_id)["name"])
        _LOGGER.debug("EPG ID string: %s", epg_id_str)
        url = "http://{}:{}/remoteControl/cmd?operation=09&epg_id={}&uui=1".format(
            self.hostname, self.port, epg_id_str
        )
        resp = requests.get(url, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def set_channel_by_name(self, channel):
        epg_id = self.get_channel_id_from_name(channel)
        return self.set_channel_by_id(epg_id)

    def rq(self, operation, params=None):
        url = "http://{}:{}/remoteControl/cmd".format(self.hostname, self.port)
        get_params = OrderedDict({"operation": operation})
        if params:
            get_params.update(params)
        resp = requests.get(url, params=get_params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()
