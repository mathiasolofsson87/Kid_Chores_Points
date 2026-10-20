"""Sensors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import ChoresEntity
from .manager import ChoresManager


@dataclass(frozen=True, kw_only=True)
class ChoresSensorDescription(SensorEntityDescription):
    value_fn: Callable[[ChoresManager], Any]
    attrs_fn: Callable[[ChoresManager], dict[str, Any]] | None = None


def _progress(m: ChoresManager) -> int:
    if m.goal <= 0:
        return 100
    return round(min(m.week / m.goal * 100, 100))


SENSORS: tuple[ChoresSensorDescription, ...] = (
    ChoresSensorDescription(
        key="points_week",
        name="Points this week",
        icon="mdi:star",
        native_unit_of_measurement="p",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda m: m.week,
    ),
    ChoresSensorDescription(
        key="points_bank",
        name="Points bank",
        icon="mdi:piggy-bank",
        native_unit_of_measurement="p",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda m: m.bank,
    ),
    ChoresSensorDescription(
        key="wallet",
        name="Wallet",
        icon="mdi:wallet",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda m: m.wallet,
        attrs_fn=lambda m: {
            "currency": m.currency,
            # cards show the wallet once it is in use
            "enabled": bool(m.payouts) or m.wallet > 0,
        },
    ),
    ChoresSensorDescription(
        key="weekly_goal",
        name="Weekly goal",
        icon="mdi:flag-checkered",
        native_unit_of_measurement="p",
        value_fn=lambda m: m.goal,
    ),
    ChoresSensorDescription(
        key="points_to_goal",
        name="Points to goal",
        icon="mdi:flag-variant",
        native_unit_of_measurement="p",
        value_fn=lambda m: max(m.goal - m.week, 0),
    ),
    ChoresSensorDescription(
        key="week_progress",
        name="Week progress",
        icon="mdi:progress-star",
        native_unit_of_measurement="%",
        value_fn=_progress,
    ),
    ChoresSensorDescription(
        key="points_today",
        name="Points today",
        icon="mdi:calendar-check",
        native_unit_of_measurement="p",
        value_fn=lambda m: m.today["points"],
        attrs_fn=lambda m: {
            "date": m.today["date"],
            "mandatory_done": m.today["mandatory_done"],
            "bonus_done": m.today["bonus_done"],
            "pending": m.today["pending"],
        },
    ),
    ChoresSensorDescription(
        key="mandatory_remaining",
        name="Mandatory chores remaining",
        icon="mdi:format-list-checks",
        value_fn=lambda m: len(m.mandatory_remaining()),
        attrs_fn=lambda m: {
            "remaining": m.mandatory_remaining(),
            "done": m.today["mandatory_done"],
            "bonus_chores": m.bonus,
            "mandatory_chores": m.mandatory,
        },
    ),
    ChoresSensorDescription(
        key="pending_bonus",
        name="Pending bonus points",
        icon="mdi:timer-sand",
        native_unit_of_measurement="p",
        value_fn=lambda m: sum(p["points"] for p in m.today["pending"]),
    ),
    ChoresSensorDescription(
        key="points_history",
        name="Points history",
        icon="mdi:timeline-clock",
        value_fn=lambda m: len(m.history),
        attrs_fn=lambda m: {"history": list(reversed(m.history))},
    ),
    ChoresSensorDescription(
        key="last_week_result",
        name="Last week result",
        icon="mdi:history",
        value_fn=lambda m: m.last_week or None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback
) -> None:
    manager: ChoresManager = entry.runtime_data
    async_add_entities(ChoresSensor(manager, d) for d in SENSORS)


class ChoresSensor(ChoresEntity, SensorEntity):
    entity_description: ChoresSensorDescription
    _unrecorded_attributes = frozenset({"history"})

    def __init__(self, manager: ChoresManager, description: ChoresSensorDescription):
        super().__init__(manager, description.key)
        self.entity_description = description

    @property
    def native_unit_of_measurement(self) -> str | None:
        if self.entity_description.key == "wallet":
            return self.manager.currency
        return super().native_unit_of_measurement

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.manager)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {
            "key": self.entity_description.key,
            "entry_id": self.manager.entry.entry_id,
        }
        if fn := self.entity_description.attrs_fn:
            attrs.update(fn(self.manager))
        return attrs
