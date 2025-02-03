"""Support for PMScan sensors."""
from __future__ import annotations

import logging
import asyncio
import struct
from datetime import datetime, timedelta
from typing import Any

from bleak import BleakClient
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
    async_register_callback,
    BluetoothChange,
    async_ble_device_from_address,
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
    CONCENTRATION_PARTS_PER_MILLION,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import dt as dt_util

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Définition des caractéristiques Bluetooth
PMSCAN_SERVICE_UUID = "f3641900-00b0-4240-ba50-05ca45bf8abc"
REAL_TIME_DATA_UUID = "f3641901-00b0-4240-ba50-05ca45bf8abc"
CURRENT_TIME_UUID = "f3641906-00b0-4240-ba50-05ca45bf8abc"

# Intervalle de mesure par défaut en secondes
DEFAULT_MEASUREMENT_INTERVAL = 5
# Intervalle de mesure minimum et maximum (en secondes)
MIN_MEASUREMENT_INTERVAL = 1
MAX_MEASUREMENT_INTERVAL = 3600

# Délai maximum entre deux mesures avant de considérer les données comme périmées
MAX_TIME_BETWEEN_UPDATES = timedelta(seconds=10)

def parse_notification_data(data: bytearray) -> dict[str, Any]:
    """Parse notification data from PMScan device."""
    try:
        if len(data) != 20:
            _LOGGER.error("Taille des données invalide: %d bytes (attendu: 20 bytes)", len(data))
            return {}

        _LOGGER.debug("Données brutes: %s", ' '.join(f'{x:02X}' for x in data))
        
        # Format: AA AA AA AA BB CC DD DD EE EE FF FF GG GG HH HH II II XX XX
        timestamp, state, cmd, particles_count, pm1_0, pm2_5, pm10_0, temp, humidity = struct.unpack("<IBBHHHHHHxx", data)
        
        # Vérification des valeurs PM pendant le démarrage
        if pm1_0 == 0xFFFF or pm2_5 == 0xFFFF or pm10_0 == 0xFFFF:
            _LOGGER.warning("Capteur en phase de démarrage, valeurs PM non valides")
            return {}
        
        # Calcul et vérification des valeurs
        temp_value = temp / 10.0
        humidity_value = humidity / 10.0
        
        if humidity_value > 100:
            _LOGGER.warning("Valeur d'humidité anormale détectée: %f%%", humidity_value)
            humidity_value = min(humidity_value, 100)
        
        if temp_value < -40 or temp_value > 85:
            _LOGGER.warning("Température hors limites: %f°C", temp_value)
        
        result = {
            "state": state,
            "command": cmd,
            "particles_count": particles_count,
            "pm1_0": pm1_0 / 10.0,
            "pm2_5": pm2_5 / 10.0,
            "pm10": pm10_0 / 10.0,
            "temperature": temp_value,
            "humidity": humidity_value,
            "timestamp": timestamp,
        }
        
        _LOGGER.debug("Données analysées: %s", result)
        return result
        
    except Exception as e:
        _LOGGER.error("Erreur lors de l'analyse des données: %s", str(e))
        return {}

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigType, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up PMScan sensors."""
    address = entry.data["address"]
    _LOGGER.debug("Configuration des capteurs PMScan pour l'adresse %s", address)

    # Récupération des options
    measurement_interval = entry.options.get("measurement_interval", DEFAULT_MEASUREMENT_INTERVAL)
    measurement_interval = max(MIN_MEASUREMENT_INTERVAL, min(measurement_interval, MAX_MEASUREMENT_INTERVAL))
    keep_connection = entry.options.get("keep_connection", True)
    _LOGGER.debug("Options configurées - Intervalle: %d secondes, Connexion permanente: %s", 
                 measurement_interval, keep_connection)

    sensors = []
    for discovery_info in async_discovered_service_info(hass):
        if discovery_info.address == address:
            _LOGGER.debug("Appareil PMScan trouvé: %s", discovery_info.name)
            sensors.extend([
                PMScanStateSensor(discovery_info),
                PMScanCommandSensor(discovery_info),
                PMScanParticlesSensor(discovery_info),
                PMScanPM1Sensor(discovery_info),
                PMScanPM25Sensor(discovery_info),
                PMScanPM10Sensor(discovery_info),
                PMScanTemperatureSensor(discovery_info),
                PMScanHumiditySensor(discovery_info),
            ])
            break

    if not sensors:
        _LOGGER.error("Aucun appareil PMScan trouvé à l'adresse %s", address)
        return

    async_add_entities(sensors)

    async def connect_and_subscribe():
        """Connect to device and subscribe to notifications."""
        while True:
            try:
                device = async_ble_device_from_address(hass, address)
                if not device:
                    _LOGGER.error("Appareil non trouvé: %s", address)
                    await asyncio.sleep(5)
                    continue

                async with BleakClient(device, timeout=20.0) as client:
                    _LOGGER.info("Connexion établie avec le PMScan %s", address)
                    
                    # Configuration de l'intervalle de mesure
                    interval_bytes = measurement_interval.to_bytes(2, byteorder='little')
                    await client.write_gatt_char(REAL_TIME_DATA_UUID, interval_bytes)
                    _LOGGER.info("Intervalle de mesure configuré à %d secondes", measurement_interval)

                    last_update = None
                    check_interval = asyncio.create_task(asyncio.sleep(0))

                    def notification_handler(sender: int, data: bytearray) -> None:
                        """Handle notification from PMScan device."""
                        nonlocal last_update
                        _LOGGER.debug("Notification reçue de %s: %s", sender, data.hex())
                        parsed_data = parse_notification_data(data)
                        if parsed_data:
                            last_update = dt_util.utcnow()
                            for sensor in sensors:
                                if sensor.value_type in parsed_data:
                                    sensor.update_value(parsed_data[sensor.value_type])

                    # Activation des notifications
                    await client.start_notify(REAL_TIME_DATA_UUID, notification_handler)
                    _LOGGER.info("Notifications activées pour %s", REAL_TIME_DATA_UUID)

                    # Boucle de vérification des mises à jour
                    while True:
                        try:
                            await check_interval
                            current_time = dt_util.utcnow()
                            
                            if last_update is None or current_time - last_update > MAX_TIME_BETWEEN_UPDATES:
                                _LOGGER.warning("Pas de mise à jour reçue depuis %s secondes, reconnexion...", 
                                             MAX_TIME_BETWEEN_UPDATES.total_seconds())
                                break

                            check_interval = asyncio.create_task(asyncio.sleep(measurement_interval))
                            
                        except asyncio.CancelledError:
                            break

                    if keep_connection:
                        # Si on maintient la connexion, on attend indéfiniment
                        while True:
                            await asyncio.sleep(1)
                    else:
                        # Sinon, on se déconnecte après chaque mise à jour
                        await client.stop_notify(REAL_TIME_DATA_UUID)
                        _LOGGER.info("Déconnexion du PMScan %s", address)
                        return

            except Exception as e:
                _LOGGER.error("Erreur lors de la connexion au PMScan: %s", str(e))
                if not keep_connection:
                    # Si on ne maintient pas la connexion, on attend plus longtemps entre les tentatives
                    await asyncio.sleep(measurement_interval)
                else:
                    # Sinon, on réessaie plus rapidement
                    await asyncio.sleep(5)

    # Démarrer la connexion en arrière-plan
    hass.async_create_task(connect_and_subscribe())

    @callback
    def _async_update_ble(
        service_info: BluetoothServiceInfoBleak, change: BluetoothChange
    ) -> None:
        """Handle updated bluetooth data."""
        if service_info.address != address:
            return

        _LOGGER.debug(
            "Mise à jour Bluetooth reçue - Adresse: %s, Données: %s",
            service_info.address,
            service_info.manufacturer_data,
        )

        if service_info.manufacturer_data:
            for sensor in sensors:
                sensor.update_from_bluetooth(service_info)

    entry.async_on_unload(
        async_register_callback(
            hass,
            _async_update_ble,
            {"address": address},
            BluetoothChange.ADVERTISEMENT,
        )
    )

class PMScanSensor(SensorEntity):
    """Representation of a PMScan sensor."""

    def __init__(self, discovery_info: BluetoothServiceInfoBleak) -> None:
        """Initialize the sensor."""
        self._discovery_info = discovery_info
        self._attr_device_class = None
        self._attr_native_unit_of_measurement = None
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._value = None
        self.value_type = None
        _LOGGER.debug(
            "Initialisation du capteur PMScan - Nom: %s, Adresse: %s",
            discovery_info.name,
            discovery_info.address,
        )

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._discovery_info.address)},
            "name": f"PMScan ({self._discovery_info.name})",
            "manufacturer": "Tera Sensor",
            "model": "PMScan",
        }

    def update_value(self, value: float) -> None:
        """Update sensor value."""
        self._value = value
        self.async_write_ha_state()

    def update_from_bluetooth(self, service_info: BluetoothServiceInfoBleak) -> None:
        """Update sensor state from Bluetooth data."""
        if not service_info.manufacturer_data:
            return

        try:
            # Recherche des données dans manufacturer_data
            for company_id, data in service_info.manufacturer_data.items():
                _LOGGER.debug(
                    "Données fabricant reçues - ID: %s, Données: %s",
                    company_id,
                    data.hex(),
                )
                parsed_data = parse_notification_data(data)
                if parsed_data and self.value_type in parsed_data:
                    self.update_value(parsed_data[self.value_type])
                break
        except Exception as e:
            _LOGGER.error("Erreur lors de la mise à jour des données: %s", str(e))

class PMScanStateSensor(PMScanSensor):
    """Representation of PMScan state sensor."""

    def __init__(self, discovery_info: BluetoothServiceInfoBleak) -> None:
        """Initialize the sensor."""
        super().__init__(discovery_info)
        self._attr_name = f"PMScan {discovery_info.name} État"
        self._attr_unique_id = f"{discovery_info.address}_state"
        self._attr_state_class = None  # Désactive la classe d'état pour permettre les valeurs non numériques
        self._attr_icon = "mdi:state-machine"
        self.value_type = "state"

    @property
    def native_value(self) -> str | None:
        """Return the state."""
        if self._value is not None:
            return f"0x{self._value:02X}"
        return None

class PMScanCommandSensor(PMScanSensor):
    """Representation of PMScan command sensor."""

    def __init__(self, discovery_info: BluetoothServiceInfoBleak) -> None:
        """Initialize the sensor."""
        super().__init__(discovery_info)
        self._attr_name = f"PMScan {discovery_info.name} Commande"
        self._attr_unique_id = f"{discovery_info.address}_command"
        self._attr_state_class = None  # Désactive la classe d'état pour permettre les valeurs non numériques
        self._attr_icon = "mdi:console"
        self.value_type = "command"

    @property
    def native_value(self) -> str | None:
        """Return the command."""
        if self._value is not None:
            return f"0x{self._value:02X}"
        return None

class PMScanParticlesSensor(PMScanSensor):
    """Representation of PMScan particles sensor."""

    def __init__(self, discovery_info: BluetoothServiceInfoBleak) -> None:
        """Initialize the sensor."""
        super().__init__(discovery_info)
        self._attr_name = f"PMScan {discovery_info.name} Particules"
        self._attr_unique_id = f"{discovery_info.address}_particles"
        self._attr_native_unit_of_measurement = "p/ml"
        self._attr_icon = "mdi:molecule"
        self.value_type = "particles_count"

    @property
    def native_value(self) -> float | None:
        """Return the particle count."""
        return self._value

class PMScanPM1Sensor(PMScanSensor):
    """Representation of a PMScan PM1.0 sensor."""

    def __init__(self, discovery_info: BluetoothServiceInfoBleak) -> None:
        """Initialize the sensor."""
        super().__init__(discovery_info)
        self._attr_name = "PM1.0"
        self._attr_unique_id = f"{discovery_info.address}_pm1_0"
        self._attr_native_unit_of_measurement = CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
        self._attr_device_class = SensorDeviceClass.PM1
        self.value_type = "pm1_0"

    @property
    def native_value(self) -> float | None:
        """Return the PM1.0 value."""
        return self._value

class PMScanPM25Sensor(PMScanSensor):
    """Representation of a PMScan PM2.5 sensor."""

    def __init__(self, discovery_info: BluetoothServiceInfoBleak) -> None:
        """Initialize the sensor."""
        super().__init__(discovery_info)
        self._attr_name = "PM2.5"
        self._attr_unique_id = f"{discovery_info.address}_pm2_5"
        self._attr_native_unit_of_measurement = CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
        self._attr_device_class = SensorDeviceClass.PM25
        self.value_type = "pm2_5"

    @property
    def native_value(self) -> float | None:
        """Return the PM2.5 value."""
        return self._value

class PMScanPM10Sensor(PMScanSensor):
    """Representation of a PMScan PM10 sensor."""

    def __init__(self, discovery_info: BluetoothServiceInfoBleak) -> None:
        """Initialize the sensor."""
        super().__init__(discovery_info)
        self._attr_name = "PM10"
        self._attr_unique_id = f"{discovery_info.address}_pm10_0"
        self._attr_native_unit_of_measurement = CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
        self._attr_device_class = SensorDeviceClass.PM10
        self.value_type = "pm10"

    @property
    def native_value(self) -> float | None:
        """Return the PM10 value."""
        return self._value

class PMScanTemperatureSensor(PMScanSensor):
    """Representation of PMScan temperature sensor."""

    def __init__(self, discovery_info: BluetoothServiceInfoBleak) -> None:
        """Initialize the sensor."""
        super().__init__(discovery_info)
        self._attr_name = f"PMScan {discovery_info.name} Température PCB"
        self._attr_unique_id = f"{discovery_info.address}_temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self.value_type = "temperature"

    @property
    def native_value(self) -> float | None:
        """Return the temperature."""
        return self._value

class PMScanHumiditySensor(PMScanSensor):
    """Representation of PMScan humidity sensor."""

    def __init__(self, discovery_info: BluetoothServiceInfoBleak) -> None:
        """Initialize the sensor."""
        super().__init__(discovery_info)
        self._attr_name = f"PMScan {discovery_info.name} Humidité interne"
        self._attr_unique_id = f"{discovery_info.address}_humidity"
        self._attr_device_class = SensorDeviceClass.HUMIDITY
        self._attr_native_unit_of_measurement = PERCENTAGE
        self.value_type = "humidity"

    @property
    def native_value(self) -> float | None:
        """Return the humidity."""
        return self._value 