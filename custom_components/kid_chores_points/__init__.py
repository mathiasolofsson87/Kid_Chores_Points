"""Kid Chores & Points integration."""

from __future__ import annotations

from pathlib import Path

import voluptuous as vol

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    ATTR_ENTRY,
    CARD_URL,
    DOMAIN,
    PLATFORMS,
    SERVICE_ADJUST,
    SERVICE_CLOSE_WEEK,
    SERVICE_COMPLETE,
    SERVICE_REDEEM,
)
from .manager import ChoresManager

type ChoresConfigEntry = ConfigEntry[ChoresManager]

_BASE = {vol.Optional(ATTR_ENTRY): cv.string}


def _manager(hass: HomeAssistant, call: ServiceCall) -> ChoresManager:
    entries = [
        e
        for e in hass.config_entries.async_entries(DOMAIN)
        if e.state is ConfigEntryState.LOADED
    ]
    if entry_id := call.data.get(ATTR_ENTRY):
        entries = [e for e in entries if e.entry_id == entry_id]
    if not entries:
        raise ServiceValidationError("No loaded Kid Chores & Points entry found")
    if len(entries) > 1:
        raise ServiceValidationError(
            "Several entries exist; specify which one with 'config_entry'"
        )
    return entries[0].runtime_data


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the rewards card and domain-wide services."""
    card_file = Path(__file__).parent / "www" / "kid-chores-rewards-card.js"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(card_file), cache_headers=False)]
    )
    add_extra_js_url(hass, f"{CARD_URL}?v={card_file.stat().st_mtime_ns}")

    async def complete(call: ServiceCall) -> None:
        await _manager(hass, call).async_complete(call.data["name"])

    async def redeem(call: ServiceCall) -> None:
        await _manager(hass, call).async_redeem(
            call.data["reward"], call.data["units"]
        )

    async def adjust(call: ServiceCall) -> None:
        await _manager(hass, call).async_adjust(
            call.data["target"], call.data["points"], call.data.get("reason")
        )

    async def close_week(call: ServiceCall) -> None:
        await _manager(hass, call).async_close_week()

    hass.services.async_register(
        DOMAIN,
        SERVICE_COMPLETE,
        complete,
        vol.Schema({**_BASE, vol.Required("name"): cv.string}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REDEEM,
        redeem,
        vol.Schema(
            {
                **_BASE,
                vol.Required("reward"): cv.string,
                vol.Optional("units", default=1): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=100)
                ),
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ADJUST,
        adjust,
        vol.Schema(
            {
                **_BASE,
                vol.Required("target"): vol.In(["week", "bank"]),
                vol.Required("points"): vol.Coerce(int),
                vol.Optional("reason"): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN, SERVICE_CLOSE_WEEK, close_week, vol.Schema(_BASE)
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ChoresConfigEntry) -> bool:
    manager = ChoresManager(hass, entry)
    await manager.async_load()
    entry.runtime_data = manager
    manager.async_start()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_reload))
    return True


async def _reload(hass: HomeAssistant, entry: ChoresConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ChoresConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.async_stop()
    return unloaded
