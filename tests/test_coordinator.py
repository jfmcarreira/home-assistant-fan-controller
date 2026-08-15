"""Tests for Fan Controller coordination logic."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.fan_controller.const import (
    CONF_AVG_HUMIDITY_SENSOR,
    CONF_FAN_ENTITY,
    CONF_HUMIDITY_PROGRESS_REQUIRED_DROP,
    CONF_LIGHT_ENTITY,
    HUMIDITY_PROGRESS_WINDOW_SECONDS,
)
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


def test_humidity_recovery_requires_configured_drop_every_ten_minutes(hass: HomeAssistant, config_entry) -> None:
    """High-humidity operation starts post-run when humidity stops improving."""
    config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(config_entry, options={CONF_HUMIDITY_PROGRESS_REQUIRED_DROP: 2})
    coordinator = FanCoordinator(hass, config_entry)
    coordinator._humidity_light_on = 60.0
    coordinator._current_humidity = 80.0
    hass.states.async_set(config_entry.data[CONF_AVG_HUMIDITY_SENSOR], "50")
    started_at = datetime(2026, 8, 11, 18, 0, tzinfo=UTC)

    with patch(
        "custom_components.fan_controller.coordinator.dt_util.utcnow",
        return_value=started_at,
    ):
        coordinator.start_humidity_delta_check()

    coordinator._current_humidity = 78.0
    with patch(
        "custom_components.fan_controller.coordinator.dt_util.utcnow",
        return_value=started_at + timedelta(minutes=10),
    ):
        assert not coordinator.is_humidity_recovered()

    coordinator._current_humidity = 77.0
    with patch(
        "custom_components.fan_controller.coordinator.dt_util.utcnow",
        return_value=started_at + timedelta(minutes=20),
    ):
        assert coordinator.is_humidity_recovered()

    coordinator.clear_humidity_delta_check()


def test_humidity_delta_check_schedules_and_cancels_deadline(hass: HomeAssistant, config_entry) -> None:
    """Each progress window schedules a check and clearing it cancels the callback."""
    coordinator = FanCoordinator(hass, config_entry)

    with patch("custom_components.fan_controller.coordinator.async_call_later") as schedule:
        coordinator.start_humidity_delta_check()

        assert schedule.call_args.args[1] == HUMIDITY_PROGRESS_WINDOW_SECONDS

        coordinator.clear_humidity_delta_check()

    schedule.return_value.assert_called_once()


async def test_humidity_delta_timeout_detects_stalled_humidity_without_sensor_event(
    hass: HomeAssistant, config_entry
) -> None:
    """The progress timer starts post-run mode even when no sensor state changes arrive."""
    coordinator = FanCoordinator(hass, config_entry)
    started_at = datetime(2026, 8, 11, 18, 0, tzinfo=UTC)
    coordinator._humidity_light_on = 60.0
    coordinator._current_humidity = 80.0
    coordinator._humidity_delta_started_at = started_at
    coordinator._humidity_delta_start_humidity = 80.0
    coordinator.state = "fan_on_high_humidity"
    hass.states.async_set(config_entry.data[CONF_FAN_ENTITY], "on")
    hass.states.async_set(config_entry.data[CONF_LIGHT_ENTITY], "off")
    hass.states.async_set(config_entry.data[CONF_AVG_HUMIDITY_SENSOR], "50")

    with patch(
        "custom_components.fan_controller.coordinator.dt_util.utcnow",
        return_value=started_at + timedelta(minutes=10),
    ):
        await coordinator._async_handle_humidity_delta_timeout()

    assert coordinator.current_state_name == "fan_on_timeout"
    coordinator.cancel_timer()
