"""Models for bluetooth adapters."""

from __future__ import annotations

from typing import Final, TypedDict


class AdapterDetails(TypedDict, total=False):
    """Adapter details."""

    address: str
    sw_version: str
    hw_version: str | None
    passive_scan: bool


ADAPTER_ADDRESS: Final = "address"
ADAPTER_SW_VERSION: Final = "sw_version"
ADAPTER_HW_VERSION: Final = "hw_version"
ADAPTER_PASSIVE_SCAN: Final = "passive_scan"
