"""Tests for SAJ Sununo-TL Series Monitor coordinator."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
import sys
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

# Add config path to sys.path for custom component imports
config_path = Path(__file__).parent.parent.parent.parent / "config"
if str(config_path) not in sys.path:
    sys.path.insert(0, str(config_path))

from custom_components.saj_sununo_monitor.coordinator import (
    AVERAGE_KEYS,
    SajSununoDataUpdateCoordinator,
)


@pytest.fixture
def coordinator(hass: HomeAssistant) -> SajSununoDataUpdateCoordinator:
    """Create a coordinator with short intervals for testing."""
    return SajSununoDataUpdateCoordinator(
        hass=hass,
        host="192.168.1.1",
        scan_interval=timedelta(milliseconds=100),
        storage_interval=timedelta(milliseconds=300),
    )


def _make_sample_data(v_pv1: float | None, i_pv1: float | None) -> dict[str, Any]:
    """Create a sample data dict with v-pv1 and i-pv1 values."""
    return {
        "state": "OK",
        "v-grid": 230.0,
        "i-grid": 5.0,
        "f-grid": 50.0,
        "p-ac": 1000.0,
        "temp": 34.0,
        "e-today": 10.0,
        "t-today": 240,
        "e-total": 1200.0,
        "CO2": 44.0,
        "t-total": 3600,
        "v-pv1": v_pv1,
        "i-pv1": i_pv1,
        "v-pv2": 155.0,
        "i-pv2": 7.8,
        "v-pv3": None,
        "i-pv3": None,
        "v-pv4": None,
        "i-pv4": None,
        "v-bus": 400.0,
    }


@pytest.mark.asyncio
async def test_polling_with_one_poll_failure(
    hass: HomeAssistant, coordinator: SajSununoDataUpdateCoordinator
) -> None:
    """Test average calculation when one poll fails and others succeed.

    Simulates a series of polls spanning one storage interval:
    - Poll 1: Succeeds with v-pv1=150.0, i-pv1=8.0
    - Poll 2: Fails (timeout/unavailable)
    - Poll 3: Succeeds with v-pv1=149.0, i-pv1=8.2

    Verifies that the averages are calculated only from successful polls:
    - v-pv1 average: (150.0 + 149.0) / 2 = 149.5
    - i-pv1 average: (8.0 + 8.2) / 2 = 8.1
    """
    published_data_list: list[dict[str, Any]] = []

    def capture_updated_data(data: dict[str, Any]) -> None:
        """Capture published data."""
        published_data_list.append(data.copy())

    coordinator.async_set_updated_data = MagicMock(side_effect=capture_updated_data)
    coordinator.async_set_update_error = MagicMock()

    # Simulate successful fetch for poll 1
    poll_1_data = _make_sample_data(v_pv1=150.0, i_pv1=8.0)
    async with coordinator._lock:
        coordinator._add_sample(poll_1_data)

    # Simulate poll 2 failure (no sample added)
    # This represents a timeout or device unavailable situation

    # Simulate successful fetch for poll 3
    poll_3_data = _make_sample_data(v_pv1=149.0, i_pv1=8.2)
    async with coordinator._lock:
        coordinator._add_sample(poll_3_data)

    # Trigger storage interval publication
    await coordinator._async_publish_means(None)

    # Verify data was published
    assert len(published_data_list) == 1
    published_data = published_data_list[0]

    # Verify averaged values are calculated from the two successful polls
    # v-pv1 average: (150.0 + 149.0) / 2 = 149.5
    assert published_data["v-pv1"] == pytest.approx(149.5, rel=0.01)

    # i-pv1 average: (8.0 + 8.2) / 2 = 8.1
    assert published_data["i-pv1"] == pytest.approx(8.1, rel=0.01)

    # Verify buffer is cleared after storage
    async with coordinator._lock:
        assert len(coordinator._buffer["v-pv1"]) == 0
        assert len(coordinator._buffer["i-pv1"]) == 0


@pytest.mark.asyncio
async def test_polling_with_all_polls_failing(
    hass: HomeAssistant, coordinator: SajSununoDataUpdateCoordinator
) -> None:
    """Test error handling when all polls fail during a storage interval.

    Simulates a series of polls spanning one storage interval:
    - Poll 1: Fails (timeout)
    - Poll 2: Fails (device unavailable)
    - Poll 3: Fails (network error)

    Verifies that an error is set when no samples are collected.
    """
    published_data_list: list[dict[str, Any]] = []
    error_list: list[Exception] = []

    def capture_updated_data(data: dict[str, Any]) -> None:
        """Capture published data."""
        published_data_list.append(data.copy())

    def capture_error(error: Exception) -> None:
        """Capture error."""
        error_list.append(error)

    coordinator.async_set_updated_data = MagicMock(side_effect=capture_updated_data)
    coordinator.async_set_update_error = MagicMock(side_effect=capture_error)

    # Simulate three failed polls (no samples added)
    # In real scenario, these would be calls to _async_poll_device that catch
    # exceptions and return without adding samples

    # No samples are added to the buffer during this storage interval

    # Verify initial state
    async with coordinator._lock:
        assert coordinator._interval_has_sample is False

    # Trigger storage interval publication
    await coordinator._async_publish_means(None)

    # Verify no data was published, but error was set
    assert len(published_data_list) == 0
    assert len(error_list) == 1
    assert "No samples collected" in str(error_list[0])

    # Verify buffer is cleared even though it was empty
    async with coordinator._lock:
        assert len(coordinator._buffer["v-pv1"]) == 0
        assert len(coordinator._buffer["i-pv1"]) == 0
