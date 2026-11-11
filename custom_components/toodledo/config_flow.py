"""Config flow for Toodledo."""
from __future__ import annotations

from urllib.parse import parse_qs, urlparse
import secrets
import time

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ToodledoClient, ToodledoError
from .const import (
    AUTH_URL, CONF_ACCESS_TOKEN, CONF_CLIENT_ID, CONF_CLIENT_SECRET,
    CONF_EXPIRES_AT, CONF_REFRESH_TOKEN, DOMAIN,
)


class ToodledoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            self.client_id = user_input[CONF_CLIENT_ID].strip()
            self.client_secret = user_input[CONF_CLIENT_SECRET].strip()
            self.state = secrets.token_urlsafe(24)
            return await self.async_step_authorize()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_CLIENT_ID): str,
                vol.Required(CONF_CLIENT_SECRET): str,
            }),
            errors=errors,
        )

    async def async_step_authorize(self, user_input=None):
        errors = {}
        if user_input is not None:
            parsed = urlparse(user_input["redirected_url"].strip())
            params = parse_qs(parsed.query)
            code = params.get("code", [None])[0]
            returned_state = params.get("state", [None])[0]
            if params.get("error"):
                errors["base"] = "authorization_denied"
            elif not code:
                errors["base"] = "missing_code"
            elif returned_state != self.state:
                errors["base"] = "state_mismatch"
            else:
                client = ToodledoClient(
                    async_get_clientsession(self.hass), self.client_id,
                    self.client_secret, "", "", 0,
                )
                try:
                    tokens = await client.exchange_code(code)
                except ToodledoError:
                    errors["base"] = "token_exchange"
                else:
                    await self.async_set_unique_id(self.client_id)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title="Toodledo",
                        data={
                            CONF_CLIENT_ID: self.client_id,
                            CONF_CLIENT_SECRET: self.client_secret,
                            CONF_ACCESS_TOKEN: tokens["access_token"],
                            CONF_REFRESH_TOKEN: tokens["refresh_token"],
                            CONF_EXPIRES_AT: time.time() + int(tokens.get("expires_in", 7200)) - 60,
                        },
                    )
        auth_url = (
            f"{AUTH_URL}?response_type=code&client_id={self.client_id}"
            f"&state={self.state}&scope=basic%20tasks%20write"
        )
        return self.async_show_form(
            step_id="authorize",
            data_schema=vol.Schema({vol.Required("redirected_url"): str}),
            errors=errors,
            description_placeholders={"auth_url": auth_url},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ToodledoOptionsFlow(config_entry)


class ToodledoOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional("scan_interval", default=self.config_entry.options.get("scan_interval", 15)): vol.All(int, vol.Range(min=5, max=60))
            }),
        )
