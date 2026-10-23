"""Tests for the per-chore breakdown in the parents' weekly summary."""

from __future__ import annotations

from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.kid_chores_points.const import (
    CONF_MANDATORY,
    CONF_NOTIFY_PARENTS,
    CONF_WEEK_BREAKDOWN,
)


async def _week(m, freezer):
    freezer.move_to("2026-03-02 10:00:00")
    await m.async_complete("Dishes")
    await m.async_complete("Trash")
    await m.async_complete("Vacuum")
    freezer.move_to("2026-03-03 10:00:00")
    await m.async_complete("Dishes")


async def test_summary_lists_each_chore_with_counts(hass, make_manager, freezer):
    parents = async_mock_service(hass, "notify", "parent_phone")
    m = await make_manager(**{CONF_NOTIFY_PARENTS: ["parent_phone"]})
    await _week(m, freezer)
    await m.async_close_week()
    msg = parents[-1].data["message"]
    assert "⚠️ Trash 1/7" in msg
    assert "⚠️ Dishes 2/7" in msg
    assert "⭐ Vacuum ×1" in msg
    assert msg.index("Trash") < msg.index("Dishes")  # worst first


async def test_breakdown_can_be_turned_off_and_skips_reverted(
    hass, make_manager, freezer
):
    parents = async_mock_service(hass, "notify", "parent_phone")
    m = await make_manager(
        **{CONF_NOTIFY_PARENTS: ["parent_phone"], CONF_WEEK_BREAKDOWN: False}
    )
    await _week(m, freezer)
    await m.async_close_week()
    assert "Dishes" not in parents[-1].data["message"]


async def test_reverted_and_old_weeks_are_not_counted(hass, make_manager, freezer):
    parents = async_mock_service(hass, "notify", "parent_phone")
    m = await make_manager(**{CONF_NOTIFY_PARENTS: ["parent_phone"]})
    freezer.move_to("2026-03-02 10:00:00")
    await m.async_complete("Dishes")
    await m.async_close_week()
    await m.async_complete("Trash")
    await m.async_undo()
    await m.async_close_week()
    msg = parents[-1].data["message"]
    assert "❌ Trash 0/7" in msg
    assert "Dishes 1/7" not in msg


async def test_chores_done_every_day_are_folded_when_many(
    hass, make_manager, freezer
):
    parents = async_mock_service(hass, "notify", "parent_phone")
    names = {f"Chore {i}": 1 for i in range(12)}
    m = await make_manager(**{CONF_NOTIFY_PARENTS: ["parent_phone"], CONF_MANDATORY: names})
    for day in range(2, 9):
        freezer.move_to(f"2026-03-{day:02d} 10:00:00")
        for name in list(names)[:6]:
            await m.async_complete(name)
    await m.async_close_week()
    msg = parents[-1].data["message"]
    assert "+4 more, all done" in msg
    assert msg.count("✅") == 2  # lines are filled up to 8 before folding


async def test_a_linked_chore_is_counted_against_the_days_it_was_due(
    hass, make_manager, freezer
):
    from homeassistant.helpers import entity_registry as er

    from custom_components.kid_chores_points.const import CONF_CHORE_IDS

    parents = async_mock_service(hass, "notify", "parent_phone")
    reg = er.async_get(hass).async_get_or_create(
        "sensor", "maintenance_supporter", "maintenance_supporter_bath_t1",
        suggested_object_id="shower_t1",
    )
    freezer.move_to("2026-03-02 10:00:00")
    m = await make_manager(
        **{
            CONF_NOTIFY_PARENTS: ["parent_phone"],
            CONF_MANDATORY: {"Dishes": 20, "Shower": 10},
            CONF_CHORE_IDS: {"Shower": "t1"},
        }
    )
    hass.states.async_set(reg.entity_id, "due_soon")
    await m.async_complete("Shower")
    hass.states.async_set(reg.entity_id, "ok")
    freezer.move_to("2026-03-04 10:00:00")
    hass.states.async_set(reg.entity_id, "overdue")  # due again, not done
    await m.async_close_week()
    msg = parents[-1].data["message"]
    assert "⚠️ Shower 1/2" in msg
    assert "❌ Dishes 0/7" in msg
