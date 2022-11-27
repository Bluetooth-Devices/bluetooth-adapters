from __future__ import annotations

import asyncio
import logging

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

    async def refresh(self) -> None:
        """Refresh the adapters."""
        await self._bluez.load()
        await asyncio.get_running_loop().run_in_executor(
            None, self._create_bluetooth_devices
        )
        self._adapters = None

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
                if adapter1 := details.get("org.bluez.Adapter1"):
                    device = self._devices[adapter]
                    usb_device = device.usb_device
                    adapters[adapter] = AdapterDetails(
                        address=adapter1["Address"],
                        sw_version=adapter1[
                            "Name"
                        ],  # This is actually the BlueZ version
                        hw_version=adapter1.get("Modalias"),
                        passive_scan="org.bluez.AdvertisementMonitorManager1"
                        in details,
                        manufacturer=usb_device.manufacturer if usb_device else None,
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
