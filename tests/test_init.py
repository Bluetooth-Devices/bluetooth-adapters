import asyncio
from typing import Any
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
from dbus_fast import MessageType

import bluetooth_adapters.dbus as bluetooth_adapters_dbus
from bluetooth_adapters import (
    DEFAULT_ADDRESS,
    AdvertisementHistory,
    BlueZDBusObjects,
    adapter_human_name,
    adapter_unique_name,
    get_adapters,
    get_bluetooth_adapters,
    get_dbus_managed_objects,
)


@pytest.mark.asyncio
async def test_get_bluetooth_adapters_file_not_found():
    """Test get_bluetooth_adapters()."""

    class MockMessageBus:
        def __init__(self, *args, **kwargs):
            raise FileNotFoundError

    with patch("bluetooth_adapters.dbus.MessageBus", MockMessageBus):
        assert await get_bluetooth_adapters() == []


@pytest.mark.asyncio
async def test_get_bluetooth_adapters_connection_refused():
    """Test get_bluetooth_adapters with connection refused."""

    class MockMessageBus:
        def __init__(self, *args, **kwargs):
            raise ConnectionRefusedError

    with patch("bluetooth_adapters.dbus.MessageBus", MockMessageBus):
        assert await get_bluetooth_adapters() == []


@pytest.mark.asyncio
async def test_get_bluetooth_adapters_connect_refused_docker():
    class MockMessageBus:
        def __init__(self, *args, **kwargs):
            pass

        async def connect(self):
            raise ConnectionRefusedError

        async def call(self):
            return None

    with patch("bluetooth_adapters.dbus.MessageBus", MockMessageBus), patch(
        "bluetooth_adapters.dbus.is_docker_env", return_value=True
    ):
        assert await get_bluetooth_adapters() == []


@pytest.mark.asyncio
async def test_get_bluetooth_adapters_connect_fails():
    class MockMessageBus:
        def __init__(self, *args, **kwargs):
            pass

        async def connect(self):
            raise FileNotFoundError

        async def call(self):
            return None

    with patch("bluetooth_adapters.dbus.MessageBus", MockMessageBus):
        assert await get_bluetooth_adapters() == []


@pytest.mark.asyncio
async def test_get_bluetooth_adapters_connect_fails_docker():
    class MockMessageBus:
        def __init__(self, *args, **kwargs):
            pass

        async def connect(self):
            raise FileNotFoundError

        async def call(self):
            return None

    with patch("bluetooth_adapters.dbus.MessageBus", MockMessageBus), patch(
        "bluetooth_adapters.dbus.is_docker_env", return_value=True
    ):
        assert await get_bluetooth_adapters() == []


@pytest.mark.asyncio
async def test_get_bluetooth_adapters_connect_broken_pipe():
    class MockMessageBus:
        def __init__(self, *args, **kwargs):
            pass

        async def connect(self):
            raise BrokenPipeError

        async def call(self):
            return None

    with patch("bluetooth_adapters.dbus.MessageBus", MockMessageBus):
        assert await get_bluetooth_adapters() == []


@pytest.mark.asyncio
async def test_get_bluetooth_adapters_connect_broken_pipe_docker():
    class MockMessageBus:
        def __init__(self, *args, **kwargs):
            pass

        async def connect(self):
            raise BrokenPipeError

        async def call(self):
            return None

    with patch("bluetooth_adapters.dbus.MessageBus", MockMessageBus), patch(
        "bluetooth_adapters.dbus.is_docker_env", return_value=True
    ):
        assert await get_bluetooth_adapters() == []


@pytest.mark.asyncio
async def test_get_bluetooth_adapters_connect_eof_error():
    class MockMessageBus:
        def __init__(self, *args, **kwargs):
            pass

        async def connect(self):
            return AsyncMock(
                disconnect=MagicMock(), call=AsyncMock(side_effect=EOFError)
            )

        async def call(self):
            raise EOFError

    with patch("bluetooth_adapters.dbus.MessageBus", MockMessageBus):
        assert await get_bluetooth_adapters() == []


@pytest.mark.asyncio
async def test_get_bluetooth_adapters_no_call_return():
    class MockMessageBus:
        def __init__(self, *args, **kwargs):
            pass

        async def connect(self):
            return AsyncMock(disconnect=MagicMock(), call=AsyncMock())

        async def call(self):
            return None

    with patch("bluetooth_adapters.dbus.MessageBus", MockMessageBus):
        assert await get_bluetooth_adapters() == []


@pytest.mark.asyncio
async def test_get_bluetooth_adapters_times_out():
    async def _stall(*args: Any) -> None:
        await asyncio.sleep(10)

    class MockMessageBus:
        def __init__(self, *args, **kwargs):
            pass

        async def connect(self):
            return AsyncMock(
                disconnect=MagicMock(),
                call=AsyncMock(side_effect=_stall),
            )

    with patch.object(bluetooth_adapters_dbus, "REPLY_TIMEOUT", 0), patch(
        "bluetooth_adapters.dbus.MessageBus", MockMessageBus
    ):
        assert await get_bluetooth_adapters() == []


@pytest.mark.asyncio
async def test_get_bluetooth_adapters_no_wrong_return():
    class MockMessageBus:
        def __init__(self, *args, **kwargs):
            pass

        async def connect(self):
            return AsyncMock(
                disconnect=MagicMock(),
                call=AsyncMock(
                    return_value=MagicMock(
                        body=[
                            {
                                "/org/bluez/hci0": "",
                                "/org/bluez/hci1": "",
                                "/org/bluez/hci1/any": "",
                            }
                        ],
                        message_type="wrong",
                    )
                ),
            )

    with patch("bluetooth_adapters.dbus.MessageBus", MockMessageBus):
        assert await get_bluetooth_adapters() == []


@pytest.mark.asyncio
async def test_get_bluetooth_adapters_correct_return_valid_message():
    class MockMessageBus:
        def __init__(self, *args, **kwargs):
            pass

        async def connect(self):
            return AsyncMock(
                disconnect=MagicMock(),
                call=AsyncMock(
                    return_value=MagicMock(
                        body=[
                            {
                                "/other": {},
                                "/org/bluez/hci0": {},
                                "/org/bluez/hci1": {},
                                "/org/bluez/hci1/any": {},
                            }
                        ],
                        message_type=MessageType.METHOD_RETURN,
                    )
                ),
            )

    with patch("bluetooth_adapters.dbus.MessageBus", MockMessageBus):
        assert await get_bluetooth_adapters() == ["hci0", "hci1"]


@pytest.mark.asyncio
async def test_get_dbus_managed_objects():
    class MockMessageBus:
        def __init__(self, *args, **kwargs):
            pass

        async def connect(self):
            return AsyncMock(
                disconnect=MagicMock(),
                call=AsyncMock(
                    return_value=MagicMock(
                        body=[
                            {
                                "/other": {},
                                "/org/bluez/hci0": {},
                                "/org/bluez/hci1": {},
                                "/org/bluez/hci1/any": {},
                            }
                        ],
                        message_type=MessageType.METHOD_RETURN,
                    )
                ),
            )

    with patch("bluetooth_adapters.dbus.MessageBus", MockMessageBus):
        assert await get_dbus_managed_objects() == {
            "/other": {},
            "/org/bluez/hci0": {},
            "/org/bluez/hci1": {},
            "/org/bluez/hci1/any": {},
        }


@pytest.mark.asyncio
async def test_BlueZDBusObjects():
    class MockMessageBus:
        def __init__(self, *args, **kwargs):
            pass

        async def connect(self):
            return AsyncMock(
                disconnect=MagicMock(),
                call=AsyncMock(
                    return_value=MagicMock(
                        body=[
                            {
                                "/other": {},
                                "/org/bluez/hci0": {},
                                "/org/bluez/hci1": {},
                                "/org/bluez/hci1/any": {},
                                "/org/bluez/hci0/dev_54_D2_72_AB_35_95": {
                                    "org.freedesktop.DBus.Introspectable": {},
                                    "org.bluez.Device1": {
                                        "Address": "54:D2:72:AB:35:95",
                                        "AddressType": "public",
                                        "Name": "Nuki_1EAB3595",
                                        "Alias": "Nuki_1EAB3595",
                                        "Paired": False,
                                        "Trusted": False,
                                        "Blocked": False,
                                        "LegacyPairing": False,
                                        "RSSI": -78,
                                        "Connected": False,
                                        "UUIDs": [],
                                        "Adapter": "/org/bluez/hci0",
                                        "ManufacturerData": {
                                            "76": b"\\x02\\x15\\xa9.\\xe2\\x00U\\x01\\x11\\xe4\\x91l\\x08\\x00 \\x0c\\x9af\\x1e\\xab5\\x95\\xc4"
                                        },
                                        "ServicesResolved": False,
                                        "AdvertisingFlags": {
                                            "__type": "<class 'bytearray'>",
                                            "repr": "bytearray(b'\\x06')",
                                        },
                                    },
                                    "org.freedesktop.DBus.Properties": {},
                                },
                                "/org/bluez/hci1/dev_54_D2_72_AB_35_95": {
                                    "org.freedesktop.DBus.Introspectable": {},
                                    "org.bluez.Device1": {
                                        "Address": "54:D2:72:AB:35:95",
                                        "AddressType": "public",
                                        "Name": "Nuki_1EAB3595",
                                        "Alias": "Nuki_1EAB3595",
                                        "Paired": False,
                                        "Trusted": False,
                                        "Blocked": False,
                                        "LegacyPairing": False,
                                        "RSSI": -100,
                                        "Connected": False,
                                        "UUIDs": [],
                                        "Adapter": "/org/bluez/hci0",
                                        "ManufacturerData": {
                                            "76": b"\\x02\\x15\\xa9.\\xe2\\x00U\\x01\\x11\\xe4\\x91l\\x08\\x00 \\x0c\\x9af\\x1e\\xab5\\x95\\xc4"
                                        },
                                        "ServicesResolved": False,
                                        "AdvertisingFlags": {
                                            "__type": "<class 'bytearray'>",
                                            "repr": "bytearray(b'\\x06')",
                                        },
                                    },
                                    "org.freedesktop.DBus.Properties": {},
                                },
                            }
                        ],
                        message_type=MessageType.METHOD_RETURN,
                    )
                ),
            )

    with patch("bluetooth_adapters.dbus.MessageBus", MockMessageBus):
        bluez = BlueZDBusObjects()
        await bluez.load()
        assert bluez.adapters == ["hci0", "hci1"]
        assert bluez.adapter_details == {"hci0": {}, "hci1": {}}
        assert bluez.history == {
            "54:D2:72:AB:35:95": AdvertisementHistory(ANY, ANY, "hci0")
        }
        assert bluez.history["54:D2:72:AB:35:95"].device.rssi == -78


@pytest.mark.asyncio
async def test_get_adapters_linux():
    """Test get_adapters."""

    class MockMessageBus:
        def __init__(self, *args, **kwargs):
            pass

        async def connect(self):
            return AsyncMock(
                disconnect=MagicMock(),
                call=AsyncMock(
                    return_value=MagicMock(
                        body=[
                            {
                                "/other": {},
                                "/org/bluez/hci0": {
                                    "org.bluez.Adapter1": {
                                        "Address": "00:1A:7D:DA:71:04",
                                        "AddressType": "public",
                                        "Alias": "homeassistant",
                                        "Class": 2883584,
                                        "Discoverable": False,
                                        "DiscoverableTimeout": 180,
                                        "Discovering": True,
                                        "Modalias": "usb:v1D6Bp0246d053F",
                                        "Name": "homeassistant",
                                        "Pairable": False,
                                        "PairableTimeout": 0,
                                        "Powered": True,
                                        "Roles": ["central", "peripheral"],
                                        "UUIDs": [
                                            "0000110e-0000-1000-8000-00805f9b34fb",
                                            "0000110a-0000-1000-8000-00805f9b34fb",
                                            "00001200-0000-1000-8000-00805f9b34fb",
                                            "0000110b-0000-1000-8000-00805f9b34fb",
                                            "00001108-0000-1000-8000-00805f9b34fb",
                                            "0000110c-0000-1000-8000-00805f9b34fb",
                                            "00001800-0000-1000-8000-00805f9b34fb",
                                            "00001801-0000-1000-8000-00805f9b34fb",
                                            "0000180a-0000-1000-8000-00805f9b34fb",
                                            "00001112-0000-1000-8000-00805f9b34fb",
                                        ],
                                    },
                                    "org.bluez.GattManager1": {},
                                    "org.bluez.LEAdvertisingManager1": {
                                        "ActiveInstances": 0,
                                        "SupportedIncludes": [
                                            "tx-power",
                                            "appearance",
                                            "local-name",
                                        ],
                                        "SupportedInstances": 5,
                                    },
                                    "org.bluez.Media1": {},
                                    "org.bluez.NetworkServer1": {},
                                    "org.freedesktop.DBus.Introspectable": {},
                                    "org.freedesktop.DBus.Properties": {},
                                },
                                "/org/bluez/hci1": {},
                                "/org/bluez/hci1/any": {},
                                "/org/bluez/hci0/dev_54_D2_72_AB_35_95": {
                                    "org.freedesktop.DBus.Introspectable": {},
                                    "org.bluez.Device1": {
                                        "Address": "54:D2:72:AB:35:95",
                                        "AddressType": "public",
                                        "Name": "Nuki_1EAB3595",
                                        "Alias": "Nuki_1EAB3595",
                                        "Paired": False,
                                        "Trusted": False,
                                        "Blocked": False,
                                        "LegacyPairing": False,
                                        "RSSI": -78,
                                        "Connected": False,
                                        "UUIDs": [],
                                        "Adapter": "/org/bluez/hci0",
                                        "ManufacturerData": {
                                            "76": b"\\x02\\x15\\xa9.\\xe2\\x00U\\x01\\x11\\xe4\\x91l\\x08\\x00 \\x0c\\x9af\\x1e\\xab5\\x95\\xc4"
                                        },
                                        "ServicesResolved": False,
                                        "AdvertisingFlags": {
                                            "__type": "<class 'bytearray'>",
                                            "repr": "bytearray(b'\\x06')",
                                        },
                                    },
                                    "org.freedesktop.DBus.Properties": {},
                                },
                                "/org/bluez/hci1/dev_54_D2_72_AB_35_95": {
                                    "org.freedesktop.DBus.Introspectable": {},
                                    "org.bluez.Device1": {
                                        "Address": "54:D2:72:AB:35:95",
                                        "AddressType": "public",
                                        "Name": "Nuki_1EAB3595",
                                        "Alias": "Nuki_1EAB3595",
                                        "Paired": False,
                                        "Trusted": False,
                                        "Blocked": False,
                                        "LegacyPairing": False,
                                        "RSSI": -100,
                                        "Connected": False,
                                        "UUIDs": [],
                                        "Adapter": "/org/bluez/hci0",
                                        "ManufacturerData": {
                                            "76": b"\\x02\\x15\\xa9.\\xe2\\x00U\\x01\\x11\\xe4\\x91l\\x08\\x00 \\x0c\\x9af\\x1e\\xab5\\x95\\xc4"
                                        },
                                        "ServicesResolved": False,
                                        "AdvertisingFlags": {
                                            "__type": "<class 'bytearray'>",
                                            "repr": "bytearray(b'\\x06')",
                                        },
                                    },
                                    "org.freedesktop.DBus.Properties": {},
                                },
                            }
                        ],
                        message_type=MessageType.METHOD_RETURN,
                    )
                ),
            )

    with patch("platform.system", return_value="Linux"), patch(
        "bluetooth_adapters.dbus.MessageBus", MockMessageBus
    ):
        bluetooth_adapters = get_adapters()
        await bluetooth_adapters.refresh()
        assert bluetooth_adapters.default_adapter == "hci0"
        assert bluetooth_adapters.history == {
            "54:D2:72:AB:35:95": AdvertisementHistory(
                device=ANY, advertisement_data=ANY, source="hci0"
            )
        }
        assert bluetooth_adapters.adapters == {
            "hci0": {
                "address": "00:1A:7D:DA:71:04",
                "hw_version": "usb:v1D6Bp0246d053F",
                "passive_scan": False,
                "sw_version": "homeassistant",
            },
        }
        assert bluetooth_adapters.adapters == {
            "hci0": {
                "address": "00:1A:7D:DA:71:04",
                "hw_version": "usb:v1D6Bp0246d053F",
                "passive_scan": False,
                "sw_version": "homeassistant",
            },
        }


@pytest.mark.asyncio
async def test_get_adapters_macos():
    """Test get_adapters macos."""

    with patch("platform.system", return_value="Darwin"), patch(
        "platform.release", return_value="18.7.0"
    ):
        bluetooth_adapters = get_adapters()
        await bluetooth_adapters.refresh()
        assert bluetooth_adapters.default_adapter == "Core Bluetooth"
        assert bluetooth_adapters.history == {}
        assert bluetooth_adapters.adapters == {
            "Core Bluetooth": {
                "address": "00:00:00:00:00:00",
                "passive_scan": False,
                "sw_version": "18.7.0",
            }
        }


@pytest.mark.asyncio
async def test_get_adapters_windows():
    """Test get_adapters windows."""

    with patch("platform.system", return_value="Windows"), patch(
        "platform.release", return_value="18.7.0"
    ):
        bluetooth_adapters = get_adapters()
        await bluetooth_adapters.refresh()
        assert bluetooth_adapters.default_adapter == "bluetooth"
        assert bluetooth_adapters.history == {}
        assert bluetooth_adapters.adapters == {
            "bluetooth": {
                "address": "00:00:00:00:00:00",
                "passive_scan": False,
                "sw_version": "18.7.0",
            }
        }


def test_adapter_human_name():
    """Test adapter human name."""
    assert adapter_human_name("hci0", DEFAULT_ADDRESS) == "hci0"
    assert adapter_human_name("hci0", "aa:bb:cc:dd:ee:ff") == "hci0 (aa:bb:cc:dd:ee:ff)"


def test_adapter_unique_name():
    """Test adapter unique name."""
    assert adapter_unique_name("hci0", DEFAULT_ADDRESS) == "hci0"
    assert adapter_unique_name("hci0", "aa:bb:cc:dd:ee:ff") == "aa:bb:cc:dd:ee:ff"
