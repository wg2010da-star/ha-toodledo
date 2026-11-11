"""Native Home Assistant to-do list for Toodledo."""
from datetime import date, datetime, timezone
import logging

from homeassistant.components.todo import (
    TodoItem, TodoItemStatus, TodoListEntity, TodoListEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import ToodledoError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([ToodledoTodoEntity(hass.data[DOMAIN][entry.entry_id])])


class ToodledoTodoEntity(CoordinatorEntity, TodoListEntity):
    _attr_has_entity_name = True
    _attr_name = "Tasks"
    _attr_icon = "mdi:format-list-checks"
    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
        | TodoListEntityFeature.SET_DUE_DATE_ON_ITEM
        | TodoListEntityFeature.SET_DESCRIPTION_ON_ITEM
    )

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_tasks"

    @property
    def todo_items(self):
        items = []
        for task in (self.coordinator.data or []):
            due = None
            if task.get("duedate"):
                try:
                    due = datetime.fromtimestamp(int(task["duedate"]), timezone.utc).date()
                except (ValueError, TypeError, OSError):
                    pass
            items.append(TodoItem(
                uid=str(task["id"]),
                summary=task.get("title") or "(ohne Titel)",
                status=(TodoItemStatus.COMPLETED if int(task.get("completed") or 0) > 0
                        else TodoItemStatus.NEEDS_ACTION),
                due=due,
                description=task.get("note") or None,
            ))
        return items

    async def async_create_todo_item(self, item: TodoItem) -> None:
        due = int(datetime.combine(item.due, datetime.min.time(), timezone.utc).timestamp()) if item.due else None
        await self.coordinator.client.add_task(item.summary or "", due, item.description)
        await self.coordinator.async_request_refresh()

    async def async_update_todo_item(self, item: TodoItem) -> None:
        fields = {"title": item.summary or ""}
        fields["completed"] = int(datetime.now(timezone.utc).timestamp()) if item.status == TodoItemStatus.COMPLETED else 0
        if item.due:
            fields["duedate"] = int(datetime.combine(item.due, datetime.min.time(), timezone.utc).timestamp())
        if item.description is not None:
            fields["note"] = item.description
        await self.coordinator.client.edit_task(item.uid, **fields)
        await self.coordinator.async_request_refresh()

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        await self.coordinator.client.delete_tasks(uids)
        await self.coordinator.async_request_refresh()
