"""Tests for the notifications sent when a parent adjusts points or money."""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.kid_chores_points.const import (
    CONF_ADJUST_NOTIFY,
    CONF_LANGUAGE_KID,
    CONF_NOTIFY_KID,
    CONF_NOTIFY_PARENTS,
)


@pytest.fixture
def kid(hass):
    return async_mock_service(hass, "notify", "kid_phone")


@pytest.fixture
def parents(hass):
    return async_mock_service(hass, "notify", "parent_phone")


async def _manager(make_manager, **options):
    return await make_manager(
        **{CONF_NOTIFY_KID: ["kid_phone"], CONF_NOTIFY_PARENTS: ["parent_phone"], **options}
    )


async def test_adding_points_notifies_the_child_and_the_parents(make_manager, kid, parents):
    m = await _manager(make_manager)
    await m.async_adjust("bank", 20, "Helped grandma")
    assert kid[-1].data["title"] == "Points added ⭐"
    assert kid[-1].data["message"] == (
        f"You got +20 points in the bank. Reason: Helped grandma. Bank: {m.bank} points."
    )
    assert parents[-1].data["title"] == "Points adjusted ✏️"
    assert parents[-1].data["message"] == (
        f"Bank adjusted by +20. Reason: Helped grandma. Balance: {m.bank} points."
    )


async def test_deducting_points_and_the_week_target(make_manager, kid, parents):
    m = await _manager(make_manager)
    await m.async_adjust("week", 8, None)
    await m.async_adjust("week", -3, "Messy room")
    assert kid[-1].data["title"] == "Points deducted"
    assert kid[-1].data["message"] == (
        f"You lost 3 points this week. Reason: Messy room. Week total: {m.week} points."
    )
    assert parents[-1].data["message"].startswith("This week's points adjusted by -3.")


async def test_a_missing_reason_is_left_out(make_manager, kid):
    m = await _manager(make_manager)
    await m.async_adjust("bank", 5, "  ")
    assert "Reason" not in kid[-1].data["message"]


async def test_the_message_shows_the_change_that_was_actually_made(make_manager, kid):
    m = await _manager(make_manager)
    await m.async_adjust("bank", 4, "x")
    await m.async_adjust("bank", -10, "y")
    assert kid[-1].data["message"].startswith("You lost 4 points from the bank.")
    count = len(kid)
    await m.async_adjust("bank", -10, "z")  # already 0, nothing changes
    assert len(kid) == count


async def test_the_child_gets_swedish_text(make_manager, kid):
    m = await _manager(make_manager, **{CONF_LANGUAGE_KID: "sv"})
    await m.async_adjust("bank", 20, "Hjälpte farmor")
    assert kid[-1].data["title"] == "Poäng tillagda ⭐"
    assert kid[-1].data["message"].startswith(
        "Du fick +20 poäng i banken. Anledning: Hjälpte farmor."
    )


async def test_wallet_adjustments_notify_too(make_manager, kid, parents):
    m = await _manager(make_manager)
    await m.async_adjust_wallet(20, "Birthday")
    assert kid[-1].data["title"] == "Money added! 💰"
    assert kid[-1].data["message"] == (
        f"20 {m.currency} was added to your wallet. Reason: Birthday."
        f" You now have {m.wallet} {m.currency}."
    )
    assert parents[-1].data["title"] == "Wallet adjusted 💰"
    await m.async_adjust_wallet(-5, None)
    assert kid[-1].data["title"] == "Money deducted"


async def test_adjust_notifications_can_be_switched_off(make_manager, kid, parents):
    m = await _manager(make_manager, **{CONF_ADJUST_NOTIFY: False})
    await m.async_adjust("bank", 20, "x")
    await m.async_adjust_wallet(5, "y")
    assert not kid
    assert not parents
