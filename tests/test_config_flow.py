"""Tests for the config flow."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.kid_chores_points.const import (
    CONF_CHORE_IDS,
    CONF_MANDATORY,
    DEFAULT_OPTIONS,
    DOMAIN,
)


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


# ----------------------------------------------------------------------
# Linking chores to Maintenance Supporter tasks
# ----------------------------------------------------------------------
@pytest.fixture
def ms_tasks(hass):
    """A Maintenance Supporter object with two tasks (no need to set it up)."""
    MockConfigEntry(
        domain="maintenance_supporter",
        data={
            "object": {"name": "Kitchen"},
            "tasks": {"id-dishes": {"name": "Dishes"}, "id-trash": {"name": "Trash"}},
        },
    ).add_to_hass(hass)


@pytest.fixture
def entry(hass):
    entry = MockConfigEntry(domain=DOMAIN, title="Anna", options=DEFAULT_OPTIONS)
    entry.add_to_hass(hass)
    return entry


async def _step(hass, flow_id, user_input=None):
    return await hass.config_entries.options.async_configure(flow_id, user_input)


async def _open(hass, entry, *path):
    """Open the options flow and follow menu choices `path`."""
    result = await hass.config_entries.options.async_init(entry.entry_id)
    for choice in path:
        result = await _step(hass, result["flow_id"], {"next_step_id": choice})
    return result


async def test_picking_a_task_links_the_chore_by_id(hass, entry, ms_tasks):
    result = await _open(hass, entry, "mandatory", "mandatory_add")
    options = result["data_schema"].schema["name"].config["options"]
    assert {o["value"] for o in options} == {"id-dishes", "id-trash"}

    await _step(hass, result["flow_id"], {"name": "id-dishes", "points": 20})
    assert entry.options[CONF_MANDATORY] == {"Dishes": 20}
    assert entry.options[CONF_CHORE_IDS] == {"Dishes": "id-dishes"}


async def test_a_typed_name_is_not_linked(hass, entry, ms_tasks):
    result = await _open(hass, entry, "mandatory", "mandatory_add")
    await _step(hass, result["flow_id"], {"name": "Walk the dog", "points": 5})
    assert entry.options[CONF_MANDATORY] == {"Walk the dog": 5}
    assert entry.options[CONF_CHORE_IDS] == {}


async def test_editing_points_keeps_the_chore_name_and_link(hass, entry, ms_tasks):
    hass.config_entries.async_update_entry(
        entry,
        options={
            **entry.options,
            CONF_MANDATORY: {"Old name": 20},
            CONF_CHORE_IDS: {"Old name": "id-dishes"},  # the task was renamed since
        },
    )
    result = await _open(hass, entry, "mandatory", "mandatory_edit")
    result = await _step(hass, result["flow_id"], {"name": "Old name"})
    # the form starts on the linked task, not on the old name
    name_field = next(k for k in result["data_schema"].schema if k == "name")
    assert name_field.default() == "id-dishes"
    await _step(hass, result["flow_id"], {"name": "id-dishes", "points": 25})
    assert entry.options[CONF_MANDATORY] == {"Old name": 25}
    assert entry.options[CONF_CHORE_IDS] == {"Old name": "id-dishes"}


async def test_repicking_another_task_renames_and_relinks(hass, entry, ms_tasks):
    hass.config_entries.async_update_entry(
        entry, options={**entry.options, CONF_MANDATORY: {"Dishes": 20}}
    )
    result = await _open(hass, entry, "mandatory", "mandatory_edit")
    result = await _step(hass, result["flow_id"], {"name": "Dishes"})
    await _step(hass, result["flow_id"], {"name": "id-trash", "points": 20})
    assert entry.options[CONF_MANDATORY] == {"Trash": 20}
    assert entry.options[CONF_CHORE_IDS] == {"Trash": "id-trash"}


async def test_removing_a_chore_forgets_its_link(hass, entry, ms_tasks):
    hass.config_entries.async_update_entry(
        entry,
        options={
            **entry.options,
            CONF_MANDATORY: {"Dishes": 20},
            CONF_CHORE_IDS: {"Dishes": "id-dishes"},
        },
    )
    result = await _open(hass, entry, "mandatory", "mandatory_remove")
    await _step(hass, result["flow_id"], {"names": ["Dishes"]})
    assert entry.options[CONF_MANDATORY] == {}
    assert entry.options[CONF_CHORE_IDS] == {}


async def test_editing_never_changes_the_shared_defaults(hass, entry, ms_tasks):
    result = await _open(hass, entry, "mandatory", "mandatory_add")
    await _step(hass, result["flow_id"], {"name": "Walk the dog", "points": 5})
    assert DEFAULT_OPTIONS[CONF_MANDATORY] == {}
    assert DEFAULT_OPTIONS[CONF_CHORE_IDS] == {}
