"""Constants for the Cambridge Audio CXA integration."""

DOMAIN = "cambridge_cxa"
DEFAULT_NAME = "Cambridge Audio CXA"
DEFAULT_PORT = 5000
CONF_CXA_TYPE = "cxa_type"

CXA_TYPE_CXA61 = "CXA61"
CXA_TYPE_CXA81 = "CXA81"
CXA_TYPES = [CXA_TYPE_CXA61, CXA_TYPE_CXA81]

MAX_VOLUME = 96  # CXA volume range is 0–96

# ---------------------------------------------------------------------------
# RS232 GET commands
# ---------------------------------------------------------------------------
AMP_CMD_GET_PWSTATE = "#01,01"
AMP_CMD_GET_CURRENT_SOURCE = "#03,01"
AMP_CMD_GET_MUTE_STATE = "#01,03"
AMP_CMD_GET_VOLUME = "#01,14"
AMP_CMD_GET_PREAMP = "#01,21"
AMP_CMD_GET_BRIGHTNESS = "#01,15"
AMP_CMD_GET_PHASE = "#01,22"

# ---------------------------------------------------------------------------
# RS232 SET commands
# ---------------------------------------------------------------------------
AMP_CMD_SET_PWR_ON = "#01,02,1"
AMP_CMD_SET_PWR_OFF = "#01,02,0"
AMP_CMD_SET_MUTE_ON = "#01,04,1"
AMP_CMD_SET_MUTE_OFF = "#01,04,0"

# Volume — step-based (community-documented; verify on your unit)
AMP_CMD_VOL_UP = "#01,16"
AMP_CMD_VOL_DOWN = "#01,17"
# Absolute volume set: send "#01,14,{0-96}"

# Pre-amp mode (CXA81)
AMP_CMD_SET_PREAMP_ON = "#01,21,1"
AMP_CMD_SET_PREAMP_OFF = "#01,21,0"

# Phase inversion (CXA81)
AMP_CMD_SET_PHASE_NORMAL = "#01,22,0"
AMP_CMD_SET_PHASE_INVERTED = "#01,22,1"

# Balance — step-based (each call shifts one step)
AMP_CMD_BALANCE_LEFT = "#01,23,0"
AMP_CMD_BALANCE_RIGHT = "#01,23,1"

# Display brightness set: send "#01,15,{0-3}"

# ---------------------------------------------------------------------------
# RS232 reply constants / prefixes
# ---------------------------------------------------------------------------
AMP_REPLY_PWR_ON = "#02,01,1"
AMP_REPLY_PWR_STANDBY = "#02,01,0"
AMP_REPLY_MUTE_ON = "#02,03,1"
AMP_REPLY_MUTE_OFF = "#02,03,0"
AMP_REPLY_VOLUME_PREFIX = "#02,14,"
AMP_REPLY_PREAMP_ON = "#02,21,1"
AMP_REPLY_PREAMP_OFF = "#02,21,0"
AMP_REPLY_BRIGHTNESS_PREFIX = "#02,15,"
AMP_REPLY_PHASE_NORMAL = "#02,22,0"
AMP_REPLY_PHASE_INVERTED = "#02,22,1"

# ---------------------------------------------------------------------------
# Input source maps
# ---------------------------------------------------------------------------
NORMAL_INPUTS_CXA61 = {
    "A1": "#03,04,00",
    "A2": "#03,04,01",
    "A3": "#03,04,02",
    "A4": "#03,04,03",
    "D1": "#03,04,04",
    "D2": "#03,04,05",
    "D3": "#03,04,06",
    "Bluetooth": "#03,04,14",
    "USB": "#03,04,16",
    "MP3": "#03,04,10",
}

NORMAL_INPUTS_CXA81 = {
    "A1": "#03,04,00",
    "A2": "#03,04,01",
    "A3": "#03,04,02",
    "A4": "#03,04,03",
    "D1": "#03,04,04",
    "D2": "#03,04,05",
    "D3": "#03,04,06",
    "Bluetooth": "#03,04,14",
    "USB": "#03,04,16",
    "XLR": "#03,04,20",
}

NORMAL_INPUTS_AMP_REPLY_CXA61 = {
    "#04,01,00": "A1",
    "#04,01,01": "A2",
    "#04,01,02": "A3",
    "#04,01,03": "A4",
    "#04,01,04": "D1",
    "#04,01,05": "D2",
    "#04,01,06": "D3",
    "#04,01,14": "Bluetooth",
    "#04,01,16": "USB",
    "#04,01,10": "MP3",
}

NORMAL_INPUTS_AMP_REPLY_CXA81 = {
    "#04,01,00": "A1",
    "#04,01,01": "A2",
    "#04,01,02": "A3",
    "#04,01,03": "A4",
    "#04,01,04": "D1",
    "#04,01,05": "D2",
    "#04,01,06": "D3",
    "#04,01,14": "Bluetooth",
    "#04,01,16": "USB",
    "#04,01,20": "XLR",
}

# ---------------------------------------------------------------------------
# Speaker / sound mode
# ---------------------------------------------------------------------------
SOUND_MODES = {
    "Speaker A": "#1,25,0",
    "Speaker A+B": "#1,25,1",
    "Speaker B": "#1,25,2",
}

# ---------------------------------------------------------------------------
# Display brightness
# ---------------------------------------------------------------------------
BRIGHTNESS_OPTIONS = {
    "Off": "0",
    "Dim": "1",
    "Medium": "2",
    "Full": "3",
}
