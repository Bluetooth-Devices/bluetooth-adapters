"""Shared pytest fixtures.

The Linux backend pulls adapter data from two independent sources: BlueZ via
D-Bus (mocked per-test through ``MessageBus``) **and** a direct kernel HCI
socket query (``get_adapters_from_hci``). If a test only stubs the D-Bus side
the kernel query leaks real host adapters into the result — exactly the
failure mode that closed issue #118.

The autouse fixture below stubs ``get_adapters_from_hci`` to return ``{}`` for
every test. Tests that need a non-empty HCI payload can override it with a
nested ``patch(...)`` — the inner patch wins and restores the autouse stub on
exit.
"""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _stub_get_adapters_from_hci() -> Iterator[None]:
    """Prevent the kernel HCI query from leaking real host adapters into tests."""
    with patch(
        "bluetooth_adapters.systems.linux.get_adapters_from_hci",
        return_value={},
    ):
        yield
