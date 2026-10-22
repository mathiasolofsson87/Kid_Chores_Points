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

from .const import CONF_MEDALS_GRACE
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
        name="Points this week",  # mandatory points; bonus is counted separately
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
        key="bonus_week",
        name="Bonus points this week",
        icon="mdi:star-plus",
        native_unit_of_measurement="p",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda m: m.week_bonus,
        # bonus points are banked only if the weekly goal (mandatory points) is met
        attrs_fn=lambda m: {"enabled": bool(m.bonus) or m.week_bonus > 0},
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
            "chore_ids": m.chore_ids,
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
        attrs_fn=lambda m: {
            "history": [
                {**e, "can_revert": m.can_revert(e)} for e in reversed(m.history)
            ],
            "undo_label": m.undo_label,
        },
    ),
    ChoresSensorDescription(
        key="day_streak",
        name="Day streak",
        icon="mdi:fire",
        native_unit_of_measurement="days",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda m: m.day_streak(),
        attrs_fn=lambda m: {
            "enabled": m.medals_on,
            "best": m.medal_data["best_day"],
            "at_risk": m.streak_at_risk(),
            "grace": bool(m.opt(CONF_MEDALS_GRACE)),
            "next": m.next_medal("day"),
        },
    ),
    ChoresSensorDescription(
        key="week_streak",
        name="Week streak",
        icon="mdi:trophy-outline",
        native_unit_of_measurement="weeks",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda m: m.medal_data["week_streak"],
        attrs_fn=lambda m: {
            "enabled": m.medals_on,
            "best": m.medal_data["best_week"],
            "next": m.next_medal("week"),
        },
    ),
    ChoresSensorDescription(
        key="medals",
        name="Medals",
        icon="mdi:medal",
        value_fn=lambda m: len(m.medal_data["earned"]),
        attrs_fn=lambda m: {"enabled": m.medals_on, "medals": m.medal_list()},
    ),
    ChoresSensorDescription(
        key="chores_done",
        name="Chores done",
        icon="mdi:check-all",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda m: m.medal_data["chores_done"],
    ),
    ChoresSensorDescription(
        key="bonus_chores_done",
        name="Bonus chores done",
        icon="mdi:star-plus-outline",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda m: m.medal_data["bonus_done"],
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
    _unrecorded_attributes = frozenset({"history", "medals"})

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
