"""Tests for the Fan Controller config and options flows."""

from __future__ import annotations

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.fan_controller.config_flow import FanOptionsFlow
from custom_components.fan_controller.const import (
    CONF_FAN_ENTITY,
    CONF_FAN_TIMEOUT,
    CONF_HUMIDITY_PROGRESS_REQUIRED_DROP,
    CONF_HUMIDITY_THRESHOLD,
    CONF_MAX_TIMEOUT,
    CONF_NAME,
    DOMAIN,
)

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


async def test_user_flow_creates_entry(hass: HomeAssistant, configured_entity_ids: dict[str, str]) -> None:
    """The user flow creates an entry for registered entities."""
    data = {CONF_NAME: "Bathroom", **configured_entity_ids}

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=data
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Bathroom"
    assert result["data"] == data


async def test_user_flow_rejects_wrong_entity_domain(
    hass: HomeAssistant, configured_entity_ids: dict[str, str]
) -> None:
    """The fan selector rejects an entity from a different domain."""
    data = {CONF_NAME: "Bathroom", **configured_entity_ids}
    data[CONF_FAN_ENTITY] = configured_entity_ids["light_entity"]

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=data
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_FAN_ENTITY: "entity_not_found"}


async def test_user_flow_rejects_duplicate_fan(
    hass: HomeAssistant,
    config_entry,
    configured_entity_ids: dict[str, str],
) -> None:
    """A fan can only be controlled by one entry."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={CONF_NAME: "Second Bathroom", **configured_entity_ids},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_FAN_ENTITY: "already_configured"}


async def test_options_flow_saves_values(config_entry) -> None:
    """The options flow persists the configured control limits."""
    options = {
        CONF_FAN_TIMEOUT: 600,
        CONF_MAX_TIMEOUT: 30,
        CONF_HUMIDITY_THRESHOLD: 25,
        CONF_HUMIDITY_PROGRESS_REQUIRED_DROP: 3,
    }

    result = await FanOptionsFlow(config_entry).async_step_init(options)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == options
