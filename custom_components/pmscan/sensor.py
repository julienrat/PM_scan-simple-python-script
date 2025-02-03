"""Support for PMScan sensors."""
from __future__ import annotations

import logging
import struct
from datetime import datetime

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    PERCENTAGE,
    TEMP_CELSIUS,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

_LOGGER = logging.getLogger(__name__)

# Configuration des UUIDs BLE
PMSCAN_SERVICE_UUID = "f3641900-00b0-4240-ba50-05ca45bf8abc"
REAL_TIME_DATA_UUID = "f3641901-00b0-4240-ba50-05ca45bf8abc"
CURRENT_TIME_UUID = "f3641906-00b0-4240-ba50-05ca45bf8abc"

SCAN_INTERVAL = 60

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the PMScan sensors."""
    coordinator = PMScanCoordinator(hass, config_entry)
    await coordinator.async_config_entry_first_refresh()

    entities = []
    for description in SENSOR_TYPES:
        entities.append(PMScanSensor(coordinator, description))
    
    async_add_entities(entities)

class PMScanCoordinator(DataUpdateCoordinator):
    """PMScan data update coordinator."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="PMScan",
            update_interval=SCAN_INTERVAL,
        )
        self.config_entry = config_entry
        self.device: BLEDevice | None = None
        self.client: BleakClient | None = None

    async def _async_update_data(self):
        """Fetch data from PMScan."""
        if not self.device:
            devices = await BleakScanner.discover()
            for device in devices:
                if device.name and "PMScan" in device.name:
                    self.device = device
                    break
            if not self.device:
                raise BleakError("PMScan not found")

        try:
            async with BleakClient(self.device) as client:
                # Envoi du timestamp
                timestamp = int(datetime.now().timestamp())
                await client.write_gatt_char(
                    CURRENT_TIME_UUID,
                    struct.pack("<I", timestamp)
                )

                # Lecture des données
                data = await client.read_gatt_char(REAL_TIME_DATA_UUID)
                return self.parse_data(data)

        except BleakError as error:
            self.device = None
            raise error

    @staticmethod
    def parse_data(data):
        """Parse PMScan data."""
        timestamp, _, _, _, pm1_0, pm2_5, pm10_0, temp, humidity, _ = struct.unpack("<IBBHHHHHHh", data)
        return {
            "pm1_0": pm1_0 / 10.0,
            "pm2_5": pm2_5 / 10.0,
            "pm10_0": pm10_0 / 10.0,
            "temperature": temp / 10.0,
            "humidity": humidity / 10.0,
        }

SENSOR_TYPES = [
    {
        "key": "pm1_0",
        "name": "PM1.0",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "icon": "mdi:air-filter",
    },
    {
        "key": "pm2_5",
        "name": "PM2.5",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "icon": "mdi:air-filter",
    },
    {
        "key": "pm10_0",
        "name": "PM10.0",
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        "icon": "mdi:air-filter",
    },
    {
        "key": "temperature",
        "name": "Temperature",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": TEMP_CELSIUS,
        "icon": "mdi:thermometer",
    },
    {
        "key": "humidity",
        "name": "Humidity",
        "device_class": SensorDeviceClass.HUMIDITY,
        "state_class": SensorStateClass.MEASUREMENT,
        "native_unit_of_measurement": PERCENTAGE,
        "icon": "mdi:water-percent",
    },
]

class PMScanSensor(CoordinatorEntity, SensorEntity):
    """Representation of a PMScan sensor."""

    def __init__(self, coordinator: PMScanCoordinator, description: dict) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = f"PMScan {description['name']}"
        self._attr_unique_id = f"pmscan_{description['key']}"
        self._attr_device_class = description["device_class"]
        self._attr_state_class = description["state_class"]
        self._attr_native_unit_of_measurement = description["native_unit_of_measurement"]
        self._attr_icon = description["icon"]
        self._key = description["key"]
        
        self._attr_device_info = DeviceInfo(
            identifiers={("pmscan", coordinator.config_entry.entry_id)},
            name="PMScan Air Quality Monitor",
            manufacturer="PMScan",
            model="PMScan Air Quality Monitor",
        )

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._key) 