"""Cambridge Audio CXA switch entities — pre-amp mode and phase inversion."""
from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    AMP_CMD_SET_PHASE_INVERTED,
    AMP_CMD_SET_PHASE_NORMAL,
    AMP_CMD_SET_PREAMP_OFF,
    AMP_CMD_SET_PREAMP_ON,
    AMP_REPLY_PHASE_INVERTED,
    AMP_REPLY_PREAMP_ON,
    DEFAULT_NAME,
    DOMAIN,
)
from .coordinator import CambridgeCXACoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Cambridge CXA switch entities from a config entry."""
    coordinator: CambridgeCXACoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            CambridgeCXAPreampSwitch(coordinator, entry),
            CambridgeCXAPhaseSwitch(coordinator, entry),
        ]
    )


class _CambridgeCXASwitch(CoordinatorEntity[CambridgeCXACoordinator], SwitchEntity):
    """Shared base for CXA switch entities."""

    def __init__(
        self, coordinator: CambridgeCXACoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.data.get(CONF_NAME, DEFAULT_NAME),
            manufacturer="Cambridge Audio",
            model=self.coordinator.cxa_type,
        )

    @property
    def available(self) -> bool:
        """Unavailable when the last coordinator update failed or amp is off."""
        return super().available and bool(self.coordinator.data)


class CambridgeCXAPreampSwitch(_CambridgeCXASwitch):
    """Switch to toggle pre-amp output mode (#01,21)."""

    _attr_name = "Pre-amp Mode"
    _attr_icon = "mdi:amplifier"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_preamp"

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None
        return AMP_REPLY_PREAMP_ON in self.coordinator.data.get("preamp", "")

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_command(AMP_CMD_SET_PREAMP_ON)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_command(AMP_CMD_SET_PREAMP_OFF)
        await self.coordinator.async_request_refresh()


class CambridgeCXAPhaseSwitch(_CambridgeCXASwitch):
    """Switch to toggle phase inversion (#01,22)."""

    _attr_name = "Phase Inversion"
    _attr_icon = "mdi:sine-wave"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_phase"

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None
        return AMP_REPLY_PHASE_INVERTED in self.coordinator.data.get("phase", "")

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_command(AMP_CMD_SET_PHASE_INVERTED)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_command(AMP_CMD_SET_PHASE_NORMAL)
        await self.coordinator.async_request_refresh()
