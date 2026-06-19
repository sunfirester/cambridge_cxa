"""Cambridge Audio CXA coordinator — async TCP connection and data polling."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    AMP_CMD_GET_CURRENT_SOURCE,
    AMP_CMD_GET_MUTE_STATE,
    AMP_CMD_GET_PWSTATE,
    AMP_REPLY_PWR_ON,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=30)


class CambridgeCXACoordinator(DataUpdateCoordinator[dict]):
    """Manages the TCP connection and periodic polling for the CXA amplifier.

    All I/O is protected by a single asyncio.Lock so that entity action
    commands (e.g. turn_on) never interleave with the update polling cycle.
    """

    def __init__(
        self, hass: HomeAssistant, host: str, port: int, cxa_type: str
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self._host = host
        self._port = port
        self.cxa_type = cxa_type
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._command_lock = asyncio.Lock()

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
        async with self._command_lock:
            await self._close_connection()

    async def async_command(self, command: str) -> None:
        """Send a command with no reply expected (e.g. power on, volume step).

        After sending, we attempt to drain any reply the amp may have sent
        (e.g. a volume echo) with a short timeout.  Without this, stale reply
        bytes sit in the TCP buffer and corrupt the next readuntil() call in
        the polling cycle, making the integration think the amp switched off.
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
                # Consume any unsolicited reply within 300 ms.
                try:
                    reply = await asyncio.wait_for(
                        self._reader.readuntil(b"\r"),  # type: ignore[union-attr]
                        timeout=0.3,
                    )
                    _LOGGER.debug("RX (unsolicited after %s): %s", command, reply.decode("utf-8").strip())
                except (asyncio.TimeoutError, asyncio.LimitOverrunError):
                    pass  # No reply — expected for many commands
            except OSError as err:
                _LOGGER.warning("Send failed for '%s': %s", command, err)
                await self._close_connection()

    async def async_command_with_reply(self, command: str) -> str:
        """Send a command and return the reply line."""
        async with self._command_lock:
            return await self._send_with_reply(command)

    # ------------------------------------------------------------------
    # DataUpdateCoordinator hook
    # ------------------------------------------------------------------

    async def _async_update_data(self) -> dict:
        """Fetch all amplifier state under one lock acquisition.

        Holding the lock for the entire sequence prevents entity action
        commands from slipping between individual command/reply pairs and
        corrupting the readline() buffer.
        """
        async with self._command_lock:
            power = await self._send_with_reply(AMP_CMD_GET_PWSTATE)

            if not power:
                raise UpdateFailed(
                    f"No response from Cambridge CXA at {self._host}:{self._port}"
                )

            data: dict = {"power": power}

            if AMP_REPLY_PWR_ON in power:
                data["source"] = await self._send_with_reply(AMP_CMD_GET_CURRENT_SOURCE)
                data["mute"] = await self._send_with_reply(AMP_CMD_GET_MUTE_STATE)

            return data

    # ------------------------------------------------------------------
    # Internal helpers  (must be called with _command_lock already held)
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

    async def _send_with_reply(self, command: str) -> str:
        """Send command and read one reply line (lock must be held).

        Reconnects automatically if the connection was lost.
        Returns an empty string on any failure.
        """
        await self._ensure_connected()
        if not self._is_connected():
            return ""
        try:
            _LOGGER.debug("TX: %s", command)
            self._writer.write((command + "\r").encode("utf-8"))  # type: ignore[union-attr]
            await self._writer.drain()  # type: ignore[union-attr]
            # The CXA protocol uses \r (CR) as line terminator, not \n.
            # readline() would wait for \n and time out every time.
            reply = await asyncio.wait_for(
                self._reader.readuntil(b"\r"),  # type: ignore[union-attr]
                timeout=2.0,
            )
            decoded = reply.decode("utf-8").strip()
            _LOGGER.debug("RX: %s", decoded)
            return decoded
        except (OSError, asyncio.TimeoutError, UnicodeDecodeError, asyncio.LimitOverrunError) as err:
            _LOGGER.warning("Command '%s' failed: %s", command, err)
            await self._close_connection()
            return ""
