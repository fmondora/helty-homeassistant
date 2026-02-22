"""Config flow for Helty VMC integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

from .api import HeltyCloudAPI, HeltyAuthError, HeltyConnectionError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class HeltyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Helty VMC."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step: email + password."""
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL]
            password = user_input[CONF_PASSWORD]

            # Prevent duplicate entries for same email
            await self.async_set_unique_id(email.lower())
            self._abort_if_unique_id_configured()

            try:
                async with aiohttp.ClientSession() as session:
                    api = HeltyCloudAPI(session)
                    await api.authenticate(email, password)
                    devices = await api.find_devices()
            except HeltyAuthError:
                errors["base"] = "invalid_auth"
            except (HeltyConnectionError, aiohttp.ClientError):
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during config flow")
                errors["base"] = "unknown"
            else:
                if not devices:
                    errors["base"] = "no_devices"
                else:
                    return self.async_create_entry(
                        title=f"Helty VMC ({email})",
                        data={
                            CONF_EMAIL: email,
                            CONF_PASSWORD: password,
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
