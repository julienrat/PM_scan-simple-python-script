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
MEMORY_DATA_UUID = "f3641902-00b0-4240-ba50-05ca45bf8abc"
TEMP_HUMID_ALERT_UUID = "f3641903-00b0-4240-ba50-05ca45bf8abc"
BATTERY_LEVEL_UUID = "f3641904-00b0-4240-ba50-05ca45bf8abc"
BATTERY_CHARGING_UUID = "f3641905-00b0-4240-ba50-05ca45bf8abc"
CURRENT_TIME_UUID = "f3641906-00b0-4240-ba50-05ca45bf8abc"
ACQUISITION_INTERVAL_UUID = "f3641907-00b0-4240-ba50-05ca45bf8abc"
POWER_MODE_UUID = "f3641908-00b0-4240-ba50-05ca45bf8abc"
TEMP_HUMID_THRESHOLD_UUID = "f3641909-00b0-4240-ba50-05ca45bf8abc"
DISPLAY_SETTINGS_UUID = "f364190a-00b0-4240-ba50-05ca45bf8abc"
BATTERY_HEARTBEAT_UUID = "f364190b-00b0-4240-ba50-05ca45bf8abc"

# Constantes pour l'état de charge de la batterie
BATTERY_NOT_CHARGING = 0
BATTERY_PRE_CHARGING = 1
BATTERY_CHARGING = 2
BATTERY_FULLY_CHARGED = 3

# Intervalle de mesure par défaut en secondes
DEFAULT_MEASUREMENT_INTERVAL = 5
# Intervalle de mesure minimum et maximum (en secondes)
MIN_MEASUREMENT_INTERVAL = 1
MAX_MEASUREMENT_INTERVAL = 3600

# Délai maximum entre deux mesures avant de considérer les données comme périmées
MAX_TIME_BETWEEN_UPDATES = timedelta(seconds=10)

# Constantes pour la gestion des connexions
MAX_CONNECTION_ATTEMPTS = 3
CONNECTION_TIMEOUT = 30.0
RECONNECTION_DELAY = 10

# Seuils de qualité de l'air pour PM10 (en µg/m³)
AIR_QUALITY_THRESHOLDS = {
    10: ("EXCELLENTE", "Verte"),     # < 10 µg/m³
    30: ("BONNE", "Jaune"),          # < 30 µg/m³
    50: ("MOYENNE", "Orange"),        # < 50 µg/m³
    80: ("MAUVAISE", "Rouge"),       # < 80 µg/m³
    float('inf'): ("TRÈS MAUVAISE", "Violette")  # ≥ 80 µg/m³
}

# Log des UUIDs au démarrage
_LOGGER.debug("UUIDs Bluetooth configurés:")
_LOGGER.debug("Service: %s", PMSCAN_SERVICE_UUID)
_LOGGER.debug("Données temps réel: %s", REAL_TIME_DATA_UUID)
_LOGGER.debug("Horloge: %s", CURRENT_TIME_UUID)
_LOGGER.debug("Niveau batterie: %s", BATTERY_LEVEL_UUID)
_LOGGER.debug("État charge: %s", BATTERY_CHARGING_UUID)

def parse_notification_data(data: bytearray) -> dict[str, Any]:
    """Parse notification data from PMScan device."""
    try:
        if len(data) != 20:
            _LOGGER.error("Taille des données invalide: %d bytes (attendu: 20 bytes)", len(data))
            return {}

        _LOGGER.debug("Données brutes: %s", ' '.join(f'{x:02X}' for x in data))
        
        # Format des données (20 bytes):
        # - Timestamp (4 bytes): Horodatage Unix
        # - State (1 byte): État du capteur
        # - Command (1 byte): Commande en cours
        # - Particles count (2 bytes): Nombre de particules par ml
        # - PM1.0 (2 bytes): Concentration en µg/m³ (divisé par 10)
        # - PM2.5 (2 bytes): Concentration en µg/m³ (divisé par 10)
        # - PM10.0 (2 bytes): Concentration en µg/m³ (divisé par 10)
        # - Temperature (2 bytes): Température en °C (divisé par 10)
        # - Humidity (2 bytes): Humidité en % (divisé par 10)
        # - Reserved (2 bytes): Non utilisé
            
        timestamp, state, cmd, particles_count, pm1_0, pm2_5, pm10_0, temp, humidity = struct.unpack("<IBBHHHHHHxx", data)
        
        # Vérification des valeurs PM pendant le démarrage (0xFFFF = capteur en initialisation)
        if pm1_0 == 0xFFFF or pm2_5 == 0xFFFF or pm10_0 == 0xFFFF:
            _LOGGER.warning("Capteur en phase de démarrage, valeurs PM non valides")
            return {}
        
        # Calcul et vérification des valeurs
        humidity_value = humidity / 10.0
        if humidity_value > 100:
            _LOGGER.warning("Valeur d'humidité anormale détectée: %f%%", humidity_value)
            humidity_value = min(humidity_value, 100)  # Limite à 100%
        
        temp_value = temp / 10.0
        if temp_value < -40 or temp_value > 85:
            _LOGGER.warning("Température hors limites: %f°C", temp_value)
            _LOGGER.info("Note: La température est celle du PCB interne, pas de l'environnement")
        
        result = {
            "timestamp": timestamp,
            "state": state,
            "command": cmd,
            "particles_count": particles_count,
            "pm1_0": pm1_0 / 10.0,
            "pm2_5": pm2_5 / 10.0,
            "pm10": pm10_0 / 10.0,
            "temperature": temp_value,
            "humidity": humidity_value
        }
        
        _LOGGER.debug("Données analysées: %s", result)
        return result
        
    except Exception as e:
        _LOGGER.error("Erreur lors de l'analyse des données: %s", str(e))
        return {}

def get_air_quality_info(pm10_value: float) -> tuple[str, str]:
    """
    Détermine la qualité de l'air et la couleur correspondante basée sur la valeur PM10.
    
    Args:
        pm10_value (float): Valeur PM10 en µg/m³
        
    Returns:
        tuple: (qualité, couleur_led)
    """
    for threshold, (quality, led_color) in AIR_QUALITY_THRESHOLDS.items():
        if pm10_value < threshold:
            return quality, led_color
    return AIR_QUALITY_THRESHOLDS[float('inf')]

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

    # Variable pour suivre l'état de la connexion
    connection_active = False
    connection_attempts = 0

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
                PMScanBatteryLevelSensor(discovery_info),
                PMScanBatteryChargingSensor(discovery_info),
                PMScanAirQualitySensor(discovery_info),
            ])
            break

    if not sensors:
        _LOGGER.error("Aucun appareil PMScan trouvé à l'adresse %s", address)
        return

    async_add_entities(sensors)

    async def connect_and_subscribe():
        """Connect to device and subscribe to notifications."""
        nonlocal connection_active, connection_attempts
        
        while True:
            if connection_active:
                _LOGGER.debug("Une connexion est déjà active, attente...")
                await asyncio.sleep(RECONNECTION_DELAY)
                continue

            if connection_attempts >= MAX_CONNECTION_ATTEMPTS:
                _LOGGER.error("Nombre maximum de tentatives de connexion atteint (%d)", MAX_CONNECTION_ATTEMPTS)
                await asyncio.sleep(60)  # Attente plus longue avant de réessayer
                connection_attempts = 0
                continue

            try:
                connection_active = True
                connection_attempts += 1
                
                device = async_ble_device_from_address(hass, address)
                if not device:
                    _LOGGER.error("Appareil non trouvé: %s", address)
                    connection_active = False
                    await asyncio.sleep(RECONNECTION_DELAY)
                    continue

                async with BleakClient(device, timeout=CONNECTION_TIMEOUT) as client:
                    _LOGGER.info("Connexion établie avec le PMScan %s (tentative %d/%d)", 
                               address, connection_attempts, MAX_CONNECTION_ATTEMPTS)

                    # Vérification de la connexion
                    if not client.is_connected:
                        _LOGGER.error("La connexion a échoué immédiatement après l'établissement")
                        raise Exception("Échec de la connexion")

                    # Attente courte pour stabiliser la connexion
                    await asyncio.sleep(1)
                    
                    try:
                        # Découverte des services
                        services = await client.get_services()
                        if not services:
                            _LOGGER.error("Aucun service découvert sur l'appareil")
                            raise Exception("Aucun service découvert")

                        # Vérification du service PMScan
                        pmscan_service = None
                        for service in services:
                            if service.uuid.lower() == PMSCAN_SERVICE_UUID.lower():
                                pmscan_service = service
                                break

                        if not pmscan_service:
                            _LOGGER.error("Service PMScan non trouvé")
                            raise Exception("Service PMScan non trouvé")

                        _LOGGER.info("Service PMScan trouvé avec succès")
                        connection_attempts = 0  # Réinitialisation du compteur après une connexion réussie
                    
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
                            
                            # Gestion des différentes caractéristiques
                            if str(sender).endswith(REAL_TIME_DATA_UUID[-12:]):
                                parsed_data = parse_notification_data(data)
                                if parsed_data:
                                    last_update = dt_util.utcnow()
                                    for sensor in sensors:
                                        if sensor.value_type in parsed_data:
                                            sensor.update_value(parsed_data[sensor.value_type])
                            
                            elif str(sender).endswith(BATTERY_LEVEL_UUID[-12:]):
                                battery_level = data[0]
                                _LOGGER.debug("Niveau de batterie reçu: %d%%", battery_level)
                                for sensor in sensors:
                                    if sensor.value_type == "battery_level":
                                        sensor.update_value(battery_level)
                            
                            elif str(sender).endswith(BATTERY_CHARGING_UUID[-12:]):
                                charging_state = data[0]
                                _LOGGER.debug("État de charge reçu: %d", charging_state)
                                for sensor in sensors:
                                    if sensor.value_type == "battery_charging":
                                        sensor.update_value(charging_state)

                        # Activation des notifications pour toutes les caractéristiques
                        await client.start_notify(REAL_TIME_DATA_UUID, notification_handler)
                        _LOGGER.info("Notifications activées pour les données temps réel")
                        
                        await client.start_notify(BATTERY_LEVEL_UUID, notification_handler)
                        _LOGGER.info("Notifications activées pour le niveau de batterie")
                        
                        await client.start_notify(BATTERY_CHARGING_UUID, notification_handler)
                        _LOGGER.info("Notifications activées pour l'état de charge")

                        # Lecture initiale du niveau de batterie et de l'état de charge
                        try:
                            battery_level = await client.read_gatt_char(BATTERY_LEVEL_UUID)
                            charging_state = await client.read_gatt_char(BATTERY_CHARGING_UUID)
                            
                            # Mise à jour des capteurs avec les valeurs initiales
                            for sensor in sensors:
                                if sensor.value_type == "battery_level":
                                    sensor.update_value(battery_level[0])
                                elif sensor.value_type == "battery_charging":
                                    sensor.update_value(charging_state[0])
                        except Exception as e:
                            _LOGGER.warning("Erreur lors de la lecture initiale de la batterie: %s", str(e))

                        while True:
                            try:
                                await check_interval
                                check_interval = asyncio.create_task(asyncio.sleep(60))  # Vérifie toutes les minutes
                                
                                if last_update and dt_util.utcnow() - last_update > MAX_TIME_BETWEEN_UPDATES:
                                    _LOGGER.warning("Pas de données reçues depuis %s", MAX_TIME_BETWEEN_UPDATES)
                                    break
                                    
                            except asyncio.CancelledError:
                                break

                    except Exception as e:
                        _LOGGER.error("Erreur de connexion (tentative %d/%d): %s", 
                                    connection_attempts, MAX_CONNECTION_ATTEMPTS, str(e))
                        connection_active = False
                        await asyncio.sleep(RECONNECTION_DELAY)

            except Exception as e:
                _LOGGER.error("Erreur de connexion (tentative %d/%d): %s", 
                            connection_attempts, MAX_CONNECTION_ATTEMPTS, str(e))
                connection_active = False
                await asyncio.sleep(RECONNECTION_DELAY)

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
        self._attr_state_class = None
        self._attr_icon = "mdi:state-machine"
        self.value_type = "state"
        self._attr_device_class = None
        self._attr_native_unit_of_measurement = None
        self._attr_suggested_display_precision = None

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
        self._attr_state_class = None
        self._attr_icon = "mdi:console"
        self.value_type = "command"
        self._attr_device_class = None
        self._attr_native_unit_of_measurement = None
        self._attr_suggested_display_precision = None

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

class PMScanBatteryLevelSensor(PMScanSensor):
    """Representation of PMScan battery level sensor."""

    def __init__(self, discovery_info: BluetoothServiceInfoBleak) -> None:
        """Initialize the sensor."""
        super().__init__(discovery_info)
        self._attr_name = f"PMScan {discovery_info.name} Niveau Batterie"
        self._attr_unique_id = f"{discovery_info.address}_battery_level"
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:battery"
        self.value_type = "battery_level"

    @property
    def native_value(self) -> int | None:
        """Return the battery level."""
        return self._value

class PMScanBatteryChargingSensor(PMScanSensor):
    """Representation of PMScan battery charging state sensor."""

    def __init__(self, discovery_info: BluetoothServiceInfoBleak) -> None:
        """Initialize the sensor."""
        super().__init__(discovery_info)
        self._attr_name = f"PMScan {discovery_info.name} État Charge"
        self._attr_unique_id = f"{discovery_info.address}_battery_charging"
        self._attr_state_class = None
        self._attr_icon = "mdi:battery-charging"
        self.value_type = "battery_charging"
        self._attr_device_class = None
        self._attr_native_unit_of_measurement = None

    @property
    def native_value(self) -> str | None:
        """Return the charging state."""
        if self._value is None:
            return None
        
        states = {
            BATTERY_NOT_CHARGING: "Non branché",
            BATTERY_PRE_CHARGING: "Pré-charge",
            BATTERY_CHARGING: "En charge",
            BATTERY_FULLY_CHARGED: "Chargé"
        }
        return states.get(self._value, f"Inconnu ({self._value})")

class PMScanAirQualitySensor(PMScanSensor):
    """Representation of PMScan air quality sensor."""

    def __init__(self, discovery_info: BluetoothServiceInfoBleak) -> None:
        """Initialize the sensor."""
        super().__init__(discovery_info)
        self._attr_name = f"PMScan {discovery_info.name} Qualité Air"
        self._attr_unique_id = f"{discovery_info.address}_air_quality"
        self._attr_state_class = None
        self._attr_icon = "mdi:air-filter"
        self.value_type = "pm10"
        self._attr_device_class = None
        self._attr_native_unit_of_measurement = None
        self._attr_suggested_display_precision = None

    @property
    def native_value(self) -> str | None:
        """Return the air quality."""
        if self._value is not None:
            quality, _ = get_air_quality_info(self._value)
            return quality
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if self._value is not None:
            _, led_color = get_air_quality_info(self._value)
            return {
                "led_color": led_color,
                "pm10_value": self._value
            }
        return {} 