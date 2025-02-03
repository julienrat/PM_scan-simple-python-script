"""Config flow for PMScan integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
    async_get_scanner,
    async_scanner_count,
)
from homeassistant.const import CONF_ADDRESS
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from . import DOMAIN
from .sensor import (
    DEFAULT_MEASUREMENT_INTERVAL,
    MIN_MEASUREMENT_INTERVAL,
    MAX_MEASUREMENT_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

CONF_MEASUREMENT_INTERVAL = "measurement_interval"
CONF_KEEP_CONNECTION = "keep_connection"

# UUID du service PMScan
PMSCAN_SERVICE_UUID = "f3641900-00b0-4240-ba50-05ca45bf8abc"
# Nom partiel pour identifier un PMScan
PMSCAN_NAME_PREFIX = "PMScan"

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for PMScan integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = {
            vol.Optional(
                CONF_MEASUREMENT_INTERVAL,
                default=self.config_entry.options.get(
                    CONF_MEASUREMENT_INTERVAL, DEFAULT_MEASUREMENT_INTERVAL
                ),
            ): vol.All(
                vol.Coerce(int),
                vol.Range(min=MIN_MEASUREMENT_INTERVAL, max=MAX_MEASUREMENT_INTERVAL),
            ),
            vol.Optional(
                CONF_KEEP_CONNECTION,
                default=self.config_entry.options.get(CONF_KEEP_CONNECTION, True),
            ): bool,
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(options),
        )

class PMScanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PMScan."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_devices: dict[str, BluetoothServiceInfoBleak] = {}
        _LOGGER.debug("Initialisation du flux de configuration PMScan")

    def _is_pmscan_device(self, discovery_info: BluetoothServiceInfoBleak) -> bool:
        """Vérifie si l'appareil est un PMScan."""
        try:
            # Vérifie le nom de l'appareil
            if discovery_info.name and PMSCAN_NAME_PREFIX in discovery_info.name:
                _LOGGER.debug("Appareil trouvé avec le nom PMScan: %s", discovery_info.name)
                return True
                
            # Vérifie les services UUID
            if discovery_info.service_uuids and PMSCAN_SERVICE_UUID in discovery_info.service_uuids:
                _LOGGER.debug("Appareil trouvé avec l'UUID PMScan: %s", discovery_info.address)
                return True
                
            # Vérifie les données du fabricant si disponibles
            if discovery_info.manufacturer_data:
                _LOGGER.debug("Données fabricant trouvées: %s", discovery_info.manufacturer_data)
                
            _LOGGER.debug(
                "Appareil non reconnu comme PMScan - Nom: %s, UUIDs: %s",
                discovery_info.name,
                discovery_info.service_uuids
            )
            return False
        except Exception as e:
            _LOGGER.error("Erreur lors de la vérification de l'appareil: %s", str(e))
            return False

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle the bluetooth discovery step."""
        _LOGGER.debug(
            "Découverte Bluetooth - Nom: %s, Adresse: %s",
            discovery_info.name,
            discovery_info.address,
        )
        _LOGGER.debug("UUIDs disponibles: %s", discovery_info.service_uuids)
        _LOGGER.debug("Force du signal (RSSI): %s", discovery_info.rssi)

        if discovery_info.name and "PMScan" in discovery_info.name:
            await self.async_set_unique_id(discovery_info.address)
            self._abort_if_unique_id_configured()
            _LOGGER.info("PMScan trouvé! Adresse: %s", discovery_info.address)
            self._discovered_devices[discovery_info.address] = discovery_info
            return await self.async_step_user()

        return self.async_abort(reason="not_supported")

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the user step."""
        _LOGGER.debug("Démarrage du flux de configuration PMScan")

        errors: dict[str, str] = {}

        if not user_input:
            # Recherche des appareils Bluetooth
            _LOGGER.debug("Recherche des appareils Bluetooth...")
            discovered_devices = async_discovered_service_info(self.hass)

            for discovery_info in discovered_devices:
                _LOGGER.debug(
                    "Appareil trouvé - Nom: %s, Adresse: %s, RSSI: %s",
                    discovery_info.name,
                    discovery_info.address,
                    discovery_info.rssi,
                )

                if discovery_info.manufacturer_data:
                    _LOGGER.debug(
                        "Données fabricant: %s", discovery_info.manufacturer_data
                    )

                if discovery_info.service_uuids:
                    _LOGGER.debug("Services disponibles: %s", discovery_info.service_uuids)

                self._discovered_devices[discovery_info.address] = discovery_info

            if not self._discovered_devices:
                return self.async_abort(reason="no_devices_found")

            addresses = [
                address
                for address, device in self._discovered_devices.items()
                if device.name and "PMScan" in device.name
            ]
            _LOGGER.info("Appareils trouvés: %s", addresses)

            if not addresses:
                return self.async_abort(reason="no_devices_found")

            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {vol.Required(CONF_ADDRESS): vol.In(addresses)}
                ),
                errors=errors,
            )

        address = user_input[CONF_ADDRESS]
        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"PMScan ({address})",
            data={CONF_ADDRESS: address},
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry) 