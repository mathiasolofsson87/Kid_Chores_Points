"""Mandatory chores linked to a Maintenance Supporter task that is not due today."""

from __future__ import annotations

from homeassistant.helpers import entity_registry as er

from custom_components.kid_chores_points.const import CONF_CHORE_IDS, CONF_MANDATORY, CONF_MEDALS


def _task_sensor(hass, task_id, state):
    """A Maintenance Supporter status sensor, as the registry and state machine see it."""
    reg = er.async_get(hass)
    entry = reg.async_get_or_create(
        "sensor",
        "maintenance_supporter",
        f"maintenance_supporter_bathroom_{task_id}",
        suggested_object_id=f"shower_{task_id}",
    )
    hass.states.async_set(entry.entity_id, state)
    return entry.entity_id


async def _manager(make_manager):
    return await make_manager(
        **{CONF_MANDATORY: {"Dishes": 20, "Shower": 10}, CONF_CHORE_IDS: {"Shower": "t1"}}
    )


async def test_a_linked_chore_that_is_not_due_does_not_hold_the_day_open(
    hass, make_manager
):
    _task_sensor(hass, "t1", "ok")
    m = await _manager(make_manager)
    assert m.mandatory_remaining() == ["Dishes"]
    await m.async_complete("Dishes")
    assert m.mandatory_remaining() == []


async def test_it_counts_again_when_it_is_due(hass, make_manager):
    entity_id = _task_sensor(hass, "t1", "ok")
    m = await _manager(make_manager)
    hass.states.async_set(entity_id, "due_soon")
    assert m.mandatory_remaining() == ["Dishes", "Shower"]
    hass.states.async_set(entity_id, "overdue")
    assert m.mandatory_remaining() == ["Dishes", "Shower"]


async def test_unknown_or_missing_status_counts_as_due(hass, make_manager):
    m = await _manager(make_manager)  # no Maintenance Supporter sensor at all
    assert m.mandatory_remaining() == ["Dishes", "Shower"]
    entity_id = _task_sensor(hass, "t1", "unavailable")
    assert m.mandatory_remaining() == ["Dishes", "Shower"]
    hass.states.async_set(entity_id, "unknown")
    assert m.mandatory_remaining() == ["Dishes", "Shower"]


async def test_unlinked_chores_are_always_daily(hass, make_manager):
    _task_sensor(hass, "t1", "ok")
    m = await make_manager(**{CONF_MANDATORY: {"Dishes": 20, "Shower": 10}})
    assert m.mandatory_remaining() == ["Dishes", "Shower"]


async def test_bonus_unlocks_when_the_only_open_chore_is_not_due(hass, make_manager):
    _task_sensor(hass, "t1", "ok")
    m = await _manager(make_manager)
    await m.async_complete("Vacuum")  # held back until the mandatory chores are done
    assert m.today["pending"]
    await m.async_complete("Dishes")
    assert not m.today["pending"]


async def test_a_finished_day_is_marked_when_the_integration_starts(
    hass, make_manager
):
    from custom_components.kid_chores_points.const import CONF_MEDALS

    _task_sensor(hass, "t1", "ok")
    m = await make_manager(
        **{
            CONF_MEDALS: True,
            CONF_MANDATORY: {"Dishes": 20, "Shower": 10},
            CONF_CHORE_IDS: {"Shower": "t1"},
        }
    )
    await m.async_complete("Dishes")
    m.medal_data["perfect_days"].clear()  # as if the day was never marked
    m.async_start()
    assert m.medal_data["perfect_days"]
    assert m.day_streak() == 1


async def test_no_streak_warning_when_nothing_is_open(hass, make_manager, freezer):
    from custom_components.kid_chores_points.const import CONF_MEDALS

    freezer.move_to("2026-03-02 10:00:00")
    _task_sensor(hass, "t1", "ok")
    m = await make_manager(
        **{
            CONF_MEDALS: True,
            CONF_MANDATORY: {"Dishes": 20, "Shower": 10},
            CONF_CHORE_IDS: {"Shower": "t1"},
        }
    )
    await m.async_complete("Dishes")
    freezer.move_to("2026-03-03 10:00:00")
    assert m.streak_at_risk()  # Dishes is open again
    await m.async_complete("Dishes")
    m.medal_data["perfect_days"].remove("2026-03-03")
    assert not m.streak_at_risk()  # nothing left to do


async def test_a_task_turning_overdue_takes_back_yesterdays_perfect_day(
    hass, make_manager
):
    from datetime import timedelta

    from homeassistant.util import dt as dt_util

    entity_id = _task_sensor(hass, "t1", "ok")
    m = await make_manager(
        **{
            CONF_MANDATORY: {"Dishes": 20, "Shower": 10},
            CONF_CHORE_IDS: {"Shower": "t1"},
            CONF_MEDALS: True,
        }
    )
    yesterday = (dt_util.now().date() - timedelta(days=1)).isoformat()
    m.medal_data["perfect_days"].append(yesterday)
    hass.states.async_set(entity_id, "overdue")
    m._check_day_done()
    assert yesterday not in m.medal_data["perfect_days"]


async def test_a_forgiven_day_is_logged_in_the_history(hass, make_manager):
    from datetime import timedelta

    from homeassistant.util import dt as dt_util

    from custom_components.kid_chores_points.const import CONF_MEDALS_GRACE

    m = await make_manager(**{CONF_MEDALS: True, CONF_MEDALS_GRACE: True})
    today = dt_util.now().date()
    m.medal_data["perfect_days"] = [(today - timedelta(days=d)).isoformat() for d in (2, 3)]
    m._note_grace_used()
    m._note_grace_used()  # only once
    entries = [e for e in m.history if e["type"] == "grace"]
    assert [e["label"] for e in entries] == [(today - timedelta(days=1)).isoformat()]


async def test_a_day_marked_perfect_before_a_task_showed_as_due_is_unmarked(
    hass, make_manager
):
    from homeassistant.util import dt as dt_util

    entity_id = _task_sensor(hass, "t1", "ok")
    m = await make_manager(
        **{
            CONF_MANDATORY: {"Shower": 10},
            CONF_CHORE_IDS: {"Shower": "t1"},
            CONF_MEDALS: True,
        }
    )
    today = dt_util.now().date().isoformat()
    m._check_day_done()  # just after midnight: nothing looks due yet
    assert today in m.medal_data["perfect_days"]
    hass.states.async_set(entity_id, "due_soon")
    m._check_day_done()
    assert today not in m.medal_data["perfect_days"]


async def test_the_day_end_check_has_the_final_word(hass, make_manager):
    from homeassistant.util import dt as dt_util

    entity_id = _task_sensor(hass, "t1", "ok")
    m = await make_manager(
        **{
            CONF_MANDATORY: {"Shower": 10},
            CONF_CHORE_IDS: {"Shower": "t1"},
            CONF_MEDALS: True,
        }
    )
    today = dt_util.now().date().isoformat()
    m._on_day_end(None)
    assert today in m.medal_data["perfect_days"]
    hass.states.async_set(entity_id, "overdue")
    m._on_day_end(None)
    assert today not in m.medal_data["perfect_days"]
