"""DataUpdateCoordinator for SAJ Sununo-TL Series Monitor."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import datetime, timedelta
import logging
from typing import Any

import defusedxml.ElementTree as ET

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval
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
    "v-pv3": ("v-pv3", float),  # Optional third string
    "i-pv3": ("i-pv3", float),  # Optional third string
    "v-pv4": ("v-pv4", float),  # Optional fourth string
    "i-pv4": ("i-pv4", float),  # Optional fourth string
    "v-bus": ("v-bus", float),
}

AVERAGE_KEYS = {
    "v-grid",
    "i-grid",
    "f-grid",
    "p-ac",
    "temp",
    "v-pv1",
    "i-pv1",
    "v-pv2",
    "i-pv2",
    "v-pv3",
    "i-pv3",
    "v-pv4",
    "i-pv4",
}

REQUEST_TIMEOUT = 10


class SajSununoDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching SAJ Sununo data."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        scan_interval: timedelta,
        storage_interval: timedelta,
    ) -> None:
        """Initialize the coordinator."""
        self.host = host
        self._scan_interval = scan_interval
        self._storage_interval = storage_interval
        self._buffer: dict[str, list[float]] = {key: [] for key in AVERAGE_KEYS}
        self._interval_last_sample: dict[str, Any] | None = None
        self._interval_has_sample: bool = False
        self._lock = asyncio.Lock()
        self._unsub_scan: Callable[[], None] | None = None
        self._unsub_storage: Callable[[], None] | None = None
        self._missing_pv_sensors: set[str] = set()
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=None,
        )

    async def async_start(self) -> None:
        """Start polling and aggregation."""
        if self._unsub_scan or self._unsub_storage:
            return

        self._unsub_scan = async_track_time_interval(
            self.hass, self._async_poll_device, self._scan_interval
        )
        self._unsub_storage = async_track_time_interval(
            self.hass, self._async_publish_means, self._storage_interval
        )

    async def async_stop(self) -> None:
        """Stop polling and aggregation."""
        if self._unsub_scan is not None:
            self._unsub_scan()
            self._unsub_scan = None
        if self._unsub_storage is not None:
            self._unsub_storage()
            self._unsub_storage = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch an initial sample and return averaged data."""
        data = await self._async_fetch_sample()
        async with self._lock:
            self._add_sample(data)
            return self._build_mean_data()

    async def _async_poll_device(self, _: datetime) -> None:
        """Poll the inverter and buffer samples."""
        try:
            data = await self._async_fetch_sample()
        except UpdateFailed as err:
            _LOGGER.debug("Sample poll failed: %s", err)
            return

        async with self._lock:
            self._add_sample(data)

    async def _async_publish_means(self, _: datetime) -> None:
        """Publish averaged data at the storage interval."""
        async with self._lock:
            if not self._interval_has_sample:
                self.async_set_update_error(UpdateFailed("No samples collected"))
                return

            mean_data = self._build_mean_data()
            self._clear_buffer()

        self.async_set_updated_data(mean_data)

    def _add_sample(self, data: dict[str, Any]) -> None:
        """Store a sample for averaging."""
        self._interval_last_sample = data
        self._interval_has_sample = True
        for key in AVERAGE_KEYS:
            if (value := data.get(key)) is None:
                continue
            try:
                self._buffer[key].append(float(value))
            except (TypeError, ValueError):
                _LOGGER.debug("Skipping non-numeric sample for %s: %s", key, value)

    def _clear_buffer(self) -> None:
        """Clear buffered samples after publishing."""
        for values in self._buffer.values():
            values.clear()
        self._interval_last_sample = None
        self._interval_has_sample = False

    def _build_mean_data(self) -> dict[str, Any]:
        """Build averaged data using buffered samples and last known values."""
        if self._interval_last_sample is None:
            return {}

        mean_data = dict(self._interval_last_sample)
        for key, values in self._buffer.items():
            if values:
                mean_data[key] = sum(values) / len(values)

        return mean_data

    async def _async_fetch_sample(self) -> dict[str, Any]:
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
                # Only warn once for missing PV sensors
                if (
                    key.startswith(("v-pv", "i-pv"))
                    and key not in self._missing_pv_sensors
                ):
                    _LOGGER.warning("Missing PV sensor XML element: %s", xml_tag)
                    self._missing_pv_sensors.add(key)
                elif not key.startswith(("v-pv", "i-pv")):
                    _LOGGER.warning("Missing XML element: %s", xml_tag)
                continue

            try:
                raw_value = element.text.strip()

                # Handle special cases where value might have trailing units/text
                if key in ("v-pv2", "i-pv2", "v-pv3", "i-pv3", "v-pv4", "i-pv4"):
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
