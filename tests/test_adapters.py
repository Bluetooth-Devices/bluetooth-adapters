"""Tests for the BluetoothAdapters abstract base class."""

import pytest

from bluetooth_adapters.adapters import BluetoothAdapters
from bluetooth_adapters.models import AdapterDetails


class CompleteAdapters(BluetoothAdapters):
    """A subclass that implements every abstract member."""

    @property
    def adapters(self):
        return {"hci0": AdapterDetails(address="00:11:22:33:44:55")}

    @property
    def default_adapter(self):
        return "hci0"


class MissingDefaultAdapter(BluetoothAdapters):
    """A subclass that forgets to implement default_adapter."""

    @property
    def adapters(self):
        return {}


def test_base_class_cannot_be_instantiated():
    """The base class is abstract and must not be instantiable."""
    with pytest.raises(TypeError):
        BluetoothAdapters()  # type: ignore[abstract]


def test_incomplete_subclass_cannot_be_instantiated():
    """A subclass missing an abstract member stays abstract."""
    with pytest.raises(TypeError):
        MissingDefaultAdapter()  # type: ignore[abstract]


def test_complete_subclass_can_be_instantiated():
    """A subclass implementing every abstract member instantiates cleanly."""
    adapters = CompleteAdapters()
    assert adapters.adapters == {"hci0": AdapterDetails(address="00:11:22:33:44:55")}
    assert adapters.default_adapter == "hci0"


@pytest.mark.asyncio
async def test_concrete_defaults_on_subclass():
    """refresh() and history have usable concrete defaults from the base."""
    adapters = CompleteAdapters()
    await adapters.refresh()
    assert adapters.history == {}
