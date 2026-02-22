"""Async API client for Helty HCloud."""

from __future__ import annotations

import asyncio
import json
import logging
import time

import aiohttp

from .const import (
    API_BASE_URL,
    COGNITO_CLIENT_ID,
    COGNITO_REGION,
    SENSOR_FIELDS,
    STATUS_READ_DELAY,
)

_LOGGER = logging.getLogger(__name__)

COGNITO_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/"


class HeltyAuthError(Exception):
    """Authentication error."""


class HeltyConnectionError(Exception):
    """Connection error."""


class HeltyCloudAPI:
    """Async client for the Helty HCloud REST API."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize the API client."""
        self._session = session
        self._access_token: str | None = None
        self._id_token: str | None = None
        self._refresh_token: str | None = None
        self._token_expiry: float = 0
        self._email: str | None = None
        self._password: str | None = None

    @property
    def id_token(self) -> str | None:
        """Return the current ID token."""
        return self._id_token

    async def _cognito_request(self, action: str, payload: dict) -> dict:
        """Make a direct HTTP request to the Cognito API."""
        headers = {
            "Content-Type": "application/x-amz-json-1.1",
            "X-Amz-Target": f"AWSCognitoIdentityProviderService.{action}",
        }
        try:
            async with self._session.post(
                COGNITO_URL,
                headers=headers,
                data=json.dumps(payload),
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                body = json.loads(await resp.text())
                if resp.status != 200:
                    error_type = body.get("__type", "")
                    error_msg = body.get("message", "Unknown error")
                    if "NotAuthorizedException" in error_type:
                        raise HeltyAuthError("Invalid email or password")
                    if "UserNotFoundException" in error_type:
                        raise HeltyAuthError("User not found")
                    raise HeltyConnectionError(
                        f"Cognito error: {error_type} - {error_msg}"
                    )
                return body
        except aiohttp.ClientError as err:
            raise HeltyConnectionError(
                f"Failed to connect to Cognito: {err}"
            ) from err

    async def authenticate(self, email: str, password: str) -> dict:
        """Authenticate with AWS Cognito and return tokens."""
        self._email = email
        self._password = password

        response = await self._cognito_request(
            "InitiateAuth",
            {
                "AuthFlow": "USER_PASSWORD_AUTH",
                "ClientId": COGNITO_CLIENT_ID,
                "AuthParameters": {
                    "USERNAME": email,
                    "PASSWORD": password,
                },
            },
        )

        if "AuthenticationResult" not in response:
            challenge = response.get("ChallengeName", "unknown")
            raise HeltyAuthError(f"Authentication challenge required: {challenge}")

        result = response["AuthenticationResult"]
        self._access_token = result.get("AccessToken")
        self._id_token = result["IdToken"]
        self._refresh_token = result.get("RefreshToken", self._refresh_token)
        # Tokens expire in 1 hour; refresh 5 minutes early
        self._token_expiry = time.time() + result.get("ExpiresIn", 3600) - 300
        return result

    async def _ensure_token(self) -> None:
        """Refresh the token if expired."""
        if time.time() < self._token_expiry:
            return

        if self._refresh_token:
            try:
                await self._refresh_auth()
                return
            except Exception:
                _LOGGER.debug("Token refresh failed, re-authenticating")

        if self._email and self._password:
            await self.authenticate(self._email, self._password)
        else:
            raise HeltyAuthError("Token expired and no credentials available")

    async def _refresh_auth(self) -> None:
        """Refresh authentication using refresh token."""
        response = await self._cognito_request(
            "InitiateAuth",
            {
                "AuthFlow": "REFRESH_TOKEN_AUTH",
                "ClientId": COGNITO_CLIENT_ID,
                "AuthParameters": {
                    "REFRESH_TOKEN": self._refresh_token,
                },
            },
        )

        result = response["AuthenticationResult"]
        self._access_token = result.get("AccessToken")
        self._id_token = result["IdToken"]
        self._token_expiry = time.time() + result.get("ExpiresIn", 3600) - 300

    async def _request(
        self, method: str, path: str, data: dict | None = None
    ) -> dict | list | None:
        """Make an authenticated API request."""
        await self._ensure_token()

        url = f"{API_BASE_URL}{path}"
        headers = {
            "Authorization": f"Bearer {self._id_token}",
            "Content-Type": "application/json",
        }

        try:
            async with self._session.request(
                method, url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 401:
                    # Token may have been invalidated; force refresh and retry once
                    self._token_expiry = 0
                    await self._ensure_token()
                    headers["Authorization"] = f"Bearer {self._id_token}"
                    async with self._session.request(
                        method, url, headers=headers, json=data,
                        timeout=aiohttp.ClientTimeout(total=15),
                    ) as retry_resp:
                        retry_resp.raise_for_status()
                        return await retry_resp.json()
                resp.raise_for_status()
                text = await resp.text()
                if not text:
                    return {}
                return await resp.json()
        except aiohttp.ClientError as err:
            raise HeltyConnectionError(f"API request failed: {err}") from err

    async def find_devices(self) -> list[dict]:
        """Find VMC devices assigned to the authenticated user."""
        result = await self._request(
            "POST",
            "/board/product/search",
            {"pageSize": 50, "pageNumber": 0, "status": "OK"},
        )

        products = result.get("data", []) if isinstance(result, dict) else []
        devices = []
        for p in products:
            ci = p.get("clientInfo")
            if not ci or not ci.get("mail"):
                continue
            # Only include devices belonging to the authenticated user
            if self._email and ci["mail"].lower() != self._email.lower():
                continue
            cb = p.get("cloudBoard", {})
            inst = p.get("currentInstallation", {})
            devices.append(
                {
                    "product_id": p["_id"],
                    "serial": p.get("serialNumber"),
                    "model": p.get("productType", {}).get("model", "Unknown"),
                    "line": p.get("productType", {}).get("line", ""),
                    "board_serial": p.get("boardSerialNumber"),
                    "board_id": cb.get("_id") if cb else None,
                    "installation": (
                        f"{inst.get('name', '')} - {inst.get('place', '')}"
                        if inst
                        else "N/A"
                    ),
                    "owner": f"{ci.get('name', '')} {ci.get('lastName', '')}",
                    "email": ci.get("mail"),
                }
            )
        return devices

    async def send_command(self, board_serial: str, command_id: int) -> dict:
        """Send a command to a VMC device."""
        result = await self._request(
            "POST",
            f"/board/board/sendcommand/{board_serial}",
            {"commandId": command_id, "values": []},
        )
        return result or {}

    async def read_sensors(
        self, board_serial: str, product_serial: str
    ) -> dict:
        """Send GetStatus and read sensor data. Returns parsed dict."""
        # Send GetStatus command
        await self.send_command(board_serial, 0)

        # Wait for the device to respond via MQTT
        await asyncio.sleep(STATUS_READ_DELAY)

        # Read last status
        raw = await self._request(
            "POST",
            "/log/commandlogs/laststatus",
            {"serialNumber": product_serial},
        )

        return self._parse_sensor_data(raw)

    @staticmethod
    def _parse_sensor_data(raw: list | dict | None) -> dict:
        """Parse raw sensor response into a clean dict."""
        data: dict = {}
        if not raw or not isinstance(raw, list):
            return data

        for item in raw:
            field = item.get("field", "")
            value = item.get("value", 0)
            if field in SENSOR_FIELDS:
                key, divisor, _unit = SENSOR_FIELDS[field]
                if divisor is not None and divisor != 1.0:
                    data[key] = round(value / divisor, 1)
                else:
                    data[key] = value

        return data
