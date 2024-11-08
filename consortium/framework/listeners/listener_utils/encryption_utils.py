import secrets
import string


def generate_token(length: int = 32, generate_as_bytes: bool = False) -> str | bytes:
    """
    Generate a random token of a particular length using a cryptographically secure
    random number generator as provided by the Python `secrets` module.

    Args:
        length:
            The length of the token to generate. The default length is 32.
        generate_as_bytes:
            Whether to generate the token as bytes or as a hexadecimal string. The
            default value is `False` to generate as a hexadecimal string.

    Returns:
        The generated token as either a hexadecimal string or as bytes.
    """

    if generate_as_bytes:
        return secrets.token_bytes(length)
    return secrets.token_hex(length)


def generate_string(
    characters_sample: str = string.ascii_uppercase + string.digits,
    length: int = 32,
) -> str:
    """
    Generate a random string from a given set of characters using a cryptographically
    secure random number generator as provided by the Python `secrets` module.

    Args:
        characters_sample:
            The set of characters to sample from when generating the string. The default
            value is a set of alphanumeric characters in lowercase.
        length:
            The length of the string to generate. The default length is 32.

    Returns:
        The generated string.
    """
    return "".join(secrets.choice(characters_sample) for _ in range(length))
