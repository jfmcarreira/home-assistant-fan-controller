"""Regression tests for fan-controller timer transitions."""

import pytest

from custom_components.fan_controller.coordinator import FanStateMachine


class Controller:
    """Minimal model used to observe state-machine side effects."""

    def __init__(self) -> None:
        self.fan_on = False
        self.light_on = False
        self.high_humidity = False
        self.humidity_recovered = False
        self.calls: list[tuple[str, float | str | None]] = []

    def is_fan_on(self) -> bool:
        return self.fan_on

    def is_light_on(self) -> bool:
        return self.light_on

    def is_high_humidity(self) -> bool:
        return self.high_humidity

    def is_humidity_recovered(self) -> bool:
        return self.humidity_recovered

    def is_auto_on_disabled(self) -> bool:
        return False

    def turn_on_fan(self, reason: str) -> None:
        self.calls.append(("turn_on_fan", reason))

    def turn_off_fan(self, reason: str) -> None:
        self.calls.append(("turn_off_fan", reason))

    def set_timer(self, seconds: float) -> None:
        self.calls.append(("set_timer", seconds))

    def cancel_timer(self) -> None:
        self.calls.append(("cancel_timer", None))

    def get_fan_timeout_seconds(self) -> float:
        return 300.0

    def get_max_timeout_seconds(self) -> float:
        return 1_800.0

    def log_humidity_recovered(self) -> None:
        self.calls.append(("log_humidity_recovered", None))

    def start_humidity_progress_check(self) -> None:
        self.calls.append(("start_humidity_progress_check", None))

    def clear_humidity_progress_check(self) -> None:
        self.calls.append(("clear_humidity_progress_check", None))

    def record_humidity_light_on(self) -> None:
        self.calls.append(("record_humidity_light_on", None))

    def record_humidity_fan_on(self) -> None:
        self.calls.append(("record_humidity_fan_on", None))


@pytest.mark.asyncio
async def test_manual_fan_state_update_does_not_restart_runtime_timer() -> None:
    """Fan state updates must not extend the manual runtime limit."""
    controller = Controller()
    machine = FanStateMachine(controller)
    controller.fan_on = True

    machine.state_update()
    assert controller.calls == [("cancel_timer", None), ("set_timer", 1_800.0)]

    controller.calls.clear()
    machine.state_update()

    assert controller.calls == []


@pytest.mark.asyncio
async def test_humidity_update_does_not_restart_post_run_timer() -> None:
    """Humidity changes below the threshold must not extend the post-run timer."""
    controller = Controller()
    controller.fan_on = True
    machine = FanStateMachine(controller)
    controller.state = "fan_on_timeout"

    machine.humidity_update()

    assert controller.calls == []


@pytest.mark.asyncio
async def test_high_humidity_state_starts_and_clears_progress_check() -> None:
    """The progress watchdog is active only while humidity is high."""
    controller = Controller()
    machine = FanStateMachine(controller)
    controller.state = "fan_on_timeout"
    controller.high_humidity = True

    machine.humidity_update()
    assert ("start_humidity_progress_check", None) in controller.calls

    controller.calls.clear()
    controller.humidity_recovered = True
    machine.humidity_update()

    assert ("clear_humidity_progress_check", None) in controller.calls
