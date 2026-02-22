# Helty HCloud - Knowledge Base

Reverse-engineered from the HCloud web application at `hcloud.heltyair.com` (Angular SPA).

## Architecture Overview

```
Helty VMC Device (Flow40 Pure)
    |
    |-- WiFi --> Local Network (192.168.1.x, port 5001 NOT usable with Cloud Panel)
    |
    |-- MQTT (AWS IoT Core) --> HCloud Backend --> REST API
    |                                                |
    |-- Tuya (v3.5, productKey cbptny9rjkskvbnc)     |
                                                      |
                                         hcloud.heltyair.com (Angular SPA)
                                         api.hcloud.heltyair.com (REST)
```

**Key insight**: Cloud Panel devices do NOT support local TCP port 5001 (old Air Guard protocol).
All communication goes through the cloud via MQTT. Commands are sent via REST API, responses
come back asynchronously via MQTT and are cached in the `laststatus` log endpoint.

---

## AWS Cognito Authentication

| Parameter | Value |
|-----------|-------|
| Region | `eu-central-1` |
| User Pool ID | `eu-central-1_lejYSlqKZ` |
| Client ID | `7k0c21g92bk3413frij8rso6rk` |
| Client Secret | `REDACTED_COGNITO_CLIENT_SECRET` |
| Auth Flow | `USER_PASSWORD_AUTH` (no SECRET_HASH needed) |
| OAuth Domain | `hcloud-prod.auth.eu-central-1.amazoncognito.com` |
| OAuth Client ID | `REDACTED_OAUTH_CLIENT_ID` |
| OAuth Scopes | `profile`, `openid` |
| Redirect Sign In | `https://hcloud.heltyair.com/login` |
| Redirect Sign Out | `https://hcloud.heltyair.com/logout` |
| S3 Bucket | `REDACTED_S3_BUCKET` |
| IoT Account | `REDACTED_AWS_IOT_ACCOUNT` |

**Auth returns**: `AccessToken`, `IdToken`, `RefreshToken`. Use `IdToken` as Bearer token for API calls.

---

## User Roles

| Role | Sub-role | Description |
|------|----------|-------------|
| ADMIN | admin, editor | Full access to everything |
| COSTRUTTORE | admin, staff | Manufacturer - can manage board types, firmware, products |
| RIVENDITORE | rivenditore, installatore | Reseller/Installer - can manage products, installations |
| CLIENTE | cliente | End user - limited to own devices, sensors, basic commands |

### CLIENTE Role Restrictions
- Cannot access: `boardstats`, `productStats`, `boardType` management, user management
- Can access: own products, send commands, read sensor data via `laststatus`
- Cannot access: `logGetData`, `logSearch`, `logGetLast` (all return 404)
- Can access: `logGetLastStatus` (POST `/log/commandlogs/laststatus`)

---

## REST API Reference

Base URL: `https://api.hcloud.heltyair.com`

All requests require header: `Authorization: Bearer {IdToken}`

### Products (Devices)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/board/product/search` | Search products. Body: `{pageSize, pageNumber, status}` |
| GET | `/board/product/{productId}` | Get single product |
| GET | `/board/product/allcoords` | Get all product coordinates |
| GET | `/board/product/clienthasproducts/{clientId}` | Check if client has products |
| POST | `/board/product/count/{...}` | Count products |

**Product search filters**: `status` can be `"OK"`, `"IN CORSO"`, `"NON INSTALLATO"`.
Body format: `{"pageSize": 50, "pageNumber": 0, "status": "OK"}`

### Boards

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/board/board/{boardSerial}` | Get board by serial (includes boardType with commands/units) |
| POST | `/board/board/sendcommand/{boardSerial}` | Send command. Body: `{commandId, values}` |
| POST | `/board/board/sendmultiplecommands/{boardSerial}` | Send multiple commands |
| GET | `/board/board/allcoords` | Get all board coordinates |
| GET | `/board/board/typeSerials/{...}` | Get serials by type |

### Logs & Sensor Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/log/commandlogs/laststatus` | **Get last sensor readings**. Body: `{serialNumber}` (PRODUCT serial!) |
| GET | `/log/commandlogs/data/board/{boardId}` | Board log data (admin only) |
| GET | `/log/commandlogs/data/product/{productId}` | Product log data (admin only) |
| GET | `/log/commandlogs/lastlog/{boardId}` | Last log entry (admin only) |
| POST | `/log/commandlogs/boardstats` | Board statistics (admin only) |
| POST | `/log/commandlogs/productStats` | Product statistics (costruttore/rivenditore only) |

### Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/user/user/{userId}` | Get user |
| POST | `/user/user/search` | Search users |
| PUT | `/user/user/preferencemap` | Update preference map |
| GET | `/user/user/clients` | Get clients |
| POST | `/auth/user/changepassword` | Change password |
| GET | `/user/user/config/is-webapp-allowed` | Check webapp access |

### Board Types

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/board/boardType/{boardTypeId}` | Get board type definition |
| GET | `/board/boardType/getbyid/{id}` | Get by internal ID |
| POST | `/board/boardType/search` | Search board types |
| GET | `/board/boardType/alllines` | Get all product lines |

### Product Types

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/board/productType/search/` | Search product types |
| GET | `/board/productType/getLines` | Get product lines |
| GET | `/board/productType/clienttypes` | Get client-visible types |
| GET | `/board/productType/sellertypes` | Get seller-visible types |

### Installations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/board/installation/{productId}` | Add installation |
| DELETE | `/board/installation/{installationId}` | Delete installation |
| GET | `/board/installation/all` | Get all installations |

### Scenarios

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/board/scenario/search` | Search scenarios |
| POST | `/board/scenario/update/{scenarioId}` | Update scenario |
| POST | `/board/scenario-template/search` | Search scenario templates |

### Notifications

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/user/notification/list` | List notifications |
| GET | `/user/notification/preview` | Preview notifications |
| PUT | `/user/notification/markallasread` | Mark all as read |
| PUT | `/user/notification/{id}/markasread` | Mark one as read |

### Firmware

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/firmware/{firmwareId}` | Download firmware |
| POST | `/firmware/uploadurl` | Get upload URL |
| POST | `/firmware/update` | Update firmware |
| POST | `/firmware/remove` | Remove firmware |

### Auth Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/admin/newCustomer` | Create new customer |
| POST | `/auth/admin/newHeltyCustomer` | Create new Helty customer |
| POST | `/auth/admin/newStaff` | Create new staff |
| POST | `/auth/admin/newconstructor/` | Create new constructor |
| POST | `/auth/admin/newseller` | Create new seller |
| POST | `/auth/admin/resend-conf-email/` | Resend confirmation email |
| DELETE | `/auth/admin/staff/{staffId}` | Delete staff |

---

## Reading Sensor Data

**This is the key workflow to get temperature, CO2, humidity, VOC readings:**

1. Send `GetStatus` command (commandId=0):
   ```
   POST /board/board/sendcommand/{boardSerial}
   Body: {"commandId": 0, "values": []}
   Response: {} (empty - async)
   ```

2. Wait ~4 seconds for device to respond via MQTT

3. Read cached response:
   ```
   POST /log/commandlogs/laststatus
   Body: {"serialNumber": "{productSerial}"}   <-- NOTE: product serial, NOT board serial!
   ```

4. Response format:
   ```json
   [
     {"field": "VMCStatus",          "value": 2,    "unitId": "c4hA23O7eQQKuQpi"},
     {"field": "TemperaturaInterna", "value": 166,  "unitId": "eNRRFEl95UjuqOdO"},
     {"field": "TemperaturaEsterna", "value": 58,   "unitId": "eNRRFEl95UjuqOdO"},
     {"field": "Humidity",           "value": 463,  "unitId": "Hq8mtkeIl1ltUFbj"},
     {"field": "Anidride",           "value": 1920, "unitId": "cZG6FLnyFOi90sLt"},
     {"field": "Isobutilene",        "value": 800,  "unitId": "erSLnleTFolRlKfn"}
   ]
   ```

### Value Conversions

| Field | boardUnit | Divisor | Unit | Example |
|-------|-----------|---------|------|---------|
| TemperaturaInterna | dC | /10 | °C | 166 = 16.6°C |
| TemperaturaEsterna | dC | /10 | °C | 58 = 5.8°C |
| Humidity | dPerc | /10 | % | 463 = 46.3% |
| Anidride (CO2) | freeNum | 1 | ppm | 1920 = 1920 ppm |
| Isobutilene (VOC) | freeNum | 1 | ppb | 800 = 800 ppb |
| VMCStatus | freeNum | - | - | See status codes below |

### VMC Status Codes

| Value | Status |
|-------|--------|
| 0 | Off |
| 1 | On (normal speed) |
| 2 | Hyperventilation (boost) |
| 3 | Night mode (silent) |
| 4 | Cooling/Free heating |

---

## VMC Commands (Full List)

### Control Commands (no parameters)

| ID | Name | CLI Key | Description |
|----|------|---------|-------------|
| 20 | PowerOff | `off` | Turn VMC off |
| 21 | Cooling | `cooling` | Free cooling/heating mode |
| 22 | Night | `night` | Night (silent) mode |
| 23 | Hyperventilation | `hyper` | Hyperventilation (boost) mode |
| 24 | SpeedPlus | `speed+` | Increase speed by 1 |
| 25 | SpeedLess | `speed-` | Decrease speed by 1 |
| 44 | SetSpeed1 | `speed1` | Set speed 1 (low) |
| 45 | SetSpeed2 | `speed2` | Set speed 2 (medium-low) |
| 46 | SetSpeed3 | `speed3` | Set speed 3 (medium-high) |
| 47 | SetSpeed4 | `speed4` | Set speed 4 (high) |
| 37 | ResetFilter | `reset-filter` | Reset filter counter |
| 38 | EnableSensor | `sensor-on` | Enable automatic sensor mode |
| 39 | DisableSensor | `sensor-off` | Disable sensor mode |
| 40 | EnableStandby | `standby-on` | Enable standby |
| 41 | DisableStandby | `standby-off` | Disable standby |
| 42 | EnableLightLed | `led-on` | Turn LED panel on |
| 43 | DisableLightLed | `led-off` | Turn LED panel off |

### Read Commands (return data via laststatus)

| ID | Name | CLI Key | Response Fields |
|----|------|---------|-----------------|
| 0 | GetStatus | `status` | VMCStatus, TemperaturaInterna, TemperaturaEsterna, Humidity, Anidride, Isobutilene, + internal fields |
| 1 | GetInfo | `info` | ELPTIME, IP, V.Pacchetto Aggiornamento, V.Pacchetto Scenario, Informazioni Dettaglio |
| 32 | GetParamSpeed | `get-speeds` | FanInt/ExtSpeed1-4, NightSpeed, HyperSpeed, RaffSpeed, HighHumTrigg, LowHumTrigg, RoundsK, SpeedServoClose |
| 33 | GetParamTrigger | `get-triggers` | CO2Trigg, VocTrigg, DeltaTemp, IceAlarm, TempHumTrig, HumHighSpeed, NightLedIntensity, DeltaFreeHeating/Cooling, ConfortHeating/Cooling, etc. |
| 34 | GetParamOffset | - | OffsetSondaInterna/Esterna/Sensore/Co2, OffsetCo2, OffsetVoc, OffsetUr |
| 35 | GetParamServo | - | Servo1-3 AngleClose/Open |
| 36 | GetParamFilter | `get-filter` | Lt10SSpeed1-4, Lt10SHyper/Night/Raff/DeltaTemp/CO2Trigg/HighHumTrigg/LowHumTrigg, FilterLife |
| 48 | GetLightLed | `get-led` | Intensity |
| 49 | GetNumTab | - | NumTab |
| 51 | GetTargetId | - | TargetId |

### Write Commands (take parameters)

| ID | Name | Description | Parameters |
|----|------|-------------|------------|
| 2 | SendUpg | Send firmware upgrade | Versione, Url Base |
| 3 | Reset | Reset device | ResetType |
| 5 | GetAssociation | Get association | (returns Seriale Prodotto, CAT) |
| 8 | SendScene | Send scenario | Versione, Link |
| 9 | SetDateOffset | Set date offset | Offset (min: -1440, max: 1440, default: 60) |
| 26 | LedIntensity | Set LED brightness | Intensity (5-100%, step 7, default 50) |
| 27 | SetParamSpeed | Set speed params | 20 fan speed parameters |
| 28 | SetParamTrigger | Set trigger params | 27 sensor trigger parameters |
| 29 | SetParamOffset | Set sensor offsets | 7 offset parameters |
| 30 | SetParamServo | Set servo angles | 6 servo angle parameters |
| 31 | SetParamFilter | Set filter params | 12 filter parameters |
| 50 | SetNumTab | Set NumTab | NumTab (1-31, default 1) |
| 52 | SetTargetId | Set TargetId | TargetId (1-240, default 2) |

---

## GetStatus Response Fields (Complete)

| Index | Field | CLIENTE Visible | Unit |
|-------|-------|-----------------|------|
| 0 | Stato Registri | No | - |
| 1 | VMCStatus | Yes | Num |
| 1001 | TemperaturaInterna | Yes | °C (dC, /10) |
| 1002 | TemperaturaEsterna | Yes | °C (dC, /10) |
| 0 | Giri Ventola Interna | No | - |
| 0 | Giri Ventola Esterna | No | - |
| 0 | Angolo Servo 1 | No | - |
| 0 | Angolo Servo 2 | No | - |
| 0 | Tp Rug | No | - |
| 0 | Angolo Servo 3 | No | - |
| 1005 | Humidity | Yes | % (dPerc, /10) |
| 0 | Temperatura Sensore | No | - |
| 0 | Umidita BUS | No | - |
| 0 | Temperatura BUS | No | - |
| 1006 | Anidride (CO2) | Yes | ppm |
| 1016 | Isobutilene (VOC) | Yes | ppb |
| 0 | FilterCounter | No | - |
| 0 | Rounds K | No | - |
| 0 | TotalCounter | No | - |
| 0 | EvtTrigger | No | - |

Fields with index > 0 and CLIENTE=Yes are returned by the `laststatus` endpoint for CLIENTE role users.

---

## Unit Definitions (Key Units)

| unitId | Label | boardUnit | Symbol | Min | Max | Default |
|--------|-------|-----------|--------|-----|-----|---------|
| eNRRFEl95UjuqOdO | Temperatura | dC | °C | -500 | 500 | 0 |
| Hq8mtkeIl1ltUFbj | Umidita | dPerc | % | 0 | 1000 | 0 |
| cZG6FLnyFOi90sLt | CO2Trigg | freeNum | ppm | 1 | 9999 | 1200 |
| erSLnleTFolRlKfn | VocTrigg | freeNum | ppb | 1 | 9999 | 600 |
| c4hA23O7eQQKuQpi | Num | freeNum | - | 0 | 1000 | 0 |
| eeWBK48nQVBS91If | Intensity | freeNum | % | 5 | 100 | 50 |
| ByHHZ5o8mqnXqVW6 | Filter | freeNum | - | 0 | 65000 | 8500 |

### Fan Speed Defaults (% PWM)

| Parameter | Internal | External |
|-----------|----------|----------|
| Speed 1 | 30% | 35% |
| Speed 2 | 45% | 50% |
| Speed 3 | 55% | 60% |
| Speed 4 | 85% | 90% |
| Night | 20% | 25% |
| Hyper | 100% | 100% |
| Raff (cooling) | 30% | 85% |
| High Hum Trigger | 90% | 90% |
| Low Hum Trigger | 40% | 40% |

### Trigger Defaults

| Parameter | Default | Unit/Notes |
|-----------|---------|------------|
| CO2 Trigger | 1200 | ppm |
| VOC Trigger | 600 | ppb |
| DeltaTemp | 230 | dC (23.0°C) |
| IceAlarm | -180 | dC (-18.0°C) |
| TempHumTrig | 150 | dC (15.0°C) |
| HumHighSpeed | 60 | % |
| NightLedIntensity | 10 | % |
| DeltaFreeHeating | 30 | dC (3.0°C) |
| DeltaFreeCooling | 30 | dC (3.0°C) |
| ConfortHeating | 200 | dC (20.0°C) |
| ConfortCooling | 220 | dC (22.0°C) |
| FreeCoolingMaxMin | 20 | - |
| Rendimento | 4 | efficiency factor |
| RoundsK | 66 | - |
| FilterLife | 8500 | hours |

### Sensor Offset Defaults

| Parameter | Default |
|-----------|---------|
| OffsetSondaInterna | 0 |
| OffsetSondaEsterna | 0 |
| OffsetSondaSensore | 0 |
| OffsetSondaCo2 | -15 |
| OffsetCo2 | -20 |
| OffsetVoc | -50 |
| OffsetUr | -15 |

### Servo Angle Defaults

| Servo | Close | Open |
|-------|-------|------|
| Servo 1 | 0° | 90° |
| Servo 2 | 0° | 110° |
| Servo 3 | 0° | 60° |

---

## MQTT Topics

| Type | Topic ARN |
|------|-----------|
| Command | `arn:aws:iot:eu-central-1:REDACTED_AWS_IOT_ACCOUNT:topic/{constructorId}/prod/cmd/{boardSerial}` |
| Event | `arn:aws:iot:eu-central-1:REDACTED_AWS_IOT_ACCOUNT:topic/{constructorId}/prod/evt/{boardSerial}` |

Constructor ID for Helty: `REDACTED_CONSTRUCTOR_ID`

No Identity Pool ID was found in the webapp config, so direct MQTT subscription
from client-side is not straightforward. The webapp relies on REST polling via `laststatus`.

---

## Tuya Integration

The VMC devices also use Tuya ecosystem internally:

| Parameter | Value |
|-----------|-------|
| Product Key | `cbptny9rjkskvbnc` |
| Protocol Version | 3.5 |
| Encryption | Yes |

Devices appear on the local network as Tuya v3.5 devices but require local keys
from the Tuya IoT developer portal to communicate locally. They are NOT visible
in the standard Tuya/Smart Life app - they use a custom Tuya OEM integration
managed by Helty's backend.

The HCloud user profile stores Tuya credentials:
```json
{
  "tuya": {
    "uid": "REDACTED_TUYA_UID",
    "email": "...",
    "password": "REDACTED_TUYA_PASSWORD",
    "homeId": REDACTED_TUYA_HOME_ID
  }
}
```

---

## Device Identification

### Board Type
- ID: `rhSZ0LPx`
- MongoDB ID: `62f4feb7f7a5074120cfac0a`
- Line: `SINOTTICO VMC`
- Model: `FULL`
- Supported Firmware: 105, 107, 109, 112, 113, 115, 117, 119, 123

### Network Identification
- MAC prefix: `00:04:74` (Legrand)
- Port 5001 open but NOT usable (connection reset by Cloud Panel devices)
- mDNS: not advertised

---

## Board Type Configuration Endpoint

The richest source of data is `GET /board/board/{boardSerial}` which returns the full
board type definition including all commands, response fields, units, and firmware list.
This is available to CLIENTE role users.
