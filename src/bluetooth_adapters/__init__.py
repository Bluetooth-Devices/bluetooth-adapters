__version__ = "0.3.4"

import asyncio
import logging
from functools import cache
from pathlib import Path
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
    return list(await get_bluetooth_adapter_details())


async def get_bluetooth_adapter_details() -> dict[str, dict[str, Any]]:
    """Return a list of bluetooth adapter with details."""
    adapters: dict[str, dict[str, Any]] = {}
    results = await _get_dbus_managed_objects()
    for path, packed_data in results.items():
        path_str = str(path)
        if path_str.startswith("/org/bluez/hci"):
            split_path = path_str.split("/")
            adapter = split_path[3]
            if adapter not in adapters:
                adapters[adapter] = unpack_variants(packed_data)
    return adapters


async def get_dbus_managed_objects() -> dict[str, Any]:
    """Return a list of bluetooth adapter with details."""
    results = await _get_dbus_managed_objects()
    return {path: unpack_variants(packed_data) for path, packed_data in results.items()}


async def _get_dbus_managed_objects() -> dict[str, Any]:
    try:
        bus = await MessageBus(
            bus_type=BusType.SYSTEM, negotiate_unix_fd=True
        ).connect()
    except FileNotFoundError as ex:
        if is_docker_env():
            _LOGGER.debug(
                "DBus service not found; docker config may "
                "be missing `-v /run/dbus:/run/dbus:ro`: %s",
                ex,
            )
        _LOGGER.debug(
            "DBus service not found; make sure the DBus socket " "is available: %s",
            ex,
        )
        return {}
    except BrokenPipeError as ex:
        if is_docker_env():
            _LOGGER.debug(
                "DBus connection broken: %s; try restarting "
                "`bluetooth`, `dbus`, and finally the docker container",
                ex,
            )
        _LOGGER.debug(
            "DBus connection broken: %s; try restarting " "`bluetooth` and `dbus`", ex
        )
        return {}
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
        _LOGGER.debug(
            "Dbus timeout waiting for reply to GetManagedObjects; try restarting "
            "`bluetooth` and `dbus`"
        )
        return {}
    bus.disconnect()
    if not reply or reply.message_type != MessageType.METHOD_RETURN:
        _LOGGER.error(
            "Received an unexpected reply from Dbus while "
            "calling GetManagedObjects on org.bluez: %s",
            reply,
        )
        return {}
    results: dict[str, Any] = reply.body[0]
    return results


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


@cache
def is_docker_env() -> bool:
    """Return True if we run in a docker env."""
    return Path("/.dockerenv").exists()
