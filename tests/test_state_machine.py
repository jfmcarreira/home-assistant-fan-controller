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

    def start_humidity_delta_check(self) -> None:
        self.calls.append(("start_humidity_delta_check", None))

    def clear_humidity_delta_check(self) -> None:
        self.calls.append(("clear_humidity_delta_check", None))

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
async def test_fan_started_with_light_on_has_no_manual_runtime_limit() -> None:
    """Fan starts while the light is on use the active light-session behavior."""
    controller = Controller()
    machine = FanStateMachine(controller)
    controller.light_on = True
    machine.state_update()
    controller.calls.clear()

    controller.fan_on = True
    machine.state_update()

    assert machine.current_state.id == "light_on_fan_on"
    assert not any(call[0] == "set_timer" for call in controller.calls)


@pytest.mark.asyncio
async def test_humidity_started_fan_with_light_on_has_no_manual_runtime_limit() -> None:
    """Humidity-driven operation is not treated as a manually started fan."""
    controller = Controller()
    machine = FanStateMachine(controller)
    controller.light_on = True
    machine.state_update()
    controller.calls.clear()

    controller.high_humidity = True
    machine.humidity_update()

    assert machine.current_state.id == "light_on_fan_on"
    assert not any(call[0] == "set_timer" for call in controller.calls)


@pytest.mark.asyncio
async def test_fan_reenabled_during_light_session_has_no_manual_runtime_limit() -> None:
    """Re-enabling a fan after opting out keeps the active light-session behavior."""
    controller = Controller()
    machine = FanStateMachine(controller)
    controller.light_on = True
    machine.state_update()
    controller.high_humidity = True
    machine.humidity_update()
    controller.fan_on = True
    machine.state_update()

    controller.fan_on = False
    machine.state_update()
    assert machine.current_state.id == "light_on_fan_off"

    controller.calls.clear()
    controller.fan_on = True
    machine.state_update()

    assert machine.current_state.id == "light_on_fan_on"
    assert not any(call[0] == "set_timer" for call in controller.calls)


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
    assert ("start_humidity_delta_check", None) in controller.calls

    controller.calls.clear()
    controller.humidity_recovered = True
    machine.humidity_update()

    assert ("clear_humidity_delta_check", None) in controller.calls


@pytest.mark.asyncio
async def test_light_on_returns_high_humidity_state_to_active_light_session() -> None:
    """A new light session must not inherit the prior humidity timeout."""
    controller = Controller()
    controller.fan_on = True
    controller.light_on = True
    controller.state = "fan_on_high_humidity"
    machine = FanStateMachine(controller)

    machine.state_update()

    assert machine.current_state.id == "light_on_fan_on"
    assert ("clear_humidity_delta_check", None) in controller.calls
    assert ("record_humidity_light_on", None) in controller.calls

    controller.calls.clear()
    controller.humidity_recovered = True
    machine.humidity_update()
    machine.timer_update()

    assert machine.current_state.id == "light_on_fan_on"
    assert ("turn_off_fan", "humidity recovery timeout elapsed") not in controller.calls
