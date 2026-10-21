"""Tests for Maintenance Supporter events and the "whose completions count" rule."""

from __future__ import annotations

from custom_components.kid_chores_points.const import (
    CONF_KID_PERSONS,
    EVENT_TASK_COMPLETED,
)

KID_USER = "user-kid"
PARENT_USER = "user-parent"


async def _fire(hass, **data):
    hass.bus.async_fire(EVENT_TASK_COMPLETED, data)
    await hass.async_block_till_done()


async def test_event_awards_points(hass, make_manager):
    m = await make_manager()
    m.async_start()
    await _fire(hass, task_name="Dishes")
    assert m.week == 20


async def test_event_without_task_name_is_ignored(hass, make_manager):
    m = await make_manager()
    m.async_start()
    await _fire(hass, something="else")
    assert m.week == 0


async def test_event_for_unknown_task_is_ignored(hass, make_manager):
    m = await make_manager()
    m.async_start()
    await _fire(hass, task_name="Not a chore")
    assert m.week == 0


async def test_only_the_childs_own_completions_count(hass, make_manager):
    hass.states.async_set("person.kid", "home", {"user_id": KID_USER})
    m = await make_manager(**{CONF_KID_PERSONS: ["person.kid"]})
    m.async_start()

    await _fire(hass, task_name="Dishes", completed_by=PARENT_USER)
    assert m.week == 0

    await _fire(hass, task_name="Dishes", completed_by=KID_USER)
    assert m.week == 20


async def test_completion_without_user_still_counts(hass, make_manager):
    hass.states.async_set("person.kid", "home", {"user_id": KID_USER})
    m = await make_manager(**{CONF_KID_PERSONS: ["person.kid"]})
    m.async_start()
    await _fire(hass, task_name="Dishes")  # NFC tag / automation
    assert m.week == 20


async def test_everyone_counts_when_child_has_no_linked_user(hass, make_manager):
    hass.states.async_set("person.kid", "home", {})
    m = await make_manager(**{CONF_KID_PERSONS: ["person.kid"]})
    m.async_start()
    await _fire(hass, task_name="Dishes", completed_by=PARENT_USER)
    assert m.week == 20


async def test_everyone_counts_when_no_child_person_is_set(hass, make_manager):
    m = await make_manager()
    m.async_start()
    await _fire(hass, task_name="Dishes", completed_by=PARENT_USER)
    assert m.week == 20


async def test_renamed_task_still_matches_by_task_id(hass, make_manager):
    m = await make_manager(chore_ids={"Dishes": "id-dishes"})
    m.async_start()
    await _fire(hass, task_id="id-dishes", task_name="Wash the dishes")
    assert m.week == 20
    assert m.today["mandatory_done"] == ["Dishes"]


async def test_task_id_wins_over_a_clashing_name(hass, make_manager):
    m = await make_manager(chore_ids={"Dishes": "id-dishes"})
    m.async_start()
    await _fire(hass, task_id="id-dishes", task_name="Trash")
    assert m.today["mandatory_done"] == ["Dishes"]


async def test_unlinked_chore_falls_back_to_the_name(hass, make_manager):
    m = await make_manager(chore_ids={"Trash": "id-trash"})
    m.async_start()
    await _fire(hass, task_id="id-dishes", task_name="Dishes")
    assert m.today["mandatory_done"] == ["Dishes"]


async def test_link_to_a_removed_chore_is_ignored(hass, make_manager):
    m = await make_manager(chore_ids={"Gone": "id-gone"})
    m.async_start()
    await _fire(hass, task_id="id-gone", task_name="Not a chore")
    assert m.week == 0
