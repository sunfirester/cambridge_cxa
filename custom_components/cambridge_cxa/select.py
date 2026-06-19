"""Cambridge Audio CXA select entity — display brightness."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    AMP_REPLY_BRIGHTNESS_PREFIX,
    BRIGHTNESS_OPTIONS,
    DEFAULT_NAME,
    DOMAIN,
)
from .coordinator import CambridgeCXACoordinator

_LOGGER = logging.getLogger(__name__)

# Reverse lookup: "0" -> "Off", "1" -> "Dim", etc.
_BRIGHTNESS_REPLY_MAP: dict[str, str] = {v: k for k, v in BRIGHTNESS_OPTIONS.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Cambridge CXA select entities from a config entry."""
    coordinator: CambridgeCXACoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CambridgeCXABrightnessSelect(coordinator, entry)])


class CambridgeCXABrightnessSelect(
    CoordinatorEntity[CambridgeCXACoordinator], SelectEntity
):
    """Select entity controlling the front-panel display brightness (#01,15)."""

    _attr_name = "Display Brightness"
    _attr_icon = "mdi:brightness-6"

    def __init__(
        self, coordinator: CambridgeCXACoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_brightness"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.data.get(CONF_NAME, DEFAULT_NAME),
            manufacturer="Cambridge Audio",
            model=self.coordinator.cxa_type,
        )

    @property
    def options(self) -> list[str]:
        return list(BRIGHTNESS_OPTIONS.keys())

    @property
    def current_option(self) -> str | None:
        """Parse the brightness reply (#02,15,{0-3}) to a label."""
        if not self.coordinator.data:
            return None
        reply = self.coordinator.data.get("brightness", "")
        if reply.startswith(AMP_REPLY_BRIGHTNESS_PREFIX):
            level = reply[len(AMP_REPLY_BRIGHTNESS_PREFIX):]
            return _BRIGHTNESS_REPLY_MAP.get(level)
        return None

    @property
    def available(self) -> bool:
        return super().available and bool(self.coordinator.data)

    async def async_select_option(self, option: str) -> None:
        level = BRIGHTNESS_OPTIONS.get(option)
        if level is not None:
            await self.coordinator.async_command(f"#01,15,{level}")
            await self.coordinator.async_request_refresh()
