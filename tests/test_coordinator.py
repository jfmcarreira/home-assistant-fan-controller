"""Tests for Fan Controller coordination logic."""

import pytest
from homeassistant.core import HomeAssistant

from custom_components.fan_controller.const import CONF_AVG_HUMIDITY_SENSOR
from custom_components.fan_controller.coordinator import FanCoordinator


@pytest.mark.parametrize(
    ("humidity_reference", "expected_threshold"),
    [(60.0, 66.0), (65.0, 70.25)],
)
def test_humidity_threshold_uses_remaining_headroom(
    hass: HomeAssistant,
    config_entry,
    humidity_reference: float,
    expected_threshold: float,
) -> None:
    """The default 15% threshold is calculated from remaining headroom."""
    coordinator = FanCoordinator(hass, config_entry)
    coordinator._humidity_light_on = humidity_reference
    coordinator._humidity_fan_on = humidity_reference
    hass.states.async_set(config_entry.data[CONF_AVG_HUMIDITY_SENSOR], str(humidity_reference))

    assert coordinator.humidity_threshold == expected_threshold

    coordinator._current_humidity = expected_threshold
    assert not coordinator.is_high_humidity()

    coordinator._current_humidity = expected_threshold + 0.01
    assert coordinator.is_high_humidity()


@pytest.mark.parametrize(
    ("current_humidity", "expected_recovered"),
    [(60.0, True), (59.9, True), (None, False)],
)
def test_humidity_recovery_requires_available_humidity_at_or_below_baseline(
    hass: HomeAssistant,
    config_entry,
    current_humidity: float | None,
    expected_recovered: bool,
) -> None:
    """Post-run timing begins only after available humidity reaches the baseline."""
    coordinator = FanCoordinator(hass, config_entry)
    coordinator._humidity_light_on = 60.0
    hass.states.async_set(config_entry.data[CONF_AVG_HUMIDITY_SENSOR], "50")
    coordinator._current_humidity = current_humidity

    assert coordinator.is_humidity_recovered() is expected_recovered
