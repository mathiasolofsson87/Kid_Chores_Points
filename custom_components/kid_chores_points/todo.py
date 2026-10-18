"""To-do list holding redeemed rewards for a parent to hand out."""

from __future__ import annotations

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import ChoresEntity
from .manager import ChoresManager


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([RewardsTodo(entry.runtime_data)])


class RewardsTodo(ChoresEntity, TodoListEntity):
    _attr_name = "Redeemed rewards"
    _attr_icon = "mdi:gift-open"
    _attr_supported_features = (
        TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
        | TodoListEntityFeature.SET_DESCRIPTION_ON_ITEM
    )

    def __init__(self, manager: ChoresManager) -> None:
        super().__init__(manager, "rewards_todo")

    @property
    def todo_items(self) -> list[TodoItem]:
        return [
            TodoItem(
                uid=i["uid"],
                summary=i["summary"],
                description=i.get("description"),
                status=TodoItemStatus.COMPLETED if i["done"] else TodoItemStatus.NEEDS_ACTION,
            )
            for i in self.manager.reward_log
        ]

    async def async_update_todo_item(self, item: TodoItem) -> None:
        for i in self.manager.reward_log:
            if i["uid"] == item.uid:
                i["summary"] = item.summary or i["summary"]
                i["description"] = item.description
                i["done"] = item.status == TodoItemStatus.COMPLETED
        self.manager.reward_log_changed()

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        self.manager.data["reward_log"] = [
            i for i in self.manager.reward_log if i["uid"] not in uids
        ]
        self.manager.reward_log_changed()
