"""Constants for the Orange Livebox TV UHD integration."""
from datetime import timedelta

__version__ = "2.0.0"

DOMAIN = "liveboxtvuhd"
PLATFORMS = ["media_player", "remote"]
COUNTRIES = ["france", "caraibe", "poland"]

SCAN_INTERVAL = timedelta(seconds=30)
CONF_COUNTRY = "country"
CONF_MAC = "mac"

DEFAULT_NAME = "Orange Livebox TV UHD"
DEFAULT_PORT = 8080
DEFAULT_COUNTRY = "france"

# Livebox operation codes
OPERATION_INFORMATION = "10"
OPERATION_CHANNEL_CHANGE = "09"
OPERATION_KEYPRESS = "01"

# Livebox key codes
KEYS = {
    "POWER": 116,
    "0": 512,
    "1": 513,
    "2": 514,
    "3": 515,
    "4": 516,
    "5": 517,
    "6": 518,
    "7": 519,
    "8": 520,
    "9": 521,
    "CH+": 402,
    "CHANNEL_UP": 402,
    "CH-": 403,
    "CHANNEL_DOWN": 403,
    "VOL+": 115,
    "VOLUME_UP": 115,
    "VOL-": 114,
    "VOLUME_DOWN": 114,
    "MUTE": 113,
    "UP": 103,
    "DPAD_UP": 103,
    "DOWN": 108,
    "DPAD_DOWN": 108,
    "LEFT": 105,
    "DPAD_LEFT": 105,
    "RIGHT": 106,
    "DPAD_RIGHT": 106,
    "OK": 352,
    "DPAD_CENTER": 352,
    "BACK": 158,
    "MENU": 139,
    "PLAY/PAUSE": 164,
    "MEDIA_PLAY_PAUSE": 164,
    "FBWD": 168,
    "MEDIA_REWIND": 168,
    "FFWD": 159,
    "MEDIA_FAST_FORWARD": 159,
    "REC": 167,
    "MEDIA_RECORD": 167,
    "VOD": 393,
    "GUIDE": 365,
}
