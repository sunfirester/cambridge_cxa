"""Config flow for Cambridge Audio CXA integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_CXA_TYPE,
    CXA_TYPES,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=65535)
        ),
        vol.Required(CONF_CXA_TYPE): vol.In(CXA_TYPES),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
    }
)


async def _test_connection(host: str, port: int) -> bool:
    """Try opening a TCP connection to ser2net to validate host/port."""
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=10.0
        )
        writer.close()
        try:
            await writer.wait_closed()
        except OSError:
            pass
        return True
    except (OSError, asyncio.TimeoutError):
        return False


class CambridgeCXAConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the Cambridge Audio CXA UI config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step shown to the user."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host: str = user_input[CONF_HOST].strip()
            port: int = user_input[CONF_PORT]

            # Prevent configuring the same ser2net endpoint twice
            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()

            if not await _test_connection(host, port):
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, DEFAULT_NAME),
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_CXA_TYPE: user_input[CONF_CXA_TYPE],
                        CONF_NAME: user_input.get(CONF_NAME, DEFAULT_NAME),
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
