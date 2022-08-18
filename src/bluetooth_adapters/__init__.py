__version__ = "0.2.0"

import asyncio
import logging
from typing import Any

import async_timeout
from dbus_next import BusType, Message, MessageType
from dbus_next.aio import MessageBus
from dbus_next.signature import Variant

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


async def get_bluetooth_adapter_details() -> dict[str, dict[str, Any]]:
    """Return a list of bluetooth adapter with details."""
    adapters: dict[str, dict[str, Any]] = {}
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
    results: dict[str, Any] = reply.body[0]
    for path, packed_data in results.items():
        path_str = str(path)
        if path_str.startswith("/org/bluez/hci"):
            split_path = path_str.split("/")
            adapter = split_path[3]
            if adapter not in adapters:
                adapters[adapter] = unpack_variants(packed_data)
    return adapters


def unpack_variants(dictionary: dict[str, Variant]) -> dict[str, Any]:
    """Recursively unpacks all ``Variant`` types in a dictionary to their
    corresponding Python types.

    ``dbus-next`` doesn't automatically do this, so this needs to be called on
    all dictionaries ("a{sv}") returned from D-Bus messages.

    This function comes from bleak.
    """
    unpacked = {}
    for k, v in dictionary.items():
        v = v.value if isinstance(v, Variant) else v
        if isinstance(v, dict):
            v = unpack_variants(v)
        elif isinstance(v, list):
            v = [x.value if isinstance(x, Variant) else x for x in v]
        unpacked[k] = v
    return unpacked
