import secrets
import string


def generate_token(length: int = 32, generate_as_bytes: bool = False) -> str | bytes:
    """
    Generate cryptographically secure random bytes or their hexadecimal representation.

    Args:
        length:
            Number of random bytes to generate. A hexadecimal string contains twice
            this number of characters. The default is 32.
        generate_as_bytes:
            Whether to return bytes instead of a hexadecimal string. The default is
            ``False``.

    Returns:
        The generated value as either a hexadecimal string or as bytes.
    """

    if generate_as_bytes:
        return secrets.token_bytes(length)
    return secrets.token_hex(length)


def generate_string(
    characters_sample: str = string.ascii_uppercase + string.digits,
    length: int = 32,
) -> str:
    """
    Generate a cryptographically secure random string from a supplied character set.

    Args:
        characters_sample:
            The set of characters to sample from when generating the string. The default
            value is uppercase ASCII letters and digits.
        length:
            Number of characters to generate. The default is 32.

    Returns:
        The generated string.
    """
    return "".join(secrets.choice(characters_sample) for _ in range(length))
