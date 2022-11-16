from __future__ import annotations

from ..adapters import BluetoothAdapters
from ..const import UNIX_DEFAULT_BLUETOOTH_ADAPTER
from ..dbus import BlueZDBusObjects
from ..history import AdvertisementHistory
from ..models import AdapterDetails


class LinuxAdapters(BluetoothAdapters):
    """Class for getting the bluetooth adapters on a Linux system."""

    def __init__(self) -> None:
        """Initialize the adapter."""
        self._bluez = BlueZDBusObjects()

    async def refresh(self) -> None:
        """Refresh the adapters."""
        await self._bluez.load()

    @property
    def history(self) -> dict[str, AdvertisementHistory]:
        """Get the bluez history."""
        return self._bluez.history

    @property
    def adapters(self) -> dict[str, AdapterDetails]:
        """Get the adapter details."""
        adapters: dict[str, AdapterDetails] = {}
        adapter_details = self._bluez.adapter_details
        for adapter, details in adapter_details.items():
            adapter1 = details["org.bluez.Adapter1"]
            adapters[adapter] = AdapterDetails(
                address=adapter1["Address"],
                sw_version=adapter1["Name"],  # This is actually the BlueZ version
                hw_version=adapter1.get("Modalias"),
                passive_scan="org.bluez.AdvertisementMonitorManager1" in details,
            )
        return adapters

    @property
    def default_adapter(self) -> str:
        """Get the default adapter."""
        return UNIX_DEFAULT_BLUETOOTH_ADAPTER
