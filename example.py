import asyncio

from bluetooth_adapters import get_adapters


async def go() -> None:
    bluetooth_adapters = get_adapters()
    await bluetooth_adapters.refresh()
    print(bluetooth_adapters.adapters)


asyncio.run(go())
