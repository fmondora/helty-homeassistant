"""Constants for the Helty VMC integration."""

DOMAIN = "helty"

# API Configuration
API_BASE_URL = "https://api.hcloud.heltyair.com"
COGNITO_REGION = "eu-central-1"
COGNITO_CLIENT_ID = "7k0c21g92bk3413frij8rso6rk"

# Polling interval
UPDATE_INTERVAL = 60  # seconds

# Delay after sending GetStatus before reading laststatus
STATUS_READ_DELAY = 4  # seconds

# VMC Command IDs
CMD_GET_STATUS = 0
CMD_GET_INFO = 1
CMD_POWER_OFF = 20
CMD_COOLING = 21
CMD_NIGHT = 22
CMD_HYPER = 23
CMD_SPEED_PLUS = 24
CMD_SPEED_MINUS = 25
CMD_SET_SPEED_1 = 44
CMD_SET_SPEED_2 = 45
CMD_SET_SPEED_3 = 46
CMD_SET_SPEED_4 = 47
CMD_RESET_FILTER = 37
CMD_ENABLE_SENSOR = 38
CMD_DISABLE_SENSOR = 39
CMD_ENABLE_STANDBY = 40
CMD_DISABLE_STANDBY = 41
CMD_ENABLE_LED = 42
CMD_DISABLE_LED = 43

# Speed level to command ID mapping
SPEED_COMMANDS = {
    1: CMD_SET_SPEED_1,
    2: CMD_SET_SPEED_2,
    3: CMD_SET_SPEED_3,
    4: CMD_SET_SPEED_4,
}

# Fan preset modes
PRESET_NORMAL = "normal"
PRESET_NIGHT = "night"
PRESET_HYPER = "hyper"
PRESET_COOLING = "cooling"

PRESET_MODE_COMMANDS = {
    PRESET_NORMAL: CMD_SET_SPEED_1,
    PRESET_NIGHT: CMD_NIGHT,
    PRESET_HYPER: CMD_HYPER,
    PRESET_COOLING: CMD_COOLING,
}

PRESET_MODES = [PRESET_NORMAL, PRESET_NIGHT, PRESET_HYPER, PRESET_COOLING]

# VMC Status codes
VMC_STATUS_OFF = 0
VMC_STATUS_NORMAL = 1
VMC_STATUS_HYPER = 2
VMC_STATUS_NIGHT = 3
VMC_STATUS_COOLING = 4

VMC_STATUS_NAMES = {
    VMC_STATUS_OFF: "Off",
    VMC_STATUS_NORMAL: "Normal",
    VMC_STATUS_HYPER: "Hyperventilation",
    VMC_STATUS_NIGHT: "Night",
    VMC_STATUS_COOLING: "Cooling",
}

# Map VMC status to preset mode
VMC_STATUS_TO_PRESET = {
    VMC_STATUS_NORMAL: PRESET_NORMAL,
    VMC_STATUS_HYPER: PRESET_HYPER,
    VMC_STATUS_NIGHT: PRESET_NIGHT,
    VMC_STATUS_COOLING: PRESET_COOLING,
}

# Sensor field definitions: (field_name, label, divisor, unit)
SENSOR_FIELDS = {
    "TemperaturaInterna": ("temp_indoor", 10.0, "°C"),
    "TemperaturaEsterna": ("temp_outdoor", 10.0, "°C"),
    "Humidity": ("humidity", 10.0, "%"),
    "Anidride": ("co2", 1.0, "ppm"),
    "Isobutilene": ("voc", 1.0, "ppb"),
    "VMCStatus": ("vmc_status", None, ""),
}

# Number of speed levels
SPEED_COUNT = 4
