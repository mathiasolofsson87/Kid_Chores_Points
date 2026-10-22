"""The medal catalogue: which medals exist, their tier and their default targets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .const import MEDAL_BONUS_MAX

# What a medal counts
DAY = "day"  # days in a row with every mandatory chore done
WEEK = "week"  # weeks in a row with the goal reached
CHORES = "chores"  # chores done in total
BONUS = "bonus"  # bonus chores done in total
TREAT = "treat"  # rewards handed out

# The medals a parent can tune in Configure, one form per group
GROUPS = (DAY, WEEK, CHORES, BONUS)

# Counters kept in the store (changed by a history entry, so a revert can take them back)
COUNTERS = ("chores_done", "bonus_done", "treats")

# The counter behind each kind of medal (streaks are worked out separately)
COUNTER = {
    CHORES: "chores_done",
    BONUS: "bonus_done",
    TREAT: "treats",
}

AT_MAX = {DAY: 365, WEEK: 104, CHORES: 100000, BONUS: 100000}


@dataclass(frozen=True)
class Medal:
    id: str
    kind: str
    tier: str  # bronze | silver | gold | diamond | treat
    at: int  # default target
    bonus: int  # default bonus points (paid into the bank)

    @property
    def configurable(self) -> bool:
        """Whether the parent can change the target (First Treat is fixed)."""
        return self.kind in GROUPS

    @property
    def pays(self) -> bool:
        """Whether the bonus can be changed (First Treat is honorary)."""
        return self.kind in (DAY, WEEK, CHORES, BONUS)


MEDALS: tuple[Medal, ...] = (
    Medal("day_3", DAY, "bronze", 3, 5),
    Medal("day_7", DAY, "silver", 7, 10),
    Medal("day_14", DAY, "gold", 14, 20),
    Medal("day_30", DAY, "diamond", 30, 40),
    Medal("week_10", WEEK, "bronze", 10, 50),
    Medal("week_12", WEEK, "silver", 12, 50),
    Medal("week_16", WEEK, "gold", 16, 50),
    Medal("week_20", WEEK, "diamond", 20, 50),
    Medal("chores_25", CHORES, "bronze", 25, 5),
    Medal("chores_100", CHORES, "silver", 100, 10),
    Medal("chores_250", CHORES, "gold", 250, 20),
    Medal("chores_500", CHORES, "diamond", 500, 35),
    Medal("chores_1000", CHORES, "diamond", 1000, 50),
    Medal("first_treat", TREAT, "treat", 1, 0),
    Medal("bonus_10", BONUS, "bronze", 10, 5),
    Medal("bonus_50", BONUS, "silver", 50, 15),
    Medal("bonus_100", BONUS, "gold", 100, 30),
    Medal("bonus_250", BONUS, "diamond", 250, 45),
)

BY_ID = {m.id: m for m in MEDALS}


def group_medals(group: str) -> list[Medal]:
    """The medals of one configurable group, in order."""
    return [m for m in MEDALS if m.kind == group]


def medal_rules(overrides: dict[str, Any]) -> dict[str, tuple[int, int]]:
    """{medal id: (target, bonus)} with the parent's changes applied."""
    rules: dict[str, tuple[int, int]] = {}
    for m in MEDALS:
        at, bonus = m.at, m.bonus
        if m.configurable and (own := overrides.get(m.id)):
            at = max(int(own.get("at", at)), 1)
            if m.pays:
                bonus = min(max(int(own.get("bonus", bonus)), 0), MEDAL_BONUS_MAX)
        rules[m.id] = (at, bonus)
    return rules
