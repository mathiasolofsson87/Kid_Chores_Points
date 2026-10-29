"""Tests for streaks and medals."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.util import dt as dt_util

import pytest
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.kid_chores_points.const import (
    CONF_BEDTIME,
    CONF_BONUS,
    CONF_BEDTIME_LEAD,
    CONF_MEDAL_RULES,
    CONF_MEDALS,
    CONF_MEDALS_GRACE,
    CONF_MEDALS_NOTIFY,
    CONF_NOTIFY_KID,
    CONF_NOTIFY_PARENTS,
    CONF_REWARDS,
)
from custom_components.kid_chores_points.manager import ChoresManager

MON, TUE, WED, THU, FRI = (f"2026-03-0{d} 10:00:00" for d in (2, 3, 4, 5, 6))


@pytest.fixture
def kid(hass):
    return async_mock_service(hass, "notify", "kid_phone")


@pytest.fixture
def parents(hass):
    return async_mock_service(hass, "notify", "parent_phone")


async def _on(make_manager, **options) -> ChoresManager:
    return await make_manager(**{CONF_MEDALS: True, **options})


async def _perfect_day(m, freezer, when) -> None:
    """Do every mandatory chore on the day of `when`."""
    freezer.move_to(when)
    for chore in m.mandatory:
        await m.async_complete(chore)


def _entries(m, kind):
    return [e for e in m.history if e["type"] == kind]


# ----------------------------------------------------------------------
# Off by default
# ----------------------------------------------------------------------
async def test_nothing_is_counted_while_switched_off(make_manager, freezer):
    m = await make_manager()
    await _perfect_day(m, freezer, MON)
    assert m.day_streak() == 0
    assert m.medal_data["chores_done"] == 0
    assert m.medal_data["perfect_days"] == []
    assert m.medal_data["earned"] == {}


# ----------------------------------------------------------------------
# Day streaks
# ----------------------------------------------------------------------
async def test_perfect_days_make_a_streak_and_earn_the_medal(make_manager, freezer):
    m = await _on(make_manager)
    await _perfect_day(m, freezer, MON)
    await _perfect_day(m, freezer, TUE)
    assert m.day_streak() == 2
    assert "day_3" not in m.medal_data["earned"]

    await _perfect_day(m, freezer, WED)
    assert m.day_streak() == 3
    assert m.medal_data["earned"]["day_3"] == {"date": "2026-03-04"}
    assert m.bank == 5  # the bonus goes straight to the bank
    medal = _entries(m, "medal")[0]
    assert (medal["label"], medal["points"], medal["target"]) == ("Little Sprout", 5, "bank")
    assert medal["medal"] == "day_3"
    assert m.medal_data["best_day"] == 3


async def test_a_day_with_chores_left_is_not_perfect(make_manager, freezer):
    m = await _on(make_manager)
    freezer.move_to(MON)
    await m.async_complete("Dishes")  # Trash is still open
    assert m.day_streak() == 0
    assert m.medal_data["perfect_days"] == []


async def test_todays_unfinished_chores_do_not_break_the_streak(make_manager, freezer):
    m = await _on(make_manager)
    await _perfect_day(m, freezer, MON)
    await _perfect_day(m, freezer, TUE)
    freezer.move_to(WED)
    assert m.day_streak() == 2
    assert m.streak_at_risk()

    freezer.move_to(THU)  # Wednesday passed without finishing
    assert m.day_streak() == 0
    assert not m.streak_at_risk()
    assert m.medal_data["best_day"] == 2


async def test_grace_forgives_one_missed_day_per_week(make_manager, freezer):
    m = await _on(make_manager, **{CONF_MEDALS_GRACE: True})
    await _perfect_day(m, freezer, MON)
    await _perfect_day(m, freezer, TUE)
    await _perfect_day(m, freezer, THU)  # Wednesday missed
    assert m.day_streak() == 3  # the missed day is bridged, not counted


async def test_without_grace_a_missed_day_breaks_the_streak(make_manager, freezer):
    m = await _on(make_manager)
    await _perfect_day(m, freezer, MON)
    await _perfect_day(m, freezer, TUE)
    await _perfect_day(m, freezer, THU)
    assert m.day_streak() == 1


async def test_grace_covers_only_one_day_in_a_week(make_manager, freezer):
    m = await _on(make_manager, **{CONF_MEDALS_GRACE: True})
    await _perfect_day(m, freezer, MON)
    await _perfect_day(m, freezer, THU)  # Tuesday and Wednesday missed
    assert m.day_streak() == 1


async def test_a_medal_is_only_paid_once(make_manager, freezer):
    m = await _on(make_manager)
    for day in (MON, TUE, WED, THU):
        await _perfect_day(m, freezer, day)
    assert m.day_streak() == 4
    assert len(_entries(m, "medal")) == 1
    assert m.bank == 5


async def test_a_medal_is_not_paid_again_when_the_streak_restarts(make_manager, freezer):
    m = await _on(make_manager)
    for day in (MON, TUE, WED):
        await _perfect_day(m, freezer, day)
    assert m.bank == 5 and "day_3" in m.medal_data["earned"]

    # Thursday is missed, then the streak starts over and reaches 3 days again
    for day in ("2026-03-06 10:00:00", "2026-03-07 10:00:00", "2026-03-08 10:00:00"):
        await _perfect_day(m, freezer, day)
    assert m.day_streak() == 3
    assert len(_entries(m, "medal")) == 1
    assert m.bank == 5  # the 3-day medal paid once, not twice
    assert m.medal_data["best_day"] == 3


async def test_undo_takes_back_the_medal_its_bonus_and_the_day(make_manager, freezer):
    m = await _on(make_manager)
    await _perfect_day(m, freezer, MON)
    await _perfect_day(m, freezer, TUE)
    await _perfect_day(m, freezer, WED)
    assert m.bank == 5 and "day_3" in m.medal_data["earned"]

    await m.async_undo()  # the Trash that made the third perfect day
    assert m.bank == 0
    assert m.medal_data["earned"] == {}
    assert m.day_streak() == 2
    assert m.medal_data["chores_done"] == 5
    assert all(e["reverted"] for e in _entries(m, "medal"))

    await m.async_complete("Trash")  # doing it again earns the medal again
    assert "day_3" in m.medal_data["earned"]
    assert m.bank == 5


async def test_reverting_an_earlier_chore_makes_that_day_imperfect(make_manager, freezer):
    m = await _on(make_manager)
    await _perfect_day(m, freezer, MON)
    dishes = next(e for e in m.history if e["label"] == "Dishes")
    await m.async_revert(dishes["id"])
    assert m.medal_data["perfect_days"] == []
    assert m.day_streak() == 0


# ----------------------------------------------------------------------
# Counters: chores and bonus chores
# ----------------------------------------------------------------------
async def test_chores_and_bonus_chores_are_counted(make_manager, freezer):
    m = await _on(make_manager)
    freezer.move_to(MON)
    await m.async_complete("Vacuum")  # held until the mandatory chores are done
    assert (m.medal_data["chores_done"], m.medal_data["bonus_done"]) == (0, 0)
    await m.async_complete("Dishes")
    await m.async_complete("Trash")  # releases the bonus chore
    assert (m.medal_data["chores_done"], m.medal_data["bonus_done"]) == (3, 1)
    await m.async_complete("Vacuum")  # paid right away now
    assert (m.medal_data["chores_done"], m.medal_data["bonus_done"]) == (4, 2)


async def test_a_chore_count_medal_is_earned_at_its_target(make_manager, freezer):
    m = await _on(make_manager, **{CONF_MEDAL_RULES: {"chores_25": {"at": 2, "bonus": 7}}})
    await _perfect_day(m, freezer, MON)
    assert m.medal_data["earned"]["chores_25"] == {"date": "2026-03-02"}
    assert m.bank == 7


# ----------------------------------------------------------------------
# Week streaks
# ----------------------------------------------------------------------
async def test_week_streak_counts_weeks_and_resets_on_a_miss(make_manager, freezer):
    m = await _on(make_manager, **{CONF_MEDAL_RULES: {"week_10": {"at": 2, "bonus": 50}}})
    await _perfect_day(m, freezer, MON)  # 50 of 50
    await m.async_close_week()
    assert m.medal_data["week_streak"] == 1
    assert "week_10" not in m.medal_data["earned"]

    await _perfect_day(m, freezer, TUE)
    bank = m.bank
    await m.async_close_week()
    assert m.medal_data["week_streak"] == 2
    assert m.medal_data["earned"]["week_10"] == {"date": "2026-03-03"}
    assert m.bank == bank + 50 + 10 + 50  # points, goal bonus and the medal

    await m.async_close_week()  # nothing done this week
    assert m.medal_data["week_streak"] == 0
    assert m.medal_data["best_week"] == 2


async def test_a_week_medal_cannot_be_reverted_with_the_week(make_manager, freezer):
    m = await _on(make_manager, **{CONF_MEDAL_RULES: {"week_10": {"at": 1, "bonus": 50}}})
    await _perfect_day(m, freezer, MON)
    await m.async_close_week()
    assert not any(m.can_revert(e) for e in _entries(m, "medal"))


# ----------------------------------------------------------------------
# Rewards and the wallet
# ----------------------------------------------------------------------
async def test_first_treat_is_earned_by_a_reward_that_is_handed_out(make_manager):
    m = await _on(make_manager)
    await m.async_adjust("bank", 100, "start")
    await m.async_redeem("Cash out")  # money into the wallet, not a treat
    assert m.medal_data["treats"] == 0
    assert "first_treat" not in m.medal_data["earned"]

    await m.async_redeem("15 min Xbox")
    assert m.medal_data["treats"] == 1
    assert "first_treat" in m.medal_data["earned"]
    assert m.bank == 100 - 10 - 10  # First Treat pays no bonus points


async def test_undoing_the_reward_takes_first_treat_back(make_manager):
    m = await _on(make_manager)
    await m.async_adjust("bank", 100, "start")
    await m.async_redeem("15 min Xbox")
    await m.async_undo()
    assert m.medal_data["treats"] == 0
    assert "first_treat" not in m.medal_data["earned"]
    assert m.bank == 100


async def test_medals_that_do_not_apply_are_marked_unavailable(make_manager):
    m = await _on(make_manager, **{CONF_REWARDS: {"Cash out": 10}})  # only a cash-out reward
    by_id = {x["id"]: x for x in m.medal_list()}
    assert by_id["first_treat"]["available"] is False
    assert by_id["day_3"]["available"] is True
    assert by_id["bonus_10"]["available"] is True  # the fixture has a bonus chore

    m = await _on(make_manager, **{CONF_BONUS: {}})
    assert {x["id"]: x for x in m.medal_list()}["bonus_10"]["available"] is False


# ----------------------------------------------------------------------
# Rules, progress and the medal list
# ----------------------------------------------------------------------
async def test_the_parents_targets_and_bonuses_replace_the_defaults(make_manager):
    m = await _on(make_manager, **{CONF_MEDAL_RULES: {"day_7": {"at": 5, "bonus": 99}}})
    day_7 = next(x for x in m.medal_list() if x["id"] == "day_7")
    assert (day_7["at"], day_7["bonus"]) == (5, 50)  # the bonus is capped at 50
    assert next(x for x in m.medal_list() if x["id"] == "day_3")["at"] == 3


async def test_medal_list_shows_progress_and_the_next_medal(make_manager, freezer):
    m = await _on(make_manager)
    await _perfect_day(m, freezer, MON)
    await _perfect_day(m, freezer, TUE)
    day_3 = next(x for x in m.medal_list() if x["id"] == "day_3")
    assert (day_3["progress"], day_3["at"], day_3["earned"]) == (2, 3, None)
    nxt = m.next_medal("day")
    assert (nxt["id"], nxt["name"], nxt["at"], nxt["remaining"]) == ("day_3", "Little Sprout", 3, 1)
    assert nxt["names"] == {"en": "Little Sprout", "sv": "Lilla Grodden"}
    assert day_3["hows"]["sv"] == "Gör alla dagens sysslor 3 dagar i rad"


async def test_medal_names_follow_the_language(hass, make_manager, freezer):
    hass.config.language = "sv"
    m = await _on(make_manager)
    assert next(x for x in m.medal_list() if x["id"] == "day_3")["name"] == "Lilla Grodden"


# ----------------------------------------------------------------------
# Notifications
# ----------------------------------------------------------------------
async def test_earning_a_medal_notifies_the_child_and_the_parents(
    make_manager, kid, parents, freezer
):
    m = await _on(
        make_manager, **{CONF_NOTIFY_KID: ["kid_phone"], CONF_NOTIFY_PARENTS: ["parent_phone"]}
    )
    for day in (MON, TUE, WED):
        await _perfect_day(m, freezer, day)
    medal_kid = [c for c in kid if c.data["title"] == "New medal! 🏅"]
    assert len(medal_kid) == 1
    assert medal_kid[0].data["message"] == (
        "You earned “Little Sprout”: Do all your daily chores 3 days in a row."
        " +5 points were added to the bank."
    )
    medal_parents = [c for c in parents if c.data["title"] == "Medal earned 🏅"]
    assert len(medal_parents) == 1


async def test_medal_notifications_can_be_switched_off(make_manager, kid, freezer):
    m = await _on(make_manager, **{CONF_NOTIFY_KID: ["kid_phone"], CONF_MEDALS_NOTIFY: False})
    for day in (MON, TUE, WED):
        await _perfect_day(m, freezer, day)
    assert "day_3" in m.medal_data["earned"]
    assert not [c for c in kid if c.data["title"] == "New medal! 🏅"]


async def test_bedtime_reminder_warns_about_a_streak_at_risk(make_manager, kid, freezer):
    m = await _on(
        make_manager,
        **{CONF_NOTIFY_KID: ["kid_phone"], CONF_BEDTIME: "20:30", CONF_BEDTIME_LEAD: 45},
    )
    await _perfect_day(m, freezer, MON)
    await _perfect_day(m, freezer, TUE)
    freezer.move_to("2026-03-04 19:45:00")
    await m._on_minute(freezer())
    bedtime = [c for c in kid if c.data["title"] == "Almost bedtime 🌙"]
    assert bedtime[0].data["message"].endswith("\n🔥 Your 2-day streak is at risk!")


async def test_bedtime_reminder_is_unchanged_without_a_streak(make_manager, kid, freezer):
    m = await _on(
        make_manager,
        **{CONF_NOTIFY_KID: ["kid_phone"], CONF_BEDTIME: "20:30", CONF_BEDTIME_LEAD: 45},
    )
    freezer.move_to("2026-03-04 19:45:00")
    await m._on_minute(freezer())
    assert "streak" not in kid[0].data["message"]


# ----------------------------------------------------------------------
# Persistence
# ----------------------------------------------------------------------
async def test_medals_and_streaks_survive_a_restart(hass, make_manager, freezer):
    m = await _on(make_manager)
    for day in (MON, TUE, WED):
        await _perfect_day(m, freezer, day)
    await m.async_stop()

    restored = ChoresManager(hass, m.entry)
    await restored.async_load()
    assert restored.day_streak() == 3
    assert "day_3" in restored.medal_data["earned"]
    assert restored.medal_data["chores_done"] == 6


async def test_an_old_store_without_medals_loads(hass, make_manager):
    m = await make_manager()
    del m.data["medals"]
    await m.async_stop()
    restored = ChoresManager(hass, m.entry)
    await restored.async_load()
    assert restored.medal_data["earned"] == {}
    assert restored.medal_data["perfect_days"] == []


async def test_best_day_streak_drops_when_a_perfect_day_is_taken_back(make_manager):
    m = await _on(make_manager)
    today = dt_util.now().date()
    m.medal_data["perfect_days"] = [
        (today - timedelta(days=d)).isoformat() for d in range(1, 7)
    ]
    m.medal_data["best_day"] = 7
    m._fix_best_day()
    assert m.medal_data["best_day"] == 6
