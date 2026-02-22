"""Sensor platform for Helty VMC."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_BILLION,
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HeltyDataUpdateCoordinator

SENSOR_DEFINITIONS = [
    {
        "key": "temp_indoor",
        "name": "Indoor Temperature",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "native_unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    {
        "key": "temp_outdoor",
        "name": "Outdoor Temperature",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "native_unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    {
        "key": "humidity",
        "name": "Humidity",
        "device_class": SensorDeviceClass.HUMIDITY,
        "native_unit": PERCENTAGE,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    {
        "key": "co2",
        "name": "CO2",
        "device_class": SensorDeviceClass.CO2,
        "native_unit": CONCENTRATION_PARTS_PER_MILLION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
    {
        "key": "voc",
        "name": "VOC",
        "device_class": SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS_PARTS,
        "native_unit": CONCENTRATION_PARTS_PER_BILLION,
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": None,
    },
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Helty VMC sensor entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device, coordinator in zip(data["devices"], data["coordinators"]):
        for sensor_def in SENSOR_DEFINITIONS:
            entities.append(
                HeltyVmcSensor(coordinator, device, sensor_def)
            )
    async_add_entities(entities)


class HeltyVmcSensor(
    CoordinatorEntity[HeltyDataUpdateCoordinator], SensorEntity
):
    """Representation of a Helty VMC sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HeltyDataUpdateCoordinator,
        device: dict,
        sensor_def: dict,
    ) -> None:
        """Initialize the sensor entity."""
        super().__init__(coordinator)
        self._key = sensor_def["key"]
        self._attr_name = sensor_def["name"]
        self._attr_unique_id = f"{device['serial']}_{self._key}"
        self._attr_device_class = sensor_def["device_class"]
        self._attr_native_unit_of_measurement = sensor_def["native_unit"]
        self._attr_state_class = sensor_def["state_class"]
        if sensor_def.get("icon"):
            self._attr_icon = sensor_def["icon"]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device["serial"])},
        )

    @property
    def native_value(self) -> float | int | None:
        """Return the sensor value."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._key)
