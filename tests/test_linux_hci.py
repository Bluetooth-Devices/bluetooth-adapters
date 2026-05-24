"""Tests for the raw kernel HCI device query in systems/linux_hci.py.

These exercise ``get_adapters_from_hci`` directly by faking the ``socket`` and
``fcntl`` module references it holds, so the ctypes struct parsing and ioctl
plumbing are covered without any real Bluetooth hardware. This is the code path
that issue #118 exposed as both fragile and untested.
"""

from __future__ import annotations

import ctypes
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from bluetooth_adapters.systems import linux_hci
from bluetooth_adapters.systems.linux_hci import (
    HCIGETDEVINFO,
    HCIGETDEVLIST,
    get_adapters_from_hci,
)


def _make_ioctl(devices: dict[int, tuple[str, list[int]]]):
    """Build a fake ``fcntl.ioctl`` that populates the ctypes buffers.

    ``devices`` maps a device id to ``(name, bdaddr_bytes)`` where
    ``bdaddr_bytes`` is the 6-byte little-endian address as stored by the
    kernel (``bdaddr_t.__str__`` reverses it when rendering).
    """

    def ioctl(_fd: int, request: int, arg: Any) -> int:
        if request == HCIGETDEVLIST:
            arg.dev_num = len(devices)
            for i, dev_id in enumerate(devices):
                arg.dev_req[i].dev_id = dev_id
        elif request == HCIGETDEVINFO:
            name, bdaddr = devices[arg.dev_id]
            arg.name = name.encode()
            arg.bdaddr.b = (ctypes.c_uint8 * 6)(*bdaddr)
        return 0

    return ioctl


def test_get_adapters_from_hci_parses_devices():
    """Two adapters are returned with decoded names and addresses."""
    devices = {
        0: ("hci0", [0x04, 0x71, 0xDA, 0x7D, 0x1A, 0x00]),
        1: ("hci1", [0x05, 0x71, 0xDA, 0x7D, 0x1A, 0x00]),
    }
    fake_fcntl = MagicMock()
    fake_fcntl.ioctl.side_effect = _make_ioctl(devices)

    with (
        patch.object(linux_hci, "fcntl", fake_fcntl),
        patch.object(linux_hci, "socket"),
    ):
        out = get_adapters_from_hci()

    assert set(out) == {0, 1}
    assert out[0]["name"] == "hci0"
    assert out[0]["bdaddr"] == "00:1A:7D:DA:71:04"
    assert out[1]["name"] == "hci1"
    assert out[1]["bdaddr"] == "00:1A:7D:DA:71:05"


def test_get_adapters_from_hci_empty_when_no_devices():
    """No HCI devices yields an empty mapping (and only one ioctl call)."""
    fake_fcntl = MagicMock()
    fake_fcntl.ioctl.side_effect = _make_ioctl({})

    with (
        patch.object(linux_hci, "fcntl", fake_fcntl),
        patch.object(linux_hci, "socket"),
    ):
        out = get_adapters_from_hci()

    assert out == {}
    # Only the device-list ioctl runs; no per-device queries.
    assert fake_fcntl.ioctl.call_count == 1


def test_get_adapters_from_hci_closes_socket():
    """The socket is always closed, even on the happy path."""
    fake_fcntl = MagicMock()
    fake_fcntl.ioctl.side_effect = _make_ioctl({})
    fake_socket_mod = MagicMock()
    sock = fake_socket_mod.socket.return_value

    with (
        patch.object(linux_hci, "fcntl", fake_fcntl),
        patch.object(linux_hci, "socket", fake_socket_mod),
    ):
        get_adapters_from_hci()

    sock.close.assert_called_once()


def test_get_adapters_from_hci_raises_without_fcntl():
    """On platforms without fcntl (Windows) a RuntimeError is raised."""
    with patch.object(linux_hci, "fcntl", None):
        with pytest.raises(RuntimeError, match="fcntl is not available"):
            get_adapters_from_hci()


def test_get_adapters_from_hci_oserror_returns_empty():
    """An OSError from the kernel ioctl is swallowed and returns {}."""
    fake_fcntl = MagicMock()
    fake_fcntl.ioctl.side_effect = OSError("HCIGETDEVLIST failed")

    with (
        patch.object(linux_hci, "fcntl", fake_fcntl),
        patch.object(linux_hci, "socket"),
    ):
        out = get_adapters_from_hci()

    assert out == {}


def test_get_adapters_from_hci_negative_ret_returns_empty():
    """A negative ioctl return (raised as OSError internally) yields {}."""
    fake_fcntl = MagicMock()
    fake_fcntl.ioctl.return_value = -1

    with (
        patch.object(linux_hci, "fcntl", fake_fcntl),
        patch.object(linux_hci, "socket"),
    ):
        out = get_adapters_from_hci()

    assert out == {}


def test_get_adapters_from_hci_unexpected_error_returns_empty():
    """A non-OSError exception is logged and returns {} rather than raising."""
    fake_fcntl = MagicMock()
    fake_fcntl.ioctl.side_effect = ValueError("boom")

    with (
        patch.object(linux_hci, "fcntl", fake_fcntl),
        patch.object(linux_hci, "socket"),
    ):
        out = get_adapters_from_hci()

    assert out == {}


def test_bdaddr_t_str_reverses_bytes():
    """bdaddr_t renders the kernel's little-endian bytes as big-endian text."""
    addr = linux_hci.bdaddr_t()
    addr.b = (ctypes.c_uint8 * 6)(0x04, 0x71, 0xDA, 0x7D, 0x1A, 0x00)
    assert str(addr) == "00:1A:7D:DA:71:04"
