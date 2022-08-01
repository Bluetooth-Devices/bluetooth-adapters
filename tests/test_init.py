import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dbus_next import MessageType

import bluetooth_adapters
from bluetooth_adapters import get_bluetooth_adapters


@pytest.mark.asyncio
async def test_get_bluetooth_adapters_file_not_found():
    """Test get_bluetooth_adapters()."""

    class MockMessageBus:
        def __init__(self, *args, **kwargs):
            raise FileNotFoundError

    with patch("bluetooth_adapters.MessageBus", MockMessageBus):
        assert await get_bluetooth_adapters() == []


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
        assert await get_bluetooth_adapters() == []


@pytest.mark.asyncio
async def test_get_bluetooth_adapters_no_call_return():
    class MockMessageBus:
        def __init__(self, *args, **kwargs):
            pass

        async def connect(self):
            return AsyncMock(disconnect=MagicMock(), call=AsyncMock())

        async def call(self):
            return None

    with patch("bluetooth_adapters.MessageBus", MockMessageBus):
        assert await get_bluetooth_adapters() == []


@pytest.mark.asyncio
async def test_get_bluetooth_adapters_times_out():
    async def _stall(*args: Any) -> None:
        await asyncio.sleep(10)

    class MockMessageBus:
        def __init__(self, *args, **kwargs):
            pass

        async def connect(self):
            return AsyncMock(
                disconnect=MagicMock(),
                call=AsyncMock(side_effect=_stall),
            )

    with patch.object(bluetooth_adapters, "REPLY_TIMEOUT", 0), patch(
        "bluetooth_adapters.MessageBus", MockMessageBus
    ):
        assert await get_bluetooth_adapters() == []


@pytest.mark.asyncio
async def test_get_bluetooth_adapters_no_wrong_return():
    class MockMessageBus:
        def __init__(self, *args, **kwargs):
            pass

        async def connect(self):
            return AsyncMock(
                disconnect=MagicMock(),
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
                ),
            )

    with patch("bluetooth_adapters.MessageBus", MockMessageBus):
        assert await get_bluetooth_adapters() == []


@pytest.mark.asyncio
async def test_get_bluetooth_adapters_correct_return_valid_message():
    class MockMessageBus:
        def __init__(self, *args, **kwargs):
            pass

        async def connect(self):
            return AsyncMock(
                disconnect=MagicMock(),
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
                ),
            )

    with patch("bluetooth_adapters.MessageBus", MockMessageBus):
        assert await get_bluetooth_adapters() == ["hci0", "hci1"]
