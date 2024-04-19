import asyncio
import time
from platform import system
from typing import Any
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

try:
    from dbus_fast import MessageType
except (AttributeError, ImportError):
    MessageType = None
    # dbus_fast is not available on Windows
from uart_devices import BluetoothDevice as UARTBluetoothDevice
from uart_devices import UARTDevice
from usb_devices import BluetoothDevice as USBBluetoothDevice
from usb_devices import NotAUSBDeviceError, USBDevice

import bluetooth_adapters.dbus as bluetooth_adapters_dbus

if system() != "Windows":
    from bluetooth_adapters import (
        BlueZDBusObjects,
        get_bluetooth_adapters,
        get_dbus_managed_objects,
    )
else:
    BlueZDBusObjects = None  # type: ignore
    get_bluetooth_adapters = None  # type: ignore
    get_dbus_managed_objects = None  # type: ignore

from bluetooth_adapters import (
    DEFAULT_ADDRESS,
    AdapterDetails,
    AdvertisementHistory,
    DiscoveredDeviceAdvertisementData,
    DiscoveredDeviceAdvertisementDataDict,
    adapter_human_name,
    adapter_model,
    adapter_unique_name,
    discovered_device_advertisement_data_from_dict,
    discovered_device_advertisement_data_to_dict,
    expire_stale_scanner_discovered_device_advertisement_data,
    get_adapters,
    load_history_from_managed_objects,
)


@pytest.mark.asyncio
@pytest.mark.skipif(
    MessageType is None or get_dbus_managed_objects is None,
    reason="dbus_fast is not available",
)
async def test_get_bluetooth_adapters_file_not_found():
    """Test get_bluetooth_adapters()."""

    class MockMessageBus:
        def __init__(self, *args, **kwargs):
            raise FileNotFoundError

    with patch("bluetooth_adapters.dbus.MessageBus", MockMessageBus):
        assert await get_bluetooth_adapters() == []


@pytest.mark.asyncio
@pytest.mark.skipif(
    MessageType is None or get_dbus_managed_objects is None,
    reason="dbus_fast is not available",
)
async def test_get_bluetooth_adapters_connection_refused():
    """Test get_bluetooth_adapters with connection refused."""

    class MockMessageBus:
        def __init__(self, *args, **kwargs):
            raise ConnectionRefusedError

    with patch("bluetooth_adapters.dbus.MessageBus", MockMessageBus):
        assert await get_bluetooth_adapters() == []


@pytest.mark.asyncio
@pytest.mark.skipif(
    MessageType is None or get_dbus_managed_objects is None,
    reason="dbus_fast is not available",
)
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
@pytest.mark.skipif(
    MessageType is None or get_dbus_managed_objects is None,
    reason="dbus_fast is not available",
)
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
@pytest.mark.skipif(
    MessageType is None or get_dbus_managed_objects is None,
    reason="dbus_fast is not available",
)
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
@pytest.mark.skipif(
    MessageType is None or get_dbus_managed_objects is None,
    reason="dbus_fast is not available",
)
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
@pytest.mark.skipif(
    MessageType is None or get_dbus_managed_objects is None,
    reason="dbus_fast is not available",
)
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
@pytest.mark.skipif(
    MessageType is None or get_dbus_managed_objects is None,
    reason="dbus_fast is not available",
)
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
@pytest.mark.skipif(
    MessageType is None or get_dbus_managed_objects is None,
    reason="dbus_fast is not available",
)
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
@pytest.mark.skipif(
    MessageType is None or get_dbus_managed_objects is None,
    reason="dbus_fast is not available",
)
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
@pytest.mark.skipif(
    MessageType is None or get_dbus_managed_objects is None,
    reason="dbus_fast is not available",
)
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
@pytest.mark.skipif(
    MessageType is None or get_dbus_managed_objects is None,
    reason="dbus_fast is not available",
)
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
@pytest.mark.skipif(
    MessageType is None or get_dbus_managed_objects is None,
    reason="dbus_fast is not available",
)
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
@pytest.mark.skipif(
    MessageType is None or get_dbus_managed_objects is None,
    reason="dbus_fast is not available",
)
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
        assert (
            len(
                load_history_from_managed_objects(
                    bluez.unpacked_managed_objects, "hci1"
                )
            )
            == 1
        )


@pytest.mark.asyncio
@pytest.mark.skipif(
    MessageType is None or get_dbus_managed_objects is None,
    reason="dbus_fast is not available",
)
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
                                "/org/bluez/hci2": {
                                    "org.bluez.Adapter1": {
                                        "Address": "00:00:00:00:00:00",
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
                                "/org/bluez/hci3": {
                                    "org.bluez.Adapter1": {
                                        "Address": "00:1A:7D:DA:71:05",
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

    class MockUSBDevice(USBDevice):
        def __init__(self, *args, **kwargs):
            self.manufacturer = "XTech"
            self.product = "Bluetooth 4.0 USB Adapter"
            self.vendor_id = "0a12"
            self.product_id = "0001"
            pass

    class MockBluetoothDevice(USBBluetoothDevice):
        def __init__(self, *args, **kwargs):
            self.usb_device = MockUSBDevice()
            pass

        def setup(self, *args, **kwargs):
            pass

    with patch("platform.system", return_value="Linux"), patch(
        "bluetooth_adapters.dbus.MessageBus", MockMessageBus
    ), patch(
        "bluetooth_adapters.systems.linux.USBBluetoothDevice", MockBluetoothDevice
    ):
        bluetooth_adapters = get_adapters()
        await bluetooth_adapters.refresh()
        assert bluetooth_adapters.default_adapter == "hci0"
        assert bluetooth_adapters.history == {
            "54:D2:72:AB:35:95": AdvertisementHistory(
                device=ANY, advertisement_data=ANY, source="hci0"
            )
        }
        # hci0 should show
        # hci1 is empty so it should not be in the list
        # hci2 should not show as 00:00:00:00:00:00 are filtered downstream now
        # hci3 should show
        assert bluetooth_adapters.adapters == {
            "hci0": {
                "address": "00:1A:7D:DA:71:04",
                "hw_version": "usb:v1D6Bp0246d053F",
                "manufacturer": "XTech",
                "passive_scan": False,
                "product": "Bluetooth 4.0 USB Adapter",
                "product_id": "0001",
                "sw_version": "homeassistant",
                "vendor_id": "0a12",
            },
            "hci2": {
                "address": "00:00:00:00:00:00",
                "hw_version": "usb:v1D6Bp0246d053F",
                "manufacturer": "XTech",
                "passive_scan": False,
                "product": "Bluetooth 4.0 USB Adapter",
                "product_id": "0001",
                "sw_version": "homeassistant",
                "vendor_id": "0a12",
            },
            "hci3": {
                "address": "00:1A:7D:DA:71:05",
                "hw_version": "usb:v1D6Bp0246d053F",
                "manufacturer": "XTech",
                "passive_scan": False,
                "product": "Bluetooth 4.0 USB Adapter",
                "product_id": "0001",
                "sw_version": "homeassistant",
                "vendor_id": "0a12",
            },
        }


@pytest.mark.asyncio
@pytest.mark.skipif(
    MessageType is None or get_dbus_managed_objects is None,
    reason="dbus_fast is not available",
)
async def test_get_adapters_linux_uart():
    """Test get_adapters with uart devices."""

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
                                "/org/bluez/hci2": {
                                    "org.bluez.Adapter1": {
                                        "Address": "00:00:00:00:00:00",
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
                                "/org/bluez/hci3": {
                                    "org.bluez.Adapter1": {
                                        "Address": "00:1A:7D:DA:71:05",
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

    class MockUARTDevice(UARTDevice):
        def __init__(self, *args, **kwargs):
            self.manufacturer = "XTech"
            self.product = "Bluetooth 4.0 USB Adapter"
            pass

    class MockUARTBluetoothDevice(UARTBluetoothDevice):
        def __init__(self, *args, **kwargs):
            self.uart_device = MockUARTDevice()
            pass

        def setup(self, *args, **kwargs):
            pass

    class MockUSBBluetoothDevice(UARTBluetoothDevice):
        def __init__(self, *args, **kwargs):
            self.uart_device = MockUARTDevice()
            pass

        def setup(self, *args, **kwargs):
            raise NotAUSBDeviceError

    with patch("platform.system", return_value="Linux"), patch(
        "bluetooth_adapters.dbus.MessageBus", MockMessageBus
    ), patch(
        "bluetooth_adapters.systems.linux.USBBluetoothDevice", MockUSBBluetoothDevice
    ), patch(
        "bluetooth_adapters.systems.linux.UARTBluetoothDevice", MockUARTBluetoothDevice
    ):
        bluetooth_adapters = get_adapters()
        await bluetooth_adapters.refresh()
        assert bluetooth_adapters.default_adapter == "hci0"
        assert bluetooth_adapters.history == {
            "54:D2:72:AB:35:95": AdvertisementHistory(
                device=ANY, advertisement_data=ANY, source="hci0"
            )
        }
        # hci0 should show
        # hci1 is empty so it should not be in the list
        # hci2 should not show as 00:00:00:00:00:00 are filtered downstream now
        # hci3 should show
        assert bluetooth_adapters.adapters == {
            "hci0": {
                "address": "00:1A:7D:DA:71:04",
                "hw_version": "usb:v1D6Bp0246d053F",
                "manufacturer": "cyber-blue(HK)Ltd",
                "passive_scan": False,
                "product": "Bluetooth 4.0 USB Adapter",
                "product_id": None,
                "sw_version": "homeassistant",
                "vendor_id": None,
            },
            "hci2": {
                "address": "00:00:00:00:00:00",
                "hw_version": "usb:v1D6Bp0246d053F",
                "manufacturer": "XTech",
                "passive_scan": False,
                "product": "Bluetooth 4.0 USB Adapter",
                "product_id": None,
                "sw_version": "homeassistant",
                "vendor_id": None,
            },
            "hci3": {
                "address": "00:1A:7D:DA:71:05",
                "hw_version": "usb:v1D6Bp0246d053F",
                "manufacturer": "cyber-blue(HK)Ltd",
                "passive_scan": False,
                "product": "Bluetooth 4.0 USB Adapter",
                "product_id": None,
                "sw_version": "homeassistant",
                "vendor_id": None,
            },
        }


@pytest.mark.asyncio
@pytest.mark.skipif(
    MessageType is None or get_dbus_managed_objects is None,
    reason="dbus_fast is not available",
)
async def test_get_adapters_linux_no_usb_device():
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
                                "/org/bluez/hci3": {
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
                                "/org/bluez/hci4": {},
                                "/org/bluez/hci5/any": {},
                                "/org/bluez/hci3/dev_54_D2_72_AB_35_95": {
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
                                        "Adapter": "/org/bluez/hci3",
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

    class NoMfrMockUSBDevice(USBDevice):
        def __init__(self, *args, **kwargs):
            self.manufacturer = None
            self.product = "Bluetooth 4.0 USB Adapter"
            self.vendor_id = "0a12"
            self.product_id = "0001"
            pass

    class NoMfrMockBluetoothDevice(USBBluetoothDevice):
        def __init__(self, *args, **kwargs):
            self.usb_device = NoMfrMockUSBDevice()
            pass

        def setup(self, *args, **kwargs):
            pass

    with patch("platform.system", return_value="Linux"), patch(
        "bluetooth_adapters.dbus.MessageBus", MockMessageBus
    ), patch(
        "bluetooth_adapters.systems.linux.USBBluetoothDevice", NoMfrMockBluetoothDevice
    ):
        bluetooth_adapters = get_adapters()
        await bluetooth_adapters.refresh()
        assert bluetooth_adapters.default_adapter == "hci0"
        assert bluetooth_adapters.history == {
            "54:D2:72:AB:35:95": AdvertisementHistory(
                device=ANY, advertisement_data=ANY, source="hci3"
            )
        }
        assert bluetooth_adapters.adapters == {
            "hci3": {
                "address": "00:1A:7D:DA:71:04",
                "manufacturer": "cyber-blue(HK)Ltd",
                "product": "Bluetooth 4.0 USB Adapter",
                "vendor_id": "0a12",
                "product_id": "0001",
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
                "manufacturer": "Apple",
                "product": "Unknown MacOS Model",
                "vendor_id": "Unknown",
                "product_id": "Unknown",
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
                "manufacturer": "Microsoft",
                "product": "Unknown Windows Model",
                "vendor_id": "Unknown",
                "product_id": "Unknown",
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


def test_adapter_model():
    """Test adapter model."""
    windows_details = AdapterDetails(
        {
            "address": "00:00:00:00:00:00",
            "passive_scan": False,
            "sw_version": "18.7.0",
            "manufacturer": "Microsoft",
            "product": "Unknown Windows Model",
            "vendor_id": "Unknown",
            "product_id": "Unknown",
        }
    )
    assert adapter_model(windows_details) == "Unknown Windows Model"
    linux_details = AdapterDetails(
        {
            "address": "00:1A:7D:DA:71:04",
            "manufacturer": "XTech",
            "product": "Bluetooth 4.0 USB Adapter",
            "vendor_id": "0a12",
            "product_id": "0001",
            "hw_version": "usb:v1D6Bp0246d053F",
            "passive_scan": False,
            "sw_version": "homeassistant",
        }
    )
    assert adapter_model(linux_details) == "Bluetooth 4.0 USB Adapter (0a12:0001)"


def test_discovered_device_advertisement_data_to_dict():
    """Test discovered device advertisement data to dict."""
    result = discovered_device_advertisement_data_to_dict(
        DiscoveredDeviceAdvertisementData(
            True,
            100,
            {
                "AA:BB:CC:DD:EE:FF": (
                    BLEDevice(
                        address="AA:BB:CC:DD:EE:FF",
                        name="Test Device",
                        details={"details": "test"},
                        rssi=-50,
                    ),
                    AdvertisementData(
                        local_name="Test Device",
                        manufacturer_data={0x004C: b"\x02\x15\xaa\xbb\xcc\xdd\xee\xff"},
                        tx_power=50,
                        service_data={
                            "0000180d-0000-1000-8000-00805f9b34fb": b"\x00\x00\x00\x00"
                        },
                        service_uuids=["0000180d-0000-1000-8000-00805f9b34fb"],
                        platform_data=("Test Device", ""),
                        rssi=-50,
                    ),
                )
            },
            {"AA:BB:CC:DD:EE:FF": 100000},
        )
    )
    assert result == {
        "connectable": True,
        "discovered_device_advertisement_datas": {
            "AA:BB:CC:DD:EE:FF": {
                "advertisement_data": {
                    "local_name": "Test " "Device",
                    "manufacturer_data": {"76": "0215aabbccddeeff"},
                    "rssi": -50,
                    "service_data": {
                        "0000180d-0000-1000-8000-00805f9b34fb": "00000000"
                    },
                    "service_uuids": ["0000180d-0000-1000-8000-00805f9b34fb"],
                    "tx_power": 50,
                    "platform_data": ["Test Device", ""],
                },
                "device": {
                    "address": "AA:BB:CC:DD:EE:FF",
                    "details": {"details": "test"},
                    "name": "Test " "Device",
                    "rssi": -50,
                },
            }
        },
        "discovered_device_timestamps": {"AA:BB:CC:DD:EE:FF": ANY},
        "expire_seconds": 100,
    }


def test_discovered_device_advertisement_data_from_dict():
    now = time.time()
    result = discovered_device_advertisement_data_from_dict(
        {
            "connectable": True,
            "discovered_device_advertisement_datas": {
                "AA:BB:CC:DD:EE:FF": {
                    "advertisement_data": {
                        "local_name": "Test " "Device",
                        "manufacturer_data": {"76": "0215aabbccddeeff"},
                        "rssi": -50,
                        "service_data": {
                            "0000180d-0000-1000-8000-00805f9b34fb": "00000000"
                        },
                        "service_uuids": ["0000180d-0000-1000-8000-00805f9b34fb"],
                        "tx_power": 50,
                        "platform_data": ["Test Device", ""],
                    },
                    "device": {
                        "address": "AA:BB:CC:DD:EE:FF",
                        "details": {"details": "test"},
                        "name": "Test " "Device",
                        "rssi": -50,
                    },
                }
            },
            "discovered_device_timestamps": {"AA:BB:CC:DD:EE:FF": now},
            "expire_seconds": 100,
        }
    )

    expected_ble_device = BLEDevice(
        address="AA:BB:CC:DD:EE:FF",
        name="Test Device",
        details={"details": "test"},
        rssi=-50,
    )

    expected_advertisement_data = AdvertisementData(
        local_name="Test Device",
        manufacturer_data={0x004C: b"\x02\x15\xAA\xBB\xCC\xDD\xEE\xFF"},
        tx_power=50,
        service_data={"0000180d-0000-1000-8000-00805f9b34fb": b"\x00\x00\x00\x00"},
        service_uuids=["0000180d-0000-1000-8000-00805f9b34fb"],
        platform_data=("Test Device", ""),
        rssi=-50,
    )
    assert result is not None
    out_ble_device = result.discovered_device_advertisement_datas["AA:BB:CC:DD:EE:FF"][
        0
    ]
    out_advertisement_data = result.discovered_device_advertisement_datas[
        "AA:BB:CC:DD:EE:FF"
    ][1]
    assert out_ble_device.address == expected_ble_device.address
    assert out_ble_device.name == expected_ble_device.name
    assert out_ble_device.details == expected_ble_device.details
    assert out_ble_device.rssi == expected_ble_device.rssi
    assert out_ble_device.metadata == expected_ble_device.metadata
    assert out_advertisement_data == expected_advertisement_data

    assert result == DiscoveredDeviceAdvertisementData(
        connectable=True,
        expire_seconds=100,
        discovered_device_advertisement_datas={
            "AA:BB:CC:DD:EE:FF": (
                ANY,
                expected_advertisement_data,
            )
        },
        discovered_device_timestamps={"AA:BB:CC:DD:EE:FF": ANY},
    )


@pytest.mark.skipif(
    MessageType is None or get_dbus_managed_objects is None,
    reason="dbus_fast is not available",
)
def test_expire_stale_scanner_discovered_device_advertisement_data():
    """Test expire_stale_scanner_discovered_device_advertisement_data."""
    now = time.time()
    data = {
        "myscanner": DiscoveredDeviceAdvertisementDataDict(
            {
                "connectable": True,
                "discovered_device_advertisement_datas": {
                    "AA:BB:CC:DD:EE:FF": {
                        "advertisement_data": {
                            "local_name": "Test " "Device",
                            "manufacturer_data": {"76": "0215aabbccddeeff"},
                            "rssi": -50,
                            "service_data": {
                                "0000180d-0000-1000-8000-00805f9b34fb": "00000000"
                            },
                            "service_uuids": ["0000180d-0000-1000-8000-00805f9b34fb"],
                            "tx_power": 50,
                            "platform_data": ["Test Device", ""],
                        },
                        "device": {
                            "address": "AA:BB:CC:DD:EE:FF",
                            "details": {"details": "test"},
                            "name": "Test " "Device",
                            "rssi": -50,
                        },
                    },
                    "CC:DD:EE:FF:AA:BB": {
                        "advertisement_data": {
                            "local_name": "Test " "Device Expired",
                            "manufacturer_data": {"76": "0215aabbccddeeff"},
                            "rssi": -50,
                            "service_data": {
                                "0000180d-0000-1000-8000-00805f9b34fb": "00000000"
                            },
                            "service_uuids": ["0000180d-0000-1000-8000-00805f9b34fb"],
                            "tx_power": 50,
                            "platform_data": ["Test Device", ""],
                        },
                        "device": {
                            "address": "CC:DD:EE:FF:AA:BB",
                            "details": {"details": "test"},
                            "name": "Test " "Device Expired",
                            "rssi": -50,
                        },
                    },
                },
                "discovered_device_timestamps": {
                    "AA:BB:CC:DD:EE:FF": now,
                    "CC:DD:EE:FF:AA:BB": now - 100,
                },
                "expire_seconds": 100,
            }
        ),
        "all_expired": DiscoveredDeviceAdvertisementDataDict(
            {
                "connectable": True,
                "discovered_device_advertisement_datas": {
                    "CC:DD:EE:FF:AA:BB": {
                        "advertisement_data": {
                            "local_name": "Test " "Device Expired",
                            "manufacturer_data": {"76": "0215aabbccddeeff"},
                            "rssi": -50,
                            "service_data": {
                                "0000180d-0000-1000-8000-00805f9b34fb": "00000000"
                            },
                            "service_uuids": ["0000180d-0000-1000-8000-00805f9b34fb"],
                            "tx_power": 50,
                            "platform_data": ["Test Device", ""],
                        },
                        "device": {
                            "address": "CC:DD:EE:FF:AA:BB",
                            "details": {"details": "test"},
                            "name": "Test " "Device Expired",
                            "rssi": -50,
                        },
                    }
                },
                "discovered_device_timestamps": {"CC:DD:EE:FF:AA:BB": now - 100},
                "expire_seconds": 100,
            }
        ),
    }
    expire_stale_scanner_discovered_device_advertisement_data(data)
    assert len(data["myscanner"]["discovered_device_advertisement_datas"]) == 1
    assert (
        "CC:DD:EE:FF:AA:BB"
        not in data["myscanner"]["discovered_device_advertisement_datas"]
    )
    assert "all_expired" not in data


def test_discovered_device_advertisement_data_from_dict_corrupt(caplog):
    """Test discovered_device_advertisement_data_from_dict with corrupt data."""
    now = time.time()
    result = discovered_device_advertisement_data_from_dict(
        {
            "connectable": True,
            "discovered_device_advertisement_datas": {
                "AA:BB:CC:DD:EE:FF": {
                    "advertisement_data": {  # type: ignore[typeddict-item]
                        "local_name": "Test " "Device",
                        "manufacturer_data": {"76": "0215aabbccddeeff"},
                        "rssi": -50,
                        "service_data": {
                            "0000180d-0000-1000-8000-00805f9b34fb": "00000000"
                        },
                        "service_uuids": ["0000180d-0000-1000-8000-00805f9b34fb"],
                    },
                    "device": {  # type: ignore[typeddict-item]
                        "address": "AA:BB:CC:DD:EE:FF",
                        "details": {"details": "test"},
                        "rssi": -50,
                    },
                }
            },
            "discovered_device_timestamps": {"AA:BB:CC:DD:EE:FF": now},
            "expire_seconds": 100,
        }
    )
    assert result is None
    assert "Error deserializing discovered_device_advertisement_data" in caplog.text
