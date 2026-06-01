"""Config flow for Plugit charger control."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import aiohttp_client

from .api import PlugitApi, PlugitApiError, PlugitAuthError, PlugitCharger
from .const import (
    CONF_CHARGE_BOX_GROUP_ID,
    CONF_CHARGE_BOX_ID,
    CONF_CHARGE_POINT_ID,
    CONF_CHARGER_SELECTION,
    CONF_PASSWORD,
    CONF_USERNAME,
    DOMAIN,
)


class PlugitConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Plugit config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._username: Optional[str] = None
        self._password: Optional[str] = None
        self._discovered_chargers: List[PlugitCharger] = []

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> config_entries.ConfigFlowResult:
        errors: Dict[str, str] = {}
        if user_input is not None:
            self._username = str(user_input[CONF_USERNAME])
            self._password = str(user_input[CONF_PASSWORD])
            try:
                self._discovered_chargers = await self._async_discover_chargers()
            except PlugitAuthError:
                errors["base"] = "invalid_auth"
            except PlugitApiError:
                errors["base"] = "cannot_connect"
            else:
                if not self._discovered_chargers:
                    errors["base"] = "no_chargers"
                else:
                    return await self.async_step_select_charger()

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_select_charger(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> config_entries.ConfigFlowResult:
        errors: Dict[str, str] = {}
        if user_input is not None:
            selected_index = int(user_input[CONF_CHARGER_SELECTION])
            charger = self._discovered_chargers[selected_index]
            unique_id = "%s:%s:%s" % (
                charger.charge_point_id,
                charger.charge_box_group_id,
                charger.charge_box_id,
            )
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=charger.display_name,
                data={
                    CONF_USERNAME: self._username,
                    CONF_PASSWORD: self._password,
                    CONF_CHARGE_POINT_ID: charger.charge_point_id,
                    CONF_CHARGE_BOX_GROUP_ID: charger.charge_box_group_id,
                    CONF_CHARGE_BOX_ID: charger.charge_box_id,
                },
            )

        options = {
            str(index): "%s (%s)" % (charger.display_name, charger.status)
            for index, charger in enumerate(self._discovered_chargers)
        }
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_CHARGER_SELECTION,
                    default=next(iter(options)) if options else vol.UNDEFINED,
                ): vol.In(options)
            }
        )
        return self.async_show_form(
            step_id="select_charger",
            data_schema=schema,
            errors=errors,
        )

    async def _async_discover_chargers(self) -> List[PlugitCharger]:
        session = aiohttp_client.async_get_clientsession(self.hass)
        api = PlugitApi(session, self._username or "", self._password or "")
        await api.async_login()
        return await api.async_discover_chargers()
