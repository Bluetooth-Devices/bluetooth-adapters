"""Utils."""
from __future__ import annotations

from .const import DEFAULT_ADDRESS


def adapter_human_name(adapter: str, address: str) -> str:
    """Return a human readable name for the adapter."""
    return adapter if address == DEFAULT_ADDRESS else f"{adapter} ({address})"


def adapter_unique_name(adapter: str, address: str) -> str:
    """Return a unique name for the adapter."""
    return adapter if address == DEFAULT_ADDRESS else address
