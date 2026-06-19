"""Cambridge Audio CXA button entities — balance control."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    AMP_CMD_BALANCE_LEFT,
    AMP_CMD_BALANCE_RIGHT,
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
    """Set up Cambridge CXA balance button entities from a config entry."""
    coordinator: CambridgeCXACoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            CambridgeCXABalanceButton(coordinator, entry, "left"),
            CambridgeCXABalanceButton(coordinator, entry, "right"),
        ]
    )


class CambridgeCXABalanceButton(
    CoordinatorEntity[CambridgeCXACoordinator], ButtonEntity
):
    """A button that nudges the balance one step left or right (#01,23).

    Balance is step-based on the CXA (no absolute position readback), so
    two separate buttons are the natural representation.
    """

    def __init__(
        self,
        coordinator: CambridgeCXACoordinator,
        entry: ConfigEntry,
        direction: str,  # "left" | "right"
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._direction = direction
        self._attr_name = f"Balance {direction.title()}"
        self._attr_icon = (
            "mdi:arrow-left-bold" if direction == "left" else "mdi:arrow-right-bold"
        )

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_balance_{self._direction}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.data.get(CONF_NAME, DEFAULT_NAME),
            manufacturer="Cambridge Audio",
            model=self.coordinator.cxa_type,
        )

    async def async_press(self) -> None:
        """Send a single balance step command."""
        cmd = (
            AMP_CMD_BALANCE_LEFT if self._direction == "left" else AMP_CMD_BALANCE_RIGHT
        )
        await self.coordinator.async_command(cmd)
