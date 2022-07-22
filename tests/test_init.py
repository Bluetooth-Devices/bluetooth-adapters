from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dbus_next import MessageType

from bluetooth_adapters import get_bluetooth_adapters


@pytest.mark.asyncio
async def test_get_bluetooth_adapters_file_not_found():
    """Test get_bluetooth_adapters()."""

    class MockMessageBus:
        def __init__(self, *args, **kwargs):
            raise FileNotFoundError

    with patch("bluetooth_adapters.MessageBus", MockMessageBus):
        assert await get_bluetooth_adapters() == set()


@pytest.mark.asyncio
async def test_get_bluetooth_adapters_connect_fails():
    class MockMessageBus:
        def __init__(self, *args, **kwargs):
            pass

        async def connect(self):
            raise FileNotFoundError

        async def call(self):
            return None

    with patch("bluetooth_adapters.MessageBus", MockMessageBus):
        assert await get_bluetooth_adapters() == set()


@pytest.mark.asyncio
async def test_get_bluetooth_adapters_no_call_return():
    class MockMessageBus:
        def __init__(self, *args, **kwargs):
            pass

        async def connect(self):
            return AsyncMock()

        async def call(self):
            return None

    with patch("bluetooth_adapters.MessageBus", MockMessageBus):
        assert await get_bluetooth_adapters() == set()


@pytest.mark.asyncio
async def test_get_bluetooth_adapters_no_wrong_return():
    class MockMessageBus:
        def __init__(self, *args, **kwargs):
            pass

        async def connect(self):
            return AsyncMock(
                call=AsyncMock(
                    return_value=MagicMock(
                        body=[
                            {
                                "/org/bluez/hci0": "",
                                "/org/bluez/hci1": "",
                                "/org/bluez/hci1/any": "",
                            }
                        ],
                        message_type="wrong",
                    )
                )
            )

        async def disconnect(self):
            pass

    with patch("bluetooth_adapters.MessageBus", MockMessageBus):
        assert await get_bluetooth_adapters() == set()


@pytest.mark.asyncio
async def test_get_bluetooth_adapters_correct_return_valid_message():
    class MockMessageBus:
        def __init__(self, *args, **kwargs):
            pass

        async def connect(self):
            return AsyncMock(
                call=AsyncMock(
                    return_value=MagicMock(
                        body=[
                            {
                                "/other": "",
                                "/org/bluez/hci0": "",
                                "/org/bluez/hci1": "",
                                "/org/bluez/hci1/any": "",
                            }
                        ],
                        message_type=MessageType.METHOD_RETURN,
                    )
                )
            )

        async def disconnect(self):
            pass

    with patch("bluetooth_adapters.MessageBus", MockMessageBus):
        assert await get_bluetooth_adapters() == {"hci0", "hci1"}
