"""Config and options flow – chores, rewards and settings are edited in the UI."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.selector import (
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
)

from .const import (
    CONF_BONUS,
    CONF_GOAL,
    CONF_GOAL_BONUS,
    CONF_KID_PERSONS,
    CONF_MANDATORY,
    CONF_NOTIFY_KID,
    CONF_NOTIFY_PARENTS,
    CONF_PARENT_PERSONS,
    CONF_POLICY,
    CONF_REWARDS,
    CONF_WEEK_START,
    DEFAULT_OPTIONS,
    DOMAIN,
    MS_DOMAIN,
    POLICIES,
    WEEK_DAYS,
)


def _points(max_: int = 5000) -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(min=0, max=max_, step=1, mode=NumberSelectorMode.BOX)
    )


def _ms_task_options(hass: HomeAssistant) -> list[SelectOptionDict]:
    """Tasks defined in Maintenance Supporter (empty if it isn't installed)."""
    options: dict[str, str] = {}
    for entry in hass.config_entries.async_entries(MS_DOMAIN):
        obj = (entry.data.get("object") or {}).get("name")
        for task in (entry.data.get("tasks") or {}).values():
            if not isinstance(task, dict) or not (name := task.get("name")):
                continue
            options.setdefault(name, f"{name} ({obj})" if obj else name)
    return [
        SelectOptionDict(value=name, label=label)
        for name, label in sorted(options.items(), key=lambda kv: kv[1].lower())
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
                title=user_input["name"].strip(), data={}, options=DEFAULT_OPTIONS
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

    def _load(self) -> dict[str, Any]:
        if not self._opts:
            self._opts = {**DEFAULT_OPTIONS, **self.config_entry.options}
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
                }
            ),
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
        return self.async_show_menu(
            step_id=step_id,
            menu_options=[f"{kind}_add", f"{kind}_remove", "init"],
            description_placeholders={"items": self._describe(kind)},
        )

    def _describe(self, kind: str) -> str:
        items = self._load()[kind]
        if not items:
            return "_(none yet)_"
        return "\n".join(f"- {name}: {pts} p" for name, pts in items.items())

    async def _add(
        self,
        kind: str,
        step_id: str,
        user_input: dict[str, Any] | None,
        from_ms: bool = False,
    ) -> ConfigFlowResult:
        if user_input is not None:
            name = user_input["name"].strip()
            if name:
                self._load()[kind][name] = int(user_input["points"])
                self._save()
            return await getattr(self, f"async_step_{kind}")()
        name_selector: Any = TextSelector()
        if from_ms and (tasks := _ms_task_options(self.hass)):
            # custom_value keeps free-text names working too
            name_selector = SelectSelector(
                SelectSelectorConfig(
                    options=tasks,
                    custom_value=True,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema(
                {
                    vol.Required("name"): name_selector,
                    vol.Required("points", default=1): _points(1000),
                }
            ),
        )

    async def _remove(
        self, kind: str, step_id: str, user_input: dict[str, Any] | None
    ) -> ConfigFlowResult:
        items = self._load()[kind]
        if user_input is not None:
            for name in user_input.get("names", []):
                items.pop(name, None)
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

    async def async_step_mandatory_remove(self, user_input=None) -> ConfigFlowResult:
        return await self._remove(CONF_MANDATORY, "mandatory_remove", user_input)

    # Bonus chores
    async def async_step_bonus(self, user_input=None) -> ConfigFlowResult:
        return self._menu("bonus", CONF_BONUS)

    async def async_step_bonus_add(self, user_input=None) -> ConfigFlowResult:
        return await self._add(CONF_BONUS, "bonus_add", user_input, True)

    async def async_step_bonus_remove(self, user_input=None) -> ConfigFlowResult:
        return await self._remove(CONF_BONUS, "bonus_remove", user_input)

    # Rewards
    async def async_step_rewards(self, user_input=None) -> ConfigFlowResult:
        return self._menu("rewards", CONF_REWARDS)

    async def async_step_rewards_add(self, user_input=None) -> ConfigFlowResult:
        return await self._add(CONF_REWARDS, "rewards_add", user_input)

    async def async_step_rewards_remove(self, user_input=None) -> ConfigFlowResult:
        return await self._remove(CONF_REWARDS, "rewards_remove", user_input)
