"""Cambridge Audio CXA integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_CXA_TYPE, DOMAIN
from .coordinator import CambridgeCXACoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["media_player", "switch", "select", "button"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Cambridge Audio CXA from a config entry."""
    coordinator = CambridgeCXACoordinator(
        hass,
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        cxa_type=entry.data[CONF_CXA_TYPE],
    )

    # async_config_entry_first_refresh raises ConfigEntryNotReady if
    # _async_update_data raises UpdateFailed (e.g. ser2net unreachable).
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Cambridge Audio CXA config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: CambridgeCXACoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_disconnect()
    return unload_ok