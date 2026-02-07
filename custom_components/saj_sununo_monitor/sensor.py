"""Platform for sensor integration."""

from __future__ import annotations

import datetime
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfMass,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SajSununoDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

SENSOR_ICONS = {
    "state": "mdi:power",
    "v-grid": "mdi:lightning-bolt",
    "i-grid": "mdi:current-ac",
    "f-grid": "mdi:sine-wave",
    "p-ac": "mdi:power-plug",
    "temp": "mdi:thermometer",
    "e-today": "mdi:solar-power",
    "t-today": "mdi:clock",
    "e-total": "mdi:solar-power",
    "CO2": "mdi:leaf",
    "t-total": "mdi:clock",
    "v-pv1": "mdi:solar-panel",
    "i-pv1": "mdi:current-dc",
    "v-pv2": "mdi:solar-panel",
    "i-pv2": "mdi:current-dc",
    "v-pv3": "mdi:solar-panel",
    "i-pv3": "mdi:current-dc",
    "v-pv4": "mdi:solar-panel",
    "i-pv4": "mdi:current-dc",
    "v-bus": "mdi:lightning-bolt",
}

SENSOR_UNITS = {
    "v-grid": UnitOfElectricPotential.VOLT,
    "i-grid": UnitOfElectricCurrent.AMPERE,
    "f-grid": UnitOfFrequency.HERTZ,
    "p-ac": UnitOfPower.WATT,
    "temp": UnitOfTemperature.CELSIUS,
    "e-today": UnitOfEnergy.KILO_WATT_HOUR,
    "t-today": UnitOfTime.HOURS,
    "e-total": UnitOfEnergy.KILO_WATT_HOUR,
    "CO2": UnitOfMass.KILOGRAMS,
    "t-total": UnitOfTime.HOURS,
    "v-pv1": UnitOfElectricPotential.VOLT,
    "i-pv1": UnitOfElectricCurrent.AMPERE,
    "v-pv2": UnitOfElectricPotential.VOLT,
    "i-pv2": UnitOfElectricCurrent.AMPERE,
    "v-pv3": UnitOfElectricPotential.VOLT,
    "i-pv3": UnitOfElectricCurrent.AMPERE,
    "v-pv4": UnitOfElectricPotential.VOLT,
    "i-pv4": UnitOfElectricCurrent.AMPERE,
    "v-bus": UnitOfElectricPotential.VOLT,
}

SENSOR_DEVICE_CLASSES = {
    "v-grid": SensorDeviceClass.VOLTAGE,
    "i-grid": SensorDeviceClass.CURRENT,
    "f-grid": SensorDeviceClass.FREQUENCY,
    "p-ac": SensorDeviceClass.POWER,
    "temp": SensorDeviceClass.TEMPERATURE,
    "e-today": SensorDeviceClass.ENERGY,
    "e-total": SensorDeviceClass.ENERGY,
    "v-pv1": SensorDeviceClass.VOLTAGE,
    "i-pv1": SensorDeviceClass.CURRENT,
    "v-pv2": SensorDeviceClass.VOLTAGE,
    "i-pv2": SensorDeviceClass.CURRENT,
    "v-pv3": SensorDeviceClass.VOLTAGE,
    "i-pv3": SensorDeviceClass.CURRENT,
    "v-pv4": SensorDeviceClass.VOLTAGE,
    "i-pv4": SensorDeviceClass.CURRENT,
    "v-bus": SensorDeviceClass.VOLTAGE,
}

SENSOR_STATE_CLASSES = {
    "v-grid": SensorStateClass.MEASUREMENT,
    "i-grid": SensorStateClass.MEASUREMENT,
    "f-grid": SensorStateClass.MEASUREMENT,
    "p-ac": SensorStateClass.MEASUREMENT,
    "temp": SensorStateClass.MEASUREMENT,
    "e-today": SensorStateClass.TOTAL_INCREASING,
    "e-total": SensorStateClass.TOTAL_INCREASING,
    "v-pv1": SensorStateClass.MEASUREMENT,
    "i-pv1": SensorStateClass.MEASUREMENT,
    "v-pv2": SensorStateClass.MEASUREMENT,
    "i-pv2": SensorStateClass.MEASUREMENT,
    "v-pv3": SensorStateClass.MEASUREMENT,
    "i-pv3": SensorStateClass.MEASUREMENT,
    "v-pv4": SensorStateClass.MEASUREMENT,
    "i-pv4": SensorStateClass.MEASUREMENT,
    "v-bus": SensorStateClass.MEASUREMENT,
}

SENSOR_ENTITY_CATEGORIES = {
    "state": EntityCategory.DIAGNOSTIC,
    "temp": EntityCategory.DIAGNOSTIC,
    "t-today": EntityCategory.DIAGNOSTIC,
    "t-total": EntityCategory.DIAGNOSTIC,
    "v-bus": EntityCategory.DIAGNOSTIC,
    "CO2": EntityCategory.DIAGNOSTIC,
}

SENSOR_FLOAT_KEYS = {
    "v-grid",
    "i-grid",
    "p-ac",
    "temp",
    "e-today",
    "t-today",
    "e-total",
    "t-total",
    "CO2",
}

SENSOR_RETAIN_LAST_ON_UNAVAILABLE = {
    "CO2",
    "e-total",
    "t-total",
    "e-today",
    "t-today",
}

# Translation key mappings (for keys that need special handling)
SENSOR_TRANSLATION_KEY_MAP = {
    "CO2": "co2",
}

# List of sensor keys to create
SENSOR_KEYS = [
    "state",
    "v-grid",
    "i-grid",
    "f-grid",
    "p-ac",
    "temp",
    "e-today",
    "t-today",
    "e-total",
    "CO2",
    "t-total",
    "v-pv1",
    "i-pv1",
    "v-pv2",
    "i-pv2",
    "v-pv3",
    "i-pv3",
    "v-pv4",
    "i-pv4",
    "v-bus",
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add SAJ Sununo-TL Series Monitor sensors from a config entry."""
    coordinator: SajSununoDataUpdateCoordinator = entry.runtime_data

    sensors = [
        SajSununoSensor(coordinator, entry, sensor_key) for sensor_key in SENSOR_KEYS
    ]

    async_add_entities(sensors, True)


class SajSununoSensor(CoordinatorEntity[SajSununoDataUpdateCoordinator], SensorEntity):
    """Representation of a SAJ Sununo-TL Series Monitor sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SajSununoDataUpdateCoordinator,
        entry: ConfigEntry,
        sensor_key: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_key = sensor_key
        self._last_value: float | str | None = None
        self._last_reset_date: datetime.date | None = None
        self._attr_unique_id = f"{entry.entry_id}_{sensor_key}"
        self._attr_translation_key = SENSOR_TRANSLATION_KEY_MAP.get(
            sensor_key, sensor_key.replace("-", "_")
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data["device_name"],
            manufacturer="SAJ",
            model=entry.data.get("model", "unknown"),
            model_id=entry.data.get("model_id", "unknown"),
            serial_number=entry.data.get("serial_number", "unknown"),
            sw_version=entry.data.get("sw_version", "unknown"),
            configuration_url=f"http://{entry.data['host']}",
        )
        self._attr_icon = SENSOR_ICONS.get(sensor_key, "mdi:help")
        self._attr_native_unit_of_measurement = SENSOR_UNITS.get(sensor_key)
        self._attr_device_class = SENSOR_DEVICE_CLASSES.get(sensor_key)
        self._attr_state_class = SENSOR_STATE_CLASSES.get(sensor_key)
        self._attr_entity_category = SENSOR_ENTITY_CATEGORIES.get(sensor_key)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        # Only the state sensor shows as unavailable when coordinator fails
        if self._sensor_key == "state":
            return self.coordinator.last_update_success
        # All other sensors remain available even when coordinator fails
        return True

    @property
    def native_value(self) -> float | str | None:
        """Return the state of the sensor."""
        # Check for midnight reset for daily sensors (always check first)
        if self._sensor_key in ("e-today", "t-today"):
            current_date = datetime.datetime.now().date()
            if self._last_reset_date is None or self._last_reset_date != current_date:
                # New day detected, reset tracking
                self._last_reset_date = current_date
                self._last_value = 0.0
                # Return 0.0 for the first reading of the new day
                return 0.0

        # If coordinator failed to update (device unavailable)
        if not self.coordinator.last_update_success:
            if self._sensor_key == "state":
                return None
            # Sensors that retain last value
            if self._sensor_key in SENSOR_RETAIN_LAST_ON_UNAVAILABLE:
                return self._last_value if self._last_value is not None else 0.0
            # All other sensors return 0.0
            return 0.0

        # Device is available, get current value
        value = self.coordinator.data.get(self._sensor_key)
        if value is None:
            return None
        if self._sensor_key in SENSOR_FLOAT_KEYS:
            value = float(value)

        self._last_value = value
        return value
