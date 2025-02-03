"""Support for PMScan sensors."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    PERCENTAGE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Définition des caractéristiques Bluetooth
PMSCAN_SERVICE_UUID = "f3641900-00b0-4240-ba50-05ca45bf8abc"
REAL_TIME_DATA_UUID = "f3641901-00b0-4240-ba50-05ca45bf8abc"

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigType, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up PMScan sensors."""
    address = entry.data["address"]

    sensors = []
    for discovery_info in async_discovered_service_info(hass):
        if discovery_info.address == address:
            sensors.extend([
                PMScanPM1Sensor(discovery_info),
                PMScanPM25Sensor(discovery_info),
                PMScanPM10Sensor(discovery_info),
                PMScanTemperatureSensor(discovery_info),
                PMScanHumiditySensor(discovery_info),
            ])
            break

    async_add_entities(sensors)

class PMScanSensor(SensorEntity):
    """Representation of a PMScan sensor."""

    def __init__(self, discovery_info: BluetoothServiceInfoBleak) -> None:
        """Initialize the sensor."""
        self._discovery_info = discovery_info
        self._attr_device_class = None
        self._attr_native_unit_of_measurement = None
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._value = None

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._discovery_info.address)},
            "name": f"PMScan ({self._discovery_info.name})",
            "manufacturer": "Tera Sensor",
            "model": "PMScan",
        }

    async def async_update(self) -> None:
        """Update the sensor."""
        if self._discovery_info.service_data and REAL_TIME_DATA_UUID in self._discovery_info.service_data:
            data = self._discovery_info.service_data[REAL_TIME_DATA_UUID]
            self._value = self._parse_data(data)
            _LOGGER.debug("Données mises à jour pour %s: %s", self.name, self._value)

    def _parse_data(self, data: bytes) -> float | None:
        """Parse sensor data."""
        try:
            # Implémentation spécifique dans les classes enfants
            return None
        except Exception as e:
            _LOGGER.error("Erreur lors de l'analyse des données: %s", str(e))
            return None

class PMScanPM1Sensor(PMScanSensor):
    """Representation of a PMScan PM1.0 sensor."""

    def __init__(self, discovery_info: BluetoothServiceInfoBleak) -> None:
        """Initialize the sensor."""
        super().__init__(discovery_info)
        self._attr_name = "PM1.0"
        self._attr_unique_id = f"{discovery_info.address}_pm1_0"
        self._attr_native_unit_of_measurement = CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
        self._attr_device_class = SensorDeviceClass.PM1

    @property
    def native_value(self) -> float | None:
        """Return the PM1.0 value."""
        return self._value

    def _parse_data(self, data: bytes) -> float | None:
        """Parse PM1.0 data."""
        if len(data) >= 2:
            return int.from_bytes(data[0:2], byteorder='little') / 10.0
        return None

class PMScanPM25Sensor(PMScanSensor):
    """Representation of a PMScan PM2.5 sensor."""

    def __init__(self, discovery_info: BluetoothServiceInfoBleak) -> None:
        """Initialize the sensor."""
        super().__init__(discovery_info)
        self._attr_name = "PM2.5"
        self._attr_unique_id = f"{discovery_info.address}_pm2_5"
        self._attr_native_unit_of_measurement = CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
        self._attr_device_class = SensorDeviceClass.PM25

    @property
    def native_value(self) -> float | None:
        """Return the PM2.5 value."""
        return self._value

    def _parse_data(self, data: bytes) -> float | None:
        """Parse PM2.5 data."""
        if len(data) >= 4:
            return int.from_bytes(data[2:4], byteorder='little') / 10.0
        return None

class PMScanPM10Sensor(PMScanSensor):
    """Representation of a PMScan PM10 sensor."""

    def __init__(self, discovery_info: BluetoothServiceInfoBleak) -> None:
        """Initialize the sensor."""
        super().__init__(discovery_info)
        self._attr_name = "PM10"
        self._attr_unique_id = f"{discovery_info.address}_pm10_0"
        self._attr_native_unit_of_measurement = CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
        self._attr_device_class = SensorDeviceClass.PM10

    @property
    def native_value(self) -> float | None:
        """Return the PM10 value."""
        return self._value

    def _parse_data(self, data: bytes) -> float | None:
        """Parse PM10 data."""
        if len(data) >= 6:
            return int.from_bytes(data[4:6], byteorder='little') / 10.0
        return None

class PMScanTemperatureSensor(PMScanSensor):
    """Representation of a PMScan temperature sensor."""

    def __init__(self, discovery_info: BluetoothServiceInfoBleak) -> None:
        """Initialize the sensor."""
        super().__init__(discovery_info)
        self._attr_name = "Temperature"
        self._attr_unique_id = f"{discovery_info.address}_temperature"
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_device_class = SensorDeviceClass.TEMPERATURE

    @property
    def native_value(self) -> float | None:
        """Return the temperature value."""
        return self._value

    def _parse_data(self, data: bytes) -> float | None:
        """Parse temperature data."""
        if len(data) >= 8:
            return int.from_bytes(data[6:8], byteorder='little') / 10.0
        return None

class PMScanHumiditySensor(PMScanSensor):
    """Representation of a PMScan humidity sensor."""

    def __init__(self, discovery_info: BluetoothServiceInfoBleak) -> None:
        """Initialize the sensor."""
        super().__init__(discovery_info)
        self._attr_name = "Humidity"
        self._attr_unique_id = f"{discovery_info.address}_humidity"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_device_class = SensorDeviceClass.HUMIDITY

    @property
    def native_value(self) -> float | None:
        """Return the humidity value."""
        return self._value

    def _parse_data(self, data: bytes) -> float | None:
        """Parse humidity data."""
        if len(data) >= 10:
            return int.from_bytes(data[8:10], byteorder='little') / 10.0
        return None 