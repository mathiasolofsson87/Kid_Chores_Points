"""Tests for undoing changes and for catching up a missed week close."""

from __future__ import annotations

import pytest

from homeassistant.exceptions import ServiceValidationError


def _seed(m, **totals):
    """Put the tracker in a state the way earlier (unrecorded) changes would have."""
    m.data.update(totals)
    m._prev = m._totals()


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
    _seed(m, bank=25)
    with pytest.raises(ServiceValidationError):
        await m.async_redeem("Cash out", units=10**9)
    assert m.bank == 25
    assert m.wallet == 0
    assert m.history == []


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
    _seed(m, bank=25)
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
    _seed(m, bank=25)
    await m.async_redeem("15 min Xbox")
    m.reward_log[0]["done"] = True  # a parent ticks it off in the to-do list
    await m.async_redeem("15 min Xbox")
    await m.async_undo()
    assert m.reward_log[0]["done"] is True


async def test_undo_a_cash_out_takes_the_money_back(make_manager):
    m = await make_manager()
    _seed(m, bank=25)
    await m.async_redeem("Cash out")
    assert m.wallet == 5
    await m.async_undo()
    assert m.bank == 25
    assert m.wallet == 0
    assert m.history[-1]["amount"] == -5


async def test_undo_adjustments(make_manager):
    m = await make_manager()
    _seed(m, bank=10)
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


async def test_closing_the_week_keeps_banking_changes_revertable(make_manager):
    m = await make_manager()
    await m.async_complete("Dishes")
    await m.async_adjust("bank", 5, "gift")
    await m.async_close_week()
    assert m.undo_label == "gift"  # the chore belongs to a closed week
    await m.async_undo()
    assert m.bank == 20  # the closed week's 20 stay
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


# ----------------------------------------------------------------------
# Reverting any entry of the history
# ----------------------------------------------------------------------
def _entry(m, label):
    return next(e for e in m.history if e["label"] == label and e["id"] == e["group"])


async def test_revert_an_older_chore_leaves_the_later_ones(make_manager):
    m = await make_manager()
    await m.async_complete("Dishes")
    await m.async_complete("Trash")
    await m.async_revert(_entry(m, "Dishes")["id"])
    assert m.week == 30
    assert m.mandatory_remaining() == ["Dishes"]
    assert m.today["points"] == 30
    assert _entry(m, "Dishes")["reverted"] is True
    assert not m.can_revert(_entry(m, "Dishes"))
    await m.async_complete("Dishes")  # can be done again
    assert m.week == 50


async def test_revert_an_older_redemption(make_manager):
    m = await make_manager()
    _seed(m, bank=30)
    await m.async_redeem("15 min Xbox")
    await m.async_redeem("Cash out")
    first = _entry(m, "15 min Xbox")
    await m.async_revert(first["id"])
    assert m.bank == 20 and m.wallet == 5
    assert m.reward_log == []


async def test_revert_cannot_be_repeated(make_manager):
    m = await make_manager()
    await m.async_adjust("bank", 5, "gift")
    entry_id = _entry(m, "gift")["id"]
    await m.async_revert(entry_id)
    with pytest.raises(ServiceValidationError):
        await m.async_revert(entry_id)
    with pytest.raises(ServiceValidationError):
        await m.async_revert("nope")


async def test_revert_a_chore_from_a_closed_week_is_refused(make_manager):
    m = await make_manager()
    await m.async_complete("Dishes")
    entry = _entry(m, "Dishes")
    assert m.can_revert(entry)
    await m.async_close_week()
    assert not m.can_revert(entry)
    with pytest.raises(ServiceValidationError):
        await m.async_revert(entry["id"])


async def test_revert_only_primary_entries_and_not_undo_entries(make_manager):
    m = await make_manager()
    await m.async_complete("Vacuum")
    await m.async_complete("Dishes")
    await m.async_complete("Trash")
    released = next(e for e in m.history if e["type"] == "bonus_released")
    assert not m.can_revert(released)
    await m.async_undo()
    assert not m.can_revert(m.history[-1])  # the undo entry itself


async def test_revert_the_chore_that_released_a_bonus_takes_the_bonus_back(make_manager):
    m = await make_manager()
    await m.async_complete("Vacuum")
    await m.async_complete("Dishes")
    await m.async_complete("Trash")
    await m.async_revert(_entry(m, "Dishes")["id"])  # not the latest
    assert m.week == 30 and m.week_bonus == 12
    await m.async_revert(_entry(m, "Trash")["id"])
    assert m.week == 0 and m.week_bonus == 0
    assert m.today["pending"] == [{"name": "Vacuum", "points": 12}]


async def test_revert_never_goes_below_zero(make_manager):
    m = await make_manager()
    await m.async_adjust_wallet(20, "allowance")
    m.data["wallet"] = 5  # most of it was spent
    await m.async_revert(_entry(m, "allowance")["id"])
    assert m.wallet == 0


async def test_old_history_entries_without_an_id_cannot_be_reverted(make_manager):
    m = await make_manager()
    m.history.append({"t": "x", "type": "chore", "label": "Old", "points": 5})
    assert not m.can_revert(m.history[-1])
