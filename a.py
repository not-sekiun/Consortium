import asyncio


async def yield_with_timeout(timeout):
    queue = asyncio.Queue()

    async def timeout_handler():
        await asyncio.sleep(timeout)
        if queue.empty():
            raise TimeoutError("Timeout")

    async def generator():
        result = yield
        await queue.put(result)
        return await queue.get()

    try:
        result = await asyncio.gather(generator(), timeout_handler())[0]
        print(result)
    except TimeoutError:
        print("Timeout")


asyncio.run(yield_with_timeout(5))  # 5-second timeout
