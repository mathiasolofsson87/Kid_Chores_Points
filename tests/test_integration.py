"""Tests that set up the whole integration and use its services and entities."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.exceptions import ServiceValidationError

from custom_components.kid_chores_points.const import (
    CONF_MANDATORY,
    CONF_REWARDS,
    DEFAULT_OPTIONS,
    DOMAIN,
)


@pytest.fixture
async def entry(hass):
    """A set-up config entry (frontend/http are not needed for the logic)."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Chores",
        options={
            **DEFAULT_OPTIONS,
            CONF_MANDATORY: {"Dishes": 20},
            CONF_REWARDS: {"15 min Xbox": 10},
        },
    )
    entry.add_to_hass(hass)
    # the real frontend/http are heavy and irrelevant here: treat as already set up
    hass.config.components.update({"frontend", "http"})
    with (
        patch("custom_components.kid_chores_points.add_extra_js_url"),
        patch.object(hass, "http", create=True) as http,
    ):
        http.async_register_static_paths = _noop
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


async def _noop(*_args, **_kwargs):
    return None


async def test_services_are_registered(hass, entry):
    for service in (
        "complete_chore",
        "redeem",
        "adjust_points",
        "adjust_wallet",
        "close_week",
        "undo",
    ):
        assert hass.services.has_service(DOMAIN, service)


async def test_complete_chore_service_updates_the_sensors(hass, entry):
    await hass.services.async_call(
        DOMAIN, "complete_chore", {"name": "Dishes"}, blocking=True
    )
    await hass.async_block_till_done()
    assert entry.runtime_data.week == 20
    states = {s.entity_id: s.state for s in hass.states.async_all("sensor")}
    assert "20" in states.values()


async def test_redeem_service_with_too_few_points_fails(hass, entry):
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "redeem", {"reward": "15 min Xbox"}, blocking=True
        )


async def test_adjust_then_redeem_adds_a_todo_item(hass, entry):
    await hass.services.async_call(
        DOMAIN,
        "adjust_points",
        {"target": "bank", "points": 30, "reason": "test"},
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN, "redeem", {"reward": "15 min Xbox", "units": 2}, blocking=True
    )
    await hass.async_block_till_done()
    manager = entry.runtime_data
    assert manager.bank == 10
    assert [r["summary"] for r in manager.reward_log] == ["2 × 15 min Xbox"]


async def test_close_week_service(hass, entry):
    manager = entry.runtime_data
    manager.data["week"] = 55
    await hass.services.async_call(DOMAIN, "close_week", {}, blocking=True)
    assert manager.week == 0
    assert manager.bank == 55


async def test_service_rejects_bad_input(hass, entry):
    with pytest.raises(Exception):
        await hass.services.async_call(
            DOMAIN, "redeem", {"reward": "x", "units": 0}, blocking=True
        )
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "complete_chore", {"name": "Unknown"}, blocking=True
        )


async def test_entry_unloads_cleanly(hass, entry):
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
