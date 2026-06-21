"""Cambridge Audio CXA coordinator — async TCP connection and push updates."""
from __future__ import annotations

import asyncio
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    AMP_CMD_GET_CURRENT_SOURCE,
    AMP_CMD_GET_MUTE_STATE,
    AMP_CMD_GET_PWSTATE,
    AMP_REPLY_PWR_ON,
    AMP_REPLY_PWR_STANDBY,
    AMP_REPLY_MUTE_ON,
    AMP_REPLY_MUTE_OFF,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

class CambridgeCXACoordinator(DataUpdateCoordinator[dict]):
    """Manages the TCP connection and push updates for the CXA amplifier.

    Uses a listen-only loop to monitor for state changes broadcasted by the
    amplifier without keeping it awake via active polling.
    """

    def __init__(
        self, hass: HomeAssistant, host: str, port: int, cxa_type: str
    ) -> None:
        """Initialize the coordinator."""
        # Note: update_interval is purposely omitted to disable periodic polling.
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
        )
        self._host = host
        self._port = port
        self.cxa_type = cxa_type
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._command_lock = asyncio.Lock()
        self._listen_task: asyncio.Task | None = None
        self.data = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def host(self) -> str:
        """Return the ser2net host."""
        return self._host

    @property
    def port(self) -> int:
        """Return the ser2net port."""
        return self._port

    async def async_connect(self) -> bool:
        """Open the TCP connection to ser2net. Used by config flow for validation."""
        async with self._command_lock:
            await self._connect()
            return self._is_connected()

    async def async_disconnect(self) -> None:
        """Close the TCP connection cleanly."""
        if self._listen_task:
            self._listen_task.cancel()
            self._listen_task = None
        async with self._command_lock:
            await self._close_connection()

    async def async_command(self, command: str) -> None:
        """Send a command with no reply expected (fire-and-forget).

        The amplifier will broadcast its new state, which is caught by _listen_loop.
        """
        async with self._command_lock:
            await self._ensure_connected()
            if not self._is_connected():
                _LOGGER.warning("Cannot send '%s': not connected", command)
                return
            try:
                _LOGGER.debug("TX: %s", command)
                self._writer.write((command + "\r").encode("utf-8"))  # type: ignore[union-attr]
                await self._writer.drain()  # type: ignore[union-attr]
            except OSError as err:
                _LOGGER.warning("Send failed for '%s': %s", command, err)
                await self._close_connection()

    # ------------------------------------------------------------------
    # DataUpdateCoordinator hook
    # ------------------------------------------------------------------

    async def _async_update_data(self) -> dict:
        """Perform initial state sync on startup.

        Because update_interval is not set, this is only called once by
        async_config_entry_first_refresh(). We establish the connection,
        seed the state via query commands, and then start the listen loop.
        """
        async with self._command_lock:
            await self._ensure_connected()
            if not self._is_connected():
                raise UpdateFailed(f"No response from Cambridge CXA at {self._host}:{self._port}")

            if self._listen_task is None or self._listen_task.done():
                self._listen_task = self.hass.loop.create_task(self._listen_loop())

            _LOGGER.info("Sending initial state-sync queries")
            # Send queries without reading the reply. The listen loop will catch the replies.
            try:
                self._writer.write((AMP_CMD_GET_PWSTATE + "\r").encode("utf-8"))  # type: ignore[union-attr]
                self._writer.write((AMP_CMD_GET_CURRENT_SOURCE + "\r").encode("utf-8"))  # type: ignore[union-attr]
                self._writer.write((AMP_CMD_GET_MUTE_STATE + "\r").encode("utf-8"))  # type: ignore[union-attr]
                await self._writer.drain()  # type: ignore[union-attr]
            except OSError as err:
                raise UpdateFailed(f"Failed to send initial sync: {err}")

            # Return whatever we have (starts empty, listen loop fills it milliseconds later)
            return self.data

    # ------------------------------------------------------------------
    # Listen Loop (Push Architecture)
    # ------------------------------------------------------------------

    async def _listen_loop(self) -> None:
        """Background task to read from the socket and update state."""
        _LOGGER.debug("Starting CXA listen loop")
        while True:
            # Check connection
            async with self._command_lock:
                await self._ensure_connected()
                reader = self._reader
            
            if not reader:
                await asyncio.sleep(5)
                continue

            try:
                # Read without holding the lock so we don't block outgoing commands
                reply = await reader.readuntil(b"\r")
                decoded = reply.decode("utf-8").strip()
                if decoded:
                    _LOGGER.debug("RX (listen_loop): %s", decoded)
                    self._handle_message(decoded)
            except (asyncio.IncompleteReadError, ConnectionError, OSError) as err:
                _LOGGER.warning("CXA connection lost during listen loop: %s", err)
                async with self._command_lock:
                    await self._close_connection()
                await asyncio.sleep(5)

    def _handle_message(self, message: str) -> None:
        """Parse incoming broadcast message and push update."""
        updated = False

        if message.startswith(AMP_REPLY_PWR_ON):
            self.data["power"] = message
            updated = True
        elif message.startswith(AMP_REPLY_PWR_STANDBY):
            self.data["power"] = message
            updated = True
        elif message.startswith("#04,01,"):
            # Source change
            self.data["source"] = message
            updated = True
        elif message.startswith(AMP_REPLY_MUTE_ON):
            self.data["mute"] = message
            updated = True
        elif message.startswith(AMP_REPLY_MUTE_OFF):
            self.data["mute"] = message
            updated = True

        if updated:
            self.async_set_updated_data(self.data)

    # ------------------------------------------------------------------
    # Internal helpers (must be called with _command_lock already held)
    # ------------------------------------------------------------------

    def _is_connected(self) -> bool:
        """Return True if the writer is open and not closing."""
        return self._writer is not None and not self._writer.is_closing()

    async def _connect(self) -> None:
        """Open a new TCP connection (lock must be held)."""
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port),
                timeout=10.0,
            )
            _LOGGER.info(
                "Connected to Cambridge CXA at %s:%s", self._host, self._port
            )
        except (OSError, asyncio.TimeoutError) as err:
            _LOGGER.warning(
                "Cannot connect to %s:%s: %s", self._host, self._port, err
            )
            self._reader = None
            self._writer = None

    async def _close_connection(self) -> None:
        """Close open streams (lock must be held)."""
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except OSError:
                pass
            finally:
                self._writer = None
                self._reader = None

    async def _ensure_connected(self) -> None:
        """Reconnect if the connection is gone (lock must be held)."""
        if not self._is_connected():
            _LOGGER.debug("Reconnecting to %s:%s", self._host, self._port)
            await self._connect()
