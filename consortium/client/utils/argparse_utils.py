from argparse import ArgumentTypeError


def positive_int(value: str) -> int:
    # argparse type callable that accepts only integers strictly greater than zero.
    # Used for --limit style arguments where zero or negative values are meaningless
    # and would otherwise be rejected server-side with a less helpful error.
    try:
        parsed_value = int(value)
    except ValueError:
        raise ArgumentTypeError(f"'{value}' is not a valid integer.") from None

    if parsed_value <= 0:
        raise ArgumentTypeError(f"'{value}' must be a positive integer greater than 0.")

    return parsed_value
