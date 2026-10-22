"""Points engine for Kid Chores & Points."""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import date, time, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util, slugify

from .medals import (
    BONUS,
    CHORES,
    COUNTER,
    COUNTERS,
    DAY,
    MEDALS,
    TREAT,
    WEEK,
    Medal,
    group_medals,
    medal_rules,
)
from .messages import translate
from .const import (
    CONF_BEDTIME,
    CONF_BEDTIME_LEAD,
    CONF_BEDTIME_WEEKEND,
    CONF_BONUS,
    CONF_CHORE_IDS,
    CONF_GOAL,
    CONF_GOAL_BONUS,
    CONF_KID_PERSONS,
    CONF_MANDATORY,
    CONF_MEDAL_RULES,
    CONF_MEDALS,
    CONF_MEDALS_GRACE,
    CONF_MEDALS_NOTIFY,
    CONF_CURRENCY,
    CONF_HISTORY_LIMIT,
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
    PERFECT_DAYS_KEPT,
    POLICY_FORFEIT,
    POLICY_HALF,
    SIGNAL_UPDATE,
    WEEK_DAYS,
    WEEKEND_NIGHTS,
)

_LOGGER = logging.getLogger(__name__)

REVERTABLE = {"chore", "bonus", "pending", "redeem", "adjust"}


def _empty_today(date: str = "") -> dict[str, Any]:
    return {
        "date": date,
        "mandatory_done": [],
        "bonus_done": [],
        "pending": [],  # [{"name": str, "points": int}]
        "points": 0,
    }


def _empty_medals() -> dict[str, Any]:
    return {
        "perfect_days": [],  # dates (ISO) with every mandatory chore done
        "week_streak": 0,  # weeks in a row with the goal reached
        "best_day": 0,
        "best_week": 0,
        "chores_done": 0,
        "bonus_done": 0,
        "treats": 0,  # rewards handed out
        "earned": {},  # {medal id: {"date": ISO date}}
    }


class ChoresManager:
    """Holds state and implements the point rules for one config entry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._store: Store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}")
        self._lock = asyncio.Lock()
        self.data: dict[str, Any] = {}
        self._prev: dict[str, int] = {}
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
    def chore_ids(self) -> dict[str, str]:
        """Chores linked to a Maintenance Supporter task: {chore: task id}."""
        return self.opt(CONF_CHORE_IDS)

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
            "week_no": 0,  # counts closed weeks; a change is only revertable within its week
            "bedtime_sent": "",  # date of the last bedtime reminder
            **stored,
        }
        self.data.pop("undo", None)  # snapshots of the old latest-only undo
        self.data["medals"] = {**_empty_medals(), **self.data.get("medals", {})}
        self._prev = self._totals()
        # Baseline for the missed-week-close catch-up: without it an upgrade (or a
        # changed first day of the week) would close the running week right away.
        week_start = self.opt(CONF_WEEK_START)
        if "last_close" not in stored or stored.get("close_ref") != week_start:
            self.data["last_close"] = self._due_close_date().isoformat()
            self.data["close_ref"] = week_start

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

    def _totals(self) -> dict[str, int]:
        return {
            "week": self.week,
            "week_bonus": self.week_bonus,
            "bank": self.bank,
            "wallet": self.wallet,
            **{counter: int(self.medal_data[counter]) for counter in COUNTERS},
        }

    def can_revert(self, entry: dict[str, Any]) -> bool:
        """Whether a history entry can be reverted (the first entry of a change, once)."""
        if entry.get("id") is None or entry["id"] != entry.get("group"):
            return False
        if entry.get("reverted") or entry["type"] not in REVERTABLE:
            return False
        # a closed week can't be reopened
        return not (entry["dw"] or entry["dwb"]) or entry["wk"] == self.data["week_no"]

    @property
    def undo_label(self) -> str | None:
        """What `undo` would revert (the latest revertable change), or None."""
        for entry in reversed(self.history):
            if self.can_revert(entry):
                return entry["label"]
        return None

    # ------------------------------------------------------------------
    # Streaks and medals
    # ------------------------------------------------------------------
    @property
    def medals_on(self) -> bool:
        return bool(self.opt(CONF_MEDALS))

    @property
    def medal_data(self) -> dict[str, Any]:
        return self.data["medals"]

    def medal_rules(self) -> dict[str, tuple[int, int]]:
        """{medal id: (target, bonus)} including the parent's changes."""
        return medal_rules(self.opt(CONF_MEDAL_RULES))

    def _bump(self, counter: str, by: int = 1) -> None:
        """Count progress towards the medals (only while they are switched on)."""
        if self.medals_on:
            self.medal_data[counter] += by

    def _week_key(self, day: date) -> int:
        """A number that is the same for all days of one (configured) week."""
        start = WEEK_DAYS.index(self.opt(CONF_WEEK_START))
        return (day.toordinal() - 1 - start) // 7

    def day_streak(self) -> int:
        """Days in a row with every mandatory chore done, up to today.

        Today doesn't break the streak until it is over, so a streak that ran
        through yesterday still counts. With the grace option, one missed day
        per week is forgiven (it is bridged, not counted).
        """
        if not self.medals_on:
            return 0
        days = {date.fromisoformat(d) for d in self.medal_data["perfect_days"]}
        if not days:
            return 0
        today = dt_util.now().date()
        day = today if today in days else today - timedelta(days=1)
        first, grace, used, streak = min(days), bool(self.opt(CONF_MEDALS_GRACE)), set(), 0
        while day >= first:
            if day in days:
                streak += 1
            elif grace and (week := self._week_key(day)) not in used:
                used.add(week)
            else:
                break
            day -= timedelta(days=1)
        return streak

    def streak_at_risk(self) -> bool:
        """A running day streak that today's chores still have to extend."""
        today = dt_util.now().date().isoformat()
        return (
            self.medals_on
            and today not in self.medal_data["perfect_days"]
            and self.day_streak() > 0
        )

    def _mark_perfect_day(self) -> None:
        """Today has every mandatory chore done."""
        if not self.medals_on or not self.mandatory:
            return
        days = self.medal_data["perfect_days"]
        today = dt_util.now().date().isoformat()
        if today not in days:
            days.append(today)
            days.sort()
            del days[:-PERFECT_DAYS_KEPT]
        self.medal_data["best_day"] = max(self.medal_data["best_day"], self.day_streak())

    def _progress(self, kind: str) -> int:
        if kind == DAY:
            return self.day_streak()
        if kind == WEEK:
            return int(self.medal_data["week_streak"])
        return int(self.medal_data[COUNTER[kind]])

    def _award_medals(
        self, kinds: set[str], group: str, notices: list[tuple[str, str, str]]
    ) -> None:
        """Hand out the medals of `kinds` that were just reached (under the lock).

        Each medal is earned once. Its bonus goes straight to the bank and is
        recorded in the history `group` of the change that earned it, so
        reverting that change takes the medal and its bonus back.
        """
        if not self.medals_on:
            return
        earned = self.medal_data["earned"]
        rules = self.medal_rules()
        today = dt_util.now().date().isoformat()
        for medal in MEDALS:
            if medal.kind not in kinds or medal.id in earned:
                continue
            at, bonus = rules[medal.id]
            if self._progress(medal.kind) < at:
                continue
            earned[medal.id] = {"date": today}
            self.data["bank"] = self.bank + bonus
            name = self.tr(f"medal_{medal.id}")
            self._record("medal", name, bonus, "bank", group=group, medal=medal.id)
            notices.extend(self._medal_notices(medal, at, bonus, name))

    def _medal_notices(
        self, medal: Medal, at: int, bonus: int, name: str
    ) -> list[tuple[str, str, str]]:
        how = self.tr(f"how_{medal.kind}", n=at)
        notices = [("log", "", self.tr("medal_log", name=name))]
        if self.opt(CONF_MEDALS_NOTIFY):
            extra = self.tr("medal_bonus", bonus=bonus) if bonus else ""
            notices += [
                (
                    CONF_NOTIFY_KID,
                    self.tr("medal_title"),
                    self.tr("medal_kid", name=name, how=how) + extra,
                ),
                (
                    CONF_NOTIFY_PARENTS,
                    self.tr("medal_parents_title"),
                    self.tr("medal_parents", name=name, how=how) + extra,
                ),
            ]
        return notices

    def next_medal(self, kind: str) -> dict[str, Any] | None:
        """The next medal of a group that isn't earned yet, and how far off it is."""
        earned, rules = self.medal_data["earned"], self.medal_rules()
        for medal in group_medals(kind):
            if medal.id not in earned:
                at = rules[medal.id][0]
                return {
                    "id": medal.id,
                    "name": self.tr(f"medal_{medal.id}"),
                    "at": at,
                    "remaining": max(at - self._progress(kind), 0),
                }
        return None

    def _medal_available(self, medal: Medal) -> bool:
        """Whether a medal makes sense for this setup (e.g. no wallet medals without a wallet)."""
        md = self.medal_data
        if medal.kind == BONUS:
            return bool(self.bonus) or md["bonus_done"] > 0
        if medal.kind == TREAT:
            return any(r not in self.payouts for r in self.rewards) or md["treats"] > 0
        return True

    def medal_list(self) -> list[dict[str, Any]]:
        """Every medal with its name, target, bonus, progress and when it was earned."""
        earned, rules = self.medal_data["earned"], self.medal_rules()
        out: list[dict[str, Any]] = []
        for medal in MEDALS:
            at, bonus = rules[medal.id]
            got = earned.get(medal.id)
            out.append(
                {
                    "id": medal.id,
                    "kind": medal.kind,
                    "tier": medal.tier,
                    "name": self.tr(f"medal_{medal.id}"),
                    "how": self.tr(f"how_{medal.kind}", n=at),
                    "at": at,
                    "bonus": bonus,
                    "earned": got["date"] if got else None,
                    "progress": at if got else min(self._progress(medal.kind), at),
                    "available": bool(got) or self._medal_available(medal),
                }
            )
        return out

    def _due_close_date(self) -> date:
        """The most recent date whose week-close time (23:59) has already passed."""
        now = dt_util.now()
        close_day = (WEEK_DAYS.index(self.opt(CONF_WEEK_START)) - 1) % 7
        for back in range(8):
            day = (now - timedelta(days=back)).date()
            if day.weekday() == close_day and (back or (now.hour, now.minute) >= (23, 59)):
                return day
        raise AssertionError("unreachable: every weekday occurs within 7 days")

    def _record(
        self,
        kind: str,
        label: str,
        points: int,
        target: str = "week",
        pending: int = 0,
        amount: int = 0,
        entry_id: str | None = None,
        group: str | None = None,
        **extra: Any,
    ) -> None:
        """Append a points/wallet change to the history (call after updating totals).

        `amount` is the change in wallet money (not points). Entries of one change
        (a chore and the bonus it releases) share a `group`; the entry whose id is the
        group id is the one that can be reverted. The `d*` fields are what the entry
        changed in the totals, so it can be reverted later.
        """
        now = self._totals()
        entry_id = entry_id or uuid.uuid4().hex[:12]
        dm = {c: now[c] - self._prev[c] for c in COUNTERS if now[c] != self._prev[c]}
        self.history.append(
            {
                "id": entry_id,
                "group": group or entry_id,
                "day": dt_util.now().date().isoformat(),
                "wk": self.data["week_no"],
                "dw": now["week"] - self._prev["week"],
                "dwb": now["week_bonus"] - self._prev["week_bonus"],
                "db": now["bank"] - self._prev["bank"],
                "dwal": now["wallet"] - self._prev["wallet"],
                **({"dm": dm} if dm else {}),  # medal counters this entry changed
                **extra,
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
        self._prev = now
        del self.history[: -int(self.opt(CONF_HISTORY_LIMIT))]

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
        if self.opt(CONF_BEDTIME) or self.opt(CONF_BEDTIME_WEEKEND):
            self.entry.async_on_unload(
                async_track_time_change(self.hass, self._on_minute, second=0)
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

    def _chore_for_event(self, data: Any) -> str | None:
        """The chore a completed Maintenance Supporter task belongs to.

        A chore linked to a task id keeps working when the task is renamed;
        chores without a link (or typed by hand) match on the task name.
        """
        if task_id := data.get("task_id"):
            for chore, linked in self.chore_ids.items():
                if linked == task_id and (chore in self.mandatory or chore in self.bonus):
                    return chore
        return data.get("task_name") or None

    async def _on_event(self, event: Event) -> None:
        name = self._chore_for_event(event.data)
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
        today = dt_util.as_local(now).date()
        if today.weekday() == (start - 1) % 7 and self.data["last_close"] != today.isoformat():
            await self.async_close_week(today)

    def bedtime_reminder_time(self, day: date) -> time | None:
        """When the bedtime reminder goes out on `day`, or None if there is none."""
        weekend = self.opt(CONF_BEDTIME_WEEKEND) if day.weekday() in WEEKEND_NIGHTS else ""
        bedtime = dt_util.parse_time(weekend or self.opt(CONF_BEDTIME) or "")
        if bedtime is None:
            return None
        minutes = bedtime.hour * 60 + bedtime.minute - int(self.opt(CONF_BEDTIME_LEAD))
        if minutes < 0:  # would be the evening before; the options flow refuses this
            return None
        return time(minutes // 60, minutes % 60)

    async def _on_minute(self, now: Any) -> None:
        now = dt_util.as_local(now)
        at = self.bedtime_reminder_time(now.date())
        if at is not None and (now.hour, now.minute) == (at.hour, at.minute):
            await self.async_bedtime_reminder()

    async def async_bedtime_reminder(self) -> None:
        """Tell the child which mandatory chores are still open (once per day)."""
        async with self._lock:
            today = dt_util.now().date().isoformat()
            remaining = self.mandatory_remaining()
            if self.data["bedtime_sent"] == today or not remaining:
                return
            self.data["bedtime_sent"] = today
            self._store.async_delay_save(lambda: self.data, 1)
        items = [f"{name} (+{self.mandatory[name]} p)" for name in remaining]
        if len(items) == 1:
            message = self.tr("bedtime_one", left=items[0])
        else:
            message = self.tr(
                "bedtime_many", n=len(items), left="\n".join(f"• {i}" for i in items)
            )
        if self.medals_on and (streak := self.day_streak()):
            message += "\n" + self.tr("streak_risk", n=streak)
        await self._notify(CONF_NOTIFY_KID, self.tr("bedtime_title"), message)

    async def async_catch_up(self) -> None:
        """Close a week whose 23:59 close was missed (Home Assistant was down)."""
        due = self._due_close_date()
        if due.isoformat() > self.data["last_close"]:
            _LOGGER.info("Closing the week that ended %s (missed while offline)", due)
            await self.async_close_week(due)

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

    async def _send(self, notices: list[tuple[str, str, str]]) -> None:
        """Deliver collected notices: notify targets, or "log" for the logbook."""
        for key, title, message in notices:
            if key == "log":
                await self._log(message)
            else:
                await self._notify(key, title, message)

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

            if task in mandatory and task in today["mandatory_done"]:
                return  # counted once per day
            group = uuid.uuid4().hex[:12]  # the chore and any bonus it releases
            if task in mandatory:
                today["mandatory_done"].append(task)
                award = int(mandatory[task])
                released = list(today["pending"])
                self.data["week"] = self.week + award
                kinds = {CHORES}
                self._bump("chores_done")
                self._record("chore", task, award, entry_id=group)
                if not self.mandatory_remaining():
                    pending_sum = sum(p["points"] for p in released)
                    award = pending_sum
                    kinds |= {DAY, BONUS} if released else {DAY}
                    self._mark_perfect_day()
                    for p in released:
                        self.data["week_bonus"] = self.week_bonus + int(p["points"])
                        self._bump("chores_done")
                        self._bump("bonus_done")
                        self._record(
                            "bonus_released", p["name"], int(p["points"]), group=group
                        )
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
                kinds = set()
                pts = int(bonus[task])
                remaining = self.mandatory_remaining()
                if not remaining:
                    self.data["week_bonus"] = self.week_bonus + pts
                    today["bonus_done"].append(task)
                    today["points"] += pts
                    kinds = {CHORES, BONUS}
                    self._bump("chores_done")
                    self._bump("bonus_done")
                    self._record("bonus", task, pts, entry_id=group)
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
            self._award_medals(kinds, group, notices)
            self._changed()

        await self._send(notices)

    async def async_redeem(self, reward: str, units: int = 1) -> None:
        rate = int(self.rewards.get(reward, 0))
        if rate <= 0:
            raise ServiceValidationError(f"Reward not configured: {reward}")
        cost = rate * units
        payout = int(self.payouts.get(reward, 0)) * units
        label = reward if units == 1 else f"{units} × {reward}"
        notices: list[tuple[str, str, str]] = []
        group = uuid.uuid4().hex[:12]
        async with self._lock:
            bank = self.bank
            if bank < cost:
                short = True
            else:
                short = False
                reward_uid = None
                self.data["bank"] = bank - cost
                if payout:
                    # money reward: nothing to hand out, it goes to the wallet
                    self.data["wallet"] = self.wallet + payout
                else:
                    self._bump("treats", units)
                    reward_uid = uuid.uuid4().hex
                    self.reward_log.append(
                        {
                            "uid": reward_uid,
                            "summary": label,
                            "description": self.tr(
                                "redeemed_note",
                                when=f"{dt_util.now():%Y-%m-%d %H:%M}",
                                cost=cost,
                            ),
                            "done": False,
                        }
                    )
                self._record(
                    "redeem",
                    label,
                    -cost,
                    "bank",
                    amount=payout,
                    reward_uid=reward_uid,
                    entry_id=group,
                )
                self._award_medals({TREAT}, group, notices)
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
            await self._send(notices)
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
        await self._send(notices)

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

    async def async_close_week(self, scheduled: date | None = None) -> None:
        """Close the week. `scheduled` is the date of the regular 23:59 close it stands in for."""
        notices: list[tuple[str, str, str]] = []
        group = uuid.uuid4().hex[:12]
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
            self.data["week_no"] += 1  # a closed week can't be reopened
            if scheduled:
                self.data["last_close"] = scheduled.isoformat()
            self._record(
                "week_close",
                f"{week}/{goal} {'✓' if met else '✗'}"
                + (f" · ★{bonus}{'' if met else ' ✗'}" if bonus else ""),
                to_bank,
                "bank",
                entry_id=group,
            )
            if self.medals_on:
                md = self.medal_data
                md["week_streak"] = md["week_streak"] + 1 if met else 0
                md["best_week"] = max(md["best_week"], md["week_streak"])
                self._award_medals({WEEK}, group, notices)
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
        await self._send(notices)

    async def async_undo(self) -> None:
        """Revert the most recent change that can still be reverted."""
        for entry in reversed(self.history):
            if self.can_revert(entry):
                await self.async_revert(entry["id"])
                return
        raise ServiceValidationError("Nothing to undo")

    def _revert_today(self, entry: dict[str, Any]) -> None:
        """Take a reverted change out of today's chore lists (if it was made today)."""
        today = self.data["today"]
        if entry["day"] != today["date"]:
            return
        kind, name = entry["type"], entry["label"]
        if kind == "chore" and name in today["mandatory_done"]:
            today["mandatory_done"].remove(name)
        elif kind in ("bonus", "bonus_released") and name in today["bonus_done"]:
            today["bonus_done"].remove(name)
        if kind == "bonus_released":
            today["pending"].append({"name": name, "points": entry["points"]})
        elif kind == "pending":
            for held in today["pending"]:
                if held["name"] == name:
                    today["pending"].remove(held)
                    break
        if kind in ("chore", "bonus", "bonus_released"):
            today["points"] = max(today["points"] - entry["points"], 0)

    async def async_revert(self, entry_id: str) -> None:
        """Revert one change from the history, whenever it was made."""
        async with self._lock:
            entry = next((e for e in self.history if e.get("id") == entry_id), None)
            if entry is None:
                raise ServiceValidationError("Unknown history entry")
            if entry.get("reverted"):
                raise ServiceValidationError("Already reverted")
            if not self.can_revert(entry):
                raise ServiceValidationError("This change can no longer be reverted")
            members = [e for e in self.history if e.get("group") == entry["group"]]
            before = self._totals()
            for key, delta in (
                ("week", "dw"),
                ("week_bonus", "dwb"),
                ("bank", "db"),
                ("wallet", "dwal"),
            ):
                # never below zero, e.g. when the money was already spent
                self.data[key] = max(self.data[key] - sum(e[delta] for e in members), 0)
            md = self.medal_data
            for counter in COUNTERS:
                taken = sum(e.get("dm", {}).get(counter, 0) for e in members)
                md[counter] = max(md[counter] - taken, 0)
            for e in reversed(members):
                self._revert_today(e)
                e["reverted"] = True
                if medal := e.get("medal"):
                    md["earned"].pop(medal, None)
                if e["type"] == "chore" and e["day"] in md["perfect_days"]:
                    md["perfect_days"].remove(e["day"])  # that day is no longer perfect
            if uid := entry.get("reward_uid"):
                self.data["reward_log"] = [
                    r for r in self.reward_log if r["uid"] != uid
                ]
            label = entry["label"] or self.tr("adjust_undo_label")
            bank_diff = self.bank - before["bank"]
            wallet_diff = self.wallet - before["wallet"]
            if bank_diff:
                target, points = "bank", bank_diff
            elif wallet_diff:
                target, points = "wallet", 0
            else:
                target, points = "week", self.week - before["week"]
            self._record("undo", label, points, target, amount=wallet_diff)
            self._changed()
        await self._log(self.tr("undo_log", label=label))
        await self._notify(
            CONF_NOTIFY_PARENTS,
            self.tr("undo_parents_title"),
            self.tr("undo_parents", label=label, bank=self.bank),
        )

    # ------------------------------------------------------------------
    # Reward log (todo list) helpers
    # ------------------------------------------------------------------
    @callback
    def reward_log_changed(self) -> None:
        self._changed()
