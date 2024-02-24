from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiooui
from usb_devices import BluetoothDevice, NotAUSBDeviceError

from ..adapters import BluetoothAdapters
from ..const import EMPTY_MAC_ADDRESS, UNIX_DEFAULT_BLUETOOTH_ADAPTER
from ..dbus import BlueZDBusObjects
from ..history import AdvertisementHistory
from ..models import AdapterDetails
from .linux_hci import get_adapters_from_hci

_LOGGER = logging.getLogger(__name__)


class LinuxAdapters(BluetoothAdapters):
    """Class for getting the bluetooth adapters on a Linux system."""

    def __init__(self) -> None:
        """Initialize the adapter."""
        self._bluez = BlueZDBusObjects()
        self._adapters: dict[str, AdapterDetails] | None = None
        self._devices: dict[str, BluetoothDevice] = {}
        self._hci_output: dict[int, dict[str, Any]] | None = None

    async def refresh(self) -> None:
        """Refresh the adapters."""
        loop = asyncio.get_running_loop()
        load_task = asyncio.create_task(self._bluez.load())
        adapters_from_hci_future = loop.run_in_executor(None, get_adapters_from_hci)
        futures: list[asyncio.Future[Any]] = [load_task, adapters_from_hci_future]
        if not aiooui.is_loaded():
            futures.append(aiooui.async_load())
        await asyncio.gather(*futures)
        self._hci_output = await adapters_from_hci_future
        self._adapters = None  # clear cache
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
            if self._hci_output:
                for hci_details in self._hci_output.values():
                    name = hci_details["name"]
                    mac_address = hci_details["bdaddr"].upper()
                    manufacturer = aiooui.get_vendor(mac_address)
                    adapters[name] = AdapterDetails(
                        address=mac_address,
                        sw_version="Unknown",
                        hw_version=None,
                        passive_scan=False,  # assume false if we don't know
                        manufacturer=manufacturer,
                        product=None,
                        vendor_id=None,
                        product_id=None,
                    )
            adapter_details = self._bluez.adapter_details
            for adapter, details in adapter_details.items():
                if not (adapter1 := details.get("org.bluez.Adapter1")):
                    continue
                mac_address = adapter1["Address"]
                if mac_address == EMPTY_MAC_ADDRESS:
                    # Ignore adapters with 00:00:00:00:00:00 address
                    # https://github.com/home-assistant/operating-system/issues/2944
                    continue
                device = self._devices[adapter]
                usb_device = device.usb_device
                if (
                    usb_device is None
                    or usb_device.vendor_id == usb_device.manufacturer
                    or usb_device.manufacturer is None
                    or usb_device.manufacturer == "Unknown"
                ):
                    manufacturer = aiooui.get_vendor(mac_address)
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
