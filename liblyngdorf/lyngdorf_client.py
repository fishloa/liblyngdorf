import sys
import asyncio
if sys.version_info[:2] < (3, 11):
    from async_timeout import timeout as asyncio_timeout
else:
    from asyncio import timeout as asyncio_timeout
import logging
import os
import attr
from datetime import timedelta
from typing import (
    Awaitable,
    Callable,
    DefaultDict,
    Dict,
    Hashable,
    List,
    Optional,
    Tuple,
    cast,
)

LYNGDORF_PORT = 84

_LOGGER = logging.getLogger(__package__)

class LyngdorfClient:
    """Lyngdorf client class."""

    def __init__(
        self, host
    ):
        """Initialize the client."""
        self._host = host
        self._reader = None
        self._writer = None
        self._power_state = {}
        self._loop = asyncio.get_running_loop()
        # self._loop = asyncio.get_event_loop()

    async def async_connect(self) -> None:
        """Connect to the receiver asynchronously."""
        _LOGGER.debug("%s: connecting", self._host)
        if self.connected:
            return
        await self._async_establish_connection()

    async def _async_establish_connection(self) -> None:
        """Establish a connection to the receiver."""
        
        _LOGGER.debug("%s: establishing connection", self.host)
        try:
            async with asyncio_timeout(self.timeout):
                transport_protocol = await self._loop.create_connection(
                    lambda: LyngdorfProtocol(
                        on_connection_lost=self._handle_disconnected,
                        on_message=self._process_event,
                    ),
                    self._host,
                    LYNGDORF_PORT,
                )
        except asyncio.TimeoutError as err:
            _LOGGER.debug("%s: Timeout exception on connect", self.host)
            raise asyncio.TimeoutError(f"TimeoutException: {err}", "connect") from err
        except ConnectionRefusedError as err:
            _LOGGER.debug(
                "%s: Connection refused on connect", self.host, exc_info=True
            )
            raise ConnectionRefusedError(
                f"ConnectionRefusedError: {err}", "telnet connect"
            ) from err
        _LOGGER.debug("%s: telnet connection complete", self.host)
        self._protocol = cast(LyngdorfProtocol, transport_protocol[1])
        self._connection_enabled = True
        self._last_message_time = time.monotonic()
        self._schedule_monitor()
        await self.writeCommand(self, 'VERB(1)')
        await self.writeCommand(self, 'VOL?')

    def _handle_disconnected(self) -> None:
        """Handle disconnected."""
        _LOGGER.debug("%s: disconnected", self.host)
        self._protocol = None
        self._stop_monitor()
        if not self._connection_enabled:
            return
        self._reconnect_task = asyncio.create_task(self._async_reconnect())

    async def async_disconnect(self) -> None:
        """Close the connection to the receiver asynchronously."""
        async with self._connect_lock:
            self._connection_enabled = False
            self._stop_monitor()
            reconnect_task = self._reconnect_task
            if self._reconnect_task is not None:
                self._reconnect_task.cancel()
                self._reconnect_task = None
            if self._protocol is not None:
                self._protocol.close()
                self._protocol = None

            if reconnect_task is not None:
                try:
                    await reconnect_task
                except asyncio.CancelledError:
                    pass

    # async def connect(self):
    #     """Connect to Lyngdorf device."""
    #     try:
    #         self.reader, self.writer = await asyncio.open_connection(self._host, LYNGDORF_PORT, loop=self._loop)
    #         return
    #     except ConnectionRefusedError:
    #         self._reader = None
    #         self._writer = None
    #         raise ConnectionRefusedError(f'Connection refused to {self._host}:{LYNGDORF_PORT}') 
    
    # async def start(self):
    #     try:
    #         await self.writeSetup(self)
    #         asyncio.ensure_future(self.work())
    #         if (not self._loop.is_running()):
    #             self._loop.run_forever()
    #     except KeyboardInterrupt:
    #         pass
        
        
    def writeSetup(self):
        self.writeCommand(self, 'VERB(1)')
        self.writeCommand(self, 'VOL?')

    def writeCommand(self, command):
        self._protocol.write("PW?\r")
        # if (not self.is_connected()):
        #     await self.connect(self)
        # self._writer.write(command)
        _LOGGER.debug(f'wrote '+command)
        # self._writer.write(0x0D)

    def _process_event(self, message: str) -> None:
        """Process a realtime event."""
        _LOGGER.debug("Incoming Telnet message: %s", message)

    # async def readResponse(self):
    #     resp=await self._reader.readuntil(0x0D)
    #     _LOGGER.debug(f'received '+resp)
    #     return resp
    

    # async def work(self):
    #     while (self.is_connected()):
    #         await self.readResponse(self)
    #     print("No longer Connected")
    
    # async def disconnect(self):
    #     """Disconnect from Lyngdorf device."""
    #     if self.is_connected():
    #         self._writer.close()
    #         await self._writer.wait_closed()
    #         self._writer=None
    #         self._reader=None

    # def is_connected(self):
    #     """Return true if connected to the tv."""
    #     return self._writer is not None and self._reader is not None 
        
class LyngdorfProtocol(asyncio.Protocol):
    """Protocol for the Lyngdorf interface."""

    def __init__(
        self, on_message: Callable[[str], None], on_connection_lost: Callable[[], None]
    ) -> None:
        """Initialize the protocol."""
        self._buffer = b""
        self.transport: Optional[asyncio.Transport] = None
        self._on_message = on_message
        self._on_connection_lost = on_connection_lost

    @property
    def connected(self) -> bool:
        """Return True if transport is connected."""
        if self.transport is None:
            return False
        return not self.transport.is_closing()

    def write(self, data: str) -> None:
        """Write data to the transport."""
        if self.transport is None:
            return
        if self.transport.is_closing():
            return
        self.transport.write(data.encode("utf-8"))

    def close(self) -> None:
        """Close the connection."""
        if self.transport is not None:
            self.transport.close()

    def data_received(self, data: bytes) -> None:
        """Handle data received."""
        self._buffer += data
        while b"\r" in self._buffer:
            line, _, self._buffer = self._buffer.partition(b"\r")
            with contextlib.suppress(UnicodeDecodeError):
                self._on_message(line.decode("utf-8"))

    def connection_made(self, transport: asyncio.Transport) -> None:
        """Handle connection made."""
        self.transport = transport

    def connection_lost(self, exc: Optional[Exception]) -> None:
        """Handle connection lost."""
        self.transport = None
        self._on_connection_lost()
        return super().connection_lost(exc)