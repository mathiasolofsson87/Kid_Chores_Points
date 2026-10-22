"""Config and options flow – chores, rewards and settings are edited in the UI."""

from __future__ import annotations

import copy
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TimeSelector,
)

from .const import (
    CONF_BEDTIME,
    CONF_BEDTIME_LEAD,
    CONF_BEDTIME_WEEKEND,
    CONF_BONUS,
    CONF_CHORE_IDS,
    CONF_CURRENCY,
    CONF_GOAL,
    CONF_GOAL_BONUS,
    CONF_HISTORY_LIMIT,
    CONF_KID_PERSONS,
    CONF_MANDATORY,
    CONF_MEDAL_RULES,
    CONF_MEDALS,
    CONF_MEDALS_GRACE,
    CONF_MEDALS_NOTIFY,
    CONF_NOTIFY_KID,
    CONF_NOTIFY_PARENTS,
    CONF_PARENT_PERSONS,
    CONF_POLICY,
    CONF_REWARD_PAYOUT,
    CONF_REWARDS,
    CONF_WEEK_START,
    DEFAULT_OPTIONS,
    DOMAIN,
    HISTORY_LIMIT_MAX,
    HISTORY_LIMIT_MIN,
    MEDAL_BONUS_MAX,
    MS_DOMAIN,
    POLICIES,
    WEEK_DAYS,
)
from .medals import AT_MAX, GROUPS, group_medals, medal_rules


def _points(max_: int = 5000) -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(min=0, max=max_, step=1, mode=NumberSelectorMode.BOX)
    )


def _ms_tasks(hass: HomeAssistant) -> dict[str, tuple[str, str]]:
    """Tasks defined in Maintenance Supporter: {task id: (name, label)}.

    Empty if it isn't installed.
    """
    tasks: dict[str, tuple[str, str]] = {}
    for entry in hass.config_entries.async_entries(MS_DOMAIN):
        obj = (entry.data.get("object") or {}).get("name")
        for task_id, task in (entry.data.get("tasks") or {}).items():
            if not isinstance(task, dict) or not (name := task.get("name")):
                continue
            tasks[task_id] = (name, f"{name} ({obj})" if obj else name)
    return tasks


def _ms_task_options(hass: HomeAssistant) -> list[SelectOptionDict]:
    """Task picker options; the value is the task id so renames don't matter."""
    return [
        SelectOptionDict(value=task_id, label=label)
        for task_id, (_, label) in sorted(
            _ms_tasks(hass).items(), key=lambda kv: kv[1][1].lower()
        )
    ]


class ChoresConfigFlow(ConfigFlow, domain=DOMAIN):
    """Initial setup: just a name. Everything else lives in the options flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            await self.async_set_unique_id(user_input["name"].strip().lower())
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input["name"].strip(),
                data={},
                options=copy.deepcopy(DEFAULT_OPTIONS),
            )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required("name", default="Chores & Points"): TextSelector()}
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return ChoresOptionsFlow()


class ChoresOptionsFlow(OptionsFlow):
    """Menu-driven editor. Each save is applied immediately."""

    def __init__(self) -> None:
        self._opts: dict[str, Any] = {}
        self._editing: str = ""  # reward being edited

    def _load(self) -> dict[str, Any]:
        if not self._opts:
            # deep copy: the nested dicts are edited in place and must not leak into
            # the entry's options (or the shared defaults) before they are saved
            self._opts = copy.deepcopy(
                {**DEFAULT_OPTIONS, **self.config_entry.options}
            )
        return self._opts

    def _save(self) -> None:
        self.hass.config_entries.async_update_entry(
            self.config_entry, options=dict(self._opts)
        )

    # ------------------------------------------------------------------
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        self._load()
        return self.async_show_menu(
            step_id="init",
            menu_options=[
                "mandatory",
                "bonus",
                "rewards",
                "settings",
                "medals",
                "bedtime",
                "notifications",
                "finish",
            ],
        )

    async def async_step_finish(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self.async_create_entry(data=dict(self._load()))

    # ------------------------------------------------------------------
    # General settings
    # ------------------------------------------------------------------
    async def async_step_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        opts = self._load()
        if user_input is not None:
            opts[CONF_GOAL] = int(user_input[CONF_GOAL])
            opts[CONF_GOAL_BONUS] = int(user_input[CONF_GOAL_BONUS])
            opts[CONF_POLICY] = user_input[CONF_POLICY]
            opts[CONF_WEEK_START] = user_input[CONF_WEEK_START]
            opts[CONF_CURRENCY] = user_input[CONF_CURRENCY].strip() or "kr"
            opts[CONF_HISTORY_LIMIT] = int(user_input[CONF_HISTORY_LIMIT])
            self._save()
            return await self.async_step_init()
        return self.async_show_form(
            step_id="settings",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_WEEK_START, default=opts[CONF_WEEK_START]
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=WEEK_DAYS,
                            translation_key=CONF_WEEK_START,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(CONF_GOAL, default=opts[CONF_GOAL]): _points(),
                    vol.Required(CONF_GOAL_BONUS, default=opts[CONF_GOAL_BONUS]): _points(
                        1000
                    ),
                    vol.Required(CONF_POLICY, default=opts[CONF_POLICY]): SelectSelector(
                        SelectSelectorConfig(
                            options=POLICIES,
                            translation_key=CONF_POLICY,
                            mode=SelectSelectorMode.LIST,
                        )
                    ),
                    vol.Required(
                        CONF_CURRENCY, default=opts[CONF_CURRENCY]
                    ): TextSelector(),
                    vol.Required(
                        CONF_HISTORY_LIMIT, default=opts[CONF_HISTORY_LIMIT]
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=HISTORY_LIMIT_MIN,
                            max=HISTORY_LIMIT_MAX,
                            step=10,
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
        )

    # ------------------------------------------------------------------
    # Streaks and medals
    # ------------------------------------------------------------------
    async def async_step_medals(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        self._load()
        return self.async_show_menu(
            step_id="medals",
            menu_options=["medals_settings", *(f"medals_{g}" for g in GROUPS), "init"],
        )

    async def async_step_medals_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        opts = self._load()
        if user_input is not None:
            for key in (CONF_MEDALS, CONF_MEDALS_GRACE, CONF_MEDALS_NOTIFY):
                opts[key] = bool(user_input.get(key, False))
            self._save()
            return await self.async_step_medals()
        return self.async_show_form(
            step_id="medals_settings",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MEDALS, default=opts[CONF_MEDALS]): BooleanSelector(),
                    vol.Required(
                        CONF_MEDALS_GRACE, default=opts[CONF_MEDALS_GRACE]
                    ): BooleanSelector(),
                    vol.Required(
                        CONF_MEDALS_NOTIFY, default=opts[CONF_MEDALS_NOTIFY]
                    ): BooleanSelector(),
                }
            ),
        )

    async def _medal_group(
        self, group: str, user_input: dict[str, Any] | None
    ) -> ConfigFlowResult:
        """One form with the target (and bonus) of each medal in a group."""
        opts = self._load()
        rules = medal_rules(opts[CONF_MEDAL_RULES])
        medals = group_medals(group)
        errors: dict[str, str] = {}
        if user_input is not None:
            targets = [int(user_input[f"{m.id}_at"]) for m in medals]
            if any(a >= b for a, b in zip(targets, targets[1:])):
                errors["base"] = "medal_order"  # each medal needs more than the one before
            else:
                for medal, at in zip(medals, targets):
                    own = {"at": at}
                    if medal.pays:
                        own["bonus"] = int(user_input[f"{medal.id}_bonus"])
                    opts[CONF_MEDAL_RULES][medal.id] = own
                self._save()
                return await self.async_step_medals()
        schema: dict[Any, Any] = {}
        for medal in medals:
            at, bonus = rules[medal.id]
            if user_input is not None:  # keep what was typed when the form is shown again
                at = user_input.get(f"{medal.id}_at", at)
                bonus = user_input.get(f"{medal.id}_bonus", bonus)
            schema[vol.Required(f"{medal.id}_at", default=at)] = NumberSelector(
                NumberSelectorConfig(
                    min=1, max=AT_MAX[group], step=1, mode=NumberSelectorMode.BOX
                )
            )
            if medal.pays:
                schema[vol.Required(f"{medal.id}_bonus", default=bonus)] = _points(
                    MEDAL_BONUS_MAX
                )
        return self.async_show_form(
            step_id=f"medals_{group}",
            data_schema=vol.Schema(schema),
            errors=errors,
        )

    async def async_step_medals_day(self, user_input=None) -> ConfigFlowResult:
        return await self._medal_group("day", user_input)

    async def async_step_medals_week(self, user_input=None) -> ConfigFlowResult:
        return await self._medal_group("week", user_input)

    async def async_step_medals_chores(self, user_input=None) -> ConfigFlowResult:
        return await self._medal_group("chores", user_input)

    async def async_step_medals_bonus(self, user_input=None) -> ConfigFlowResult:
        return await self._medal_group("bonus", user_input)

    async def async_step_bedtime(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        opts = self._load()
        errors: dict[str, str] = {}
        if user_input is not None:
            lead = int(user_input[CONF_BEDTIME_LEAD])
            times: dict[str, str] = {}
            for key in (CONF_BEDTIME, CONF_BEDTIME_WEEKEND):
                value = dt_util.parse_time(user_input.get(key) or "")
                times[key] = value.strftime("%H:%M") if value else ""
                # the reminder must fall on the same evening as the bedtime
                if value and value.hour * 60 + value.minute < lead:
                    errors[CONF_BEDTIME_LEAD] = "lead_too_long"
            if not errors:
                opts.update(times)
                opts[CONF_BEDTIME_LEAD] = lead
                self._save()
                return await self.async_step_init()
        return self.async_show_form(
            step_id="bedtime",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_BEDTIME,
                        description={"suggested_value": opts[CONF_BEDTIME] or None},
                    ): TimeSelector(),
                    vol.Optional(
                        CONF_BEDTIME_WEEKEND,
                        description={"suggested_value": opts[CONF_BEDTIME_WEEKEND] or None},
                    ): TimeSelector(),
                    vol.Required(
                        CONF_BEDTIME_LEAD, default=opts[CONF_BEDTIME_LEAD]
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=5, max=240, step=5, mode=NumberSelectorMode.BOX
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_notifications(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        opts = self._load()
        if user_input is not None:
            for key in (
                CONF_KID_PERSONS,
                CONF_PARENT_PERSONS,
                CONF_NOTIFY_KID,
                CONF_NOTIFY_PARENTS,
            ):
                opts[key] = user_input.get(key, [])
            self._save()
            return await self.async_step_init()
        services = sorted(
            s
            for s in self.hass.services.async_services().get("notify", {})
            if s not in ("send_message", "persistent_notification")
        )
        # keep already-saved targets selectable even if currently unavailable
        known = sorted(
            set(services) | set(opts[CONF_NOTIFY_KID]) | set(opts[CONF_NOTIFY_PARENTS])
        )

        def selector() -> SelectSelector:
            return SelectSelector(
                SelectSelectorConfig(
                    options=known,
                    multiple=True,
                    custom_value=True,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )

        person_selector = EntitySelector(
            EntitySelectorConfig(domain="person", multiple=True)
        )
        return self.async_show_form(
            step_id="notifications",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_KID_PERSONS, default=opts[CONF_KID_PERSONS]
                    ): person_selector,
                    vol.Optional(
                        CONF_PARENT_PERSONS, default=opts[CONF_PARENT_PERSONS]
                    ): person_selector,
                    vol.Optional(
                        CONF_NOTIFY_KID, default=opts[CONF_NOTIFY_KID]
                    ): selector(),
                    vol.Optional(
                        CONF_NOTIFY_PARENTS, default=opts[CONF_NOTIFY_PARENTS]
                    ): selector(),
                }
            ),
        )

    # ------------------------------------------------------------------
    # Generic "dictionary of name -> points" editors
    # ------------------------------------------------------------------
    def _menu(self, step_id: str, kind: str) -> ConfigFlowResult:
        options = [f"{kind}_add"]
        if self._load()[kind]:
            options.append(f"{kind}_edit")
        return self.async_show_menu(
            step_id=step_id,
            menu_options=[*options, f"{kind}_remove", "init"],
            description_placeholders={"items": self._describe(kind)},
        )

    def _describe(self, kind: str) -> str:
        opts = self._load()
        items = opts[kind]
        if not items:
            return "_(none yet)_"
        payouts = opts[CONF_REWARD_PAYOUT] if kind == CONF_REWARDS else {}
        cur = opts[CONF_CURRENCY]
        return "\n".join(
            f"- {name}: {pts} p"
            + (f" → {payouts[name]} {cur}" if payouts.get(name) else "")
            for name, pts in items.items()
        )

    def _name_selector(self, from_ms: bool) -> Any:
        """Free text, or a Maintenance Supporter task picker for chores."""
        if from_ms and (tasks := _ms_task_options(self.hass)):
            # custom_value keeps free-text names working too
            return SelectSelector(
                SelectSelectorConfig(
                    options=tasks,
                    custom_value=True,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
        return TextSelector()

    def _resolve(self, value: str, from_ms: bool) -> tuple[str, str | None]:
        """Turn the submitted name field into (chore name, linked task id).

        A task picked from the list is linked by id; a typed name is not.
        """
        value = str(value).strip()
        if from_ms and (task := _ms_tasks(self.hass).get(value)):
            return task[0], value
        return value, None

    def _link(self, name: str, task_id: str | None) -> None:
        """Remember (or forget) which Maintenance Supporter task a chore is."""
        ids = self._load()[CONF_CHORE_IDS]
        if task_id:
            ids[name] = task_id
        else:
            ids.pop(name, None)

    async def _add(
        self,
        kind: str,
        step_id: str,
        user_input: dict[str, Any] | None,
        from_ms: bool = False,
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            name, task_id = self._resolve(user_input["name"], from_ms)
            if name in self._load()[kind]:
                # never overwrite silently: existing items are changed via Edit
                errors["name"] = "name_exists"
            elif name:
                opts = self._load()
                opts[kind][name] = int(user_input["points"])
                if from_ms:
                    self._link(name, task_id)
                if kind == CONF_REWARDS:
                    # 0 = a normal reward, > 0 = pays that much into the wallet
                    if payout := int(user_input.get("payout", 0)):
                        opts[CONF_REWARD_PAYOUT][name] = payout
                    else:
                        opts[CONF_REWARD_PAYOUT].pop(name, None)
                self._save()
            if not errors:
                return await getattr(self, f"async_step_{kind}")()
        name_selector = self._name_selector(from_ms)
        schema: dict[Any, Any] = {
            vol.Required("name"): name_selector,
            vol.Required("points", default=1): _points(1000),
        }
        if kind == CONF_REWARDS:
            schema[vol.Optional("payout", default=0)] = _points(10000)
        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema(schema),
            errors=errors,
            description_placeholders={"currency": self._load()[CONF_CURRENCY]},
        )

    async def _edit_pick(
        self, kind: str, step_id: str, user_input: dict[str, Any] | None
    ) -> ConfigFlowResult:
        """Pick which item to edit."""
        items = self._load()[kind]
        if user_input is not None:
            self._editing = user_input["name"]
            return await getattr(self, f"async_step_{kind}_edit_item")()
        if not items:
            return await getattr(self, f"async_step_{kind}")()
        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema(
                {
                    vol.Required("name"): SelectSelector(
                        SelectSelectorConfig(
                            options=list(items), mode=SelectSelectorMode.DROPDOWN
                        )
                    )
                }
            ),
        )

    async def _edit_item(
        self,
        kind: str,
        step_id: str,
        user_input: dict[str, Any] | None,
        from_ms: bool = False,
    ) -> ConfigFlowResult:
        """Edit the picked item; the form starts with its current values."""
        opts = self._load()
        items, payouts = opts[kind], opts[CONF_REWARD_PAYOUT]
        rewards = kind == CONF_REWARDS
        old = self._editing
        if old not in items:
            return await getattr(self, f"async_step_{kind}")()
        errors: dict[str, str] = {}
        linked = opts[CONF_CHORE_IDS].get(old) if from_ms else None
        shown = linked if linked in _ms_tasks(self.hass) else old
        current = {"name": shown, "points": items[old], "payout": payouts.get(old, 0)}
        if user_input is not None:
            current = {**current, **user_input}
            if user_input["name"] == shown:
                new, task_id = old, linked  # name field untouched: keep chore and link
            else:
                new, task_id = self._resolve(user_input["name"], from_ms)
                new = new or old
            if new != old and new in items:
                errors["name"] = "name_exists"
            else:
                points = int(user_input["points"])
                # rebuild so a renamed item keeps its place in the list
                opts[kind] = {
                    (new if k == old else k): (points if k == old else v)
                    for k, v in items.items()
                }
                if rewards:
                    payouts.pop(old, None)
                    if payout := int(user_input.get("payout", 0)):
                        payouts[new] = payout
                if from_ms:
                    opts[CONF_CHORE_IDS].pop(old, None)
                    self._link(new, task_id)
                self._editing = ""
                self._save()
                return await getattr(self, f"async_step_{kind}")()
        schema: dict[Any, Any] = {
            vol.Required("name", default=current["name"]): self._name_selector(from_ms),
            vol.Required("points", default=current["points"]): _points(1000),
        }
        if rewards:
            schema[vol.Optional("payout", default=current["payout"])] = _points(10000)
        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema(schema),
            errors=errors,
            description_placeholders={"currency": opts[CONF_CURRENCY]},
        )

    async def _remove(
        self, kind: str, step_id: str, user_input: dict[str, Any] | None
    ) -> ConfigFlowResult:
        items = self._load()[kind]
        if user_input is not None:
            for name in user_input.get("names", []):
                items.pop(name, None)
                if kind != CONF_REWARDS:
                    self._load()[CONF_CHORE_IDS].pop(name, None)
            self._save()
            return await getattr(self, f"async_step_{kind}")()
        if not items:
            return await getattr(self, f"async_step_{kind}")()
        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema(
                {
                    vol.Required("names"): SelectSelector(
                        SelectSelectorConfig(
                            options=list(items), multiple=True, mode=SelectSelectorMode.LIST
                        )
                    )
                }
            ),
        )

    # Mandatory chores
    async def async_step_mandatory(self, user_input=None) -> ConfigFlowResult:
        return self._menu("mandatory", CONF_MANDATORY)

    async def async_step_mandatory_add(self, user_input=None) -> ConfigFlowResult:
        return await self._add(CONF_MANDATORY, "mandatory_add", user_input, True)

    async def async_step_mandatory_edit(self, user_input=None) -> ConfigFlowResult:
        return await self._edit_pick(CONF_MANDATORY, "mandatory_edit", user_input)

    async def async_step_mandatory_edit_item(self, user_input=None) -> ConfigFlowResult:
        return await self._edit_item(CONF_MANDATORY, "mandatory_edit_item", user_input, True)

    async def async_step_mandatory_remove(self, user_input=None) -> ConfigFlowResult:
        return await self._remove(CONF_MANDATORY, "mandatory_remove", user_input)

    # Bonus chores
    async def async_step_bonus(self, user_input=None) -> ConfigFlowResult:
        return self._menu("bonus", CONF_BONUS)

    async def async_step_bonus_add(self, user_input=None) -> ConfigFlowResult:
        return await self._add(CONF_BONUS, "bonus_add", user_input, True)

    async def async_step_bonus_edit(self, user_input=None) -> ConfigFlowResult:
        return await self._edit_pick(CONF_BONUS, "bonus_edit", user_input)

    async def async_step_bonus_edit_item(self, user_input=None) -> ConfigFlowResult:
        return await self._edit_item(CONF_BONUS, "bonus_edit_item", user_input, True)

    async def async_step_bonus_remove(self, user_input=None) -> ConfigFlowResult:
        return await self._remove(CONF_BONUS, "bonus_remove", user_input)

    # Rewards
    async def async_step_rewards(self, user_input=None) -> ConfigFlowResult:
        return self._menu("rewards", CONF_REWARDS)

    async def async_step_rewards_add(self, user_input=None) -> ConfigFlowResult:
        return await self._add(CONF_REWARDS, "rewards_add", user_input)

    async def async_step_rewards_edit(self, user_input=None) -> ConfigFlowResult:
        return await self._edit_pick(CONF_REWARDS, "rewards_edit", user_input)

    async def async_step_rewards_edit_item(self, user_input=None) -> ConfigFlowResult:
        return await self._edit_item(CONF_REWARDS, "rewards_edit_item", user_input)

    async def async_step_rewards_remove(self, user_input=None) -> ConfigFlowResult:
        if user_input is not None:
            for name in user_input.get("names", []):
                self._load()[CONF_REWARD_PAYOUT].pop(name, None)
        return await self._remove(CONF_REWARDS, "rewards_remove", user_input)
