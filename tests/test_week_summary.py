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
    assert "+" in msg and "all done" in msg
    assert "Chore 0 7/7" not in msg
