# Helty VMC - Home Assistant Integration

Custom integration for [Home Assistant](https://www.home-assistant.io/) to control **Helty Flow40 Pure** VMC (Ventilation Mechanical Controlled) devices via the HCloud cloud API.

## Author

**Francesco Mondora**
- Twitter: [@makkina](https://twitter.com/makkina)
- GitHub: [fmondora](https://github.com/fmondora)

## Features

- **Fan entity**: on/off, 4 speed levels, preset modes (Normal, Night, Hyper, Cooling)
- **5 Sensors**: indoor temperature, outdoor temperature, humidity, CO2 (ppm), VOC (ppb)
- **3 Switches**: LED panel, automatic sensor mode, standby
- Automatic sensor polling every 60 seconds
- AWS Cognito authentication with automatic token refresh
- HACS compatible

## Requirements

- A Helty VMC device with Cloud Panel (e.g. Flow40 Pure)
- An HCloud account (the one you use on [hcloud.heltyair.com](https://hcloud.heltyair.com))
- Home Assistant 2024.1 or newer

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu (top right) → **Custom repositories**
3. Add `https://github.com/fmondora/helty-homeassistant` with category **Integration**
4. Search for "Helty VMC" in HACS and click **Download**
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/helty/` folder into your Home Assistant `config/custom_components/` directory:
   ```
   config/
   └── custom_components/
       └── helty/
           ├── __init__.py
           ├── api.py
           ├── config_flow.py
           ├── const.py
           ├── coordinator.py
           ├── fan.py
           ├── manifest.json
           ├── sensor.py
           ├── strings.json
           ├── switch.py
           └── translations/
               └── en.json
   ```
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for **Helty VMC**
4. Enter your HCloud credentials:
   - **Email**: your HCloud account email
   - **Password**: your HCloud account password
5. The integration will automatically discover your VMC device(s)

After setup, the following entities will appear for each VMC device:

### Fan

| Entity | Description |
|--------|-------------|
| `fan.helty_<model>` | Main VMC control |

**Controls:**
- **On/Off**: turns the VMC on (speed 1) or off
- **Speed**: 4 levels (25% / 50% / 75% / 100%) mapped to speed 1-4
- **Preset modes**:
  - `normal` — standard ventilation (speed 1)
  - `night` — silent mode, reduced speed
  - `hyper` — boost ventilation, maximum airflow
  - `cooling` — free cooling/heating mode

### Sensors

| Entity | Description | Unit |
|--------|-------------|------|
| `sensor.helty_<model>_indoor_temperature` | Indoor air temperature | °C |
| `sensor.helty_<model>_outdoor_temperature` | Outdoor air temperature | °C |
| `sensor.helty_<model>_humidity` | Indoor humidity | % |
| `sensor.helty_<model>_co2` | CO2 concentration | ppm |
| `sensor.helty_<model>_voc` | VOC concentration | ppb |

Sensors update every 60 seconds.

### Switches

| Entity | Description |
|--------|-------------|
| `switch.helty_<model>_led` | LED panel on/off |
| `switch.helty_<model>_sensor_mode` | Automatic sensor mode on/off |
| `switch.helty_<model>_standby` | Standby mode on/off |

## Automation examples

Turn on hyper mode when CO2 is too high:

```yaml
automation:
  - alias: "VMC boost on high CO2"
    trigger:
      - platform: numeric_state
        entity_id: sensor.helty_1vmc02006e_flow40_pure_co2
        above: 1200
    action:
      - service: fan.set_preset_mode
        target:
          entity_id: fan.helty_1vmc02006e_flow40_pure
        data:
          preset_mode: hyper
```

Switch to night mode at bedtime:

```yaml
automation:
  - alias: "VMC night mode"
    trigger:
      - platform: time
        at: "22:30:00"
    action:
      - service: fan.set_preset_mode
        target:
          entity_id: fan.helty_1vmc02006e_flow40_pure
        data:
          preset_mode: night
```

## How it works

The integration communicates with the Helty HCloud REST API (`api.hcloud.heltyair.com`). The VMC device connects to the cloud via MQTT (AWS IoT Core), and commands are sent through the REST API while sensor data is retrieved by polling the `laststatus` endpoint.

```
Home Assistant → HCloud REST API → MQTT (AWS IoT Core) → Helty VMC
```

There is no local control available — the Cloud Panel does not expose a local protocol.

## License

MIT
