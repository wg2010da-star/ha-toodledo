"""Toodledo integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ToodledoClient
from .const import (
    CONF_ACCESS_TOKEN, CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_EXPIRES_AT,
    CONF_REFRESH_TOKEN, DOMAIN, PLATFORMS,
)
from .coordinator import ToodledoCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = entry.data
    client = ToodledoClient(
        async_get_clientsession(hass), data[CONF_CLIENT_ID],
        data[CONF_CLIENT_SECRET], data[CONF_ACCESS_TOKEN],
        data[CONF_REFRESH_TOKEN], data.get(CONF_EXPIRES_AT, 0),
    )
    coordinator = ToodledoCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
