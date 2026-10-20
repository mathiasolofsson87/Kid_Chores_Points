"""Tests for the config flow."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.kid_chores_points.const import DOMAIN


@pytest.fixture(autouse=True)
def no_setup(hass):
    """Only the flow is under test; skip loading the integration itself."""
    hass.config.components.update({"frontend", "http"})
    with (
        patch(
            "custom_components.kid_chores_points.async_setup", return_value=True
        ),
        patch(
            "custom_components.kid_chores_points.async_setup_entry",
            return_value=True,
        ),
    ):
        yield


async def test_user_flow_creates_an_entry(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"name": "  Anna  "}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Anna"


async def test_same_name_is_refused(hass):
    for expected in (FlowResultType.CREATE_ENTRY, FlowResultType.ABORT):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"name": "Anna"}
        )
        assert result["type"] is expected
