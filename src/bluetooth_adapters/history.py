from dataclasses import dataclass
from typing import Any

from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData


@dataclass
class AdvertisementHistory:

    device: BLEDevice
    advertisement_data: AdvertisementData
    source: str


def load_history_from_managed_objects(
    managed_objects: dict[str, Any]
) -> dict[str, AdvertisementHistory]:
    """Load the history from the bus."""
    history: dict[str, AdvertisementHistory] = {}
    for path, packed_data in managed_objects.items():
        path_str = str(path)
        if not path_str.startswith("/org/bluez/hci"):
            continue

        if not (props := packed_data.get("org.bluez.Device1")):
            continue

        address = props["Address"]
        rssi = props.get("RSSI", 0)

        if (prev_history := history.get(address)) and prev_history.device.rssi >= rssi:
            continue

        split_path = path_str.split("/")
        adapter = split_path[3]
        uuids = props.get("UUIDs", [])
        manufacturer_data = {
            k: bytes(v) for k, v in props.get("ManufacturerData", {}).items()
        }
        device = BLEDevice(
            address,
            props["Alias"],
            {"path": path, "props": props},
            rssi,
            uuids=uuids,
            manufacturer_data=manufacturer_data,
        )
        advertisement_data = AdvertisementData(
            local_name=props.get("Name"),
            manufacturer_data=manufacturer_data,
            service_data={k: bytes(v) for k, v in props.get("ServiceData", {}).items()},
            service_uuids=uuids,
            platform_data=props,
            tx_power=props.get("TxPower"),
        )
        history[device.address] = AdvertisementHistory(
            device, advertisement_data, adapter
        )

    return history
