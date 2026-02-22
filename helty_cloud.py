#!/usr/bin/env python3
"""
Helty HCloud API Client
Controls Helty VMC devices via the HCloud cloud API.
Reverse-engineered from the HCloud web application (hcloud.heltyair.com).
"""

import json
import os
import sys
import time
import boto3
import requests
from dotenv import load_dotenv

# AWS Cognito Configuration
COGNITO_REGION = "eu-central-1"
CLIENT_ID = "7k0c21g92bk3413frij8rso6rk"

# API Configuration
API_BASE_URL = "https://api.hcloud.heltyair.com"

# VMC Commands (from boardType config)
COMMANDS = {
    "status":           {"id": 0,  "name": "GetStatus",         "desc": "Read current status, temperatures, humidity, CO2, VOC"},
    "info":             {"id": 1,  "name": "GetInfo",            "desc": "Get device info (IP, firmware versions)"},
    "off":              {"id": 20, "name": "PowerOff",           "desc": "Turn VMC off"},
    "cooling":          {"id": 21, "name": "Cooling",            "desc": "Free cooling/heating mode"},
    "night":            {"id": 22, "name": "Night",              "desc": "Night (silent) mode"},
    "hyper":            {"id": 23, "name": "Hyperventilation",   "desc": "Hyperventilation (boost) mode"},
    "speed+":           {"id": 24, "name": "SpeedPlus",          "desc": "Increase speed by 1"},
    "speed-":           {"id": 25, "name": "SpeedLess",          "desc": "Decrease speed by 1"},
    "speed1":           {"id": 44, "name": "SetSpeed1",          "desc": "Set speed 1 (low)"},
    "speed2":           {"id": 45, "name": "SetSpeed2",          "desc": "Set speed 2 (medium-low)"},
    "speed3":           {"id": 46, "name": "SetSpeed3",          "desc": "Set speed 3 (medium-high)"},
    "speed4":           {"id": 47, "name": "SetSpeed4",          "desc": "Set speed 4 (high)"},
    "reset-filter":     {"id": 37, "name": "ResetFilter",        "desc": "Reset filter counter"},
    "sensor-on":        {"id": 38, "name": "EnableSensor",       "desc": "Enable automatic sensor mode"},
    "sensor-off":       {"id": 39, "name": "DisableSensor",      "desc": "Disable sensor mode"},
    "standby-on":       {"id": 40, "name": "EnableStandby",      "desc": "Enable standby"},
    "standby-off":      {"id": 41, "name": "DisableStandby",     "desc": "Disable standby"},
    "led-on":           {"id": 42, "name": "EnableLightLed",     "desc": "Turn LED panel on"},
    "led-off":          {"id": 43, "name": "DisableLightLed",    "desc": "Turn LED panel off"},
    "get-speeds":       {"id": 32, "name": "GetParamSpeed",      "desc": "Get fan speed parameters"},
    "get-triggers":     {"id": 33, "name": "GetParamTrigger",    "desc": "Get sensor trigger parameters"},
    "get-filter":       {"id": 36, "name": "GetParamFilter",     "desc": "Get filter parameters"},
    "get-led":          {"id": 48, "name": "GetLightLed",        "desc": "Get LED intensity"},
    "sensors":          {"id": -1, "name": "ReadSensors",        "desc": "Read temperature, CO2, humidity, VOC (special)"},
}

# VMC Status codes
VMC_STATUSES = {
    0: "Off",
    1: "On (normal)",
    2: "Hyperventilation",
    3: "Night mode",
    4: "Cooling",
}

# Unit conversions: boardUnit -> (divisor, suffix)
UNIT_CONVERT = {
    "dC": (10.0, "C"),
    "dPerc": (10.0, "%"),
}


def authenticate(username, password):
    """Authenticate with AWS Cognito and return tokens."""
    client = boto3.client("cognito-idp", region_name=COGNITO_REGION)
    try:
        response = client.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": username, "PASSWORD": password},
        )
        if "AuthenticationResult" in response:
            return response["AuthenticationResult"]
        elif "ChallengeName" in response:
            print(f"Challenge required: {response['ChallengeName']}")
    except Exception as e:
        print(f"Auth error: {e}")
    return None


def api(method, path, token, data=None):
    """Make an authenticated API request."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{API_BASE_URL}{path}"
    if method == "GET":
        return requests.get(url, headers=headers, timeout=15)
    elif method == "POST":
        return requests.post(url, headers=headers, json=data, timeout=15)
    elif method == "PUT":
        return requests.put(url, headers=headers, json=data, timeout=15)


def find_my_devices(token):
    """Find VMC devices assigned to the authenticated user."""
    resp = api("POST", "/board/product/search", token, {"pageSize": 50, "pageNumber": 0, "status": "OK"})
    if resp.status_code != 200:
        return []

    products = resp.json().get("data", [])
    my_devices = []
    for p in products:
        ci = p.get("clientInfo")
        if ci and ci.get("mail"):
            cb = p.get("cloudBoard", {})
            inst = p.get("currentInstallation", {})
            my_devices.append({
                "product_id": p["_id"],
                "serial": p.get("serialNumber"),
                "model": p.get("productType", {}).get("model", "Unknown"),
                "line": p.get("productType", {}).get("line", ""),
                "board_serial": p.get("boardSerialNumber"),
                "board_id": cb.get("_id") if cb else None,
                "installation": f"{inst.get('name', '')} - {inst.get('place', '')}" if inst else "N/A",
                "owner": f"{ci.get('name', '')} {ci.get('lastName', '')}",
                "email": ci.get("mail"),
            })
    return my_devices


def read_sensors(token, board_serial, product_serial):
    """Send GetStatus and read sensor data from the device."""
    # Send GetStatus command
    api("POST", f"/board/board/sendcommand/{board_serial}", token,
        {"commandId": 0, "values": []})
    # Wait for the device to respond via MQTT
    time.sleep(4)
    # Read last status from log endpoint
    resp = api("POST", "/log/commandlogs/laststatus", token,
               {"serialNumber": product_serial})
    if not resp or resp.status_code != 200:
        return None
    return resp.json()


def format_sensors(data):
    """Format sensor data for display."""
    if not data:
        print("  No sensor data available.")
        return

    # Known field mappings
    fields = {
        "TemperaturaInterna": ("Temp. Interna", 10.0, "\u00b0C"),
        "TemperaturaEsterna": ("Temp. Esterna", 10.0, "\u00b0C"),
        "Humidity":           ("Umidit\u00e0",       10.0, "%"),
        "Anidride":           ("CO2",          1.0,  "ppm"),
        "Isobutilene":        ("VOC",          1.0,  "ppb"),
        "VMCStatus":          ("Stato VMC",    None,  ""),
    }

    print("\n  +---------------------+------------+")
    print("  | Sensore             | Valore     |")
    print("  +---------------------+------------+")
    for item in data:
        name = item.get("field", "")
        value = item.get("value", 0)
        if name in fields:
            label, divisor, unit = fields[name]
            if name == "VMCStatus":
                display = VMC_STATUSES.get(value, f"Unknown ({value})")
            elif divisor and divisor != 1.0:
                display = f"{value / divisor:.1f} {unit}"
            else:
                display = f"{value} {unit}"
            print(f"  | {label:19s} | {display:>10s} |")
    print("  +---------------------+------------+")


def send_command(token, board_serial, command_name):
    """Send a command to a VMC device."""
    if command_name not in COMMANDS:
        print(f"Unknown command: {command_name}")
        print(f"Available: {', '.join(sorted(COMMANDS.keys()))}")
        return None

    cmd = COMMANDS[command_name]
    resp = api("POST", f"/board/board/sendcommand/{board_serial}", token,
               {"commandId": cmd["id"], "values": []})
    return resp


def print_devices(devices):
    """Print device list."""
    for i, d in enumerate(devices):
        print(f"\n  [{i+1}] {d['model']}")
        print(f"      Serial: {d['serial']}")
        print(f"      Board:  {d['board_serial']}")
        print(f"      Location: {d['installation']}")
        print(f"      Owner: {d['owner']}")


def print_commands():
    """Print available commands."""
    print("\n  Available commands:")
    categories = {
        "Status": ["sensors", "status", "info"],
        "Speed":  ["speed1", "speed2", "speed3", "speed4", "speed+", "speed-"],
        "Mode":   ["night", "hyper", "cooling", "off"],
        "Sensor": ["sensor-on", "sensor-off"],
        "LED":    ["led-on", "led-off"],
        "Other":  ["standby-on", "standby-off", "reset-filter"],
        "Debug":  ["get-speeds", "get-triggers", "get-filter", "get-led"],
    }
    for cat, cmds in categories.items():
        print(f"\n  {cat}:")
        for c in cmds:
            cmd = COMMANDS[c]
            print(f"    {c:20s} {cmd['desc']}")


def interactive(token, devices):
    """Interactive control mode."""
    if not devices:
        print("No devices found.")
        return

    if len(devices) == 1:
        device = devices[0]
    else:
        print_devices(devices)
        try:
            idx = int(input("\nSelect device number: ")) - 1
            device = devices[idx]
        except (ValueError, IndexError):
            print("Invalid selection.")
            return

    board = device["board_serial"]
    print(f"\nConnected to: {device['model']} at {device['installation']}")
    print(f"Board: {board}")
    print_commands()

    while True:
        try:
            cmd = input(f"\nhelty [{device['installation']}]> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if cmd in ("quit", "exit", "q"):
            break
        elif cmd in ("help", "h", "?"):
            print_commands()
        elif cmd == "devices":
            print_devices(devices)
        elif cmd == "sensors":
            print("  Reading sensors (wait ~4s)...", flush=True)
            data = read_sensors(token, board, device["serial"])
            format_sensors(data)
        elif cmd in COMMANDS:
            print(f"  Sending {COMMANDS[cmd]['name']}...", end=" ", flush=True)
            resp = send_command(token, board, cmd)
            if resp and resp.status_code == 200:
                print("OK")
                body = resp.json() if resp.text else {}
                if body:
                    print(f"  Response: {json.dumps(body, indent=2)}")
            else:
                print(f"FAILED ({resp.status_code if resp else 'no response'})")
                if resp:
                    print(f"  {resp.text[:300]}")
        else:
            print(f"  Unknown command: {cmd}")
            print(f"  Type 'help' for available commands")


def main():
    load_dotenv()

    command = sys.argv[1] if len(sys.argv) > 1 else None
    username = os.environ.get("HELTY_EMAIL")
    password = os.environ.get("HELTY_PASSWORD")

    if not username or not password:
        print("Helty VMC Cloud Controller")
        print("Set HELTY_EMAIL and HELTY_PASSWORD in .env or environment.")
        print(f"\nUsage: python {sys.argv[0]} [command]")
        print(f"\nCommands: {', '.join(sorted(COMMANDS.keys()))}")
        print("\nIf no command is given, enters interactive mode.")
        sys.exit(1)

    print("Authenticating with HCloud...")
    tokens = authenticate(username, password)
    if not tokens:
        print("Authentication failed.")
        sys.exit(1)
    print("Authenticated!")

    token = tokens["IdToken"]

    print("Finding your VMC devices...")
    devices = find_my_devices(token)

    if not devices:
        print("No VMC devices found assigned to your account.")
        sys.exit(1)

    print(f"Found {len(devices)} device(s):")
    print_devices(devices)

    if command:
        # Single command mode
        device = devices[0]
        board = device["board_serial"]
        if command == "sensors":
            print("\nReading sensors (wait ~4s)...")
            data = read_sensors(token, board, device["serial"])
            format_sensors(data)
        else:
            print(f"\nSending '{command}' to {board}...")
            resp = send_command(token, board, command)
            if resp and resp.status_code == 200:
                print("Command sent successfully!")
                body = resp.json() if resp.text else {}
                if body:
                    print(json.dumps(body, indent=2))
            else:
                print(f"Failed: {resp.status_code if resp else 'no response'}")
                if resp:
                    print(resp.text[:300])
    else:
        # Interactive mode
        interactive(token, devices)


if __name__ == "__main__":
    main()
