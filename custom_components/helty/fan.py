"""Fan platform for Helty VMC."""

from __future__ import annotations

import math
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CMD_POWER_OFF,
    DOMAIN,
    PRESET_MODES,
    PRESET_MODE_COMMANDS,
    SPEED_COMMANDS,
    SPEED_COUNT,
    VMC_STATUS_COOLING,
    VMC_STATUS_HYPER,
    VMC_STATUS_NIGHT,
    VMC_STATUS_NORMAL,
    VMC_STATUS_OFF,
    VMC_STATUS_TO_PRESET,
)
from .coordinator import HeltyDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Helty VMC fan entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device, coordinator in zip(data["devices"], data["coordinators"]):
        entities.append(HeltyVmcFan(coordinator, device, data["api"]))
    async_add_entities(entities)


class HeltyVmcFan(CoordinatorEntity[HeltyDataUpdateCoordinator], FanEntity):
    """Representation of a Helty VMC as a fan entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_preset_modes = PRESET_MODES
    _attr_speed_count = SPEED_COUNT
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.PRESET_MODE
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )

    def __init__(
        self,
        coordinator: HeltyDataUpdateCoordinator,
        device: dict,
        api,
    ) -> None:
        """Initialize the fan entity."""
        super().__init__(coordinator)
        self._api = api
        self._device = device
        self._board_serial = device["board_serial"]
        self._attr_unique_id = f"{device['serial']}_fan"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device["serial"])},
            name=f"Helty {device['model']}",
            manufacturer="Helty",
            model=device["model"],
            serial_number=device["serial"],
            configuration_url="https://hcloud.heltyair.com",
        )
        if device.get("installation") and device["installation"] != "N/A":
            self._attr_device_info["suggested_area"] = device["installation"]

    @property
    def is_on(self) -> bool | None:
        """Return true if the VMC is on."""
        if self.coordinator.data is None:
            return None
        status = self.coordinator.data.get("vmc_status")
        if status is None:
            return None
        return status != VMC_STATUS_OFF

    @property
    def percentage(self) -> int | None:
        """Return the current speed as a percentage."""
        if self.coordinator.data is None:
            return None
        status = self.coordinator.data.get("vmc_status")
        if status is None or status == VMC_STATUS_OFF:
            return 0
        # Map VMC statuses to speed percentages
        # Normal = speed level from last command (assume speed 1 = 25%)
        # We approximate: normal=25, night=25, hyper=100, cooling=25
        status_to_pct = {
            VMC_STATUS_NORMAL: 25,
            VMC_STATUS_NIGHT: 25,
            VMC_STATUS_HYPER: 100,
            VMC_STATUS_COOLING: 25,
        }
        return status_to_pct.get(status, 25)

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        if self.coordinator.data is None:
            return None
        status = self.coordinator.data.get("vmc_status")
        if status is None or status == VMC_STATUS_OFF:
            return None
        return VMC_STATUS_TO_PRESET.get(status)

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn the VMC on."""
        if preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)
            return
        if percentage is not None:
            await self.async_set_percentage(percentage)
            return
        # Default: turn on at speed 1
        await self._api.send_command(self._board_serial, SPEED_COMMANDS[1])
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the VMC off."""
        await self._api.send_command(self._board_serial, CMD_POWER_OFF)
        await self.coordinator.async_request_refresh()

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage."""
        if percentage == 0:
            await self.async_turn_off()
            return
        # Convert percentage to speed level 1-4
        speed = math.ceil(percentage / (100 / SPEED_COUNT))
        speed = max(1, min(SPEED_COUNT, speed))
        await self._api.send_command(self._board_serial, SPEED_COMMANDS[speed])
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode."""
        if preset_mode not in PRESET_MODE_COMMANDS:
            return
        await self._api.send_command(
            self._board_serial, PRESET_MODE_COMMANDS[preset_mode]
        )
        await self.coordinator.async_request_refresh()
