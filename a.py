import asyncio


async def a():
    yield 1
    await asyncio.sleep(1)
    x = yield
    print(x)
    await asyncio.sleep(1)
    yield 2


async def main():
    async for message in a():
        print(message)


asyncio.run(main())
