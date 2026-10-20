"""Binary sensors."""

from __future__ import annotations

import re
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import ChoresEntity
from .manager import ChoresManager


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback
) -> None:
    manager: ChoresManager = entry.runtime_data
    entities: list[BinarySensorEntity] = [MandatoryComplete(manager)]
    entities += [CanAfford(manager, reward) for reward in manager.rewards]
    async_add_entities(entities)


class MandatoryComplete(ChoresEntity, BinarySensorEntity):
    _attr_name = "Mandatory chores complete"
    _attr_icon = "mdi:check-decagram"

    def __init__(self, manager: ChoresManager) -> None:
        super().__init__(manager, "mandatory_complete")

    @property
    def is_on(self) -> bool:
        return not self.manager.mandatory_remaining()


class CanAfford(ChoresEntity, BinarySensorEntity):
    _attr_icon = "mdi:gift-outline"

    def __init__(self, manager: ChoresManager, reward: str) -> None:
        slug = re.sub(r"\W+", "_", reward.lower()).strip("_") or "reward"
        super().__init__(manager, f"can_afford_{slug}")
        self._reward = reward
        self._attr_name = f"Can afford {reward}"

    @property
    def is_on(self) -> bool:
        rate = int(self.manager.rewards.get(self._reward, 0))
        return rate > 0 and self.manager.bank >= rate

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "reward": self._reward,
            "cost": int(self.manager.rewards.get(self._reward, 0)),
            "bank": self.manager.bank,
            "payout": int(self.manager.payouts.get(self._reward, 0)),
            "currency": self.manager.currency,
            "entry_id": self.manager.entry.entry_id,
        }
