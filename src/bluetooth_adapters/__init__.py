__version__ = "0.1.3"

import asyncio
import logging

import async_timeout
from dbus_next import BusType, Message, MessageType
from dbus_next.aio import MessageBus

__all__ = ["get_bluetooth_adapters"]

_LOGGER = logging.getLogger(__name__)

REPLY_TIMEOUT = 8


async def get_bluetooth_adapters() -> list[str]:
    """Return a list of bluetooth adapters."""
    adapters: list[str] = []
    try:
        bus = await MessageBus(
            bus_type=BusType.SYSTEM, negotiate_unix_fd=True
        ).connect()
    except FileNotFoundError as ex:
        _LOGGER.debug("dbus not available: %s", ex)
        return adapters
    msg = Message(
        destination="org.bluez",
        path="/",
        interface="org.freedesktop.DBus.ObjectManager",
        member="GetManagedObjects",
    )
    try:
        async with async_timeout.timeout(REPLY_TIMEOUT):
            reply = await bus.call(msg)
    except asyncio.TimeoutError:
        _LOGGER.debug("D-bus timeout waiting for reply to GetManagedObjects")
        return adapters
    bus.disconnect()
    if not reply or reply.message_type != MessageType.METHOD_RETURN:
        _LOGGER.debug("Unexpected replay: %s", reply)
        return adapters
    for path in reply.body[0]:
        path_str = str(path)
        if path_str.startswith("/org/bluez/hci"):
            split_path = path_str.split("/")
            adapter = split_path[3]
            if adapter not in adapters:
                adapters.append(adapter)
    return adapters
