"""Tests for the language of the notifications."""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import async_mock_service

from homeassistant.components.frontend.storage import async_user_store

from custom_components.kid_chores_points.const import (
    CONF_KID_PERSONS,
    CONF_LANGUAGE_KID,
    CONF_LANGUAGE_PARENTS,
    CONF_NOTIFY_KID,
    CONF_NOTIFY_PARENTS,
    CONF_PARENT_PERSONS,
)


@pytest.fixture
def kid(hass):
    return async_mock_service(hass, "notify", "kid_phone")


@pytest.fixture
def parents(hass):
    return async_mock_service(hass, "notify", "parent_phone")


async def _profile_language(hass, user_id, language):
    """What the frontend saves when a user picks a language in their profile."""
    store = await async_user_store(hass, user_id)
    store.data["language"] = {"language": language, "number_format": "language"}


def _person(hass, entity_id, user_id):
    hass.states.async_set(entity_id, "home", {"user_id": user_id})


async def _manager(make_manager, **options):
    return await make_manager(
        **{CONF_NOTIFY_KID: ["kid_phone"], CONF_NOTIFY_PARENTS: ["parent_phone"], **options}
    )


async def test_notifications_follow_the_childs_profile_language(
    hass, make_manager, kid, parents
):
    _person(hass, "person.anna", "anna-id")
    await _profile_language(hass, "anna-id", "sv")
    m = await _manager(make_manager, **{CONF_KID_PERSONS: ["person.anna"]})
    await m.async_complete("Dishes")
    await m.async_complete("Trash")
    assert [c.data["title"] for c in kid] == ["Dagens uppgifter klara! ⭐"]


async def test_the_system_language_is_used_when_the_profile_has_none(
    hass, make_manager, kid
):
    _person(hass, "person.anna", "anna-id")  # no language saved for this user
    m = await _manager(make_manager, **{CONF_KID_PERSONS: ["person.anna"]})
    await m.async_complete("Dishes")
    await m.async_complete("Trash")
    assert kid[0].data["title"] == "Today's chores done! ⭐"


async def test_a_language_chosen_in_configure_wins_over_the_profile(
    hass, make_manager, kid
):
    _person(hass, "person.anna", "anna-id")
    await _profile_language(hass, "anna-id", "en")
    m = await _manager(
        make_manager, **{CONF_KID_PERSONS: ["person.anna"], CONF_LANGUAGE_KID: "sv"}
    )
    await m.async_complete("Dishes")
    await m.async_complete("Trash")
    assert kid[0].data["title"] == "Dagens uppgifter klara! ⭐"


async def test_the_child_and_the_parents_can_get_different_languages(
    hass, make_manager, kid, parents
):
    _person(hass, "person.anna", "anna-id")
    await _profile_language(hass, "anna-id", "sv")
    m = await _manager(make_manager, **{CONF_KID_PERSONS: ["person.anna"]})
    await m.async_adjust("bank", 20, "start")
    await m.async_redeem("15 min Xbox")
    assert kid[-1].data["title"] == "Inlöst! 🎉"
    assert parents[-1].data["title"] == "Reward redeemed 🎁"


async def test_parents_with_different_languages_get_the_system_language(
    hass, make_manager, parents
):
    _person(hass, "person.mum", "mum-id")
    _person(hass, "person.dad", "dad-id")
    await _profile_language(hass, "mum-id", "sv")
    await _profile_language(hass, "dad-id", "en")
    m = await _manager(
        make_manager, **{CONF_PARENT_PERSONS: ["person.mum", "person.dad"]}
    )
    await m.async_adjust("bank", 20, "start")
    await m.async_redeem("15 min Xbox")
    assert parents[-1].data["title"] == "Reward redeemed 🎁"


async def test_an_unsupported_profile_language_falls_back_to_the_system_language(
    hass, make_manager, kid
):
    _person(hass, "person.anna", "anna-id")
    await _profile_language(hass, "anna-id", "de")
    m = await _manager(make_manager, **{CONF_KID_PERSONS: ["person.anna"]})
    await m.async_complete("Dishes")
    await m.async_complete("Trash")
    assert kid[0].data["title"] == "Today's chores done! ⭐"


async def test_the_week_close_message_and_its_note_use_each_recipients_language(
    hass, make_manager, kid, parents
):
    _person(hass, "person.anna", "anna-id")
    await _profile_language(hass, "anna-id", "sv")
    m = await _manager(
        make_manager, **{CONF_KID_PERSONS: ["person.anna"], CONF_LANGUAGE_PARENTS: "en"}
    )
    await m.async_complete("Dishes")
    await m.async_complete("Trash")
    await m.async_complete("Vacuum")  # a bonus chore, so the week has a bonus note
    kid.clear()
    parents.clear()
    await m.async_close_week()
    assert kid[0].data["title"] == "Veckomålet klarat! 🏆"
    assert "Inkluderar 12 bonuspoäng." in kid[0].data["message"]
    assert parents[0].data["title"] == "Weekly summary"
    assert "Includes 12 bonus points." in parents[0].data["message"]
    assert m.last_week.endswith("Includes 12 bonus points.")  # the sensor stays in the system language


async def test_medal_names_are_available_in_every_language_for_the_cards(make_manager):
    m = await make_manager(medals_enabled=True)
    day_3 = next(x for x in m.medal_list() if x["id"] == "day_3")
    assert day_3["names"] == {"en": "Little Sprout", "sv": "Lilla Grodden"}
    assert day_3["hows"]["en"] == "Do all your daily chores 3 days in a row"
    assert day_3["hows"]["sv"] == "Gör alla dagens sysslor 3 dagar i rad"
