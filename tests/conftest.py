"""Shared fixtures for Kid Chores & Points tests."""

from __future__ import annotations

from typing import Any

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kid_chores_points.const import (
    CONF_BONUS,
    CONF_GOAL,
    CONF_GOAL_BONUS,
    CONF_MANDATORY,
    CONF_POLICY,
    CONF_REWARD_PAYOUT,
    CONF_REWARDS,
    DEFAULT_OPTIONS,
    DOMAIN,
    POLICY_ANYWAY,
)
from custom_components.kid_chores_points.manager import ChoresManager


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Allow Home Assistant to load the custom integration under test."""


@pytest.fixture
def make_manager(hass):
    """Build a loaded ChoresManager with the given option overrides."""

    async def _make(**options: Any) -> ChoresManager:
        await hass.config.async_set_time_zone("UTC")
        opts = {
            **DEFAULT_OPTIONS,
            CONF_GOAL: 50,
            CONF_GOAL_BONUS: 10,
            CONF_POLICY: POLICY_ANYWAY,
            CONF_MANDATORY: {"Dishes": 20, "Trash": 30},
            CONF_BONUS: {"Vacuum": 12},
            CONF_REWARDS: {"15 min Xbox": 10, "Cash out": 10},
            CONF_REWARD_PAYOUT: {"Cash out": 5},
            **options,
        }
        entry = MockConfigEntry(domain=DOMAIN, title="Kid", options=opts)
        entry.add_to_hass(hass)
        manager = ChoresManager(hass, entry)
        await manager.async_load()
        return manager

    return _make
