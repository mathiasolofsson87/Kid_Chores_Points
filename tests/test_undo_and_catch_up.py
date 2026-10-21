"""Tests for undoing changes and for catching up a missed week close."""

from __future__ import annotations

import pytest

from homeassistant.exceptions import ServiceValidationError

from custom_components.kid_chores_points.const import UNDO_LIMIT


# ----------------------------------------------------------------------
# Missed week close
# ----------------------------------------------------------------------
async def test_missed_week_close_is_caught_up(make_manager, freezer):
    freezer.move_to("2026-03-07 12:00:00")  # Saturday, week ends Sunday 23:59
    m = await make_manager()
    m.data["week"] = 55

    freezer.move_to("2026-03-09 08:00:00")  # Monday: Home Assistant was down on Sunday
    await m.async_catch_up()

    assert m.week == 0
    assert m.bank == 65  # 55 + goal bonus 10
    assert m.history[-1]["type"] == "week_close"


async def test_catch_up_closes_only_once(make_manager, freezer):
    freezer.move_to("2026-03-07 12:00:00")
    m = await make_manager()
    m.data["week"] = 55
    freezer.move_to("2026-03-09 08:00:00")
    await m.async_catch_up()
    m.data["week"] = 20
    await m.async_catch_up()
    assert m.week == 20  # the new week is left alone


async def test_no_catch_up_when_the_close_was_not_missed(make_manager, freezer):
    freezer.move_to("2026-03-09 08:00:00")  # a fresh tracker on Monday
    m = await make_manager()
    m.data["week"] = 55
    await m.async_catch_up()
    assert m.week == 55


async def test_no_catch_up_before_the_close_time(make_manager, freezer):
    freezer.move_to("2026-03-02 08:00:00")
    m = await make_manager()
    m.data["week"] = 55
    freezer.move_to("2026-03-08 23:58:00")  # Sunday, one minute early
    await m.async_catch_up()
    assert m.week == 55


async def test_scheduled_close_is_not_repeated_by_catch_up(make_manager, freezer):
    freezer.move_to("2026-03-02 08:00:00")
    m = await make_manager()
    m.data["week"] = 55
    freezer.move_to("2026-03-08 23:59:00")
    await m._on_week_end(freezer())
    assert m.bank == 65
    m.data["week"] = 20
    await m.async_catch_up()
    await m._on_week_end(freezer())  # a second trigger in the same minute
    assert m.week == 20


async def test_manual_close_does_not_count_as_the_scheduled_one(make_manager, freezer):
    freezer.move_to("2026-03-02 08:00:00")
    m = await make_manager()
    m.data["week"] = 55
    await m.async_close_week()  # parent closes early, on a Monday
    m.data["week"] = 30
    freezer.move_to("2026-03-08 23:59:00")
    await m._on_week_end(freezer())
    assert m.week == 0  # Sunday's regular close still runs


async def test_changing_the_week_start_does_not_close_the_week(
    hass, make_manager, freezer
):
    freezer.move_to("2026-03-04 12:00:00")  # Wednesday
    m = await make_manager()
    m.data["week"] = 40
    await m._store.async_save(m.data)
    hass.config_entries.async_update_entry(
        m.entry, options={**m.entry.options, "week_start": "wed"}
    )
    await m.async_load()  # as after the reload that follows an options change
    await m.async_catch_up()
    assert m.week == 40


# ----------------------------------------------------------------------
# Large redemptions
# ----------------------------------------------------------------------
async def test_redeem_with_huge_units_is_refused_without_side_effects(make_manager):
    m = await make_manager()
    m.data["bank"] = 25
    with pytest.raises(ServiceValidationError):
        await m.async_redeem("Cash out", units=10**9)
    assert m.bank == 25
    assert m.wallet == 0
    assert m.history == []
    assert m.data["undo"] == []


# ----------------------------------------------------------------------
# Undo
# ----------------------------------------------------------------------
async def test_undo_with_nothing_to_undo(make_manager):
    m = await make_manager()
    with pytest.raises(ServiceValidationError):
        await m.async_undo()
    assert m.undo_label is None


async def test_undo_a_mandatory_chore(make_manager):
    m = await make_manager()
    await m.async_complete("Dishes")
    assert m.undo_label == "Dishes"
    await m.async_undo()
    assert m.week == 0
    assert m.today["points"] == 0
    assert m.mandatory_remaining() == ["Dishes", "Trash"]
    assert m.history[-1]["type"] == "undo"
    assert m.history[-1]["points"] == -20
    await m.async_complete("Dishes")  # can be completed again
    assert m.week == 20


async def test_undo_a_chore_that_released_pending_bonus(make_manager):
    m = await make_manager()
    await m.async_complete("Vacuum")  # held as pending
    await m.async_complete("Dishes")
    await m.async_complete("Trash")  # releases the bonus
    assert m.week == 50 and m.week_bonus == 12
    await m.async_undo()
    assert m.week == 20 and m.week_bonus == 0
    assert m.today["pending"] == [{"name": "Vacuum", "points": 12}]
    await m.async_complete("Trash")
    assert m.week_bonus == 12


async def test_undo_a_held_bonus_chore_changes_no_points(make_manager):
    m = await make_manager()
    await m.async_complete("Vacuum")
    await m.async_undo()
    assert m.today["pending"] == []
    assert m.week == 0 and m.week_bonus == 0


async def test_undo_a_duplicate_completion_is_not_recorded(make_manager):
    m = await make_manager()
    await m.async_complete("Dishes")
    await m.async_complete("Dishes")  # ignored: counted once per day
    await m.async_undo()
    assert m.week == 0
    with pytest.raises(ServiceValidationError):
        await m.async_undo()


async def test_undo_a_redemption_refunds_and_removes_the_reward(make_manager):
    m = await make_manager()
    m.data["bank"] = 25
    await m.async_redeem("15 min Xbox")
    await m.async_redeem("15 min Xbox")
    assert len(m.reward_log) == 2
    first_uid = m.reward_log[0]["uid"]
    await m.async_undo()
    assert m.bank == 15
    assert [r["uid"] for r in m.reward_log] == [first_uid]
    assert m.history[-1]["type"] == "undo"
    assert m.history[-1]["target"] == "bank"
    assert m.history[-1]["points"] == 10


async def test_undo_keeps_other_reward_log_changes(make_manager):
    m = await make_manager()
    m.data["bank"] = 25
    await m.async_redeem("15 min Xbox")
    m.reward_log[0]["done"] = True  # a parent ticks it off in the to-do list
    await m.async_redeem("15 min Xbox")
    await m.async_undo()
    assert m.reward_log[0]["done"] is True


async def test_undo_a_cash_out_takes_the_money_back(make_manager):
    m = await make_manager()
    m.data["bank"] = 25
    await m.async_redeem("Cash out")
    assert m.wallet == 5
    await m.async_undo()
    assert m.bank == 25
    assert m.wallet == 0
    assert m.history[-1]["amount"] == -5


async def test_undo_adjustments(make_manager):
    m = await make_manager()
    m.data["bank"] = 10
    await m.async_adjust("bank", 5, "gift")
    await m.async_adjust_wallet(20, "allowance")
    await m.async_undo()
    assert m.wallet == 0 and m.bank == 15
    assert m.history[-1]["target"] == "wallet"
    assert m.history[-1]["amount"] == -20
    await m.async_undo()
    assert m.bank == 10


async def test_undo_steps_back_through_several_changes(make_manager):
    m = await make_manager()
    await m.async_complete("Dishes")
    await m.async_complete("Trash")
    await m.async_undo()
    assert m.week == 20
    await m.async_undo()
    assert m.week == 0
    assert m.undo_label is None


async def test_undo_history_is_limited(make_manager):
    m = await make_manager()
    for _ in range(UNDO_LIMIT + 5):
        await m.async_adjust("bank", 1, "x")
    assert len(m.data["undo"]) == UNDO_LIMIT


async def test_closing_the_week_clears_undo(make_manager):
    m = await make_manager()
    await m.async_complete("Dishes")
    await m.async_close_week()
    assert m.undo_label is None
    with pytest.raises(ServiceValidationError):
        await m.async_undo()


async def test_undo_survives_a_restart(hass, make_manager):
    m = await make_manager()
    await m.async_complete("Dishes")
    await m._store.async_save(m.data)
    await m.async_load()
    assert m.undo_label == "Dishes"
    await m.async_undo()
    assert m.week == 0
