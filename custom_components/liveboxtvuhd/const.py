from datetime import timedelta
__version__ = "1.4.2"
PROJECT_URL = "https://github.com/AkA57/liveboxtvuhd/"
ISSUE_URL = "{}issues".format(PROJECT_URL)

NAME = "liveboxtvuhd"
STARTUP = """
-------------------------------------------------------------------
{}
Version: {}
This is a custom integration.
If you have any issues with this you need to open an issue here:
{}
-------------------------------------------------------------------
""".format(
    NAME, __version__, ISSUE_URL
)


SCAN_INTERVAL = timedelta(seconds=10)
MIN_TIME_BETWEEN_SCANS = SCAN_INTERVAL
MIN_TIME_BETWEEN_FORCED_SCANS = timedelta(seconds=1)
DEFAULT_NAME = "liveboxtvuhd"
DEFAULT_PORT = 8080
CONF_COUNTRY = "country"
DEFAULT_COUNTRY = "france"


# Livebox operation
OPERATION_INFORMATION = '10'
OPERATION_CHANNEL_CHANGE = '09'
OPERATION_KEYPRESS = '01'

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
