"""Switch platform for Helty VMC."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CMD_DISABLE_LED,
    CMD_DISABLE_SENSOR,
    CMD_DISABLE_STANDBY,
    CMD_ENABLE_LED,
    CMD_ENABLE_SENSOR,
    CMD_ENABLE_STANDBY,
    DOMAIN,
)
from .coordinator import HeltyDataUpdateCoordinator

SWITCH_DEFINITIONS = [
    {
        "key": "led",
        "name": "LED",
        "icon": "mdi:led-on",
        "cmd_on": CMD_ENABLE_LED,
        "cmd_off": CMD_DISABLE_LED,
    },
    {
        "key": "sensor_mode",
        "name": "Sensor Mode",
        "icon": "mdi:auto-fix",
        "cmd_on": CMD_ENABLE_SENSOR,
        "cmd_off": CMD_DISABLE_SENSOR,
    },
    {
        "key": "standby",
        "name": "Standby",
        "icon": "mdi:power-standby",
        "cmd_on": CMD_ENABLE_STANDBY,
        "cmd_off": CMD_DISABLE_STANDBY,
    },
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Helty VMC switch entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device, coordinator in zip(data["devices"], data["coordinators"]):
        for switch_def in SWITCH_DEFINITIONS:
            entities.append(
                HeltyVmcSwitch(coordinator, device, data["api"], switch_def)
            )
    async_add_entities(entities)


class HeltyVmcSwitch(
    CoordinatorEntity[HeltyDataUpdateCoordinator], SwitchEntity
):
    """Representation of a Helty VMC toggle switch."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HeltyDataUpdateCoordinator,
        device: dict,
        api,
        switch_def: dict,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self._api = api
        self._board_serial = device["board_serial"]
        self._key = switch_def["key"]
        self._cmd_on = switch_def["cmd_on"]
        self._cmd_off = switch_def["cmd_off"]
        self._attr_name = switch_def["name"]
        self._attr_unique_id = f"{device['serial']}_{self._key}"
        self._attr_icon = switch_def.get("icon")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device["serial"])},
        )
        # Track assumed state since the API doesn't report toggle states
        self._assumed_on: bool | None = None

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        return self._assumed_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._api.send_command(self._board_serial, self._cmd_on)
        self._assumed_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self._api.send_command(self._board_serial, self._cmd_off)
        self._assumed_on = False
        self.async_write_ha_state()
