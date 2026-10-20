"""Tests for the points engine (ChoresManager)."""

from __future__ import annotations

import pytest

from homeassistant.exceptions import ServiceValidationError

from custom_components.kid_chores_points.const import (
    CONF_BONUS,
    CONF_GOAL,
    CONF_GOAL_BONUS,
    CONF_MANDATORY,
    CONF_POLICY,
    HISTORY_LIMIT,
    POLICY_FORFEIT,
    POLICY_HALF,
)


# ----------------------------------------------------------------------
# Completing chores
# ----------------------------------------------------------------------
async def test_mandatory_chore_awards_points(make_manager):
    m = await make_manager()
    await m.async_complete("Dishes")
    assert m.week == 20
    assert m.today["points"] == 20
    assert m.mandatory_remaining() == ["Trash"]


async def test_mandatory_chore_counts_once_per_day(make_manager):
    m = await make_manager()
    await m.async_complete("Dishes")
    await m.async_complete("Dishes")
    assert m.week == 20
    assert len([h for h in m.history if h["type"] == "chore"]) == 1


async def test_mandatory_chore_counts_again_next_day(make_manager, freezer):
    m = await make_manager()
    freezer.move_to("2026-03-02 10:00:00")
    await m.async_complete("Dishes")
    freezer.move_to("2026-03-03 10:00:00")
    await m.async_complete("Dishes")
    assert m.week == 40


async def test_unknown_chore_raises_for_service_but_not_for_events(make_manager):
    m = await make_manager()
    with pytest.raises(ServiceValidationError):
        await m.async_complete("Nope")
    await m.async_complete("Nope", raise_unknown=False)
    assert m.week == 0


# ----------------------------------------------------------------------
# Bonus chores
# ----------------------------------------------------------------------
async def test_bonus_is_held_pending_until_mandatory_done(make_manager):
    m = await make_manager()
    await m.async_complete("Vacuum")
    assert m.week_bonus == 0
    assert m.today["pending"] == [{"name": "Vacuum", "points": 12}]

    await m.async_complete("Dishes")
    assert m.week_bonus == 0  # still one mandatory chore open
    await m.async_complete("Trash")

    assert m.week == 50
    assert m.week_bonus == 12
    assert m.today["pending"] == []
    assert m.today["points"] == 20 + 30 + 12


async def test_bonus_pays_immediately_when_mandatory_done(make_manager):
    m = await make_manager()
    await m.async_complete("Dishes")
    await m.async_complete("Trash")
    await m.async_complete("Vacuum")
    assert m.week_bonus == 12
    assert m.week == 50  # bonus never counts towards the weekly goal


async def test_bonus_pays_every_time(make_manager):
    m = await make_manager()
    await m.async_complete("Dishes")
    await m.async_complete("Trash")
    await m.async_complete("Vacuum")
    await m.async_complete("Vacuum")
    assert m.week_bonus == 24


async def test_pending_bonus_is_dropped_at_midnight(make_manager, freezer):
    m = await make_manager()
    freezer.move_to("2026-03-02 10:00:00")
    await m.async_complete("Vacuum")
    freezer.move_to("2026-03-03 00:00:01")
    assert m.today["pending"] == []
    await m.async_complete("Dishes")
    await m.async_complete("Trash")
    assert m.week_bonus == 0


# ----------------------------------------------------------------------
# Closing the week
# ----------------------------------------------------------------------
async def test_close_week_goal_met_banks_everything(make_manager):
    m = await make_manager()
    m.data["week"], m.data["week_bonus"] = 55, 12
    await m.async_close_week()
    # 55 + goal bonus 10 + bonus 12
    assert m.bank == 77
    assert m.week == 0
    assert m.week_bonus == 0


async def test_close_week_goal_exactly_met(make_manager):
    m = await make_manager()
    m.data["week"], m.data["week_bonus"] = 50, 12
    await m.async_close_week()
    assert m.bank == 72


@pytest.mark.parametrize(
    ("policy", "expected"),
    [("bank_anyway", 40), (POLICY_HALF, 20), (POLICY_FORFEIT, 0)],
)
async def test_close_week_goal_missed_policies(make_manager, policy, expected):
    m = await make_manager(**{CONF_POLICY: policy})
    m.data["week"], m.data["week_bonus"] = 40, 12
    await m.async_close_week()
    assert m.bank == expected
    assert m.week_bonus == 0  # the bonus points are lost


async def test_close_week_half_rounds_down(make_manager):
    m = await make_manager(**{CONF_POLICY: POLICY_HALF})
    m.data["week"] = 41
    await m.async_close_week()
    assert m.bank == 20


async def test_close_week_without_goal_bonus(make_manager):
    m = await make_manager(**{CONF_GOAL_BONUS: 0})
    m.data["week"] = 50
    await m.async_close_week()
    assert m.bank == 50


async def test_close_week_adds_to_existing_bank(make_manager):
    m = await make_manager()
    m.data["bank"], m.data["week"] = 100, 50
    await m.async_close_week()
    assert m.bank == 160


async def test_close_week_writes_history_and_last_week(make_manager):
    m = await make_manager()
    m.data["week"] = 55
    await m.async_close_week()
    entry = m.history[-1]
    assert entry["type"] == "week_close"
    assert entry["points"] == 65
    assert "55" in m.last_week and "50" in m.last_week


async def test_week_end_only_closes_on_the_day_before_week_start(
    make_manager, freezer
):
    m = await make_manager()  # week starts on Monday
    m.data["week"] = 50

    freezer.move_to("2026-03-04 23:59:00")  # a Wednesday
    await m._on_week_end(freezer())
    assert m.week == 50

    freezer.move_to("2026-03-08 23:59:00")  # the Sunday
    await m._on_week_end(freezer())
    assert m.week == 0
    assert m.bank == 60


# ----------------------------------------------------------------------
# Rewards and the wallet
# ----------------------------------------------------------------------
async def test_redeem_deducts_bank_and_adds_to_reward_log(make_manager):
    m = await make_manager()
    m.data["bank"] = 25
    await m.async_redeem("15 min Xbox")
    assert m.bank == 15
    assert m.wallet == 0
    assert len(m.reward_log) == 1
    assert m.reward_log[0]["summary"] == "15 min Xbox"
    assert m.reward_log[0]["done"] is False


async def test_redeem_multiple_units(make_manager):
    m = await make_manager()
    m.data["bank"] = 50
    await m.async_redeem("15 min Xbox", units=3)
    assert m.bank == 20
    assert m.reward_log[0]["summary"] == "3 × 15 min Xbox"


async def test_redeem_cash_out_pays_the_wallet(make_manager):
    m = await make_manager()
    m.data["bank"] = 30
    await m.async_redeem("Cash out", units=2)
    assert m.bank == 10
    assert m.wallet == 10
    assert m.reward_log == []  # nothing to hand out
    assert m.history[-1]["amount"] == 10


async def test_redeem_without_enough_points_is_refused(make_manager):
    m = await make_manager()
    m.data["bank"] = 9
    with pytest.raises(ServiceValidationError):
        await m.async_redeem("15 min Xbox")
    assert m.bank == 9
    assert m.reward_log == []
    assert m.history == []


async def test_redeem_more_units_than_the_bank_covers_is_refused(make_manager):
    m = await make_manager()
    m.data["bank"] = 25
    with pytest.raises(ServiceValidationError):
        await m.async_redeem("15 min Xbox", units=3)
    assert m.bank == 25


async def test_redeem_unknown_reward(make_manager):
    m = await make_manager()
    m.data["bank"] = 100
    with pytest.raises(ServiceValidationError):
        await m.async_redeem("Pony")
    assert m.bank == 100


async def test_adjust_wallet_never_goes_below_zero(make_manager):
    m = await make_manager()
    await m.async_adjust_wallet(15, "gift")
    assert m.wallet == 15
    await m.async_adjust_wallet(-40, "payout")
    assert m.wallet == 0
    assert m.history[-1]["amount"] == -15  # the real change, not the request


# ----------------------------------------------------------------------
# Manual adjustments
# ----------------------------------------------------------------------
async def test_adjust_bank_and_week(make_manager):
    m = await make_manager()
    await m.async_adjust("bank", 20, "birthday")
    await m.async_adjust("week", 5, None)
    assert m.bank == 20
    assert m.week == 5


async def test_adjust_never_goes_below_zero(make_manager):
    m = await make_manager()
    await m.async_adjust("bank", 10, None)
    await m.async_adjust("bank", -50, None)
    assert m.bank == 0
    assert m.history[-1]["points"] == -10  # the real change


# ----------------------------------------------------------------------
# History
# ----------------------------------------------------------------------
async def test_history_is_capped(make_manager):
    m = await make_manager()
    for _ in range(HISTORY_LIMIT + 25):
        await m.async_adjust("bank", 1, "x")
    assert len(m.history) == HISTORY_LIMIT
    assert m.bank == HISTORY_LIMIT + 25


async def test_history_snapshots_balances(make_manager):
    m = await make_manager()
    await m.async_complete("Dishes")
    entry = m.history[-1]
    assert entry["type"] == "chore"
    assert entry["label"] == "Dishes"
    assert entry["points"] == 20
    assert entry["week"] == 20
