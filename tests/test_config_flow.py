"""Tests for the config flow."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType, InvalidData

from custom_components.kid_chores_points.const import (
    CONF_CHORE_IDS,
    CONF_LANGUAGE_KID,
    CONF_LANGUAGE_PARENTS,
    CONF_MANDATORY,
    CONF_MEDAL_RULES,
    CONF_MEDALS,
    CONF_MEDALS_GRACE,
    CONF_ADJUST_NOTIFY,
    CONF_MEDALS_NOTIFY,
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


# ----------------------------------------------------------------------
# Streaks and medals
# ----------------------------------------------------------------------
async def test_medals_are_off_until_switched_on(hass, entry):
    assert entry.options[CONF_MEDALS] is False
    result = await _open(hass, entry, "medals", "medals_settings")
    await _step(
        hass,
        result["flow_id"],
        {CONF_MEDALS: True, CONF_MEDALS_GRACE: True, CONF_MEDALS_NOTIFY: False},
    )
    assert entry.options[CONF_MEDALS] is True
    assert entry.options[CONF_MEDALS_GRACE] is True
    assert entry.options[CONF_MEDALS_NOTIFY] is False


async def test_day_streak_targets_and_bonuses_are_saved(hass, entry):
    result = await _open(hass, entry, "medals", "medals_day")
    fields = {str(k) for k in result["data_schema"].schema}
    assert fields == {
        f"day_{n}_{part}" for n in (3, 7, 14, 30) for part in ("at", "bonus")
    }
    await _step(
        hass,
        result["flow_id"],
        {
            "day_3_at": 2, "day_3_bonus": 5,
            "day_7_at": 5, "day_7_bonus": 12,
            "day_14_at": 14, "day_14_bonus": 20,
            "day_30_at": 30, "day_30_bonus": 50,
        },
    )  # fmt: skip
    rules = entry.options[CONF_MEDAL_RULES]
    assert rules["day_3"] == {"at": 2, "bonus": 5}
    assert rules["day_7"] == {"at": 5, "bonus": 12}
    assert DEFAULT_OPTIONS[CONF_MEDAL_RULES] == {}


async def test_a_bonus_above_the_cap_is_refused(hass, entry):
    result = await _open(hass, entry, "medals", "medals_day")
    with pytest.raises(InvalidData):
        await _step(
            hass,
            result["flow_id"],
            {
                "day_3_at": 3, "day_3_bonus": 51,
                "day_7_at": 7, "day_7_bonus": 10,
                "day_14_at": 14, "day_14_bonus": 20,
                "day_30_at": 30, "day_30_bonus": 40,
            },
        )  # fmt: skip
    assert entry.options[CONF_MEDAL_RULES] == {}


async def test_targets_must_grow_from_one_medal_to_the_next(hass, entry):
    result = await _open(hass, entry, "medals", "medals_week")
    result = await _step(
        hass,
        result["flow_id"],
        {
            "week_10_at": 10, "week_10_bonus": 50,
            "week_12_at": 10, "week_12_bonus": 50,
            "week_16_at": 16, "week_16_bonus": 50,
            "week_20_at": 20, "week_20_bonus": 50,
        },
    )  # fmt: skip
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "medal_order"}
    assert entry.options[CONF_MEDAL_RULES] == {}


# ----------------------------------------------------------------------
# Notification language
# ----------------------------------------------------------------------
async def test_notification_language_is_automatic_until_chosen(hass, entry):
    assert entry.options[CONF_LANGUAGE_KID] == "auto"
    result = await _open(hass, entry, "notifications")
    await _step(hass, result["flow_id"], {CONF_LANGUAGE_KID: "sv", CONF_LANGUAGE_PARENTS: "auto"})
    assert entry.options[CONF_LANGUAGE_KID] == "sv"
    assert entry.options[CONF_LANGUAGE_PARENTS] == "auto"


async def test_adjust_notifications_are_on_until_switched_off(hass, entry):
    assert entry.options[CONF_ADJUST_NOTIFY] is True
    result = await _open(hass, entry, "notifications")
    await _step(
        hass,
        result["flow_id"],
        {CONF_LANGUAGE_KID: "auto", CONF_LANGUAGE_PARENTS: "auto", CONF_ADJUST_NOTIFY: False},
    )
    assert entry.options[CONF_ADJUST_NOTIFY] is False


async def test_an_unknown_notification_language_is_refused(hass, entry):
    result = await _open(hass, entry, "notifications")
    with pytest.raises(InvalidData):
        await _step(hass, result["flow_id"], {CONF_LANGUAGE_KID: "de", CONF_LANGUAGE_PARENTS: "auto"})
