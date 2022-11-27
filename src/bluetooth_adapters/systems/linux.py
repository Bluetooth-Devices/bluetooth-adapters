from __future__ import annotations

import asyncio
import contextlib
import logging

import aiohttp
import async_timeout
from mac_vendor_lookup import AsyncMacLookup
from usb_devices import BluetoothDevice, NotAUSBDeviceError

from ..adapters import BluetoothAdapters
from ..const import UNIX_DEFAULT_BLUETOOTH_ADAPTER
from ..dbus import BlueZDBusObjects
from ..history import AdvertisementHistory
from ..models import AdapterDetails

_LOGGER = logging.getLogger(__name__)


class LinuxAdapters(BluetoothAdapters):
    """Class for getting the bluetooth adapters on a Linux system."""

    def __init__(self) -> None:
        """Initialize the adapter."""
        self._bluez = BlueZDBusObjects()
        self._adapters: dict[str, AdapterDetails] | None = None
        self._devices: dict[str, BluetoothDevice] = {}
        self._mac_vendor_lookup: AsyncMacLookup | None = None

    async def refresh(self) -> None:
        """Refresh the adapters."""
        await self._bluez.load()
        await asyncio.get_running_loop().run_in_executor(
            None, self._create_bluetooth_devices
        )
        if not self._mac_vendor_lookup:
            await self._async_setup()
        self._adapters = None

    async def _async_setup(self) -> None:
        self._mac_vendor_lookup = AsyncMacLookup()
        with contextlib.suppress(
            asyncio.TimeoutError, aiohttp.ClientError, asyncio.TimeoutError
        ):
            # We don't care if this fails since it only
            # improves the data we get.
            async with async_timeout.timeout(3):
                await self._mac_vendor_lookup.load_vendors()

    def _async_get_vendor(self, mac_address: str) -> str | None:
        """Lookup the vendor."""
        assert self._mac_vendor_lookup is not None  # nosec
        oui = self._mac_vendor_lookup.sanitise(mac_address)[:6]
        vendor: bytes | None = self._mac_vendor_lookup.prefixes.get(oui.encode())
        return vendor.decode()[:254] if vendor is not None else None

    def _create_bluetooth_devices(self) -> None:
        """Create the bluetooth devices."""
        self._devices = {}
        for adapter in self._bluez.adapter_details:
            i = int(adapter[3:])
            dev = BluetoothDevice(i)
            self._devices[adapter] = dev
            try:
                dev.setup()
            except NotAUSBDeviceError:
                continue
            except FileNotFoundError:
                continue
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error setting up device hci%s", dev)

    @property
    def history(self) -> dict[str, AdvertisementHistory]:
        """Get the bluez history."""
        return self._bluez.history

    @property
    def adapters(self) -> dict[str, AdapterDetails]:
        """Get the adapter details."""
        if self._adapters is None:
            adapters: dict[str, AdapterDetails] = {}
            adapter_details = self._bluez.adapter_details
            for adapter, details in adapter_details.items():
                if not (adapter1 := details.get("org.bluez.Adapter1")):
                    continue
                device = self._devices[adapter]
                usb_device = device.usb_device
                mac_address = adapter1["Address"]
                if (
                    usb_device is None
                    or usb_device.vendor_id == usb_device.manufacturer
                    or usb_device.manufacturer is None
                    or usb_device.manufacturer == "Unknown"
                ):
                    manufacturer = self._async_get_vendor(mac_address)
                else:
                    manufacturer = usb_device.manufacturer
                adapters[adapter] = AdapterDetails(
                    address=mac_address,
                    sw_version=adapter1["Name"],  # This is actually the BlueZ version
                    hw_version=adapter1.get("Modalias"),
                    passive_scan="org.bluez.AdvertisementMonitorManager1" in details,
                    manufacturer=manufacturer,
                    product=usb_device.product if usb_device else None,
                    vendor_id=usb_device.vendor_id if usb_device else None,
                    product_id=usb_device.product_id if usb_device else None,
                )
            self._adapters = adapters
        return self._adapters

    @property
    def default_adapter(self) -> str:
        """Get the default adapter."""
        return UNIX_DEFAULT_BLUETOOTH_ADAPTER
