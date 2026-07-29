from collections.abc import Hashable, Iterable, Iterator, Sequence


def chunked[T](items: Sequence[T], size: int) -> Iterator[Sequence[T]]:
    """Iterate over a sequence in fixed-size groups.

    Args:
        items: Sequence to split into groups.
        size: Maximum number of items in each group.

    Yields:
        Consecutive slices of the input sequence.

    Raises:
        ValueError: If size is less than one.
    """
    if size <= 0:
        raise ValueError("size must be greater than zero")

    for start in range(0, len(items), size):
        yield items[start : start + size]


def dedupe_preserving_order[HashableT: Hashable](
    items: Iterable[HashableT],
) -> list[HashableT]:
    """Return unique items in their first-seen order.

    Args:
        items: Iterable containing hashable values.

    Returns:
        A list containing each distinct input value once.
    """
    seen: set[HashableT] = set()
    unique_items: list[HashableT] = []

    for item in items:
        if item not in seen:
            seen.add(item)
            unique_items.append(item)

    return unique_items
