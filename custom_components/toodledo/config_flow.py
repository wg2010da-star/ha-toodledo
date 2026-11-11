"""OAuth config flow for Toodledo using Home Assistant's native callback."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.exceptions import OAuth2TokenRequestConnectionError
from homeassistant.helpers import config_entry_oauth2_flow

from .const import (
    API_BASE,
    CONF_ACCESS_TOKEN,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_EXPIRES_AT,
    CONF_REFRESH_TOKEN,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class ToodledoOAuthImplementation(config_entry_oauth2_flow.LocalOAuth2Implementation):
    """Toodledo OAuth implementation.

    Toodledo requires HTTP Basic authentication at the token endpoint and
    expects its API version/device parameters during token exchange.
    """

    token_auth_method = "client_secret_basic"

    @property
    def extra_authorize_data(self) -> dict[str, str]:
        """Return Toodledo API scopes."""
        return {"scope": "basic tasks write"}

    async def async_resolve_external_data(self, external_data: Any) -> dict:
        """Exchange the authorization code for tokens."""
        return await self._token_request(
            {
                "grant_type": "authorization_code",
                "code": external_data["code"],
                "redirect_uri": external_data["state"]["redirect_uri"],
                "vers": "3",
                "device": "Home Assistant",
                "f": "json",
            }
        )

    async def _async_refresh_token(self, token: dict) -> dict:
        """Refresh Toodledo tokens."""
        result = await self._token_request(
            {
                "grant_type": "refresh_token",
                "refresh_token": token["refresh_token"],
                "vers": "3",
                "device": "Home Assistant",
                "f": "json",
            }
        )
        if not result.get("access_token"):
            raise OAuth2TokenRequestConnectionError(domain=self.service_domain)
        return {**token, **result}


class ToodledoConfigFlow(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Handle Toodledo account setup."""

    DOMAIN = DOMAIN
    VERSION = 1

    def __init__(self) -> None:
        super().__init__()
        self.client_id = ""

    @property
    def logger(self) -> logging.Logger:
        """Return the integration logger."""
        return _LOGGER

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Ask for the user's Toodledo application credentials."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_CLIENT_ID): str,
                        vol.Required(CONF_CLIENT_SECRET): str,
                    }
                ),
            )

        self.client_id = user_input[CONF_CLIENT_ID].strip()
        client_secret = user_input[CONF_CLIENT_SECRET].strip()
        if not self.client_id or not client_secret:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_CLIENT_ID): str,
                        vol.Required(CONF_CLIENT_SECRET): str,
                    }
                ),
                errors={"base": "missing_credentials"},
            )

        implementation = ToodledoOAuthImplementation(
            self.hass,
            f"{DOMAIN}_{self.client_id}",
            self.client_id,
            client_secret,
            f"{API_BASE}/account/authorize.php",
            f"{API_BASE}/account/token.php",
        )
        self.async_register_implementation(self.hass, implementation)
        self.client_secret = client_secret
        return await self.async_step_pick_implementation(
            {"implementation": implementation.domain}
        )

    async def async_oauth_create_entry(
        self, data: dict[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Store tokens in the format used by the Toodledo API client."""
        token = data["token"]
        if not token.get("access_token") or not token.get("refresh_token"):
            return self.async_abort(reason="oauth_error")

        await self.async_set_unique_id(self.client_id)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title="Toodledo",
            data={
                CONF_CLIENT_ID: self.client_id,
                CONF_CLIENT_SECRET: self.client_secret,
                CONF_ACCESS_TOKEN: token["access_token"],
                CONF_REFRESH_TOKEN: token["refresh_token"],
                CONF_EXPIRES_AT: token["expires_at"],
            },
        )

    @staticmethod
    @config_entries.callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Return options flow."""
        return ToodledoOptionsFlow(config_entry)


class ToodledoOptionsFlow(config_entries.OptionsFlow):
    """Configure polling options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage integration options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "scan_interval",
                        default=self.config_entry.options.get("scan_interval", 15),
                    ): vol.All(int, vol.Range(min=5, max=60))
                }
            ),
        )
