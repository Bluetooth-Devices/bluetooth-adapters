"""Shared pytest fixtures for the bluetooth-adapters test suite.

Adapter discovery on Linux pulls from two independent sources:

* BlueZ over D-Bus (mocked in every test via ``bluetooth_adapters.dbus.MessageBus``)
* a direct HCI socket query, :func:`bluetooth_adapters.systems.linux_hci.get_adapters_from_hci`

The HCI query talks to the kernel's real Bluetooth devices. On a developer
laptop or CI runner that actually has a Bluetooth adapter, that real hardware
leaks into otherwise-fully-mocked tests and breaks assertions about the adapter
set (see issue #118).

The autouse fixture below neutralises the HCI source by default so the suite is
hermetic regardless of the host machine. Tests that need to exercise the HCI
merge path can depend on ``mock_get_adapters_from_hci`` and set its
``return_value``.
"""

from __future__ import annotations

from collections.abc import Iterator
from platform import system
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_get_adapters_from_hci() -> Iterator[MagicMock | None]:
    """Stop tests from picking up the host's real Bluetooth adapters.

    Patches ``get_adapters_from_hci`` (as imported into the Linux systems
    module) to return an empty mapping by default. Tests can override the
    return value to simulate HCI-only adapters.
    """
    if system() == "Windows":
        # The Linux systems module imports D-Bus machinery that is not
        # importable on Windows, and the HCI path is never exercised there.
        yield None
        return
    with patch(
        "bluetooth_adapters.systems.linux.get_adapters_from_hci",
        return_value={},
    ) as mock:
        yield mock
