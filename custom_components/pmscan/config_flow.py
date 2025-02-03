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
)
from homeassistant.const import CONF_ADDRESS
from homeassistant.data_entry_flow import FlowResult

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

PMSCAN_SERVICE_UUID = "f3641900-00b0-4240-ba50-05ca45bf8abc"

class PMScanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PMScan."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_devices = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle the bluetooth discovery step."""
        _LOGGER.debug("Découverte Bluetooth: %s", discovery_info)
        
        if PMSCAN_SERVICE_UUID in discovery_info.service_uuids:
            await self.async_set_unique_id(discovery_info.address)
            self._abort_if_unique_id_configured()
            
            self._discovered_devices[discovery_info.address] = discovery_info
            return await self.async_step_user()
            
        return self.async_abort(reason="not_supported")

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        _LOGGER.debug("Étape utilisateur: %s", user_input)
        
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            discovery_info = self._discovered_devices[address]
            return self.async_create_entry(
                title=f"PMScan ({discovery_info.name})",
                data={CONF_ADDRESS: address},
            )

        scanner = async_get_scanner(self.hass)
        current_addresses = self._async_current_ids()
        
        for discovery_info in async_discovered_service_info(self.hass):
            _LOGGER.debug("Appareil trouvé: %s", discovery_info)
            
            if (
                discovery_info.address not in current_addresses
                and PMSCAN_SERVICE_UUID in discovery_info.service_uuids
            ):
                self._discovered_devices[discovery_info.address] = discovery_info

        if not self._discovered_devices:
            return self.async_show_form(
                step_id="user",
                description_placeholders={
                    "error_message": "Aucun appareil PMScan trouvé. Assurez-vous qu'il est allumé et à portée."
                }
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(
                        {
                            address: f"{info.name} ({address})"
                            for address, info in self._discovered_devices.items()
                        }
                    )
                }
            ),
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

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
        ) 