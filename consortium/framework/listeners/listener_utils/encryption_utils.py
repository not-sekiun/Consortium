import secrets
import string


def generate_token(length: int = 32, generate_as_bytes: bool = False) -> str | bytes:
    """
    Generate a random value of a particular max_length using a cryptographically secure
    random number generator as provided by the Python `secrets` module.

    Args:
        length:
            The max_length of the value to generate. The default max_length is 32.
        generate_as_bytes:
            Whether to generate the value as bytes or as a hexadecimal string. The
            default value is `False` to generate as a hexadecimal string.

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
    Generate a random string from a given set of characters using a cryptographically
    secure random number generator as provided by the Python `secrets` module.

    Args:
        characters_sample:
            The set of characters to sample from when generating the string. The default
            value is a set of alphanumeric characters in lowercase.
        length:
            The max_length of the string to generate. The default max_length is 32.

    Returns:
        The generated string.
    """
    return "".join(secrets.choice(characters_sample) for _ in range(length))
