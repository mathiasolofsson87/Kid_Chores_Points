"""Tests for the bedtime reminder."""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.kid_chores_points.const import (
    CONF_BEDTIME,
    CONF_BEDTIME_LEAD,
    CONF_BEDTIME_WEEKEND,
    CONF_NOTIFY_KID,
    DEFAULT_OPTIONS,
    DOMAIN,
)

from homeassistant.data_entry_flow import FlowResultType

WEDNESDAY = "2026-03-04"
FRIDAY = "2026-03-06"


@pytest.fixture
def sent(hass):
    """Notifications sent to the child's phone."""
    return async_mock_service(hass, "notify", "kid_phone")


async def _manager(make_manager, **options):
    return await make_manager(
        **{CONF_BEDTIME: "20:30", CONF_BEDTIME_LEAD: 45, CONF_NOTIFY_KID: ["kid_phone"], **options}
    )


async def test_reminder_lists_the_open_chores(make_manager, sent, freezer):
    freezer.move_to(f"{WEDNESDAY} 19:45:00")  # 45 minutes before 20:30
    m = await _manager(make_manager)
    await m.async_complete("Dishes")
    await m._on_minute(freezer())
    assert len(sent) == 1
    assert sent[0].data["title"] == "Almost bedtime 🌙"
    assert sent[0].data["message"] == "Just one left: Trash (+30 p)"
    assert "Dishes" not in sent[0].data["message"]


async def test_reminder_with_several_chores_left_lists_them(make_manager, sent, freezer):
    freezer.move_to(f"{WEDNESDAY} 19:45:00")
    m = await _manager(make_manager)
    await m._on_minute(freezer())
    assert sent[0].data["message"] == "2 chores left today:\n• Dishes (+20 p)\n• Trash (+30 p)"


async def test_reminder_is_in_the_home_assistant_language(hass, make_manager, sent, freezer):
    hass.config.language = "sv"
    freezer.move_to(f"{WEDNESDAY} 19:45:00")
    m = await _manager(make_manager)
    await m.async_complete("Dishes")
    sent.clear()
    await m._on_minute(freezer())
    assert sent[0].data["title"] == "Snart läggdags 🌙"
    assert sent[0].data["message"] == "Bara en kvar: Trash (+30 p)"


async def test_no_reminder_at_other_times(make_manager, sent, freezer):
    m = await _manager(make_manager)
    for at in ("19:44:00", "19:46:00", "20:30:00"):
        freezer.move_to(f"{WEDNESDAY} {at}")
        await m._on_minute(freezer())
    assert sent == []


async def test_no_reminder_when_all_chores_are_done(make_manager, sent, freezer):
    freezer.move_to(f"{WEDNESDAY} 19:45:00")
    m = await _manager(make_manager)
    await m.async_complete("Dishes")
    await m.async_complete("Trash")
    sent.clear()  # finishing the chores sends its own notification
    await m._on_minute(freezer())
    assert sent == []


async def test_reminder_is_sent_once_per_day(make_manager, sent, freezer):
    freezer.move_to(f"{WEDNESDAY} 19:45:00")
    m = await _manager(make_manager)
    await m._on_minute(freezer())
    await m._on_minute(freezer())
    assert len(sent) == 1
    freezer.move_to("2026-03-05 19:45:00")  # the next day
    await m._on_minute(freezer())
    assert len(sent) == 2


async def test_a_reminder_does_not_repeat_after_a_restart(make_manager, sent, freezer):
    freezer.move_to(f"{WEDNESDAY} 19:45:00")
    m = await _manager(make_manager)
    await m._on_minute(freezer())
    await m._store.async_save(m.data)
    await m.async_load()
    await m._on_minute(freezer())
    assert len(sent) == 1


async def test_weekend_bedtime_is_used_on_friday_and_saturday(make_manager, sent, freezer):
    m = await _manager(make_manager, **{CONF_BEDTIME_WEEKEND: "21:30"})
    freezer.move_to(f"{FRIDAY} 19:45:00")  # the school-night time, but it is Friday
    await m._on_minute(freezer())
    assert sent == []
    freezer.move_to(f"{FRIDAY} 20:45:00")
    await m._on_minute(freezer())
    assert len(sent) == 1


async def test_weekend_bedtime_alone_leaves_weekdays_without_reminder(
    make_manager, sent, freezer
):
    m = await make_manager(
        **{CONF_BEDTIME_WEEKEND: "21:30", CONF_NOTIFY_KID: ["kid_phone"]}
    )
    freezer.move_to(f"{WEDNESDAY} 20:45:00")
    await m._on_minute(freezer())
    assert sent == []
    assert m.bedtime_reminder_time(date(2026, 3, 4)) is None


async def test_no_bedtime_means_no_reminder(make_manager, sent, freezer):
    m = await make_manager(**{CONF_NOTIFY_KID: ["kid_phone"]})
    freezer.move_to(f"{WEDNESDAY} 19:45:00")
    await m._on_minute(freezer())
    assert sent == []


async def test_reminder_follows_the_lead_time(make_manager, sent, freezer):
    m = await _manager(make_manager, **{CONF_BEDTIME_LEAD: 15})
    freezer.move_to(f"{WEDNESDAY} 19:45:00")  # the 45-minute time: too early now
    await m._on_minute(freezer())
    assert sent == []
    freezer.move_to(f"{WEDNESDAY} 20:15:00")
    await m._on_minute(freezer())
    assert len(sent) == 1


# ----------------------------------------------------------------------
# Options flow
# ----------------------------------------------------------------------
@pytest.fixture
def no_setup(hass):
    """Only the flow is under test; skip loading the integration itself."""
    hass.config.components.update({"frontend", "http"})
    with (
        patch("custom_components.kid_chores_points.async_setup", return_value=True),
        patch("custom_components.kid_chores_points.async_setup_entry", return_value=True),
    ):
        yield


@pytest.fixture
def entry(hass, no_setup):
    entry = MockConfigEntry(domain=DOMAIN, title="Anna", options=DEFAULT_OPTIONS)
    entry.add_to_hass(hass)
    return entry


async def _open_bedtime(hass, entry):
    result = await hass.config_entries.options.async_init(entry.entry_id)
    return await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "bedtime"}
    )


async def test_bedtime_is_saved_as_hours_and_minutes(hass, entry):
    result = await _open_bedtime(hass, entry)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_BEDTIME: "20:30:00", CONF_BEDTIME_WEEKEND: "21:30:00", CONF_BEDTIME_LEAD: 30},
    )
    assert result["type"] is FlowResultType.MENU
    assert entry.options[CONF_BEDTIME] == "20:30"
    assert entry.options[CONF_BEDTIME_WEEKEND] == "21:30"
    assert entry.options[CONF_BEDTIME_LEAD] == 30


async def test_clearing_the_bedtime_turns_the_reminder_off(hass, entry):
    hass.config_entries.async_update_entry(
        entry, options={**entry.options, CONF_BEDTIME: "20:30", CONF_BEDTIME_WEEKEND: "21:00"}
    )
    result = await _open_bedtime(hass, entry)
    await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_BEDTIME_LEAD: 45}  # both times left out
    )
    assert entry.options[CONF_BEDTIME] == ""
    assert entry.options[CONF_BEDTIME_WEEKEND] == ""


async def test_a_lead_time_reaching_before_midnight_is_refused(hass, entry):
    result = await _open_bedtime(hass, entry)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_BEDTIME: "00:30:00", CONF_BEDTIME_LEAD: 45}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_BEDTIME_LEAD: "lead_too_long"}
    assert entry.options[CONF_BEDTIME] == ""


async def test_the_reminder_fires_from_the_clock_when_set_up(hass, sent, freezer):
    """The whole wiring: a configured bedtime registers the minute check."""
    from pytest_homeassistant_custom_component.common import async_fire_time_changed

    from custom_components.kid_chores_points.const import CONF_MANDATORY

    await hass.config.async_set_time_zone("UTC")
    freezer.move_to(f"{WEDNESDAY} 19:44:30")
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Anna",
        options={
            **DEFAULT_OPTIONS,
            CONF_MANDATORY: {"Dishes": 20},
            CONF_BEDTIME: "20:30",
            CONF_NOTIFY_KID: ["kid_phone"],
        },
    )
    entry.add_to_hass(hass)
    hass.config.components.update({"frontend", "http"})
    with (
        patch("custom_components.kid_chores_points.add_extra_js_url"),
        patch.object(hass, "http", create=True) as http,
    ):
        http.async_register_static_paths = _noop
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    freezer.move_to(f"{WEDNESDAY} 19:45:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert len(sent) == 1
    assert "Dishes" in sent[0].data["message"]


async def _noop(*_args, **_kwargs):
    return None
