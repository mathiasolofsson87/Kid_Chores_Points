"""Tests that balances survive a restart."""

from __future__ import annotations

from custom_components.kid_chores_points.manager import ChoresManager


async def test_state_is_restored_after_restart(hass, make_manager):
    m = await make_manager()
    await m.async_complete("Dishes")
    await m.async_adjust("bank", 40, "x")
    await m.async_adjust_wallet(7, "gift")
    await m.async_stop()  # what unloading the entry does

    restored = ChoresManager(hass, m.entry)
    await restored.async_load()
    assert restored.week == 20
    assert restored.bank == 40
    assert restored.wallet == 7
    assert len(restored.history) == len(m.history)


async def test_fresh_install_starts_at_zero(make_manager):
    m = await make_manager()
    assert (m.week, m.week_bonus, m.bank, m.wallet) == (0, 0, 0, 0)
    assert m.history == []
    assert m.last_week == ""
