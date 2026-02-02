"""Config flow for SAJ Sununo-TL Series Monitor integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import defusedxml.ElementTree as ET
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

# Constants for HTTP requests
DEVICE_INFO_URL = "http://{host}/equipment_data.xml"
REAL_TIME_DATA_URL = "http://{host}/real_time_data.xml"
REQUEST_TIMEOUT = 10

# XML field mappings
DEVICE_INFO_FIELDS = {
    "model": ("Model", "unknown"),
    "model_id": ("Product_Code", "unknown"),
    "serial_number": ("SN", "unknown"),
    "sw_version": ("MFMW", "unknown"),
}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SAJ Sununo-TL Series Monitor."""

    VERSION = 1
    MINOR_VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._areas: list[str] | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await self._validate_connection(user_input["host"])
                device_info = await self._async_fetch_device_info(user_input["host"])
                return self.async_create_entry(
                    title=user_input["device_name"],
                    data={**user_input, **device_info},
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during config flow")
                errors["base"] = "unknown"

        if self._areas is None:
            self._areas = self._get_areas()

        return self.async_show_form(
            step_id="user",
            data_schema=self._build_schema(
                host="",
                device_name="",
                area=self._areas[0] if self._areas else "",
                scan_interval=DEFAULT_SCAN_INTERVAL,
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the reconfigure step."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await self._validate_connection(user_input["host"])
                device_info = await self._async_fetch_device_info(user_input["host"])
                return self.async_update_reload_and_abort(
                    entry,
                    title=user_input["device_name"],
                    data_updates={
                        "host": user_input["host"],
                        "device_name": user_input["device_name"],
                        "area": user_input["area"],
                        "scan_interval": user_input["scan_interval"],
                        **device_info,
                    },
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during reconfigure")
                errors["base"] = "unknown"

        if self._areas is None:
            self._areas = self._get_areas()

        current_data = entry.data
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self._build_schema(
                host=current_data.get("host", ""),
                device_name=current_data.get("device_name", ""),
                area=current_data.get("area", self._areas[0] if self._areas else ""),
                scan_interval=current_data.get("scan_interval", DEFAULT_SCAN_INTERVAL),
            ),
            errors=errors,
        )

    def _get_areas(self) -> list[str]:
        """Get available areas from Home Assistant."""
        if self.hass is None:
            return []
        area_registry = ar.async_get(self.hass)
        return sorted([area.name for area in area_registry.areas.values()])

    def _build_schema(
        self,
        host: str,
        device_name: str,
        area: str,
        scan_interval: int,
    ) -> vol.Schema:
        """Build configuration schema with defaults."""
        return vol.Schema(
            {
                vol.Required("host", default=host): str,
                vol.Required("device_name", default=device_name): str,
                vol.Required("area", default=area): vol.In(self._areas or []),
                vol.Required("scan_interval", default=scan_interval): vol.Coerce(int),
            }
        )

    async def _async_fetch_device_info(self, host: str) -> dict[str, str]:
        """Fetch device info from equipment_data.xml."""
        # Initialize with defaults
        device_info: dict[str, str] = {
            key: default for key, (_, default) in DEVICE_INFO_FIELDS.items()
        }

        try:
            url = DEVICE_INFO_URL.format(host=host)
            _LOGGER.debug("Fetching device info from %s", url)
            async with asyncio.timeout(REQUEST_TIMEOUT):
                session = async_get_clientsession(self.hass)
                async with session.get(url) as response:
                    response.raise_for_status()
                    xml_content = await response.text()
                    root = ET.fromstring(xml_content)
                    # Extract device info using field mappings
                    for key, (xml_tag, _) in DEVICE_INFO_FIELDS.items():
                        device_info[key] = root.findtext(xml_tag, default="unknown")
                    _LOGGER.debug("Device info fetched: %s", device_info)
        except TimeoutError as err:
            _LOGGER.error("Timeout fetching device info from %s", host)
            raise CannotConnect(f"Timeout connecting to {host}") from err
        except aiohttp.ClientError as err:
            _LOGGER.error("Error fetching device info: %s", err)

        return device_info

    async def _validate_connection(self, host: str) -> None:
        """Validate the connection to the inverter."""
        try:
            url = REAL_TIME_DATA_URL.format(host=host)
            session = async_get_clientsession(self.hass)
            async with asyncio.timeout(REQUEST_TIMEOUT):
                async with session.get(url) as response:
                    response.raise_for_status()
        except TimeoutError as err:
            _LOGGER.error("Timeout connecting to inverter at %s", host)
            raise CannotConnect(f"Timeout connecting to {host}") from err
        except aiohttp.ClientError as err:
            _LOGGER.error("Error connecting to inverter at %s: %s", host, err)
            raise CannotConnect(f"Cannot connect to {host}") from err


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
