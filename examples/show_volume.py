"""Basic webOS client example."""
import asyncio

from liblyngdorf import LyngdorfClient

HOST = "192.168.16.16"


async def main():
    """Webos client example."""
    client = LyngdorfClient(HOST)
    await client.async_connect()

    # print(f"state: {client.volume}")

    await asyncio.sleep(10000)

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
