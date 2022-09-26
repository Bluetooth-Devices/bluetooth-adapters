__version__ = "0.5.2"

from typing import Any

from .dbus import (
    _adapters_from_managed_objects,
    get_bluetooth_adapter_details,
    get_bluetooth_adapters,
    get_dbus_managed_objects,
)
from .history import AdvertisementHistory, load_history_from_managed_objects

__all__ = [
    "AdvertisementHistory",
    "BlueZDBusObjects",
    "get_bluetooth_adapters",
    "get_bluetooth_adapter_details",
    "get_dbus_managed_objects",
]


class BlueZDBusObjects:
    """Fetch and parse BlueZObjects."""

    def __init__(self) -> None:
        """Init the manager."""
        self._managed_objects: dict[str, Any] = {}

    async def load(self) -> None:
        """Load from the bus."""
        self._managed_objects = await get_dbus_managed_objects()

    @property
    def adapters(self) -> list[str]:
        """Get adapters."""
        return list(self.adapter_details)

    @property
    def adapter_details(self) -> dict[str, dict[str, Any]]:
        """Get adapters."""
        return _adapters_from_managed_objects(self._managed_objects)

    @property
    def history(self) -> dict[str, AdvertisementHistory]:
        """Get history from managed objects."""
        return load_history_from_managed_objects(self._managed_objects)
