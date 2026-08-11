"""Tests for the Auto Mode switch."""

from __future__ import annotations

from datetime import UTC, datetime

from custom_components.fan_controller.switch import FanAutoModeSwitch


class FakeCoordinator:
    """Coordinator values exposed by the Auto Mode switch."""

    auto_mode = True
    humidity_light_on = 55.0
    humidity_fan_on = 62.0
    average_humidity = 50.0
    humidity_reference = 55.0
    timer_expires_at = datetime(2026, 8, 10, 12, 0, tzinfo=UTC)
    current_state_name = "fan_on_timeout"

    def __init__(self) -> None:
        self.values: list[bool] = []

    async def async_set_auto_mode(self, value: bool) -> None:
        self.auto_mode = value
        self.values.append(value)

    def register_state_change_callback(self, callback) -> None:
        """Provide the coordinator interface required by the entity."""

    def unregister_state_change_callback(self, callback) -> None:
        """Provide the coordinator interface required by the entity."""


async def test_auto_mode_switch_delegates_to_coordinator(config_entry) -> None:
    """Switch actions update Auto Mode through the coordinator."""
    coordinator = FakeCoordinator()
    entity = FanAutoModeSwitch(coordinator, config_entry)

    await entity.async_turn_off()
    assert coordinator.values == [False]
    assert not entity.is_on

    await entity.async_turn_on()
    assert coordinator.values == [False, True]
    assert entity.is_on


def test_auto_mode_switch_exposes_controller_attributes(config_entry) -> None:
    """Diagnostic controller state is exposed as switch attributes."""
    entity = FanAutoModeSwitch(FakeCoordinator(), config_entry)

    assert entity.extra_state_attributes == {
        "humidity_when_light_turned_on": 55.0,
        "humidity_when_fan_turned_on": 62.0,
        "average_humidity": 50.0,
        "humidity_reference": 55.0,
        "timer_expires_at": "2026-08-10T12:00:00+00:00",
        "controller_state": "fan_on_timeout",
    }
