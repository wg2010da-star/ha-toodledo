"""Data update coordinator."""
from datetime import timedelta
import logging
import time

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ToodledoError
from .const import (
    CONF_ACCESS_TOKEN, CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_EXPIRES_AT,
    CONF_REFRESH_TOKEN, DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class ToodledoCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry, client):
        super().__init__(
            hass, _LOGGER, name=DOMAIN,
            update_interval=timedelta(minutes=entry.options.get("scan_interval", 15)),
        )
        self.entry = entry
        self.client = client

    async def _async_update_data(self):
        try:
            tasks = await self.client.get_tasks()
        except ToodledoError as err:
            raise UpdateFailed(str(err)) from err
        self.hass.config_entries.async_update_entry(
            self.entry,
            data={
                **self.entry.data,
                CONF_ACCESS_TOKEN: self.client.access_token,
                CONF_REFRESH_TOKEN: self.client.refresh_token,
                CONF_EXPIRES_AT: self.client.expires_at,
            },
        )
        return tasks
