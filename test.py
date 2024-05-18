import asyncio


async def error_on_even(integer: int) -> None:
    if integer % 2 == 0:
        raise ValueError("Even numbers are not allowed!")
    print(f"Received: {integer}")


async def main() -> None:
    error_on_even_tasks = []
    for i in range(10):
        error_on_even_tasks.append(error_on_even(i))
    results = await asyncio.gather(*error_on_even_tasks, return_exceptions=True)
    print(results)


if __name__ == "__main__":
    asyncio.run(main())
