"""Config flow for PMScan integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
    async_get_scanner,
    BluetoothScanningMode,
)
from homeassistant.const import CONF_ADDRESS
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

# UUID du service PMScan
PMSCAN_SERVICE_UUID = "f3641900-00b0-4240-ba50-05ca45bf8abc"
# Nom partiel pour identifier un PMScan
PMSCAN_NAME_PREFIX = "PMScan"

class PMScanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PMScan."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_devices = {}
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
        try:
            _LOGGER.debug(
                "Découverte Bluetooth - Nom: %s, Adresse: %s",
                discovery_info.name,
                discovery_info.address,
            )
            
            if discovery_info.service_uuids:
                _LOGGER.debug("UUIDs disponibles: %s", discovery_info.service_uuids)
                
            if discovery_info.rssi:
                _LOGGER.debug("Force du signal (RSSI): %d", discovery_info.rssi)
            
            if self._is_pmscan_device(discovery_info):
                _LOGGER.info("PMScan trouvé! Adresse: %s", discovery_info.address)
                await self.async_set_unique_id(discovery_info.address)
                self._abort_if_unique_id_configured()
                
                self._discovered_devices[discovery_info.address] = discovery_info
                return await self.async_step_user()
                
            return self.async_abort(reason="not_supported")
        except Exception as e:
            _LOGGER.error("Erreur lors de la découverte Bluetooth: %s", str(e))
            return self.async_abort(reason="discovery_error")

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        _LOGGER.debug("Démarrage du flux de configuration PMScan")
        
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            discovery_info = self._discovered_devices[address]
            return self.async_create_entry(
                title=f"PMScan ({discovery_info.name or address})",
                data={CONF_ADDRESS: address},
            )

        scanner = async_get_scanner(self.hass)
        if not scanner:
            _LOGGER.error("Scanner Bluetooth non disponible")
            return self.async_abort(reason="no_bluetooth")

        _LOGGER.debug("Recherche des appareils Bluetooth...")
        
        discovered_devices = {}
        for discovery_info in async_discovered_service_info(self.hass):
            _LOGGER.debug(
                "Appareil trouvé - Nom: %s, Adresse: %s, RSSI: %s, Services: %s, Données fabricant: %s",
                discovery_info.name,
                discovery_info.address,
                discovery_info.rssi,
                discovery_info.service_uuids,
                discovery_info.manufacturer_data
            )
            
            # Accepte tous les appareils pour le moment pour debug
            discovered_devices[discovery_info.address] = discovery_info

        self._discovered_devices = discovered_devices

        if not discovered_devices:
            _LOGGER.warning("Aucun appareil Bluetooth trouvé")
            return self.async_show_form(
                step_id="user",
                description_placeholders={
                    "error_message": (
                        "Aucun appareil Bluetooth trouvé. Vérifiez que :\n"
                        "1. Le Bluetooth est activé sur votre système\n"
                        "2. Vous avez les permissions Bluetooth nécessaires\n"
                        "3. L'adaptateur Bluetooth est fonctionnel"
                    )
                }
            )

        _LOGGER.info("Appareils trouvés: %s", list(discovered_devices.keys()))

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(
                        {
                            address: (
                                f"{info.name or 'Inconnu'} ({address}) "
                                f"RSSI: {info.rssi}dBm "
                                f"Services: {len(info.service_uuids or [])}"
                            )
                            for address, info in discovered_devices.items()
                        }
                    )
                }
            ),
            description_placeholders={
                "error_message": f"Sélectionnez votre appareil PMScan parmi les {len(discovered_devices)} appareils trouvés"
            }
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return PMScanOptionsFlow(config_entry)

class PMScanOptionsFlow(config_entries.OptionsFlow):
    """Handle PMScan options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        _LOGGER.debug("Initialisation du flux d'options pour %s", config_entry.title)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            _LOGGER.debug("Nouvelles options: %s", user_input)
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
        ) 