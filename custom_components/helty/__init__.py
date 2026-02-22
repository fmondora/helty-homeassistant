"""The Helty VMC integration."""

from __future__ import annotations

import logging

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .api import HeltyCloudAPI, HeltyAuthError, HeltyConnectionError
from .const import DOMAIN
from .coordinator import HeltyDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.FAN, Platform.SENSOR, Platform.SWITCH]



async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Helty VMC from a config entry."""
    session = aiohttp.ClientSession()
    api = HeltyCloudAPI(session)

    try:
        await api.authenticate(entry.data[CONF_EMAIL], entry.data[CONF_PASSWORD])
    except HeltyAuthError as err:
        await session.close()
        raise ConfigEntryAuthFailed(str(err)) from err
    except HeltyConnectionError as err:
        await session.close()
        raise ConfigEntryNotReady(str(err)) from err

    try:
        devices = await api.find_devices()
    except HeltyConnectionError as err:
        await session.close()
        raise ConfigEntryNotReady(str(err)) from err

    if not devices:
        await session.close()
        raise ConfigEntryNotReady("No VMC devices found")

    coordinators: list[HeltyDataUpdateCoordinator] = []
    for device in devices:
        coordinator = HeltyDataUpdateCoordinator(
            hass,
            api,
            device["board_serial"],
            device["serial"],
        )
        await coordinator.async_config_entry_first_refresh()
        coordinators.append(coordinator)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "session": session,
        "devices": devices,
        "coordinators": coordinators,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Helty VMC config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        await data["session"].close()
    return unload_ok
