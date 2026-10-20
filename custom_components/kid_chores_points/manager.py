"""Points engine for Kid Chores & Points."""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util, slugify

from .messages import translate
from .const import (
    CONF_BONUS,
    CONF_GOAL,
    CONF_GOAL_BONUS,
    CONF_KID_PERSONS,
    CONF_MANDATORY,
    CONF_CURRENCY,
    CONF_NOTIFY_KID,
    CONF_NOTIFY_PARENTS,
    CONF_PARENT_PERSONS,
    CONF_POLICY,
    CONF_REWARD_PAYOUT,
    CONF_REWARDS,
    CONF_WEEK_START,
    DEFAULT_OPTIONS,
    DOMAIN,
    EVENT_TASK_COMPLETED,
    HISTORY_LIMIT,
    POLICY_FORFEIT,
    POLICY_HALF,
    SIGNAL_UPDATE,
    WEEK_DAYS,
)

_LOGGER = logging.getLogger(__name__)


def _empty_today(date: str = "") -> dict[str, Any]:
    return {
        "date": date,
        "mandatory_done": [],
        "bonus_done": [],
        "pending": [],  # [{"name": str, "points": int}]
        "points": 0,
    }


class ChoresManager:
    """Holds state and implements the point rules for one config entry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._store: Store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}")
        self._lock = asyncio.Lock()
        self.data: dict[str, Any] = {}
        self.signal = SIGNAL_UPDATE.format(entry.entry_id)

    # ------------------------------------------------------------------
    # Options helpers
    # ------------------------------------------------------------------
    def opt(self, key: str) -> Any:
        return self.entry.options.get(key, DEFAULT_OPTIONS[key])

    @property
    def mandatory(self) -> dict[str, int]:
        return self.opt(CONF_MANDATORY)

    @property
    def bonus(self) -> dict[str, int]:
        return self.opt(CONF_BONUS)

    @property
    def rewards(self) -> dict[str, int]:
        return self.opt(CONF_REWARDS)

    @property
    def payouts(self) -> dict[str, int]:
        """Rewards that pay money into the wallet: {reward: money per unit}."""
        return self.opt(CONF_REWARD_PAYOUT)

    @property
    def currency(self) -> str:
        return self.opt(CONF_CURRENCY)

    @property
    def goal(self) -> int:
        return int(self.opt(CONF_GOAL))

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------
    async def async_load(self) -> None:
        stored = await self._store.async_load() or {}
        self.data = {
            "week": 0,
            "week_bonus": 0,  # bonus points this week, banked only if the goal is met
            "bank": 0,
            "wallet": 0,
            "last_week": "",
            "today": _empty_today(),
            "reward_log": [],
            "history": [],
            **stored,
        }

    @property
    def week(self) -> int:
        return int(self.data["week"])

    @property
    def week_bonus(self) -> int:
        return int(self.data["week_bonus"])

    @property
    def bank(self) -> int:
        return int(self.data["bank"])

    @property
    def wallet(self) -> int:
        return int(self.data["wallet"])

    @property
    def last_week(self) -> str:
        return self.data["last_week"]

    @property
    def reward_log(self) -> list[dict[str, Any]]:
        return self.data["reward_log"]

    @property
    def history(self) -> list[dict[str, Any]]:
        return self.data["history"]

    def _record(
        self,
        kind: str,
        label: str,
        points: int,
        target: str = "week",
        pending: int = 0,
        amount: int = 0,
    ) -> None:
        """Append a points/wallet change to the history (call after updating totals).

        `amount` is the change in wallet money (not points).
        """
        self.history.append(
            {
                "t": dt_util.now().isoformat(timespec="seconds"),
                "type": kind,
                "label": label,
                "points": points,
                "target": target,
                "pending": pending,
                "week": self.week,
                "week_bonus": self.week_bonus,
                "bank": self.bank,
                "amount": amount,
                "wallet": self.wallet,
            }
        )
        del self.history[:-HISTORY_LIMIT]

    @property
    def today(self) -> dict[str, Any]:
        """Today's state, empty if the stored day is stale."""
        today = self.data["today"]
        if today["date"] != dt_util.now().date().isoformat():
            return _empty_today(dt_util.now().date().isoformat())
        return today

    def _ensure_today(self) -> dict[str, Any]:
        date = dt_util.now().date().isoformat()
        if self.data["today"]["date"] != date:
            self.data["today"] = _empty_today(date)
        return self.data["today"]

    def mandatory_remaining(self) -> list[str]:
        done = self.today["mandatory_done"]
        return [n for n in self.mandatory if n not in done]

    @callback
    def _changed(self) -> None:
        self._store.async_delay_save(lambda: self.data, 1)
        async_dispatcher_send(self.hass, self.signal)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    @callback
    def async_start(self) -> None:
        self.entry.async_on_unload(
            self.hass.bus.async_listen(EVENT_TASK_COMPLETED, self._on_event)
        )
        self.entry.async_on_unload(
            async_track_time_change(self.hass, self._on_midnight, 0, 0, 0)
        )
        self.entry.async_on_unload(
            async_track_time_change(self.hass, self._on_week_end, 23, 59, 0)
        )

    async def async_stop(self) -> None:
        await self._store.async_save(self.data)

    def _kid_user_ids(self) -> set[str]:
        """Home Assistant user ids linked to the configured child person(s)."""
        users: set[str] = set()
        for person in self.opt(CONF_KID_PERSONS):
            state = self.hass.states.get(person)
            if state and (uid := state.attributes.get("user_id")):
                users.add(uid)
        return users

    async def _on_event(self, event: Event) -> None:
        name = event.data.get("task_name")
        if not name:
            return
        # Maintenance Supporter reports who completed the task (HA user id).
        # If the child has a linked user, only their completions count;
        # completions without a user (automatic, NFC...) still count.
        by = event.data.get("completed_by")
        kid_users = self._kid_user_ids()
        if by and kid_users and by not in kid_users:
            _LOGGER.debug("Ignoring '%s' completed by another user", name)
            return
        await self.async_complete(name, raise_unknown=False)

    @callback
    def _on_midnight(self, _now: Any) -> None:
        self._ensure_today()
        self._changed()

    async def _on_week_end(self, now: Any) -> None:
        """Close the week at 23:59 on the day before the week-start day."""
        start = WEEK_DAYS.index(self.opt(CONF_WEEK_START))
        if dt_util.as_local(now).weekday() == (start - 1) % 7:
            await self.async_close_week()

    def tr(self, key: str, **kwargs: object) -> str:
        return translate(self.hass.config.language, key, **kwargs)

    # ------------------------------------------------------------------
    # Notifications / logbook
    # ------------------------------------------------------------------
    def _person_services(self, persons: list[str]) -> set[str]:
        """Resolve person entities to the notify services of their phones."""
        registry = er.async_get(self.hass)
        found: set[str] = set()
        for person in persons:
            if (state := self.hass.states.get(person)) is None:
                continue
            for tracker in state.attributes.get("device_trackers", []):
                reg = registry.async_get(tracker)
                if reg is None or reg.config_entry_id is None:
                    continue
                cfg = self.hass.config_entries.async_get_entry(reg.config_entry_id)
                if cfg and cfg.domain == "mobile_app" and cfg.data.get("device_name"):
                    found.add(f"mobile_app_{slugify(cfg.data['device_name'])}")
        return found

    async def _notify(self, key: str, title: str, message: str) -> None:
        person_key = CONF_KID_PERSONS if key == CONF_NOTIFY_KID else CONF_PARENT_PERSONS
        targets = set(self.opt(key)) | self._person_services(self.opt(person_key))
        for service in sorted(targets):
            if not self.hass.services.has_service("notify", service):
                _LOGGER.warning("notify.%s is not available", service)
                continue
            try:
                await self.hass.services.async_call(
                    "notify", service, {"title": title, "message": message}
                )
            except Exception:  # noqa: BLE001
                _LOGGER.warning("Could not send notification via notify.%s", service)

    async def _log(self, message: str) -> None:
        try:
            await self.hass.services.async_call(
                "logbook",
                "log",
                {"name": self.entry.title, "message": message},
            )
        except Exception:  # noqa: BLE001
            _LOGGER.debug("logbook.log unavailable")

    # ------------------------------------------------------------------
    # Rules
    # ------------------------------------------------------------------
    async def async_complete(self, task: str, raise_unknown: bool = True) -> None:
        """Register a completed chore."""
        mandatory, bonus = self.mandatory, self.bonus
        if task not in mandatory and task not in bonus:
            if raise_unknown:
                raise ServiceValidationError(f"Unknown chore: {task}")
            return

        notices: list[tuple[str, str, str]] = []
        async with self._lock:
            today = self._ensure_today()

            if task in mandatory:
                if task in today["mandatory_done"]:
                    return  # counted once per day
                today["mandatory_done"].append(task)
                award = int(mandatory[task])
                released = list(today["pending"])
                self.data["week"] = self.week + award
                self._record("chore", task, award)
                if not self.mandatory_remaining():
                    pending_sum = sum(p["points"] for p in released)
                    award = pending_sum
                    for p in released:
                        self.data["week_bonus"] = self.week_bonus + int(p["points"])
                        self._record("bonus_released", p["name"], int(p["points"]))
                    today["bonus_done"].extend(p["name"] for p in today["pending"])
                    today["pending"] = []
                    msg = self.tr("mandatory_done")
                    if pending_sum:
                        msg += self.tr("pending_released", n=pending_sum)
                    notices.append(
                        (CONF_NOTIFY_KID, self.tr("mandatory_done_title"), msg)
                    )
                else:
                    award = 0
                today["points"] += int(mandatory[task]) + award
            else:
                pts = int(bonus[task])
                remaining = self.mandatory_remaining()
                if not remaining:
                    self.data["week_bonus"] = self.week_bonus + pts
                    today["bonus_done"].append(task)
                    today["points"] += pts
                    self._record("bonus", task, pts)
                else:
                    today["pending"].append({"name": task, "points": pts})
                    self._record("pending", task, 0, pending=pts)
                    notices.append(
                        (
                            CONF_NOTIFY_KID,
                            self.tr("pending_title"),
                            self.tr(
                                "pending",
                                pts=pts,
                                task=task,
                                left=", ".join(remaining),
                            ),
                        )
                    )
            self._changed()

        for key, title, msg in notices:
            await self._notify(key, title, msg)

    async def async_redeem(self, reward: str, units: int = 1) -> None:
        rate = int(self.rewards.get(reward, 0))
        if rate <= 0:
            raise ServiceValidationError(f"Reward not configured: {reward}")
        cost = rate * units
        payout = int(self.payouts.get(reward, 0)) * units
        label = reward if units == 1 else f"{units} × {reward}"
        async with self._lock:
            bank = self.bank
            if bank < cost:
                short = True
            else:
                short = False
                self.data["bank"] = bank - cost
                if payout:
                    # money reward: nothing to hand out, it goes to the wallet
                    self.data["wallet"] = self.wallet + payout
                else:
                    self.reward_log.append(
                        {
                            "uid": uuid.uuid4().hex,
                            "summary": label,
                            "description": self.tr(
                                "redeemed_note",
                                when=f"{dt_util.now():%Y-%m-%d %H:%M}",
                                cost=cost,
                            ),
                            "done": False,
                        }
                    )
                self._record("redeem", label, -cost, "bank", amount=payout)
                self._changed()
        if short:
            await self._notify(
                CONF_NOTIFY_KID,
                self.tr("not_enough_title"),
                self.tr("not_enough", label=label, cost=cost, bank=bank),
            )
            raise ServiceValidationError("Not enough points in the bank")
        left = bank - cost
        if payout:
            money = {"amount": payout, "cur": self.currency, "wallet": self.wallet}
            await self._log(
                self.tr("cashout_log", label=label, cost=cost, left=left, **money)
            )
            await self._notify(
                CONF_NOTIFY_PARENTS,
                self.tr("cashout_parents_title"),
                self.tr("cashout_parents", label=label, cost=cost, left=left, **money),
            )
            await self._notify(
                CONF_NOTIFY_KID,
                self.tr("cashout_kid_title"),
                self.tr("cashout_kid", **money),
            )
            return
        await self._log(self.tr("redeemed_log", label=label, cost=cost, left=left))
        await self._notify(
            CONF_NOTIFY_PARENTS,
            self.tr("redeemed_parents_title"),
            self.tr("redeemed_parents", label=label, cost=cost, left=left),
        )
        await self._notify(
            CONF_NOTIFY_KID,
            self.tr("redeemed_kid_title"),
            self.tr("redeemed_kid", label=label, left=left),
        )

    async def async_adjust(self, target: str, points: int, reason: str | None) -> None:
        async with self._lock:
            key = "week" if target == "week" else "bank"
            before = int(self.data[key])
            self.data[key] = max(before + points, 0)
            self._record("adjust", reason or "", self.data[key] - before, key)
            self._changed()
        await self._log(
            self.tr(
                "adjust_log",
                target=self.tr("week" if target == "week" else "bank"),
                points=points,
                reason=reason or self.tr("no_reason"),
            )
        )

    async def async_adjust_wallet(self, amount: int, reason: str | None) -> None:
        """Parent adds money to / deducts money from the wallet (never below 0)."""
        async with self._lock:
            before = self.wallet
            self.data["wallet"] = max(before + amount, 0)
            self._record(
                "adjust", reason or "", 0, "wallet", amount=self.wallet - before
            )
            self._changed()
        await self._log(
            self.tr(
                "wallet_adjust_log",
                amount=amount,
                cur=self.currency,
                reason=reason or self.tr("no_reason"),
            )
        )

    async def async_close_week(self) -> None:
        async with self._lock:
            # the goal is measured on mandatory points only; bonus points are
            # banked in full if it is met and lost otherwise
            week, goal, bonus = self.week, self.goal, self.week_bonus
            met = week >= goal
            policy = self.opt(CONF_POLICY)
            if met:
                to_bank = week + int(self.opt(CONF_GOAL_BONUS)) + bonus
            elif policy == POLICY_HALF:
                to_bank = week // 2
            elif policy == POLICY_FORFEIT:
                to_bank = 0
            else:
                to_bank = week
            note = ""
            if bonus:
                note = self.tr("bonus_banked" if met else "bonus_lost", bonus=bonus)
            self.data["bank"] = self.bank + to_bank
            bank = self.bank
            self.data["week"] = 0
            self.data["week_bonus"] = 0
            self._record(
                "week_close",
                f"{week}/{goal} {'✓' if met else '✗'}"
                + (f" · ★{bonus}{'' if met else ' ✗'}" if bonus else ""),
                to_bank,
                "bank",
            )
            self.data["last_week"] = self.tr(
                "last_week",
                week=week,
                goal=goal,
                mark="✓" if met else "✗",
                to_bank=to_bank,
            ) + (f" · {note}" if note else "")
            self._changed()
        await self._log(self.tr("week_log", week=week, goal=goal, to_bank=to_bank))
        await self._notify(
            CONF_NOTIFY_KID,
            self.tr("week_met_title" if met else "week_over_title"),
            self.tr("week_kid", week=week, goal=goal, to_bank=to_bank, bank=bank)
            + (f" {note}" if note else ""),
        )
        await self._notify(
            CONF_NOTIFY_PARENTS,
            self.tr("week_parents_title"),
            self.tr(
                "week_parents",
                week=week,
                goal=goal,
                to_bank=to_bank,
                bank=bank,
                result=self.tr("goal_met" if met else "goal_missed"),
            )
            + (f" {note}" if note else ""),
        )

    # ------------------------------------------------------------------
    # Reward log (todo list) helpers
    # ------------------------------------------------------------------
    @callback
    def reward_log_changed(self) -> None:
        self._changed()
