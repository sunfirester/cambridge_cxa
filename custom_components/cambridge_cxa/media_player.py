"""
Cambridge Audio CXA media player entity.

Communicates with the amplifier over a TCP connection to a ser2net bridge
running on a Raspberry Pi (or any RS232-over-TCP adapter).  All I/O is
async; state is driven by the shared CambridgeCXACoordinator.
"""
from __future__ import annotations

import logging
import aiohttp

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    AMP_CMD_SET_MUTE_OFF,
    AMP_CMD_SET_MUTE_ON,
    AMP_CMD_SET_PWR_OFF,
    AMP_CMD_SET_PWR_ON,
    AMP_REPLY_MUTE_ON,
    AMP_REPLY_PWR_ON,
    DEFAULT_NAME,
    DOMAIN,
    NORMAL_INPUTS_AMP_REPLY_CXA61,
    NORMAL_INPUTS_AMP_REPLY_CXA81,
    NORMAL_INPUTS_CXA61,
    NORMAL_INPUTS_CXA81,
    SOUND_MODES,
)
from .coordinator import CambridgeCXACoordinator

_LOGGER = logging.getLogger(__name__)

SUPPORT_CXA = (
    MediaPlayerEntityFeature.SELECT_SOURCE
    | MediaPlayerEntityFeature.SELECT_SOUND_MODE
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.VOLUME_STEP
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Cambridge CXA media player from a config entry."""
    coordinator: CambridgeCXACoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CambridgeCXADevice(coordinator, entry)])


class CambridgeCXADevice(
    CoordinatorEntity[CambridgeCXACoordinator], MediaPlayerEntity
):
    """Cambridge Audio CXA amplifier media player entity.

    State is read from coordinator.data (populated every 30 s).
    Commands are forwarded to coordinator.async_command() which serialises
    them with the update lock so nothing interleaves mid-poll.
    """

    _attr_has_entity_name = True
    _attr_name = None  # Use the device name as the entity name

    def __init__(
        self, coordinator: CambridgeCXACoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the media player entity."""
        super().__init__(coordinator)
        self._entry = entry
        # Sound mode is write-only (no GET command exists) — tracked locally
        self._sound_mode: str | None = None

        if coordinator.cxa_type == "CXA61":
            self._source_list = NORMAL_INPUTS_CXA61
            self._source_reply_list = NORMAL_INPUTS_AMP_REPLY_CXA61
        else:
            self._source_list = NORMAL_INPUTS_CXA81
            self._source_reply_list = NORMAL_INPUTS_AMP_REPLY_CXA81

    # ------------------------------------------------------------------
    # Entity identity / device grouping
    # ------------------------------------------------------------------

    @property
    def unique_id(self) -> str:
        """Return a unique ID tied to the config entry."""
        return self._entry.entry_id

    @property
    def device_info(self) -> DeviceInfo:
        """Group all CXA entities under one device in the registry."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.data.get(CONF_NAME, DEFAULT_NAME),
            manufacturer="Cambridge Audio",
            model=self.coordinator.cxa_type,
            configuration_url=f"http://{self.coordinator.host}",
        )

    # ------------------------------------------------------------------
    # Features
    # ------------------------------------------------------------------

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        return SUPPORT_CXA

    # ------------------------------------------------------------------
    # State — all derived from coordinator.data
    # ------------------------------------------------------------------

    @property
    def state(self) -> MediaPlayerState:
        """Return on or off based on the power reply."""
        if self.coordinator.data is None:
            return MediaPlayerState.OFF
        if AMP_REPLY_PWR_ON in self.coordinator.data.get("power", ""):
            return MediaPlayerState.ON
        return MediaPlayerState.OFF

    @property
    def is_volume_muted(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        return AMP_REPLY_MUTE_ON in self.coordinator.data.get("mute", "")



    @property
    def source(self) -> str | None:
        """Return the current input source name, or None if unknown."""
        if self.coordinator.data is None:
            return None
        media_source = self.coordinator.data.get("source", "")
        return self._source_reply_list.get(media_source)

    @property
    def source_list(self) -> list[str]:
        return sorted(self._source_list.keys())

    @property
    def sound_mode(self) -> str | None:
        """Return the locally-tracked speaker output mode."""
        return self._sound_mode

    @property
    def sound_mode_list(self) -> list[str]:
        return sorted(SOUND_MODES.keys())

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    async def async_turn_on(self) -> None:
        await self.coordinator.async_command(AMP_CMD_SET_PWR_ON)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        await self.coordinator.async_command(AMP_CMD_SET_PWR_OFF)
        await self.coordinator.async_request_refresh()

    async def async_mute_volume(self, mute: bool) -> None:
        cmd = AMP_CMD_SET_MUTE_ON if mute else AMP_CMD_SET_MUTE_OFF
        await self.coordinator.async_command(cmd)
        await self.coordinator.async_request_refresh()

    async def async_volume_up(self) -> None:
        """Send volume up command via the Raspberry Pi HTTP API."""
        try:
            url = f"http://{self.coordinator.host}:5001/vol/up"
            session = async_get_clientsession(self.coordinator.hass)
            async with session.get(url, timeout=2) as response:
                    if response.status != 200:
                        _LOGGER.error("Failed to turn volume up, Pi returned %s", response.status)
        except Exception as e:
            _LOGGER.error("Error communicating with Pi IR API: %s", e)

    async def async_volume_down(self) -> None:
        """Send volume down command via the Raspberry Pi HTTP API."""
        try:
            url = f"http://{self.coordinator.host}:5001/vol/down"
            session = async_get_clientsession(self.coordinator.hass)
            async with session.get(url, timeout=2) as response:
                    if response.status != 200:
                        _LOGGER.error("Failed to turn volume down, Pi returned %s", response.status)
        except Exception as e:
            _LOGGER.error("Error communicating with Pi IR API: %s", e)

    async def async_select_source(self, source: str) -> None:
        cmd = self._source_list.get(source)
        if cmd:
            await self.coordinator.async_command(cmd)
            await self.coordinator.async_request_refresh()

    async def async_select_sound_mode(self, sound_mode: str) -> None:
        """Switch speaker output (A / A+B / B). State tracked locally."""
        cmd = SOUND_MODES.get(sound_mode)
        if cmd:
            await self.coordinator.async_command(cmd)
            self._sound_mode = sound_mode
            self.async_write_ha_state()