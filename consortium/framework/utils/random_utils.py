import random
import secrets
import string
from typing import Literal


def random_number(start: int, end: int) -> int:
    """Return a cryptographically insecure random integer in an inclusive range.

    Args:
        start: The smallest value that may be returned.
        end: The largest value that may be returned.

    Returns:
        A random integer between start and end, inclusive.
    """
    return random.randint(start, end)


def random_port(exclude_privileged: bool = True) -> int:
    """Return a cryptographically insecure random TCP or UDP port number.

    Args:
        exclude_privileged: Whether to restrict the result to ports 1024 through 65535.

    Returns:
        A random port number.
    """
    if exclude_privileged:
        return random_number(start=1024, end=65535)

    return random_number(start=0, end=65535)


def random_ascii(length: int = 16) -> str:
    """Return a cryptographically secure random ASCII string.

    Args:
        length: Number of characters to generate.

    Returns:
        A string containing ASCII letters, digits, and punctuation.
    """
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return "".join(secrets.choice(alphabet) for _ in range(length))


def random_urlsafe(length: int = 16) -> str:
    """Return a cryptographically secure URL-safe token.

    Args:
        length: Number of random bytes used to create the token.

    Returns:
        A URL-safe token whose character length depends on the encoded byte length.
    """
    return secrets.token_urlsafe(length)


def random_alphanumeric(length: int = 16) -> str:
    """Return a cryptographically secure alphanumeric string.

    Args:
        length: Number of characters to generate.

    Returns:
        A string containing ASCII letters and digits.
    """
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def random_hex(length: int = 16) -> str:
    """Return a cryptographically secure hexadecimal string of an exact length.

    Args:
        length: Number of hexadecimal characters to generate.

    Returns:
        A lowercase hexadecimal string with exactly length characters.
    """
    return secrets.token_hex(length // 2 + length % 2)[:length]


def random_bytes(length: int = 16) -> bytes:
    """Return cryptographically secure random bytes.

    Args:
        length: Number of bytes to generate.

    Returns:
        A byte sequence with exactly length bytes.
    """
    return secrets.token_bytes(length)


def random_name(
    spacing: Literal["whitespace", "underscore", "dash", "dot"] = "whitespace",
    formatting: Literal["upper", "lower", "capitalized"] = "upper",
) -> str:
    """Return a randomly generated color-and-celestial name.

    Args:
        spacing: Separator to place between the two generated words.
        formatting: Letter case to apply to both generated words.

    Returns:
        A name consisting of a random color and celestial term.
    """
    spacing_to_char_map = {
        "whitespace": " ",
        "underscore": "_",
        "dash": "-",
        "dot": ".",
    }
    formatting_to_str_format_func_map = {
        "upper": lambda x: x.upper(),
        "lower": lambda x: x.lower(),
        "capitalized": lambda x: x.capitalize(),
    }
    colors = [
        "AMBER",
        "AMETHYST",
        "BERYL",
        "DIAMOND",
        "EMERALD",
        "JADE",
        "OBSIDIAN",
        "ONYX",
        "OPAL",
        "PERIDOT",
        "QUARTZ",
        "RUBY",
        "SAPPHIRE",
        "TOPAZ",
        "ZIRCON",
        "APRICOT",
        "CERISE",
        "CHERRY",
        "CORAL",
        "HEATHER",
        "INDIGO",
        "IRIS",
        "LAVENDER",
        "LILAC",
        "MARIGOLD",
        "OLIVE",
        "ORCHID",
        "PEACH",
        "ROSE",
        "SAFFRON",
        "SAGE",
        "AZURE",
        "CANARY",
        "CERULEAN",
        "CYAN",
        "FUCHSIA",
        "MAGENTA",
        "SCARLET",
        "TURQUOISE",
        "VERMILION",
        "VIOLET",
        "BRONZE",
        "COPPER",
        "GOLD",
        "IRON",
        "NICKEL",
        "PLATINUM",
        "SILVER",
        "STEEL",
        "TITANIUM",
    ]
    celestials = [
        "ALTAIR",
        "ANTARES",
        "APUS",
        "AQUILA",
        "ARA",
        "ARGO",
        "ARIES",
        "AURIGA",
        "CANCER",
        "CANIS",
        "CARINA",
        "CETUS",
        "CHARA",
        "COLUMBA",
        "CORVUS",
        "CRATER",
        "CRUX",
        "CYGNUS",
        "DELPHINUS",
        "DORADO",
        "DRACO",
        "FORNAX",
        "GEMINI",
        "GRUS",
        "HYDRA",
        "INDUS",
        "LEO",
        "LEPUS",
        "LIBRA",
        "LUPUS",
        "LYRA",
        "MENSA",
        "NORMA",
        "ORION",
        "PAVO",
        "PEGASUS",
        "PERSEUS",
        "PHOENIX",
        "PICTOR",
        "PISCES",
        "PUPPIS",
        "PYXIS",
        "SAGITTA",
        "SERPENS",
        "SIRIUS",
        "TAURUS",
        "TUCANA",
        "URSA",
        "VELA",
        "VIRGO",
    ]

    format_func = formatting_to_str_format_func_map.get(formatting, str.upper)
    rand_color = format_func(random.choice(colors))
    rand_celestial = format_func(random.choice(celestials))
    spacing_char = spacing_to_char_map.get(spacing, " ")

    return f"{rand_color}{spacing_char}{rand_celestial}"
