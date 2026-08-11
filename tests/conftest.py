"""Shared fixtures for Fan Controller tests."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.fan_controller.const import (
    CONF_AVG_HUMIDITY_SENSOR,
    CONF_FAN_ENTITY,
    CONF_HUMIDITY_SENSOR,
    CONF_LIGHT_ENTITY,
    CONF_NAME,
    DOMAIN,
)

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture
def configured_entity_ids(hass: HomeAssistant) -> dict[str, str]:
    """Create the entities required by the config flow and coordinator."""
    registry = er.async_get(hass)
    fan = registry.async_get_or_create("fan", "test", "bathroom_fan")
    light = registry.async_get_or_create("light", "test", "bathroom_light")
    humidity = registry.async_get_or_create("sensor", "test", "bathroom_humidity")
    average_humidity = registry.async_get_or_create("sensor", "test", "bathroom_average_humidity")

    return {
        CONF_FAN_ENTITY: fan.entity_id,
        CONF_LIGHT_ENTITY: light.entity_id,
        CONF_HUMIDITY_SENSOR: humidity.entity_id,
        CONF_AVG_HUMIDITY_SENSOR: average_humidity.entity_id,
    }


@pytest.fixture
def config_entry(configured_entity_ids: dict[str, str]) -> MockConfigEntry:
    """Create a configured Fan Controller entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Bathroom",
        unique_id="bathroom_fan",
        data={CONF_NAME: "Bathroom", **configured_entity_ids},
    )
