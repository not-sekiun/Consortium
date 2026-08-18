import sys

from consortium.framework.agents._bounded_buffer import BoundedBuffer


def _chunk_size(chunk: bytes) -> int:
    # Exact and O(1): a bytes object holds nothing by reference, so getsizeof is its
    # header plus its contents. Unlike a queued message there is no overhead constant to
    # re-derive after a Python upgrade.
    return sys.getsizeof(chunk)


# The buffer behind one declared channel: raw bytes moving between a capability and an
# attached client, with no framing and no interpretation of what the bytes mean. Blocks a
# producer once full (RELIABLE delivery); the drop-oldest and windowed policies land with
# the `delivery` declaration.
class ChannelBuffer(BoundedBuffer[bytes]):
    def __init__(self, maximum_memory_size: int | None = None):
        super().__init__(
            entry_size=_chunk_size,
            maximum_memory_size=maximum_memory_size,
        )

    async def put(
        self,
        chunk: bytes | bytearray,
        # 0 means put without waiting, None means no timeout
        timeout: float | None = None,
    ) -> None:
        # Copied rather than buffered by reference: a bytearray is mutable, so keeping
        # one would let the producer rewrite bytes it has already handed over, and its
        # over-allocated capacity would be charged instead of its contents.
        if type(chunk) is not bytes:
            chunk = bytes(chunk)
        await super().put(entry=chunk, timeout=timeout)
