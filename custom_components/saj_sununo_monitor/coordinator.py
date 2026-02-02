"""DataUpdateCoordinator for SAJ Sununo-TL Series Monitor."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import defusedxml.ElementTree as ET

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# XML field definitions: key -> xml_tag
XML_FIELDS = {
    "state": ("state", None),  # None means keep as string
    "v-grid": ("v-grid", float),
    "i-grid": ("i-grid", float),
    "f-grid": ("f-grid", float),
    "p-ac": ("p-ac", float),
    "temp": ("temp", float),
    "e-today": ("e-today", float),
    "t-today": ("t-today", float),
    "e-total": ("e-total", float),
    "CO2": ("CO2", float),
    "t-total": ("t-total", float),
    "v-pv1": ("v-pv1", float),
    "i-pv1": ("i-pv1", float),
    "v-pv2": ("v-pv2", float),  # Will handle whitespace splitting in parsing
    "i-pv2": ("i-pv2", float),  # Will handle whitespace splitting in parsing
    "v-bus": ("v-bus", float),
}

REQUEST_TIMEOUT = 10


class SajSununoDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching SAJ Sununo data."""

    def __init__(self, hass: HomeAssistant, host: str, scan_interval: int) -> None:
        """Initialize the coordinator."""
        self.host = host
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=scan_interval,  # Pass timedelta directly
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from SAJ Sununo."""
        url = f"http://{self.host}/real_time_data.xml"
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                session = async_get_clientsession(self.hass)
                async with session.get(url) as response:
                    response.raise_for_status()
                    xml_content = await response.text()
                    return self._parse_xml_data(xml_content)
        except TimeoutError as err:
            _LOGGER.error(
                "Timeout while connecting to SAJ Sununo inverter at %s", self.host
            )
            raise UpdateFailed(f"Timeout connecting to {self.host}") from err
        except Exception as err:  # Catch aiohttp, XML parsing, and other errors
            _LOGGER.error("Error fetching data from %s: %s", self.host, err)
            raise UpdateFailed(f"Error fetching data: {err}") from err

    def _parse_xml_data(self, xml_content: str) -> dict[str, Any]:
        """Parse XML data from SAJ Sununo."""
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as err:
            _LOGGER.error("Error parsing XML data: %s", err)
            raise UpdateFailed(f"XML parse error: {err}") from err

        data: dict[str, Any] = {}
        for key, (xml_tag, converter) in XML_FIELDS.items():
            element = root.find(xml_tag)
            if element is None or element.text is None:
                _LOGGER.warning("Missing XML element: %s", xml_tag)
                continue

            try:
                raw_value = element.text.strip()

                # Handle special cases where value might have trailing units/text
                if key in ("v-pv2", "i-pv2"):
                    raw_value = raw_value.split()[0]

                # Convert if needed, otherwise keep as string
                if converter is not None:
                    data[key] = converter(raw_value)
                else:
                    data[key] = raw_value
            except (ValueError, IndexError) as err:
                _LOGGER.warning("Error converting %s value %s: %s", key, raw_value, err)
                continue

        return data
