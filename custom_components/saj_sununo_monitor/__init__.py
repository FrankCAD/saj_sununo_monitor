"""The SAJ Sununo-TL Series Monitor integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .coordinator import SajSununoDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

# Type alias for config entry with runtime data
type SajSununoConfigEntry = ConfigEntry[SajSununoDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: SajSununoConfigEntry) -> bool:
    """Set up SAJ Sununo-TL Series Monitor from a config entry."""
    _LOGGER.debug("Setting up SAJ Sununo-TL Series Monitor: %s", entry.title)

    # Convert scan_interval from seconds to timedelta
    scan_interval = timedelta(
        seconds=entry.data.get("scan_interval", DEFAULT_SCAN_INTERVAL)
    )

    # Create and initialize coordinator
    coordinator = SajSununoDataUpdateCoordinator(
        hass, entry.data["host"], scan_interval
    )
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator in runtime data
    entry.runtime_data = coordinator

    # Register device in device registry
    _register_device(hass, entry)

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        _LOGGER.debug(
            "Successfully unloaded SAJ Sununo-TL Series Monitor: %s", entry.title
        )
    return unload_ok


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


def _register_device(hass: HomeAssistant, entry: SajSununoConfigEntry) -> None:
    """Register or update device in device registry."""
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.data["device_name"],
        manufacturer="SAJ",
        model=entry.data.get("model", "unknown"),
        model_id=entry.data.get("model_id", "unknown"),
        serial_number=entry.data.get("serial_number", "unknown"),
        sw_version=entry.data.get("sw_version", "unknown"),
        suggested_area=entry.data.get("area"),
    )
